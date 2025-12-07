# Transactional Ledger Service

## 1. Overview
A high-integrity financial ledger system designed to handle money movements between accounts with strict guarantees against double-spending and overdrafts. Built with **Python (FastAPI)** and **PostgreSQL**.

---

## 2. Architecture & Design Decisions

### 🧠 Database Choice: Why PostgreSQL?
I selected **PostgreSQL** (Relational) over MongoDB (NoSQL) because financial systems require strict **ACID guarantees**.
* **Atomicity:** A transfer involves two writes (Debit Sender, Credit Receiver). If one fails, the entire transaction must roll back. PostgreSQL handles this natively.
* **Consistency:** I utilized `CheckConstraints` (`CHECK (balance >= 0)`) at the database level. This ensures that even if the application logic fails, the database engine itself rejects any transaction that causes an overdraft.
* **Locking Support:** PostgreSQL provides robust row-level locking (`SELECT FOR UPDATE`), which is critical for the concurrency requirements.

### 📚 Schema Design: Double-Entry Bookkeeping
To meet the requirements of a "Real Ledger," I implemented a **Hybrid Approach**:
1.  **`accounts` Table:** Stores the current mutable `balance`. This allows for O(1) read performance and serves as the primary row for locking.
2.  **`transactions` Table:** Acts as an immutable ledger. Every money movement records a specific transaction row (Deposit, Withdrawal, Transfer).
    * *Auditability:* The history endpoint reconstructs the flow of funds by querying this table.

### 🛡️ Concurrency Strategy: Preventing Double-Spending
To handle race conditions (e.g., 10 simultaneous requests trying to withdraw funds), I implemented **Pessimistic Locking**.
* **Mechanism:** When a transfer initiates, the system executes `SELECT ... FOR UPDATE` on both the Sender and Receiver rows.
* **Result:** The database locks these specific rows. Any other incoming request trying to modify these accounts is forced to wait until the first transaction commits.
* **Deadlock Prevention:** To avoid deadlocks, accounts are always locked in a consistent order (lowest ID first).

### 🔄 Idempotency
To handle network retries safely, the `transactions` table enforces a **Unique Constraint** on the `(account_id, idempotency_key)` pair. Duplicate requests are caught by the database and handled gracefully without re-processing funds.

---

## 3. Scaling Trade-offs (The "1 Million TPS" Question)
The current design prioritizes **Safety/Consistency** over **Throughput**. The `SELECT FOR UPDATE` lock creates a bottleneck because transactions on the same account must process sequentially.

**To scale this to 1 Million Transactions Per Second (TPS), I would:**
1.  **Database Sharding:** Partition the PostgreSQL database by `account_id` to spread the locking load across multiple physical servers.
2.  **Async Processing (CQRS):** Instead of processing transfers synchronously, the API would push requests to a high-throughput message queue (e.g., **Kafka**). Workers would process the ledger updates at a steady pace.
3.  **Distributed Ledger:** Move the immutable transaction history to a distributed datastore (like **Cassandra** or **DynamoDB**) optimized for write-heavy workloads, keeping only the "hot" balance in Postgres/Redis.

---

## 4. How to Run Locally

### Prerequisites
* Python 3.10+
* PostgreSQL (Local)
* Git

### Installation
1.  Clone the repository:
    ```bash
    git clone <https://github.com/ndganesh6973/ledgerservice.git>
    cd ledger-service
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration & Start
Set your database connection string and start the server.

**Windows (PowerShell):**
```powershell
$env:DATABASE_URL="postgresql://postgres:password@localhost:5432/ledger_db"; uvicorn app.main:app --reload

Mac/Linux:
DATABASE_URL="postgresql://postgres:password@localhost:5432/ledger_db" uvicorn app.main:app --reload

The API will be available at: http://127.0.0.1:8000/docs

5. Testing (Concurrency Proof)
To verify that the locking strategy works, run the integration test script. This fires 10 simultaneous transfer requests to prove that balances remain accurate.
python tests/test_concurrency.py
Expected Output:
Results: 5 Successes, 5 Failures
Alice Final Balance: $0.00
Bob Final Balance:   $100.00
✅ TEST PASSED
6. API Reference (cURL Commands)
1. Create Account

curl -X 'POST' \
  '[http://127.0.0.1:8000/accounts/](http://127.0.0.1:8000/accounts/)' \
  -H 'Content-Type: application/json' \
  -d '{"owner": "Alice", "currency": "USD"}'
2. Deposit Funds

curl -X 'POST' \
  '[http://127.0.0.1:8000/deposit/](http://127.0.0.1:8000/deposit/)' \
  -H 'Content-Type: application/json' \
  -d '{"account_id": 1, "amount": 100, "type": "DEPOSIT", "idempotency_key": "dep_unique_1"}'
3. Transfer Funds
curl -X 'POST' \
  '[http://127.0.0.1:8000/transfer/](http://127.0.0.1:8000/transfer/)' \
  -H 'Content-Type: application/json' \
  -d '{"from_account_id": 1, "to_account_id": 2, "amount": 20, "idempotency_key": "transfer_unique_1"}'
4. View History
curl -X 'GET' '[http://127.0.0.1:8000/accounts/1/history](http://127.0.0.1:8000/accounts/1/hist