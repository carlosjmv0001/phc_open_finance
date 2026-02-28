import requests  
import time  
from .config import ISSUER_URL, HOLDER_URL, VERIFIER_URL  
from .utils import save_state  
  
def connect_agents(inviter_url, invitee_url, alias_inviter, alias_invitee):  
    print(f"--- Connecting {alias_inviter} -> {alias_invitee} ---")  
  
    # 1. Create invitation  
    invite = requests.post(f"{inviter_url}/out-of-band/create-invitation",  
                           json={"alias": alias_inviter, "handshake_protocols": ["https://didcomm.org/didexchange/1.0"]}).json()  
  
    # 2. Accept invitation  
    requests.post(f"{invitee_url}/out-of-band/receive-invitation",  
                  json=invite["invitation"],  
                  params={"alias": alias_invitee})  
  
    print("   Invitation accepted. Awaiting synchronization...")  
    time.sleep(3)  # Time for handshake  
  
def main():  
    print("### 1. ESTABLISHING CONNECTIONS ###")  
  
    # Government <-> Bot  
    connect_agents(ISSUER_URL, HOLDER_URL, "Connection_Gov_Bot", "Connection_Bot_Gov")  
  
    # Bank <-> Bot  
    connect_agents(VERIFIER_URL, HOLDER_URL, "Connection_Bank_Bot", "Connection_Bot_Bank")  
  
    print("Connections established.")  
  
if __name__ == "__main__":  
    main()