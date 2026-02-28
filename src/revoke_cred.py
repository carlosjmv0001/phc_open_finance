import requests  
import json  
import sys  
import time  
from .config import ISSUER_URL, HOLDER_URL  
from .utils import load_state, save_state  
  
def main():  
    print("### 5. REVOKING CREDENTIAL (ANONCREDS MANUAL) ###")  
  
    # 1. Fetch credential from Holder (more reliable)  
    print("   Fetching credential from Holder...")  
    try:  
        creds_resp = requests.get(f"{HOLDER_URL}/credentials")  
        if creds_resp.status_code != 200:  
            print("❌ Error fetching credentials from Holder")  
            return  
  
        credentials = creds_resp.json()['results']  
        if not credentials:  
            print("❌ No credentials found in Holder")  
            return  
  
        # Take the first (and only) credential  
        credential = credentials[0]  
        rev_reg_id = credential.get('rev_reg_id')  
        cred_rev_id = credential.get('cred_rev_id')  
  
        print(f"   ✅ Registry ID: {rev_reg_id}")  
        print(f"   ✅ Credential Revocation ID: {cred_rev_id}")  
  
    except Exception as e:  
        print(f"❌ Error: {e}")  
        return  
  
    # 2. Send Revocation Request  
    print("   Sending revocation order...")  
  
    # REMOVE connection_id - not required for published revocation  
    revoke_payload = {  
        "rev_reg_id": rev_reg_id,  
        "cred_rev_id": cred_rev_id,  
        "publish": True,  
        "notify": False  # Add this line  
    }  
  
    try:  
        revoke_resp = requests.post(f"{ISSUER_URL}/anoncreds/revocation/revoke", json=revoke_payload)  
  
        if revoke_resp.status_code == 200:  
            print("\n   ✅ SUCCESS: Credential REVOKED and published to Ledger!")  
            print("   -----------------------------------------------------")  
            print("   FINAL TEST: Run 'script 4' now.")  
            print("   The Bank MUST deny access (Invalid Signature).")  
            print("   -----------------------------------------------------")  
        else:  
            print(f"\n❌ Revocation failed: {revoke_resp.status_code}")  
            print(f"Details: {revoke_resp.text}")  
  
    except Exception as e:  
        print(f"❌ Exception: {e}")  
  
if __name__ == "__main__":  
    main()