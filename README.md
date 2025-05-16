
# 🧠 DAG-Crypto-Network

A lightweight, scalable, and fast cryptocurrency simulation based on a **block-lattice DAG structure**, inspired by Nano. This project demonstrates secure transaction processing, consensus through balance-weighted voting, asynchronous confirmation, and hybrid RSA-AES cryptographic protection.

---

## 🌐 Key Features

- ✅ **Block-Lattice Structure**: Each account maintains its own blockchain (account-chain).
- 🔄 **Asynchronous Verification**: Transactions are processed and confirmed independently.
- ⚖️ **Balance-Weighted Voting**: Only full nodes with voting power confirm transactions.
- 🔐 **ED25519 Digital Signatures**: Ensures data integrity and non-repudiation.
- 🔒 **RSA + AES Hybrid Encryption**: Secures key exchange and transaction confidentiality.
- 📈 **Performance Metrics**: Measures TPS, latency, and scalability with customizable tests.
- 📊 **Reputation System**: Penalizes dishonest voters and tracks node behavior.

---

## 📁 Project Structure

```bash
DAG_block/
├── run.py                    # CLI interface for interacting with the network
├── simulate_network.py       # Simulates real-time voting on transactions
├── performance_test.py       # Measures TPS, latency, success rate
├── ledger.py                 # Ledger storage, per-account blockchain logic
├── node.py                   # Full node logic: voting, transaction handling
├── crypto_utils.py           # Key management, signing, encryption functions
├── network.py                # P2P communication (WebSocket-based)
├── config.py                 # Parameters: consensus thresholds, reputation values
├── print_ledger.py           # CLI tool to view individual account-chains
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/DAG-Crypto-Network.git
cd DAG-Crypto-Network
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🧪 Running the Project

### 🧭 CLI Interface
Launch a full node and interact via CLI:
```bash
python run.py
```

Available options:
```
1. Register Node
2. Submit Transaction
3. Vote on Transaction
4. Show Vote Pool
5. Show Reputations
6. Exit
7. Connect to Peer
```

---

## 🧬 Simulate a Transaction + Voting
```bash
python simulate_network.py
```
This registers 5–6 nodes, simulates a transaction between nodes A and B, and triggers voting from nodes C, D, and E.

---

## ⚙️ Performance Testing
Run 100 or 1000 transactions in parallel:
```bash
python performance_test.py
```

Outputs:
- ✅ Number of successful transactions
- ⚡ Transactions per second (TPS)
- ⏱️ Average latency
- 📈 Total duration

---

## 🔍 View Ledger
```bash
python print_ledger.py
```
Prints all blocks (send/receive) for an account’s chain.

---

## 🔐 Cryptographic Security

| Feature         | Algorithm        | Purpose                          |
|-----------------|------------------|----------------------------------|
| Signing         | ED25519 (PyNaCl) | Fast and secure authentication   |
| AES Session Key | AES-GCM          | Fast symmetric encryption        |
| RSA Encryption  | RSA 2048-bit     | Secure AES key exchange          |
| Hashing         | SHA-256          | Block ID and transaction hash    |

---

## 📊 Reputation System

Each full node has a reputation score that:
- Increases for correct votes (confirmed transactions).
- Decreases for incorrect votes (on rejected transactions).

You can view reputations using the CLI or logs.

---

## 🔧 Configuration

Edit `config.py` to adjust:
- Consensus threshold (e.g., `CONSENSUS_THRESHOLD = 0.67`)
- Initial reputation, increment, penalty
- Data file paths

---


## 📚 Future Work

- Peer discovery and bootstrapping
- Real wallet integration
- Dynamic quorum and adaptive consensus

---

## 📝 License

This project is open-source under the MIT License.

---

## 🤝 Acknowledgements

Inspired by:
- Nano cryptocurrency
- Python community (PyNaCl, pycryptodome)
- Cryptography best practices
