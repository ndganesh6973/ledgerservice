import threading
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def run_test():
    print("--- 🏁 Starting Concurrency Test ---")
    
    # 1. Setup Accounts
    alice = requests.post(f"{BASE_URL}/accounts/", json={"owner": "Alice_Test", "currency": "USD"}).json()
    bob = requests.post(f"{BASE_URL}/accounts/", json={"owner": "Bob_Test", "currency": "USD"}).json()
    
    print(f"Created Alice (ID: {alice['id']}) and Bob (ID: {bob['id']})")
    
    # 2. Fund Alice with $100
    requests.post(f"{BASE_URL}/deposit/", json={
        "account_id": alice['id'], "amount": 100, "type": "DEPOSIT", "idempotency_key": "setup_fund_1"
    })
    print("Deposited $100 to Alice.")
    
    # 3. Fire 10 Threads trying to transfer $20 each
    threads = []
    results = []

    def transfer_money(i):
        res = requests.post(f"{BASE_URL}/transfer/", json={
            "from_account_id": alice['id'],
            "to_account_id": bob['id'],
            "amount": 20,
            "idempotency_key": f"race_tx_{i}"
        })
        results.append(res.status_code)

    print("🚀 Firing 10 simultaneous transfers of $20...")
    for i in range(10):
        t = threading.Thread(target=transfer_money, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    # 4. Check Results
    final_alice = requests.get(f"{BASE_URL}/accounts/{alice['id']}").json()
    final_bob = requests.get(f"{BASE_URL}/accounts/{bob['id']}").json()
    
    success_count = results.count(200)
    fail_count = results.count(400)
    
    print(f"\nResults: {success_count} Successes, {fail_count} Failures")
    print(f"Alice Final Balance: ${final_alice['balance']} (Expected: 0.00)")
    print(f"Bob Final Balance:   ${final_bob['balance']} (Expected: 100.00)")
    
    if success_count == 5 and fail_count == 5 and float(final_alice['balance']) == 0:
        print("\n✅ TEST PASSED: Database Locking prevented double-spending!")
    else:
        print("\n❌ TEST FAILED: Balance mismatch or Race Condition detected.")

if __name__ == "__main__":
    run_test()