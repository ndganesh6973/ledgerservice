import requests
import concurrent.futures
import time

# The URL where your FastAPI app is running
BASE_URL = "http://127.0.0.1:8000"

def create_account(owner):
    resp = requests.post(f"{BASE_URL}/accounts/", json={"owner": owner, "currency": "USD"})
    if resp.status_code != 200:
        print(f"Failed to create account: {resp.text}")
        return None
    return resp.json()

def deposit(account_id, amount):
    requests.post(f"{BASE_URL}/deposit/", json={
        "account_id": account_id,
        "amount": amount,
        "type": "DEPOSIT",
        "idempotency_key": f"setup_{account_id}_{time.time()}"
    })

def transfer(from_acc, to_acc, amount, count):
    # We use a unique key per request (race_test_0, race_test_1, etc.)
    # This ensures the database treats them as DISTINCT attempts, not duplicates.
    payload = {
        "from_account_id": from_acc,
        "to_account_id": to_acc,
        "amount": amount,
        "idempotency_key": f"race_test_{count}_{time.time()}" 
    }
    try:
        resp = requests.post(f"{BASE_URL}/transfer/", json=payload)
        return resp.status_code, resp.json()
    except Exception as e:
        return 500, str(e)

def run_test():
    print("--- 🏁 Starting Concurrency Test ---")
    
    # 1. Setup Accounts
    alice = create_account("Alice_Test")
    bob = create_account("Bob_Test")
    
    if not alice or not bob:
        print("❌ Could not create accounts. Is the server running?")
        return

    print(f"Created Alice (ID: {alice['id']}) and Bob (ID: {bob['id']})")
    
    # 2. Fund Alice with $100
    deposit(alice['id'], 100)
    print("Deposited $100 to Alice.")

    # 3. The Attack: 10 threads, each trying to move $20
    # Math: $100 balance / $20 transfer = 5 should succeed, 5 should fail.
    print("🚀 Firing 10 simultaneous transfers of $20...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(transfer, alice['id'], bob['id'], 20, i) 
            for i in range(10)
        ]
        results = [f.result() for f in futures]

    # 4. Analyze Results
    success_count = sum(1 for status, _ in results if status == 200)
    fail_count = sum(1 for status, _ in results if status != 200)
    
    print(f"\nResults: {success_count} Successes, {fail_count} Failures")

    # 5. Verification
    final_alice = requests.get(f"{BASE_URL}/accounts/{alice['id']}").json()
    final_bob = requests.get(f"{BASE_URL}/accounts/{bob['id']}").json()
    
    print(f"Alice Final Balance: ${final_alice['balance']} (Expected: 0.00)")
    print(f"Bob Final Balance:   ${final_bob['balance']} (Expected: 100.00)")

    # 6. Final Verdict
    # Note: We cast to float because Decimal comes back as string/number
    if float(final_alice['balance']) == 0.0 and float(final_bob['balance']) == 100.0:
        print("\n✅ TEST PASSED: Database Locking prevented double-spending!")
    else:
        print("\n❌ TEST FAILED: Balances are incorrect.")

if __name__ == "__main__":
    run_test()