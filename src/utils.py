import json  
import os  
from .config import STATE_FILE  
  
def load_state():  
    if not os.path.exists(STATE_FILE):  
        return {}  
    with open(STATE_FILE, 'r') as f:  
        return json.load(f)  
  
def save_state(key, value):  
    data = load_state()  
    data[key] = value  
    with open(STATE_FILE, 'w') as f:  
        json.dump(data, f, indent=4)  
    print(f"   [State] '{key}' saved.")  
  
def get_connection_id(agent_url, alias_filter):  
    """Fetch active connection ID by alias."""  
    import requests  
    resp = requests.get(f"{agent_url}/connections", params={"alias": alias_filter, "state": "active"})  
    results = resp.json()['results']  
    if results:  
        return results[0]['connection_id']  
    return None