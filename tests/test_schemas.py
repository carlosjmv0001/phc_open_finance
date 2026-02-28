import pytest  
from pydantic import ValidationError  
from src.schemas import CredentialAttributes, ProofRequest  
  
@pytest.mark.unit  
class TestCredentialAttributes:  
    def test_valid_attributes(self):  
        attrs = CredentialAttributes(  
            person_hash="valid-hash-123",  
            biometric_score="85.5",  
            controller_did="did:sov:abc123def456"  
        )  
        assert attrs.person_hash == "valid-hash-123"  
        assert attrs.biometric_score == "85.5"  
  
    def test_invalid_biometric_score(self):  
        with pytest.raises(ValidationError):  
            CredentialAttributes(  
                person_hash="valid-hash",  
                biometric_score="150.0",  # Above 100  
                controller_did="did:sov:abc123"  
            )  
  
    def test_invalid_did_format(self):  
        with pytest.raises(ValidationError):  
            CredentialAttributes(  
                person_hash="valid-hash",  
                biometric_score="75.0",  
                controller_did="invalid-did"  
            )  
  
    def test_short_person_hash(self):  
        with pytest.raises(ValidationError):  
            CredentialAttributes(  
                person_hash="short",  # Less than 8 chars  
                biometric_score="75.0",  
                controller_did="did:sov:abc123"  
            )  
  
@pytest.mark.unit  
class TestProofRequest:  
    def test_valid_proof_request(self):  
        proof = ProofRequest(  
            connection_id="valid-connection-id-123",  
            presentation_request={"test": "data"}  
        )  
        assert proof.connection_id == "valid-connection-id-123"  
  
    def test_invalid_connection_id(self):  
        with pytest.raises(ValidationError):  
            ProofRequest(  
                connection_id="short",  # Too short  
                presentation_request={"test": "data"}  
            )