import pytest  
import requests  
from unittest.mock import patch  
from src.issue_cred import send_credential_offer, main  
  
@pytest.mark.error  
def test_network_error_on_offer():  
    """Test network failure when sending offer"""  
    with patch('requests.post', side_effect=requests.ConnectionError("Network error")):  
        with pytest.raises(requests.ConnectionError):  
            send_credential_offer({"test": "payload"})  
  
@pytest.mark.error  
def test_api_error_response():  
    """Test API error response"""  
    with patch('requests.post') as mock_post:  
        mock_post.return_value.status_code = 500  
        mock_post.return_value.text = "Internal Server Error"  
  
        # Should raise HTTPError for 500 error  
        with pytest.raises(requests.HTTPError, match="Status: 500"):  
            send_credential_offer({"test": "payload"})  
  
@pytest.mark.error  
def test_connection_not_found():  
    """Test when connection is not found"""  
    with patch('src.issue_cred.get_connection_id', return_value=None):  
        main()  # Should return early  
  
@pytest.mark.error  
def test_holder_no_credentials():  
    """Test when Holder receives no credentials"""  
    with patch('src.issue_cred.get_connection_id', return_value="test-conn"), \
         patch('src.issue_cred.load_state', return_value={"cred_def_id": "test"}), \
         patch('requests.post'), \
         patch('requests.get') as mock_get:  
  
        # Simulate no credentials  
        mock_get.return_value.json.return_value = {"results": []}  
  
        main()  # Should handle error gracefully