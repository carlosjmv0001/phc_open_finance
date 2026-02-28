import requests  
import json  
import time  
import sys  
from .config import VERIFIER_URL  
from .utils import load_state, get_connection_id  
  
def send_proof_request(conn_id, cred_def_id):  
    """Send proof request to Holder"""  
    # Non-revocation interval (from the beginning of time to now)  
    to_timestamp = int(time.time())  
  
    proof_request = {  
        "connection_id": conn_id,  
        "presentation_request": {  
            "anoncreds": {  
                "name": "Proof of Personhood Revocable",  
                "version": "1.0",  
                "nonce": str(int(time.time())),  
                "requested_attributes": {  
                    "0_personhood_uuid": {  
                        "names": ["person_hash", "biometric_score"],  
                        "restrictions": [{"cred_def_id": cred_def_id}],  
                        "non_revoked": {"from": 0, "to": to_timestamp}  
                    }  
                },  
                "requested_predicates": {},  
                "non_revoked": {"from": 0, "to": to_timestamp}  
            }  
        }  
    }  
  
    try:  
        resp = requests.post(f"{VERIFIER_URL}/present-proof-2.0/send-request", json=proof_request)  
        if resp.status_code != 200:  
            print(f"Request Error: {resp.text}")  
            return None  
  
        pres_ex_id = resp.json().get("pres_ex_id")  
        print(f"   [OK] Transaction ID: {pres_ex_id}")  
        return pres_ex_id  
  
    except Exception as e:  
        print(f"Send error: {e}")  
        return None  
  
def main():  
    print("### 4. BANK REQUESTS PROOF (FINAL CORRECTED) ###")  
  
    state = load_state()  
    cred_def_id = state.get("cred_def_id")  
  
    if not cred_def_id:  
        print("❌ Error: 'cred_def_id' not found.")  
        return  
  
    conn_id = get_connection_id(VERIFIER_URL, "Connection_Bank_Bot")  
    if not conn_id:  
        print("❌ Error: Connection not found.")  
        return  
  
    print("   Sending challenge with revocation verification...")  
  
    pres_ex_id = send_proof_request(conn_id, cred_def_id)  
    if not pres_ex_id:  
        return  
  
    print("   Awaiting proof from Bot...")  
  
    for i in range(20):  
        time.sleep(2)  
        try:  
            status_resp = requests.get(f"{VERIFIER_URL}/present-proof-2.0/records/{pres_ex_id}")  
            if status_resp.status_code == 404: break  
  
            status_data = status_resp.json()  
            state_proof = status_data.get("state", "unknown")  
  
            sys.stdout.write(f"\r   Status: '{state_proof}'   ")  
            sys.stdout.flush()  
  
            if state_proof == "presentation-received":  
                sys.stdout.write(" [Verifying...] ")  
                verify_resp = requests.post(f"{VERIFIER_URL}/present-proof-2.0/records/{pres_ex_id}/verify-presentation")  
  
                verify_data = verify_resp.json()  
                verified = verify_data.get("verified")  
                error_msg = verify_data.get("verified_msgs", [])  
  
                print("\n\n   ✅ CYCLE COMPLETE!")  
                print(f"   TECHNICAL RESULT: {verified}")  
  
                if str(verified).lower() == "true":  
                    print("   🟢 STATUS: VALID")  
                    print("   [OPEN FINANCE] Access to banking data: GRANTED.")  
                else:  
                    print("   🔴 STATUS: INVALID / REVOKED")  
                    print("   [OPEN FINANCE] Access DENIED.")  
                    if error_msg:  
                        print(f"   Reason: {error_msg}")  
                return  
  
        except Exception as e:  
            print(f"\nPolling error: {e}")  
            break  
  
    print("\n   ⚠️ Timeout exceeded.")  
  
if __name__ == "__main__":  
    main()