# SkillCert AI Service

FastAPI service for SkillCert assessment generation and grading.

## Environment

Set these variables before starting the service:

```bash
cp ai_service/.env.example ai_service/.env
# then edit ai_service/.env and set:
# OPENAI_API_KEY=...
# OPENAI_MODEL=gpt-4o-mini
```

`OPENAI_API_KEY` is optional for local preview. If it is missing, the service
falls back to the existing TF-IDF/rule-based generator and grader.

The AI service automatically loads environment variables from `ai_service/.env`
when it starts, so you do not need to export the key in every terminal.

Optional local persistence path:

```bash
export AI_SERVICE_DB_PATH="/path/to/ai_service.db"
```

## Start

```bash
cd ai_service/app
../.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
```

## Hybrid Generation

`POST /create-assessment` first extracts key concepts with local TF-IDF logic,
then attempts LLM question generation. Valid LLM output must contain exactly:

- 8 definition questions
- 8 conceptual questions
- 7 application questions
- 7 analysis questions

If OpenAI is unavailable or the JSON fails validation, the local question
generator is used. The response includes `generation_method` as `llm` or
`local_fallback`.

Expected answers and rubrics are stored internally only. Learner-facing
responses include question text, type, difficulty, and points, but never expose
expected answers or rubrics.

## Hybrid Grading

`POST /grade-assessment` grades locally first, then attempts one batch LLM
grading call. If LLM grading succeeds, the final question score is:

- 60% LLM score
- 40% local TF-IDF/rule-based score

If LLM grading is unavailable, local grading is used entirely.

## Competency And Anomaly Checks

The service looks for model artifacts in `ai_service/models/`:

- `competency_model.joblib`
- `anomaly_model.joblib`
- `scaler.joblib`
- `feature_names.json`

Models are used only when all artifacts exist and the live feature dictionary
matches `feature_names.json`. Otherwise checks are skipped with a warning and
grading continues.

If an anomaly is detected after a passing score, the outcome becomes
`PENDING_REVIEW` instead of automatic `FAIL`.

## Assessment Report Hash

Grading returns `assessment_report` and `assessment_report_hash`. The hash is a
SHA-256 digest over deterministic JSON and can later be stored in NFT metadata
or pinned to IPFS as part of the certificate evidence trail.
