# SkillCert — Anti-Forgery Certification Registry

Blockchain-based certification system using Smart Contracts, NFTs, and AI.

## Project Structure

```
skillcert/
├── contracts/        # Solidity smart contracts (Foundry)
├── backend/          # FastAPI application server (Python)
├── ai_service/       # AI evaluation microservice (Python)
└── frontend/         # React frontend (Vite)
```

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Node.js | ≥ 18 | https://nodejs.org |
| Python | ≥ 3.11 | https://python.org |
| Foundry | latest | `curl -L https://foundry.paradigm.xyz \| bash` |
| PostgreSQL | ≥ 14 | https://postgresql.org |
| MetaMask | latest | Chrome extension |

## Quick Start

### 1. Smart Contracts

```bash
cd contracts
forge install
forge build
forge test -vvv          # run all 27 tests
forge script script/Deploy.s.sol --rpc-url arbitrum_sepolia --broadcast
```

### 2. AI Microservice

```bash
cd ai_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app/train.py          # trains and saves models to models/
uvicorn app.main:app --port 8001 --reload
```

### 3. Backend API

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # fill in your values
alembic upgrade head         # run DB migrations
uvicorn app.main:app --port 8000 --reload
```

### 4. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # fill in contract address + API URL
npm run dev                  # opens at http://localhost:5173
```

## Environment Variables

See `.env.example` in each service directory for required variables.

## Testnet Deployment

- Network: **Arbitrum Sepolia** (Chain ID: 421614)
- RPC: Get a free key from https://alchemy.com
- Faucet: https://faucet.triangleplatform.com/arbitrum/sepolia

## VS Code Extensions (Recommended)

- Juan Blanco — Solidity
- Prisma — Python
- ESLint + Prettier
- GitLens