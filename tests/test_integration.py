import pytest  
import requests  
import time  
import os  
import requests_mock  
import subprocess  
import sys  
from unittest.mock import patch  
from src.config import ISSUER_URL, HOLDER_URL, VERIFIER_URL  
from src.utils import load_state, save_state, get_connection_id  
from src.retry import retry_with_backoff  
  
@pytest.mark.integration  
class TestCredentialFlow:  
    """Test the complete credential flow."""  
  
    @pytest.fixture(autouse=True)  
    def setup(self, docker_compose):  
        """Setup for all integration tests."""  
        # Clean previous state  
        if os.path.exists("system_state.json"):  
            os.remove("system_state.json")  
  
        # Establish connections before tests  
        from src.setup_connections import main  
        main()  
  
    def test_issuer_setup(self):  
        """Test issuer configuration."""  
        from src.issuer_setup import main  
  
        # Fetch the issuer's current DID  
        did_resp = requests.get(f"{ISSUER_URL}/wallet/did/public")  
        if did_resp.status_code == 200:  
            issuer_did = did_resp.json()['result']['did']  
        else:  
            pytest.skip("Issuer has no public DID")  
  
        # Check if schema already exists in local state  
        state = load_state()  
        if "schema_id" in state:  
            # Schema already exists locally, just verify on ledger  
            schema_id = state["schema_id"]  
            resp = requests.get(f"{ISSUER_URL}/anoncreds/schema/{schema_id}")  
            assert resp.status_code == 200  
        else:  
            # Try to run setup, but catch SystemExit if schema already exists on ledger  
            try:  
                main()  
            except SystemExit:  
                # Schema already exists on ledger - ignore error  
                pass  
  
            # Reload state after setup attempt  
            state = load_state()  
  
            # If still no schema_id, fetch from ledger by current DID  
            if "schema_id" not in state:  
                # Fetch existing schemas on ledger for this issuer  
                resp = requests.get(f"{ISSUER_URL}/anoncreds/schemas",  
                                params={"schema_issuer_id": issuer_did,  
                                        "schema_name": "personhood_credential_revocable",  
                                        "schema_version": "2.0"})  
                if resp.status_code == 200 and resp.json()["schema_ids"]:  
                    schema_id = resp.json()["schema_ids"][0]  
                    save_state("schema_id", schema_id)  
                    state = load_state()  
  
            # Verify schema on ledger  
            if "schema_id" in state:  
                schema_id = state["schema_id"]  
                resp = requests.get(f"{ISSUER_URL}/anoncreds/schema/{schema_id}")  
                assert resp.status_code == 200  
  
        # Fetch cred_def_id if not in state  
        if "cred_def_id" not in state and "schema_id" in state:  
            # Fetch credential definitions by schema_id  
            resp = requests.get(f"{ISSUER_URL}/anoncreds/credential-definitions",  
                            params={"schema_id": state["schema_id"]})  
            if resp.status_code == 200 and resp.json()["credential_definition_ids"]:  
                cred_def_id = resp.json()["credential_definition_ids"][0]  
                save_state("cred_def_id", cred_def_id)  
                state = load_state()  
  
        # Verify cred def on ledger if exists  
        if "cred_def_id" in state:  
            cred_def_id = state["cred_def_id"]  
            resp = requests.get(f"{ISSUER_URL}/anoncreds/credential-definition/{cred_def_id}")  
            assert resp.status_code == 200  
  
        # Verify saved state  
        assert "schema_id" in state  
        assert "cred_def_id" in state  
  
    def test_credential_issuance(self):  
        """Test credential issuance."""  
        # Fetch the issuer's current DID  
        did_resp = requests.get(f"{ISSUER_URL}/wallet/did/public")  
        if did_resp.status_code == 200:  
            issuer_did = did_resp.json()['result']['did']  
        else:  
            pytest.skip("Issuer has no public DID")  
  
        # First check if setup was already done  
        state = load_state()  
        if "schema_id" not in state or "cred_def_id" not in state:  
            # Try to run setup, but catch SystemExit if schema already exists  
            try:  
                from src.issuer_setup import main  
                main()  
            except SystemExit:  
                # Schema already exists on ledger, load state  
                state = load_state()  
                # Fetch schema_id and cred_def_id from ledger if not in state  
                if "schema_id" not in state:  
                    resp = requests.get(f"{ISSUER_URL}/anoncreds/schemas",  
                                    params={"schema_issuer_id": issuer_did,  
                                            "schema_name": "personhood_credential_revocable",  
                                            "schema_version": "2.0"})  
                    if resp.status_code == 200 and resp.json()["schema_ids"]:  
                        schema_id = resp.json()["schema_ids"][0]  
                        save_state("schema_id", schema_id)  
  
                if "cred_def_id" not in state:  
                    state = load_state()  
                    if "schema_id" in state:  
                        resp = requests.get(f"{ISSUER_URL}/anoncreds/credential-definitions",  
                                        params={"schema_id": state["schema_id"]})  
                        if resp.status_code == 200 and resp.json()["credential_definition_ids"]:  
                            cred_def_id = resp.json()["credential_definition_ids"][0]  
                            save_state("cred_def_id", cred_def_id)  
  
        # Then issue credential  
        from src.issue_cred import main  
        main()  
  
        # Verify credential in holder  
        resp = requests.get(f"{HOLDER_URL}/credentials")  
        assert resp.status_code == 200  
        creds = resp.json()["results"]  
        assert len(creds) > 0  
  
        # Verify credential attributes  
        cred = creds[0]  
        assert "person_hash" in cred["attrs"]  
        assert "biometric_score" in cred["attrs"]  
  
    def test_proof_verification(self):  
        """Test proof verification."""  
        # Run previous steps  
        from src.issuer_setup import main  
        from src.issue_cred import main  
        main()  
        main()  
  
        # Verify proof  
        from src.verifier_proof import main  
        main()  
  
        # If we reach here without exception, proof was verified  
  
    def test_proof_verification_flow(self, docker_compose):  
        """Test complete proof verification flow"""  
        # Setup  
        from src.issuer_setup import main as setup_main  
        from src.issue_cred import main as cred_main  
        from src.verifier_proof import main as verify_main  
  
        # Run setup only once  
        try:  
            setup_main()  
        except SystemExit:  
            pass  
  
        # CLEAR EXISTING CREDENTIALS (same as revocation test)  
        print("   Clearing existing credentials...")  
        creds_resp = requests.get(f"{HOLDER_URL}/credentials")  
        if creds_resp.status_code == 200:  
            existing_creds = creds_resp.json()['results']  
            for cred in existing_creds:  
                cred_id = cred['referent']  
                delete_resp = requests.delete(f"{HOLDER_URL}/credential/{cred_id}")  
                if delete_resp.status_code != 200:  
                    print(f"   ⚠️ Failed to delete credential {cred_id}: {delete_resp.status_code}")  
            print(f"   Removed {len(existing_creds)} old credentials.")  
  
        # Issue credential specific to this test  
        cred_main()  
  
        # Capture stdout of verification  
        from io import StringIO  
        import sys  
  
        old_stdout = sys.stdout  
        sys.stdout = captured_output = StringIO()  
  
        try:  
            verify_main()  
            output = captured_output.getvalue()  
        finally:  
            sys.stdout = old_stdout  
  
        assert "🟢 STATUS: VALID" in output 
  
    def test_revoked_proof_verification(self, docker_compose):  
        """Test that revoked credentials are rejected"""  
        # Setup  
        from src.issuer_setup import main as setup_main  
        from src.issue_cred import main as cred_main  
        from src.revoke_cred import main as revoke_main  
        from src.verifier_proof import main as verify_main  
  
        # Run setup only once  
        try:  
            setup_main()  
        except SystemExit:  
            pass  
  
        # CLEAR EXISTING CREDENTIALS  
        print("   Clearing existing credentials...")  
        creds_resp = requests.get(f"{HOLDER_URL}/credentials")  
        if creds_resp.status_code == 200:  
            existing_creds = creds_resp.json()['results']  
            for cred in existing_creds:  
                cred_id = cred['referent']  
                delete_resp = requests.delete(f"{HOLDER_URL}/credential/{cred_id}")  
                if delete_resp.status_code != 200:  
                    print(f"   ⚠️ Failed to delete credential {cred_id}: {delete_resp.status_code}")  
            print(f"   Removed {len(existing_creds)} old credentials.")  
  
            # Verify it was actually cleared  
            time.sleep(1)  
            final_check = requests.get(f"{HOLDER_URL}/credentials")  
            if final_check.status_code == 200:  
                remaining = len(final_check.json()['results'])  
                print(f"   ✅ Check: Bot now has {remaining} credential(s).")  
  
        # Issue credential specific to revocation  
        cred_main()  
  
        # Revoke the issued credential  
        revoke_main()  
  
        # WAIT FOR REVOCATION SYNC ON LEDGER  
        print("   Waiting for revocation sync on ledger...")  
        time.sleep(10)  
  
        # Capture stdout of verification  
        from io import StringIO  
        import sys  
  
        old_stdout = sys.stdout  
        sys.stdout = captured_output = StringIO()  
  
        try:  
            verify_main()  
            output = captured_output.getvalue()  
        finally:  
            sys.stdout = old_stdout  
  
        assert "🔴 STATUS: INVALID / REVOKED" in output 
  
@pytest.mark.integration  
class TestErrorScenarios:  
    """Test error scenarios."""  
  
    def test_missing_did(self):  
        """Test error when DID is not registered."""  
        # Simulate no public DID  
        with requests_mock.Mocker() as m:  
            m.get(f"{ISSUER_URL}/wallet/did/public", status_code=404)  
  
            from src.issuer_setup import main  
  
            # Should return without error, but print message  
            main()  
  
    def test_missing_cred_def(self):  
        """Test error when cred_def_id is not found."""  
        # Clear state  
        if os.path.exists("system_state.json"):  
            os.remove("system_state.json")  
  
        from src.issue_cred import main  
  
        # Should return without error, but print message  
        main()  
  
    def test_existing_schema_handling(self):  
        """Test handling of existing schema"""  
        with patch('requests.post') as mock_post:  
            # Simulate schema already exists  
            mock_post.return_value.status_code = 409  
            mock_post.return_value.text = "Schema already exists"  
  
            # Should fetch existing schema instead of failing  
            with patch('requests.get') as mock_get:  
                mock_get.return_value.status_code = 200  
                mock_get.return_value.json.return_value = {  
                    "schema_ids": ["test-schema-id"]  
                }  
  
                # Should not execute sys.exit  
                from src.issuer_setup import main  
                # Test should pass without exception  
                main()  # If no exception is raised, test passes  
  
@pytest.mark.integration  
class TestRetryMechanism:  
    """Test the retry mechanism."""  
  
    def test_retry_decorator_success(self):  
        """Test retry succeeding on first attempt."""  
        @retry_with_backoff(max_attempts=3, initial_delay=0.01)  
        def success_func():  
            return "success"  
  
        assert success_func() == "success"  
  
    def test_retry_then_success(self):  
        """Test retry that fails then succeeds."""  
        from unittest.mock import Mock  
  
        mock_func = Mock(side_effect=[Exception("fail"), "success"])  
  
        @retry_with_backoff(max_attempts=3, initial_delay=0.01)  
        def test_func():  
            return mock_func()  
  
        with patch('time.sleep'):  # Skip sleep in tests  
            assert test_func() == "success"  
            assert mock_func.call_count == 2  
  
    def test_retry_max_attempts_reached(self):  
        """Test retry reaching max attempts."""  
        @retry_with_backoff(max_attempts=2, initial_delay=0.01)  
        def always_fail():  
            raise Exception("always fails")  
  
        with patch('time.sleep'):  
            with pytest.raises(Exception, match="always fails"):  
                always_fail()