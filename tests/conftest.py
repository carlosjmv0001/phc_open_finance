import pytest  
import docker  
import time  
import os  
from src.config import ISSUER_URL, HOLDER_URL, VERIFIER_URL  
  
@pytest.fixture(scope="session")  
def docker_compose():  
    """Ensure docker-compose is running."""  
    # Skip Docker check in Codespaces environments  
    if os.getenv("CODESPACES"):  
        yield  
        return  
  
    try:  
        client = docker.from_env()  
  
        # Check that containers are running  
        containers = ["agent-issuer", "agent-holder", "agent-verifier", "tails-server"]  
  
        for container in containers:  
            try:  
                c = client.containers.get(container)  
                if c.status != "running":  
                    raise Exception(f"Container {container} is not running")  
            except docker.errors.NotFound:  
                raise Exception(f"Container {container} not found")  
  
        # Wait for agents to be ready  
        time.sleep(5)  
        yield  
  
    except docker.errors.DockerException:  
        # If Docker is unavailable, assume containers are already running  
        yield  
    except Exception as e:  
        print(f"Warning: {e}")  
        yield  
  
@pytest.fixture  
def mock_state_file(tmp_path):  
    """Create a temporary state file."""  
    state_file = tmp_path / "test_state.json"  
    import src.utils  
    original_state_file = src.utils.STATE_FILE  
    src.utils.STATE_FILE = str(state_file)  
    yield str(state_file)  
    src.utils.STATE_FILE = original_state_file