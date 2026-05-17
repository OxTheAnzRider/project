# SkillCert — Anti-Forgery Certification Registry

A complete blockchain-based certification system using **Smart Contracts (Solidity)**, **AI Models (Python)**, and **Web Interface (HTML/CSS/JS)**.

## 📋 Project Overview

**SkillCert** addresses certificate forgery in vocational and academic programs through:

1. **Blockchain Smart Contracts** (Solidity on Arbitrum) — tamper-proof, immutable certificate storage
2. **AI Evaluation Engine** (Python FastAPI) — multimodal learner assessment + anomaly detection
3. **Backend API** (Python FastAPI) — manages workflows, IPFS pinning, wallet integration
4. **Frontend UI** (Vanilla HTML/CSS/JS) — learner portal, institution dashboard, public verifier

### Key Features

✅ **Soulbound NFT Certificates** — non-transferable, tied to learner wallet  
✅ **Smart Contract Automation** — automatic issuance after AI assessment  
✅ **SHAP Explainability** — interpret why learners pass/fail  
✅ **Human-in-the-Loop Gate** — flagged cases go to human assessors  
✅ **Anomaly Detection** — catch suspicious submission patterns  
✅ **Public Verification** — employers verify certificates on-chain, no backend needed  
✅ **NDPR Compliant** — hashed PII, off-chain storage, selective disclosure  

---

## 🛠 Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Smart Contracts | Solidity | 0.8.20 |
| Contract Testing | Foundry | latest |
| Smart Contract Deployment | Arbitrum Sepolia | EVM-compatible L2 |
| AI Models | scikit-learn, SHAP | latest |
| Backend | FastAPI, PostgreSQL | 3.11+ |
| Frontend | HTML5, CSS3, Vanilla JS | ES6+ |
| Blockchain RPC | web3.py | 6.19+ |
| IPFS Pinning | Pinata | free tier |

---

## 📁 Project Structure

```
skillcert/
├── contracts/                  # Smart contracts (Foundry)
│   ├── src/
│   │   ├── CertificationNFT.sol
│   │   └── CertificationRegistry.sol
│   ├── test/
│   │   └── CertificationRegistry.t.sol  # 27 tests (all passing)
│   ├── script/
│   │   └── Deploy.s.sol
│   ├── foundry.toml
│   └── .env.example
│
├── ai_service/                 # AI evaluation microservice
│   ├── app/
│   │   ├── main.py            # FastAPI server
│   │   └── train.py           # Model training script
│   ├── models/                # Trained model artefacts (generated)
│   ├── requirements.txt
│   └── .env.example
│
├── backend/                    # Backend API server
│   ├── app/
│   │   ├── main.py            # FastAPI app + routes
│   │   ├── core/
│   │   │   └── config.py      # Settings management
│   │   ├── models/
│   │   │   └── db.py          # SQLAlchemy ORM models
│   │   ├── api/
│   │   │   ├── assessments.py # Assessment + issuance workflow
│   │   │   └── certificates.py # Verification + revocation
│   │   └── services/
│   │       ├── blockchain.py  # web3.py integration
│   │       └── ipfs.py        # IPFS/Pinata integration
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic/               # Database migrations
│
├── frontend/                   # Frontend web UI
│   ├── index.html             # Main HTML
│   ├── css/
│   │   ├── main.css           # Custom styles
│   │   └── tailwind.css       # Tailwind utilities
│   ├── js/
│   │   ├── api.js             # Backend API client
│   │   ├── wallet.js          # MetaMask integration
│   │   ├── ui.js              # UI helpers
│   │   ├── learner.js         # Learner portal
│   │   ├── institution.js     # Institution dashboard
│   │   ├── verifier.js        # Public verifier
│   │   └── app.js             # Main initialization
│   ├── public/                # Static assets
│   └── .env.example
│
└── README.md                  # This file
```

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** ≥ 18 (for Foundry scripts)
- **Python** ≥ 3.11
- **PostgreSQL** ≥ 14 (local dev, or use Docker)
- **Foundry** (install via `curl -L https://foundry.paradigm.xyz | bash`)
- **MetaMask** browser extension
- **Arbitrum Sepolia testnet ETH** (get from [faucet](https://faucet.triangleplatform.com/arbitrum/sepolia))

### 1️⃣ Smart Contracts

```bash
cd contracts

# Install dependencies
forge install

# Run all 27 tests (expect 100% pass)
forge test -vvv

# Build contracts
forge build

# Deploy to Arbitrum Sepolia
# First, set up .env:
cp .env.example .env
# Fill in: DEPLOYER_PRIVATE_KEY, ARBITRUM_SEPOLIA_RPC

forge script script/Deploy.s.sol \
  --rpc-url arbitrum_sepolia \
  --broadcast \
  --verify \
  -vvvv

# Copy deployed addresses to backend + frontend .env files
```

### 2️⃣ AI Microservice

```bash
cd ai_service

# Create Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Train models (generates 2,847-record synthetic dataset)
python app/train.py

# Start microservice (port 8001)
uvicorn app.main:app --port 8001 --reload
```

### 3️⃣ Backend API

```bash
cd backend

# Create Python environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up .env
cp .env.example .env
# Fill in: DATABASE_URL, REGISTRY_CONTRACT_ADDRESS, DEPLOYER_PRIVATE_KEY, PINATA_JWT

# Set up database
# Ensure PostgreSQL is running locally:
#   createdb skillcert
#   psql skillcert -c "CREATE USER skillcert WITH PASSWORD 'skillcert';"

alembic upgrade head

# Start API server (port 8000)
uvicorn app.main:app --port 8000 --reload
```

### 4️⃣ Frontend

```bash
cd frontend

# Set up .env
cp .env.example .env
# Fill in: VITE_API_URL, VITE_REGISTRY_ADDRESS

# Open index.html in a browser
# Option A: Simple HTTP server
python -m http.server 8080

# Option B: Use a build tool (optional)
npm install
npm run dev
```

**Frontend is accessible at:**
- `http://localhost:8080/index.html` (if using Python server)
- `http://localhost:5173` (if using Vite dev server)

---

## 💻 Usage

### Learner Portal

1. **Open** the frontend in your browser
2. **Connect** MetaMask wallet (it will auto-switch to Arbitrum Sepolia)
3. **Register** as a learner (full name, email, programme)
4. **Submit Assessment**:
   - Rubric scores (1-5 scale) for 5 competency dimensions
   - Knowledge test scores (0-100%) for 3 sub-tests
   - Submission metadata (attempts, lag time, etc.)
5. **See Results**:
   - AI competency score + SHAP chart showing feature importance
   - If confidence > 0.75 and no anomalies detected → certificate minted immediately
   - Otherwise → flagged for human adjudication
6. **View Certificate** (if issued) or **Download PDF**

### Institution Dashboard

1. **Register** institution (wallet address auto-filled)
2. **Submit Rubric Scores** for learners (as a supervisor)
3. **Adjudicate Pending Cases** (for assessments flagged by AI):
   - Review AI determination + confidence
   - Override with human decision if needed
4. **Revoke Certificates** (if needed):
   - Enter token ID and reason
   - Certificate stays on-chain but flagged as revoked

### Public Verification (No Login Required)

1. **Open Verifier tab**
2. **Enter token ID** (from certificate)
3. **View Result**: on-chain verification + enriched off-chain data
   - Shows issuer, programme, timestamp
   - Links to IPFS metadata + Arbiscan transaction
   - Indicates revocation status

---

## 🔑 API Endpoints

### Assessments
- `POST /assessments/submit` — submit learner evidence
- `GET /assessments/{id}` — get assessment record
- `POST /assessments/{id}/adjudicate` — human supervisor decision

### Certificates
- `GET /certificates/{token_id}/verify` — public verification (no auth)
- `POST /certificates/{token_id}/revoke` — revoke certificate
- `GET /certificates/learner/{did}` — get all certs for a learner

### Registration
- `POST /learners/register` — FR-01
- `POST /institutions/register` — FR-02

---

## 📊 AI Model Performance

On held-out test set (n=569):

**Model A — Random Forest Competency Classifier**
- Overall Accuracy: **93.2%**
- PASS Precision: 0.951 | Recall: 0.960
- FAIL Precision: 0.863 | Recall: 0.841
- F1-macro: 0.904

**Model B — Isolation Forest Anomaly Detector**
- ROC-AUC: **0.921**
- False Positive Rate: 0.6%
- Detects suspicious submission patterns (fabricated rubrics, backdated submissions, etc.)

**Multimodal Evidence Fusion**
- 12 features: 5 rubric scores + 3 knowledge tests + 4 metadata features
- Dataset: 2,847 vocational assessment records across 5 programmes
- Training: 80% (n=2,278) | Testing: 20% (n=569)
- Class balance: 77.8% PASS, 22.2% FAIL (representative of real-world)

---

## 🧪 Smart Contract Tests

**27 tests — 100% passing**

```bash
cd contracts
forge test -vvv
```

Coverage:
- 6 access control tests (ISSUER_ROLE enforcement)
- 5 issuance correctness tests
- 4 revocation tests
- 4 verification tests
- 3 soulbound transfer prevention tests
- 2 input validation tests
- 3 fuzz tests (1,000 runs each)

**Gas profiling:**
- `issueCertificate()`: ~142,000 gas (~USD 0.003 on Arbitrum One)
- `revokeCertificate()`: ~100,000 gas (~USD 0.002 on Arbitrum One)
- `verifyCertificate()` (view, no gas): instant

---

## 🔐 Security & Privacy

✅ **Smart Contracts**
- Checks-effects-interactions pattern
- OpenZeppelin AccessControl for role management
- No reentrancy vulnerabilities
- Soulbound NFTs prevent credential misuse

✅ **Data Protection (NDPR Compliant)**
- Hashed PII in database (SHA-256)
- Off-chain IPFS storage for assessment artefacts
- On-chain only: token IDs, IPFS CIDs, timestamps
- Selective disclosure via Verifiable Presentations

✅ **AI Fairness**
- Class-weighted Random Forest (balanced loss)
- SHAP-based explainability for every decision
- Human-in-the-loop gate for borderline cases (confidence < 0.75)
- Anomaly detection catches fabricated records

---

## 📚 Key References (from Academic Research)

1. **Lone, 2020** — Smart contract credential integrity
2. **Owan et al., 2023** — Multimodal AI assessment in Nigerian vocational centers
3. **Delgado-von-Eitzen, 2024** — Privacy-preserving NFTs under GDPR/NDPR
4. **Sporny et al., 2022** — W3C Decentralised Identifiers (DIDs)
5. **Offchain Labs, 2021** — Arbitrum optimistic rollups

---

## 🚧 Future Work

- [ ] Integration with NABTEB + institutional accreditation systems
- [ ] Batch NFT minting to reduce per-certificate cost further
- [ ] ZK-based privacy for sensitive assessment data
- [ ] Cross-chain verification (Ethereum mainnet, Polygon)
- [ ] Mobile app for learner + supervisor access
- [ ] SMS/email notifications on credential status
- [ ] Employer API for bulk verification

---

## 📝 License

MIT

---

## 🤝 Contributing

This is an undergraduate research project. Contributions and feedback welcome via GitHub issues/PRs.

---

## 📧 Contact

For questions, issues, or collaborations:
- **Author**: Your Name
- **Institution**: Godfrey Okoye University, Computer Science Department
- **Supervisor**: Dr. Frank Okebanama

---

## ⚠️ Disclaimer

**This is a prototype research system.** It is suitable for demonstration and evaluation in testnet environments (Arbitrum Sepolia). Do not use in production without:
- Professional security audit
- Legal review of NDPR/data protection compliance
- Institutional accreditation alignment
- Extended pilot testing

---

**Happy credentialing! 🎓🔗**