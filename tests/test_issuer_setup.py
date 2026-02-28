import pytest  
import requests  
from unittest.mock import patch  
from src.issuer_setup import main  
  
@pytest.mark.error  
def test_schema_already_exists():  
    """Test handling when schema already exists on ledger"""  
    with patch('requests.post') as mock_post, \
         patch('requests.get') as mock_get:  
  
        # Simulate schema already exists (409)  
        mock_post.return_value.status_code = 409  
        mock_post.return_value.text = "Schema already exists"  
  
        # Mock fetch of existing schema  
        mock_get.return_value.status_code = 200  
        mock_get.return_value.json.return_value = {  
            "schema_ids": ["test-schema-id"]  
        }  
  
        # Should not execute sys.exit  
        main()  # If no exception is raised, test passes  
  
@pytest.mark.error  
def test_cred_def_already_exists():  
    """Test handling when cred_def already exists"""  
    with patch('requests.post') as mock_post, \
         patch('requests.get') as mock_get:  
  
        # Schema created successfully  
        mock_post.side_effect = [  
            # First call (schema) - success  
            type('Mock', (), {'status_code': 200})(),  
            # Second call (cred_def) - already exists  
            type('Mock', (), {'status_code': 409})()  
        ]  
  
        # Mock fetch of existing cred_def  
        mock_get.return_value.status_code = 200  
        mock_get.return_value.json.return_value = {  
            "credential_definition_ids": ["test-cred-def-id"]  
        }  
  
        main()  # Should handle existing cred_def  
  
@pytest.mark.error  
def test_did_not_registered():  
    """Test error when DID is not registered"""  
    with patch('requests.get') as mock_get:  
        mock_get.return_value.status_code = 404  
  
        main()  # Should return without error


