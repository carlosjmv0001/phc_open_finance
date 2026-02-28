from behave import given, when, then  
import requests  
import time  
import sys  
from io import StringIO  
from src.config import ISSUER_URL, HOLDER_URL, VERIFIER_URL  
from src.utils import load_state, save_state  
  
def _run_verifier_and_capture():  
    """Run verifier_proof.main and capture its stdout."""  
    from src.verifier_proof import main  
    old_stdout = sys.stdout  
    sys.stdout = buf = StringIO()  
    try:  
        main()  
    finally:  
        sys.stdout = old_stdout  
    return buf.getvalue()  
  
@given("the agents are running")  
def step_agents_running(context):  
    """Checks that all agents are reachable."""  
    for url in [ISSUER_URL, HOLDER_URL, VERIFIER_URL]:  
        resp = requests.get(f"{url}/status")  
        assert resp.status_code == 200  
  
@given("the connections are established")  
def step_connections_established(context):  
    """Checks that connections are active."""  
    from src.utils import get_connection_id  
  
    conn_id = get_connection_id(ISSUER_URL, "Connection_Gov_Bot")  
    assert conn_id is not None  
  
    conn_id = get_connection_id(VERIFIER_URL, "Connection_Bank_Bot")  
    assert conn_id is not None  
  
@when("the Government issues a personhood credential")  
def step_issue_credential(context):  
    """Executes credential issuance."""  
    # Clear existing credentials on the Holder to ensure a fresh one is used  
    print("[BDD] Clearing existing credentials on Holder...")  
    creds_resp = requests.get(f"{HOLDER_URL}/credentials")  
    if creds_resp.status_code == 200:  
        existing = creds_resp.json()["results"]  
        for cred in existing:  
            cred_id = cred["referent"]  
            delete_resp = requests.delete(f"{HOLDER_URL}/credential/{cred_id}")  
            if delete_resp.status_code != 200:  
                print(f"   ⚠️ Failed to delete credential {cred_id}: {delete_resp.status_code}")  
        if existing:  
            print(f"   Removed {len(existing)} old credential(s).")  
            time.sleep(1)  # Allow agent to settle  
    # Issue fresh credential  
    from src.issuer_setup import main as setup_main  
    from src.issue_cred import main as cred_main  
    setup_main()  
    cred_main()  
  
@then("the Bot stores the credential")  
def step_credential_stored(context):  
    """Verifies the credential was stored."""  
    resp = requests.get(f"{HOLDER_URL}/credentials")  
    creds = resp.json()["results"]  
    assert len(creds) > 0  
  
@when("the Bank requests proof of personhood")  
def step_request_proof(context):  
    """Requests proof of personhood."""  
    import time  
    time.sleep(2)  # Allow credential to settle  
    context.verification_output = _run_verifier_and_capture()  
    # Debug: show captured output if the expected string is missing  
    if "🟢 STATUS: VALID" not in context.verification_output:  
        print("[DEBUG] Captured verifier output:\n" + context.verification_output)  
  
@then("the Bot presents a valid proof")  
def step_proof_valid(context):  
    """Verifies the proof was valid."""  
    output = getattr(context, "verification_output", "")  
    assert "🟢 STATUS: VALID" in output, f"Verifier output did not contain VALID status. Captured:\n{output}" 
  
@then("the Bank grants access")  
def step_access_granted(context):  
    """Verifies access was granted."""  
    output = getattr(context, "verification_output", "")  
    assert "🟢 STATUS: VALID" in output  
  
@when("the Government revokes the credential")  
def step_revoke_credential(context):  
    """Executes revocation."""  
    from src.revoke_cred import main  
    main()  
  
@then(u'the Bot cannot present a valid proof')  
def step_proof_invalid(context):  
    """Verifies that proof fails after revocation."""  
    output = _run_verifier_and_capture()  
    assert "🔴 STATUS: INVALID / REVOKED" in output  
  
@given(u'the Bot has a valid credential')  
def step_impl(context):  
    """Ensures the Bot has an issued credential."""  
    from src.issue_cred import main  
    main()  
  
@when(u'the Bank requests a new proof')  
def step_impl(context):  
    """Bank requests proof after revocation."""  
    context.proof_output = _run_verifier_and_capture()  
  
@then(u'the Bank denies access')  
def step_impl(context):  
    """Verifies that access was denied."""  
    output = getattr(context, "proof_output", "")  
    assert "🔴 STATUS: INVALID / REVOKED" in output  
  
@given(u'the Government has no public DID')  
def step_impl(context):  
    """Removes the issuer's public DID."""  
    state = load_state()  
    if "public_did" in state:  
        context.original_did = state["public_did"]  
        del state["public_did"]  
        save_state("public_did", None)  
    else:  
        context.original_did = None  
  
@when(u'it tries to issue a credential')  
def step_impl(context):  
    """Tries to issue a credential and captures error."""  
    from unittest.mock import patch  
    import sys  
    from io import StringIO  
    old_stdout = sys.stdout  
    sys.stdout = buf = StringIO()  
    context.setup_error = None  
    try:  
        with patch('requests.get') as mock_get:  
            mock_get.return_value.status_code = 404  
            mock_get.return_value.json.return_value = {}  
            from src.issuer_setup import main as setup_main  
            setup_main()  
    except SystemExit as e:  
        context.setup_error = "SystemExit when issuing without DID"  
    except Exception as e:  
        context.setup_error = str(e)  
    finally:  
        sys.stdout = old_stdout  
        output = buf.getvalue()  
        if "ERROR: Issuer has no Public DID." in output and not context.setup_error:  
            context.setup_error = "Issuer has no Public DID"
  
@then(u'the process fails with an appropriate error')  
def step_impl(context):  
    """Verifies the process failed as expected."""  
    assert context.setup_error is not None  
    import src.issuer_setup  
    src.issuer_setup.ISSUER_DID = context.original_did  
  
@given(u'the Tails Server is offline')  
def step_impl(context):  
    """Simulates tails server offline."""  
    import os  
    context.tails_stopped = False  
    if os.getenv("CODESPACES"):  
        print("Skipping Docker test in Codespaces")  
        return  
    try:  
        import docker  
        client = docker.from_env()  
        container = client.containers.get("phc_open_finance-tails-server-1")  
        container.stop()  
        context.tails_stopped = True  
    except:  
        print("Could not stop tails server")  
  
@when(u'trying to create a revocable credential')  
def step_impl(context):  
    """Tries to create a revocable credential and captures error."""  
    try:  
        state = load_state()  
        if "cred_def_id" in state:  
            resp = requests.post(  
                f"{ISSUER_URL}/anoncreds/revocation-registry-definition",  
                json={  
                    "cred_def_id": state["cred_def_id"],  
                    "issuer_id": "JHwVxCXyxk49hhXS3DQxxy",  
                    "tag": "test_rev",  
                    "max_cred_num": 100  
                }  
            )  
            context.setup_error = None if resp.status_code == 200 else f"Error: {resp.text}"  
        else:  
            context.setup_error = "cred_def_id not found"  
    except Exception as e:  
        context.setup_error = str(e)  
  
@then(u'the process fails or continues without revocation')  
def step_impl(context):  
    """Verifies behavior when tails server is offline."""  
    import os  
    if getattr(context, 'tails_stopped', False) is False and os.getenv("CODESPACES"):  
        return  
    if context.setup_error:  
        assert "tails" in str(context.setup_error).lower() or "revocation" in str(context.setup_error).lower()  
    if getattr(context, 'tails_stopped', False):  
        import docker  
        client = docker.from_env()  
        container = client.containers.get("phc_open_finance-tails-server-1")  
        container.start()  
        time.sleep(5)