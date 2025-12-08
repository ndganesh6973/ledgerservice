# Transactional Ledger Service

> A robust internal financial ledger system ensuring high accuracy and consistency under concurrent and failure scenarios.

---

## Project Overview

This service handles money movement between accounts, supporting:

- Account creation with zero initial balance
- Deposits and withdrawals with overdraft protection (no negative balances)
- Atomic internal transfers between accounts
- Retrieval of current balance and full transaction history

Built using Python (FastAPI), PostgreSQL, SQLAlchemy, and Docker.

---

## Features

### Account Creation
- Initializes accounts with a zero balance
- Supported currencies: USD, INR

### Deposit & Withdrawal
- Perform credit and debit operations safely
- Overdraft protection enforced by database constraints

### Internal Transfers
- Atomic debit and credit across accounts
- Ensures no partial transfers on failures

### Balance & Transaction History Retrieval
- Get current balance
- Fetch full, immutable transaction history for auditing

---

## Technology Stack

- **Backend:** Python (FastAPI)  
- **Database:** PostgreSQL  
- **ORM:** SQLAlchemy  
- **Validation:** Pydantic  
- **Containerization:** Docker, Docker Compose  

---

## Database Design

PostgreSQL was chosen for its robust ACID guarantees required in financial systems:

- **Atomicity:** Transfers handled in single DB transactions  
- **Consistency:** Constraints prevent overdrafts  
- **Isolation:** Pessimistic locking (`SELECT FOR UPDATE`) prevents race conditions  
- **Durability:** Data safely persisted after commit  

### Schema Overview
- `accounts`: stores live balances and supports row locking  
- `transactions`: immutable ledger for deposits, withdrawals, and transfers  

This implements a Hybrid Double-Entry Bookkeeping model.

---

## Concurrency & Idempotency

### Concurrency Control

- Pessimistic locking on accounts to serialize access  
- Locks acquired in ascending account ID order to prevent deadlocks

### Idempotency

- Unique `(account_id, idempotency_key)` constraint avoids duplicated requests  
- Duplicate requests return original results without reprocessing funds

---

## Testing Concurrency

Run:
- python tests/test_concurrency.py


Confirms:

- No overdrafts or double spending  
- Accurate balances under heavy concurrent load

---

## Running the Project

### Option A: Using Docker (Recommended)

**Prerequisites:** 
- Docker and Docker Compose
- git clone https://github.com/ndganesh6973/ledgerservice.git
- cd ledgerservice
- docker-compose up --build

Browse API docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

### Option B: Local Setup

**Prerequisites:** Python 3.10+, PostgreSQL, Git
- git clone https://github.com/ndganesh6973/ledgerservice.git
- cd ledgerservice
- python -m venv venv
- source venv/bin/activate # Windows: venv\Scripts\activate
- pip install -r requirements.txt

**Create DB manually in PostgreSQL:**
- CREATE DATABASE ledger_db;

- Set environment variable
- export DATABASE_URL="postgresql://postgres:password@localhost:5432/ledger_db"

- PS: $env:DATABASE_URL="postgresql://postgres:password@localhost:5432/ledger_db"
- uvicorn app.main:app --reload

---

## Example API Calls

- Create Account:
curl -X POST http://127.0.0.1:8000/accounts/
- H "Content-Type: application/json"
- d '{"owner":"Alice","currency":"USD"}'

- Deposit:
curl -X POST http://127.0.0.1:8000/deposit/
- H "Content-Type: application/json"
- d '{"account_id":1,"amount":100,"type":"DEPOSIT","idempotency_key":"dep1"}'

- Transfer:
curl -X POST http://127.0.0.1:8000/transfer/
- H "Content-Type: application/json"
- d '{"from_account_id":1,"to_account_id":2,"amount":50,"idempotency_key":"tx1"}'

- Transaction History:
curl -X GET http://127.0.0.1:8000/accounts/1/history

---

## Scaling Considerations

Current design prioritizes:

- Data Integrity  
- Financial Safety  
- Strong Consistency  

To scale for millions TPS:

- Database sharding by account  
- Kafka-based async CQRS processing  
- Redis caching for hot balances  
- Use Cassandra or DynamoDB for ledger history storage

[Repository Link](https://github.com/ndganesh6973/ledgerservice)






