import requests  
import json  
import time  
import sys  
import uuid  
from .config import ISSUER_URL, HOLDER_URL  
from .utils import load_state, get_connection_id  
from .retry import retry_with_backoff  
from .schemas import CredentialAttributes  
  
@retry_with_backoff(max_attempts=3, initial_delay=1.0)  
def send_credential_offer(payload):  
    """Send credential offer with automatic retry"""  
    resp = requests.post(f"{ISSUER_URL}/issue-credential-2.0/send-offer", json=payload)  
    if resp.status_code != 200:  
        raise requests.HTTPError(f"Status: {resp.status_code}, Response: {resp.text}")  
    return resp  
  
def main():  
    print("### 3. ISSUING CREDENTIAL (ANONCREDS FORMAT) ###")  
  
    state = load_state()  
    cred_def_id = state.get("cred_def_id")  
  
    if not cred_def_id:  
        print("❌ Error: 'cred_def_id' not found.")  
        return  
  
    # 1. Verify Connection  
    conn_id_issuer = get_connection_id(ISSUER_URL, "Connection_Gov_Bot")  
    if not conn_id_issuer:  
        print("❌ Error: Connection not found.")  
        return  
  
    # 2. Send Offer  
    print(f"   [Issuer] Sending offer (AnonCreds format)...")  
  
    # Replace hardcoded payload using Pydantic  
    attributes = CredentialAttributes(  
        person_hash="humano-anoncreds-v2",  
        biometric_score="100.0",  
        controller_did=f"did:sov:{uuid.uuid4().hex[:32]}"  # Generated dynamically  
    )  
  
    payload = {  
        "connection_id": conn_id_issuer,  
        "credential_preview": {  
            "@type": "issue-credential/2.0/credential-preview",  
            "attributes": [  
                {"name": "person_hash", "value": attributes.person_hash},  
                {"name": "biometric_score", "value": attributes.biometric_score},  
                {"name": "timestamp", "value": attributes.timestamp},  
                {"name": "controller_did", "value": attributes.controller_did}  
            ]  
        },  
        "filter": {"anoncreds": {"cred_def_id": cred_def_id}},  
        "auto_remove": False  
    }  
  
    # Use the function with retry  
    try:  
        resp = send_credential_offer(payload)  
        print("   [Issuer] Offer sent successfully!")  
  
    except Exception as e:  
        print(f"\n❌ ISSUER ERROR after 3 attempts: {e}")  
        return  
  
    print("   [Bot] Processing...")  
    time.sleep(3)  
  
    # 3. Bot (Holder) logic - remains the same  
    try:  
        all_records = requests.get(f"{HOLDER_URL}/issue-credential-2.0/records").json()['results']  
        if not all_records:  
            print("❌ ERROR: Bot received nothing.")  
            return  
  
        target_record = all_records[-1].get('cred_ex_record', all_records[-1])  
        cred_ex_id = target_record['cred_ex_id']  
        state_cred = target_record['state']  
  
        print(f"   -> Record: {cred_ex_id} | State: {state_cred}")  
  
        # Automation  
        if state_cred == "offer-received":  
            requests.post(f"{HOLDER_URL}/issue-credential-2.0/records/{cred_ex_id}/send-request")  
            time.sleep(2)  
            rec = requests.get(f"{HOLDER_URL}/issue-credential-2.0/records/{cred_ex_id}").json()  
            state_cred = rec.get('cred_ex_record', rec)['state']  
  
        if state_cred == "credential-received":  
            requests.post(f"{HOLDER_URL}/issue-credential-2.0/records/{cred_ex_id}/store",  
                          json={"credential_id": cred_ex_id})  
            print("   ✅ Credential stored!")  
  
        elif state_cred == "request-sent":  
            print("   ⚠️ State 'request-sent'. Forcing Issuer...")  
            iss_recs = requests.get(f"{ISSUER_URL}/issue-credential-2.0/records", params={"state": "request-received"}).json()['results']  
            if iss_recs:  
                 t = iss_recs[-1].get('cred_ex_record', iss_recs[-1])  
                 requests.post(f"{ISSUER_URL}/issue-credential-2.0/records/{t['cred_ex_id']}/issue", json={"comment":"force"})  
                 print("   [Issuer] Issued.")  
                 time.sleep(2)  
                 requests.post(f"{HOLDER_URL}/issue-credential-2.0/records/{cred_ex_id}/store", json={"credential_id": cred_ex_id})  
                 print("   ✅ Credential stored!")  
  
        elif state_cred == "done":  
             print("   ✅ Already completed.")  
  
        # Validation  
        final = requests.get(f"{HOLDER_URL}/credentials").json()['results']  
        print(f"\n   SUMMARY: The Bot has {len(final)} credential(s).")  
  
    except Exception as e:  
        print(f"Bot error: {e}")  
  
if __name__ == "__main__":  
    main()