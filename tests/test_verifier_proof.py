import pytest  
import requests  
from unittest.mock import patch, Mock  
from src.verifier_proof import send_proof_request  
  
@pytest.mark.verification  
def test_send_proof_request():  
    """Test sending proof request"""  
    # Mock connection  
    with patch('src.verifier_proof.get_connection_id') as mock_conn:  
        mock_conn.return_value = "test-connection-id"  
  
        # Test successful request  
        with patch('requests.post') as mock_post:  
            mock_post.return_value.status_code = 200  
            mock_post.return_value.json.return_value = {"pres_ex_id": "test-id"}  
  
            result = send_proof_request("test-connection-id", "test-cred-def-id")  
            assert result is not None  
  
@pytest.mark.error  
def test_send_proof_request_api_error():  
    """Test API error"""  
    with patch('requests.post') as mock_post:  
        mock_post.return_value.status_code = 500  
        mock_post.return_value.text = "Internal Server Error"  
  
        result = send_proof_request("test-connection-id", "test-cred-def-id")  
        assert result is None  
  
@pytest.mark.error  
def test_send_proof_request_connection_not_found():  
    """Test when connection is not found"""  
    with patch('src.verifier_proof.get_connection_id') as mock_conn:  
        mock_conn.return_value = None  
  
        result = send_proof_request(None, "test-cred-def-id")  
        assert result is None