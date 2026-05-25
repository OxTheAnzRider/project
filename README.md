# SkillCert: Anti-Forgery Proof Certification Registry

SkillCert is a full-stack certification system for skill acquisition programmes. It combines learner authentication, issuer-managed courses, AI-assisted assessments, NFT certificate issuance, IPFS certificate evidence, and public certificate verification.

The project is split into four major parts:

- `frontend/` - static browser UI for learners, issuers, authentication, and certificate verification.
- `backend/` - FastAPI API, database models, auth, course/enrollment logic, assessment orchestration, certificate issuance, PDF generation, IPFS, and blockchain calls.
- `ai_service/` - FastAPI microservice for material ingestion, question generation, answer grading, hybrid OpenAI/local assessment logic, and assessment report hashes.
- `contracts/` - Solidity smart contracts for certificate NFT minting and registry verification.

## High-Level Workflow

1. issuerregisters or logs in.
2. issuercreates a course.
3. issueruploads or enters course material.
4. issuercreates one or more assessment templates for that course.
5. issuergenerates enrollment codes for learners.
6. Learner registers or logs in.
7. Learner views available courses.
8. Learner enrolls using an issuer-provided course code.
9. Learner selects an available assessment for the enrolled course.
10. Backend requests the AI service to generate exactly 30 questions.
11. Learner answers the assessment.
12. Backend sends answers to the AI service for grading.
13. AI service returns score, outcome, feedback, detailed results, and assessment report hash.
14. If the learner passes and no anomaly blocks issuance, backend generates certificate metadata/PDF, pins evidence to IPFS where configured, and issues an NFT certificate through the smart contract.
15. Learner sees result and certificate details.
16. Public verifier checks a certificate using token ID plus verification code.

## How The Parts Work Together

### Frontend

The frontend is plain HTML/CSS/JavaScript served from `frontend/public`.

Main UI areas:

- Auth pages: learner/issuerregistration and login.
- Learner dashboard: course discovery, code-based enrollment, assessment selection, answering questions, viewing result/certificate details.
- issuerdashboard: create courses, generate enrollment codes, manage materials/templates, view enrolled learners and results.
- Verification dashboard: public certificate statistics and token/code verification.

The frontend talks to the backend at:

```text
http://localhost:8000/api
```

It stores auth tokens in browser local storage. Clearing local storage logs the user out locally.

### Backend

The backend is the source of truth for users, courses, enrollments, materials, assessment records, certificates, and blockchain state references.

Important backend responsibilities:

- JWT authentication and protected routes.
- Course and enrollment-code management.
- Assessment template creation.
- Calling the AI service for question generation and grading.
- Storing learner answers and assessment outcomes.
- Certificate verification-code creation.
- Certificate PDF generation.
- IPFS pinning where configured.
- NFT issuance through the registry smart contract.
- Public certificate verification.

The backend uses SQLite for local preview through `backend/.env`:

```text
DATABASE_URL=sqlite:////home/anzicle/project/backend/dev2.db
```

### AI Service

The AI service can work independently through its own API on port `8001`.

Endpoints:

- `POST /ingest-material`
- `POST /create-assessment`
- `POST /submit-answer`
- `POST /grade-assessment`
- `GET /assessment/{id}/summary`
- `GET /health`

The AI service now supports a hybrid method:

- OpenAI LLM for high-quality question generation.
- OpenAI LLM for semantic grading where available.
- Local TF-IDF/rule-based grading as fallback and consistency checker.
- Strict Pydantic validation so malformed LLM output cannot crash the service.
- Deterministic assessment report hashing for later NFT/IPFS evidence.

If OpenAI fails, times out, or returns invalid JSON, the AI service falls back to the local generator/grader.

### Smart Contracts

The contracts live in `contracts/`.

Main contracts:

- `CertificationNFT.sol` - NFT certificate token.
- `CertificationRegistry.sol` - certificate issuance, issuer authorization, revocation, and verification registry.

The deployed backend config points to Arbitrum Sepolia. The backend signs issuance transactions using the configured private key or an issuerkey if active issuerkey management is used.

## Independent Operation

Each part can be tested independently:

### Frontend Only

Can be served as static files, but most features need the backend.

```bash
backend/.venv/bin/python -m http.server 5173 --directory frontend/public
```

Open:

```text
http://localhost:5173
```

### Backend Only

Can be started and health-checked without the frontend.

```bash
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health:

```text
http://localhost:8000/health
```

### AI Service Only

Can ingest material, generate assessment questions, grade answers, and return assessment hashes.

```bash
cd ai_service/app
../.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
```

Health:

```text
http://localhost:8001/health
```

Expected healthy LLM config when OpenAI is configured:

```json
{
  "llm": {
    "openai_key_configured": true,
    "openai_model": "gpt-4o-mini"
  }
}
```

### Contracts Only

Run tests:

```bash
cd contracts
/home/anzicle/.config/.foundry/bin/forge test
```

Build:

```bash
cd contracts
/home/anzicle/.config/.foundry/bin/forge build
```

## Manual Run Guide

Use three terminals.

### Terminal 1: AI Service

```bash
cd /home/anzicle/project/ai_service/app
../.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
```

### Terminal 2: Backend

```bash
cd /home/anzicle/project/backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Terminal 3: Frontend

```bash
cd /home/anzicle/project
backend/.venv/bin/python -m http.server 5173 --directory frontend/public
```

Then open:

```text
http://localhost:5173
```

## Environment Files

Never commit real secrets. Real `.env` files are ignored by `.gitignore`.

### AI Service

Create `ai_service/.env`:

```text
OPENAI_API_KEY=your_real_openai_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=180
AI_SERVICE_DB_PATH=/home/anzicle/project/ai_service/ai_service.db
```

### Backend

Create or update `backend/.env`:

```text
DATABASE_URL=sqlite:////home/anzicle/project/backend/dev2.db
AI_SERVICE_URL=http://localhost:8001
ARBITRUM_RPC_URL=your_arbitrum_sepolia_rpc_url
REGISTRY_CONTRACT_ADDRESS=your_registry_contract
NFT_CONTRACT_ADDRESS=your_nft_contract
DEPLOYER_PRIVATE_KEY=0xyour_private_key
SECRET_KEY=change_me
ENCRYPTION_KEY=change_me
```

Private keys must include the `0x` prefix.

## Deploying Contracts To Arbitrum Sepolia

From `contracts/`:

```bash
export ARBITRUM_SEPOLIA_RPC="https://your-arbitrum-sepolia-rpc"
export DEPLOYER_PRIVATE_KEY="0xyour_private_key"
/home/anzicle/.config/.foundry/bin/forge script script/Deploy.s.sol:Deploy --rpc-url "$ARBITRUM_SEPOLIA_RPC" --broadcast
```

After deployment, copy the deployed addresses into `backend/.env`:

```text
REGISTRY_CONTRACT_ADDRESS=...
NFT_CONTRACT_ADDRESS=...
```

Then restart the backend.

## Assessment Methodology

### Question Generation

Assessments use exactly 30 questions:

- 8 definition
- 8 conceptual
- 7 application
- 7 analysis

The learner does not choose difficulty. Difficulty is backend-controlled and hidden from learner selection.

The AI service first extracts key concepts from material, then attempts LLM generation. LLM output must pass strict validation:

- exactly 30 questions
- correct question-type distribution
- valid IDs
- valid score/point fields
- non-empty question text
- non-empty expected answers and rubrics internally

Learner-facing question responses include:

- question ID
- question text
- question type
- points

They do not expose:

- expected answers
- rubrics
- grading reasons
- internal model metadata

### Grading

The grading system is hybrid:

1. Local TF-IDF/rule-based grading always runs first.
2. OpenAI semantic grading runs in batch if available.
3. If LLM grading succeeds, final score combines:
   - 60% LLM semantic score
   - 40% local TF-IDF/rule-based score
4. If LLM grading fails, local grading is used fully.

The AI service returns:

- total score
- percentage
- `PASS`, `FAIL`, or `PENDING_REVIEW`
- feedback
- per-question detailed results
- grading method
- assessment report
- deterministic assessment report hash

### Competency And Anomaly Models

The code supports Random Forest competency classification and Isolation Forest anomaly detection, but only when compatible trained artifacts exist in `ai_service/models/`:

- `competency_model.joblib`
- `anomaly_model.joblib`
- `scaler.joblib`
- `feature_names.json`

If artifacts are missing or incompatible, the system logs a warning and continues without crashing.

Current important note:

```text
Model artifacts missing; competency/anomaly checks disabled
```

This means assessment generation and grading still work, but the optional trained model checks are skipped until model artifacts are provided.

## Certificate Issuance Methodology

When an assessment outcome is `PASS`:

1. Backend creates certificate metadata.
2. Backend generates a verification code.
3. Backend generates a certificate PDF with learner wallet, course, score, token reference, and QR/verification details.
4. Backend pins metadata/PDF evidence to IPFS where configured.
5. Backend signs a blockchain transaction.
6. `CertificationRegistry.issueCertificate(...)` mints/registers the certificate.
7. Backend stores token ID, verification code, certificate data, and issuance status.

Verification requires both:

- NFT token ID
- alphanumeric verification code

The public registry hides learner-sensitive data by default and only reveals limited verified details after a valid token/code check.

## Course Enrollment Methodology

Issuers create courses and generate enrollment codes.

Learners can view course title and description, but cannot access assessments unless enrolled.

Enrollment code validation checks:

- code exists
- code is active
- code is not revoked
- code is not expired
- quota is not exceeded

The backend tracks:

- learner wallet/user
- course
- enrollment date
- code usage
- assessment results

## Important Problems Faced And Fixed

This project went through several integration issues. These are useful to document because they explain why the final architecture looks the way it does.

### 1. Initial Flow Mismatch

Problem:

The frontend/backend originally followed a single-submit assessment flow, while the target design required material ingestion, assessment creation, question-by-question answering, grading, and certificate issuance.

Fix:

Added the corrected course, enrollment, assessment-template, question generation, and Q-by-Q assessment flow.

### 2. Missing Endpoints

Problem:

The expected `/ingest-material`, `/create-assessment`, `/submit-answer`, and `/grade-assessment` flow was not fully wired.

Fix:

Implemented/connected the AI service endpoints and backend calls.

### 3. Frontend Navigation Error

Problem:

The browser console showed:

```text
Uncaught ReferenceError: switchTab is not defined
```

Fix:

Updated frontend routing/tab logic so pages initialize correctly.

### 4. Wrong Dashboard After Login

Problem:

issuerlogin sometimes redirected to learner dashboard.

Fix:

Updated auth role handling and route protection.

### 5. Preview Connection Refused

Problem:

`localhost:8000/api` refused connection when backend was not running.

Fix:

Clarified service startup order and ports.

### 6. 401 When Creating Course

Problem:

Course creation failed when the frontend had no valid JWT or stale local storage.

Fix:

Auth token handling was corrected, and users were advised to clear local storage when testing fresh accounts.

### 7. Failed Course Enrollment Fetch

Problem:

Learner enrollment failed when backend/AI services were not running or API base URL was wrong.

Fix:

Centralized API base URL logic and bearer token handling.

### 8. Incorrect Verification Statistics

Problem:

Verification dashboard counted active course codes as courses/certificates.

Fix:

Updated registry stats to count issued certificates/courses/issuers correctly.

### 9. Weak Local AI Questions

Problem:

Rule-based question generation produced low-quality questions.

Fix:

Added OpenAI LLM generation with local fallback.

### 10. OpenAI Key Not Visible

Problem:

The key was exported in a terminal but not visible to the AI service process.

Fix:

Added dotenv loading from `ai_service/.env`, root `.env`, and `backend/.env`. Added safe health reporting:

```json
"openai_key_configured": true
```

### 11. OpenAI Timeout

Problem:

Generating 30 structured questions could exceed a short timeout.

Fix:

Added `OPENAI_TIMEOUT_SECONDS=180`.

### 12. Invalid LLM Question Distribution

Problem:

The model once returned 30 questions but with the wrong distribution.

Fix:

Added a strict question plan and retry logic. Final smoke test produced:

```json
{
  "generation_method": "llm",
  "num_questions": 30,
  "counts": {
    "definition": 8,
    "conceptual": 8,
    "application": 7,
    "analysis": 7
  }
}
```

### 13. Backend `DEBUG=release` Crash

Problem:

The environment had `DEBUG=release`, but backend settings expected a boolean.

Fix:

Added settings validation that treats `release`, `prod`, and `production` as `False`.

### 14. Backend Import Path Error

Problem:

Running backend Uvicorn from the wrong directory caused:

```text
ModuleNotFoundError: No module named 'app'
```

Fix:

Run backend from `/home/anzicle/project/backend`.

### 15. Private Key Hex Prefix Error

Problem:

Foundry deployment failed because the private key did not include `0x`.

Fix:

Use:

```text
DEPLOYER_PRIVATE_KEY=0x...
```

### 16. ABI And Contract Mismatch

Problem:

Backend ABI expected fields/functions that did not match the Solidity contract.

Fix:

Synchronized `CertificationRegistry.sol`, `CertificationNFT.sol`, and `backend/app/services/blockchain.py`.

### 17. Foundry Path Issue

Problem:

`forge` was installed but not globally on PATH.

Fix:

Use:

```bash
/home/anzicle/.config/.foundry/bin/forge
```

### 18. Real Secret In Example File Risk

Problem:

An example env file can accidentally receive real secrets during setup.

Fix:

Cleaned `ai_service/.env.example`, added `.gitignore`, and kept real keys only in ignored `.env` files.

## problems in the hybrid AI model:
the use of llm for question assessment and rubric based model for grading lead to the grading signals being misaligned due too:

1. LLM feedback and final score are coming from different systems

* The LLM may say “good/excellent” semantically. But the final score may be blended with local TF-IDF/rule-based grading.
* If local similarity is low, it can drag the final score down.

2. Answer wording is correct but does not match expected keywords

* TF-IDF/keyword grading rewards overlap with the expected answer/material.
* A learner can explain correctly in different words, but still get a low local similarity score.

3. Question type mismatch

* Application/analysis answers need reasoning.
* If the learner gives a short answer, feedback may say it is conceptually okay, but score drops for lack of depth.

# Most likely order(likelihood logic):
1. **Very likely: LLM feedback and final score are from different signals**
   Your system blends LLM grading with local TF-IDF/rule-based grading. So the feedback can sound positive, but the final score can still be pulled down by the local score.

2. **Very likely: correct wording but low keyword/TF-IDF match**
   If your answer is correct but uses different words from the expected answer/material, local grading may score it low.

3. **Likely: question type needs more depth**
   For conceptual, application, and analysis questions, short answers may get nice feedback like “good understanding” but still lose marks for missing explanation, examples, or reasoning.


**1. Confirmed: feedback and score can come from different signals**

In [ai_service/app/assessment.py](/home/anzicle/project/ai_service/app/assessment.py), the final per-question score is blended:

```python
combined_score_100 = (0.6 * float(llm_grade["score"])) + (0.4 * local_score_100)
feedback = llm_grade.get("feedback") or local_grade.get("feedback")
```

So the **feedback shown can be from the LLM**, while the **score is LLM + local score combined**. If LLM says “good” but the local score is low, the final score can still look low.

**2. Confirmed: correct wording can score low if TF-IDF/keyword match is weak**

The local grader uses keyword overlap and TF-IDF cosine similarity. For example:

- Definition questions use word overlap with the material.
- Conceptual and analysis questions use TF-IDF similarity.
- If your answer is correct but uses different wording from the source material, local score can drop.

So yes, this can happen.

**3. Confirmed: short answers can score low for application/analysis questions**

Application questions reward practical markers and length:

```python
has_example
has_practical
has_reason
completeness = len(answer.split()) / 30
```

Analysis questions reward comparison/critical-thinking words like:

```python
however, although, compared, advantage, disadvantage, tradeoff
```

So if an answer is short or lacks those reasoning/example words, it can receive nice feedback but still lose marks.

Also, the frontend displays the score and feedback side by side in [frontend/public/scripts/learner.js](/home/anzicle/project/frontend/public/scripts/learner.js), so the mismatch becomes visible to the learner.

Verdict: **yes, all three are real possibilities in the current implementation.**


I’d solve it by making the **score, feedback, and displayed explanation come from the same final grading decision**, not from separate pieces.

Best approach:

1. **Make LLM the primary semantic grader**
   Since learners may answer correctly in different words, the LLM should carry more weight than TF-IDF.

   Current:

   ```text
   60% LLM + 40% local
   ```

   Better:

   ```text
   80% LLM + 20% local
   ```

   Or even:

   ```text
   LLM is final score
   local score is only a warning/check
   ```

2. **Use local grading as a consistency checker, not a score drag**
   Instead of letting TF-IDF punish correct answers, use it like this:

   - If LLM score is high and local score is low, flag: “low keyword overlap.”
   - Do not automatically reduce the learner’s score heavily.
   - Only reduce score if the LLM confidence is low or the answer is suspicious.

3. **Generate feedback after final score is calculated**
   Right now, feedback may say “excellent” while the blended score is low.

   Better flow:

   ```text
   local score calculated
   LLM score calculated
   final score calculated
   feedback generated from final score + reason
   ```

   So if final score is 42%, feedback should not say “excellent.” It should say something like:

   ```text
   Your answer shows some understanding, but the final score was reduced because it missed required rubric points.
   ```

4. **Show score breakdown in the UI**
   For debugging and transparency, show:

   ```text
   Final score: 58%
   Semantic score: 82%
   Local similarity score: 22%
   Reason: Answer was semantically relevant but had low overlap with expected course terms.
   ```

   You can hide this later, but during testing it is very useful.

5. **Improve question-type rubrics**
   Application and analysis questions should not depend on magic words like “however” or “advantage.”

   Better rubric:
   - Does the answer address the scenario?
   - Does it apply the correct concept?
   - Does it explain why?
   - Does it mention consequences or tradeoffs?

6. **Use expected answer/rubric from LLM more strongly**
   Since questions are LLM-generated, the expected answer and rubric should guide grading more than raw material TF-IDF.

   So for each answer, grade against:

   ```text
   question + expected_answer + rubric + student_answer
   ```

   Not mainly against material keyword overlap.

My recommended fix would be:

```text
Final score = 85% LLM score + 15% local score
```

Then generate learner feedback from the **final score**, while keeping local score as an internal consistency signal.

That would reduce unfair low scores while still keeping your local method as backup and anti-random-answer protection.

## Current Confirmed Status

Confirmed during development:

- OpenAI key visible to AI service.
- `gpt-4o-mini` reachable through OpenAI API.
- Real LLM generation produced valid 30-question assessment.
- Learner-facing questions did not expose expected answers.
- Backend blockchain health connected to Arbitrum Sepolia.
- Chain ID confirmed as `421614`.
- Smart contract tests passed with Foundry.
- Backend config parses production-style `DEBUG=release`.

Remaining caveat:

- Competency/anomaly trained model artifacts are not currently present, so those optional checks are disabled.

## Important Things To Note

- Do not commit `.env` files.
- Do not paste private keys or OpenAI keys into public files.
- Backend must be running before frontend workflows work.
- AI service must be running before assessment generation/grading works.
- Arbitrum Sepolia RPC must be valid before certificate minting works.
- Deployer private key must have test ETH for gas.
- Learners should not choose difficulty.
- Assessments always use 30 questions.
- LLM output is never trusted blindly; it is validated before use.
- Certificate verification requires token ID plus verification code.
- Public verification dashboard should not expose full learner data by default.

## Suggested Full Test Flow

1. Start AI service.
2. Start backend.
3. Start frontend.
4. Open `http://localhost:5173`.
5. Register issueraccount.
6. Create course.
7. Add material.
8. Create assessment template.
9. Generate enrollment code.
10. Log out.
11. Register learner account.
12. Enroll using code.
13. Select assessment.
14. Answer all 30 questions.
15. Submit for grading.
16. Confirm result.
17. If passed, confirm NFT/certificate issuance.
18. Use verification dashboard with token ID and verification code.

## Project Structure

```text
.
├── ai_service/
│   ├── app/
│   │   ├── main.py
│   │   ├── assessment.py
│   │   ├── llm_service.py
│   │   ├── model_service.py
│   │   ├── persistence.py
│   │   └── hash_utils.py
│   ├── models/
│   ├── requirements.txt
│   └── README.md
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   └── requirements.txt
├── contracts/
│   ├── src/
│   ├── script/
│   └── test/
├── frontend/
│   └── public/
│       ├── auth/
│       ├── scripts/
│       ├── styles/
│       └── index.html
└── README.md
```
SC-SVIMH31DFD
tpl_1779298660_f8468a
