import pytest  
import json  
import os  
import requests_mock  
import requests  
from src.utils import load_state, save_state, get_connection_id  
from src.config import ISSUER_URL, HOLDER_URL, VERIFIER_URL  
  
@pytest.mark.unit  
def test_load_state_empty(mock_state_file):  
    """Test loading state when file does not exist."""  
    assert load_state() == {}  
  
@pytest.mark.unit  
def test_save_and_load_state(mock_state_file):  
    """Test saving and loading state."""  
    # Save state  
    save_state("test_key", "test_value")  
  
    # Verify file was created  
    assert os.path.exists(mock_state_file)  
  
    # Load and verify  
    state = load_state()  
    assert state["test_key"] == "test_value"  
  
@pytest.mark.unit  
def test_save_state_overwrite(mock_state_file):  
    """Test overwriting existing state."""  
    save_state("key1", "value1")  
    save_state("key2", "value2")  
  
    state = load_state()  
    assert state["key1"] == "value1"  
    assert state["key2"] == "value2"  
  
@pytest.mark.unit  
def test_get_connection_id_success():  
    """Test fetching connection ID successfully."""  
    with requests_mock.Mocker() as m:  
        m.get(  
            f"{ISSUER_URL}/connections",  
            json={  
                "results": [  
                    {  
                        "connection_id": "conn-123",  
                        "alias": "test_alias",  
                        "state": "active"  
                    }  
                ]  
            }  
        )  
  
        conn_id = get_connection_id(ISSUER_URL, "test_alias")  
        assert conn_id == "conn-123"  
  
@pytest.mark.unit  
def test_get_connection_id_not_found():  
    """Test fetching connection ID when not found."""  
    with requests_mock.Mocker() as m:  
        m.get(  
            f"{ISSUER_URL}/connections",  
            json={"results": []}  
        )  
  
        conn_id = get_connection_id(ISSUER_URL, "nonexistent")  
        assert conn_id is None  
  
@pytest.mark.error  
def test_get_connection_id_api_error():  
    """Test fetching connection ID with API error."""  
    with requests_mock.Mocker() as m:  
        m.get(  
            f"{ISSUER_URL}/connections",  
            status_code=500  
        )  
  
        with pytest.raises(requests.exceptions.RequestException):  
            get_connection_id(ISSUER_URL, "test_alias")