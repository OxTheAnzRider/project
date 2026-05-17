const API_BASE = window.API_BASE || 'http://localhost:8000/api'

class APIClient {
    async request(method, endpoint, data = null) {
        const url = `${API_BASE}${endpoint}`
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        }
        if (data) options.body = JSON.stringify(data)

        try {
            const resp = await fetch(url, options)
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({ message: resp.statusText }))
                throw new Error(err.message || `HTTP ${resp.status}`)
            }
            return await resp.json()
        } catch (err) {
            console.error(`API ${method} ${endpoint}:`, err)
            throw err
        }
    }

    // ── Learners ─────────────────────────────────────────────────────────
    registerLearner(fullName, email, walletAddress, programme) {
        return this.request('POST', '/learners/register', {
            full_name: fullName,
            email,
            wallet_address: walletAddress,
            programme,
        })
    }

    // ── Assessments ──────────────────────────────────────────────────────
    ingestMaterial(data) {
        return this.request('POST', '/assessments/materials/ingest', data)
    }

    createAssessment(data) {
        return this.request('POST', '/assessments/create', data)
    }

    submitAnswer(assessmentId, questionId, answerText) {
        return this.request('POST', `/assessments/${assessmentId}/answers/submit`, {
            question_id: questionId,
            answer_text: answerText,
        })
    }

    gradeAssessment(assessmentId) {
        return this.request('POST', `/assessments/${assessmentId}/grade`, {})
    }

    getAssessmentResult(assessmentId) {
        return this.request('GET', `/assessments/${assessmentId}/result`)
    }

    getAssessment(id) {
        return this.getAssessmentResult(id)
    }

    submitAssessment(data) {
        return this.createAssessment(data)
    }

    adjudicateAssessment(id, outcome, supervisorWallet, notes) {
        return this.request('POST', `/assessments/${id}/adjudicate`, {
            outcome,
            supervisor_wallet: supervisorWallet,
            notes,
        })
    }

    // ── Certificates ─────────────────────────────────────────────────────
    async verifyCertificate(tokenId) {
        return this.request('GET', `/certificates/${tokenId}/verify`)
    }

    revokeCertificate(tokenId, institutionWallet, reason) {
        return this.request('POST', `/certificates/${tokenId}/revoke`, {
            institution_wallet: institutionWallet,
            reason,
        })
    }

    getLearnerCertificates(did) {
        return this.request('GET', `/certificates/learner/${encodeURIComponent(did)}`)
    }

    // ── Institutions ─────────────────────────────────────────────────────
    registerInstitution(name, walletAddress) {
        return this.request('POST', '/institutions/register', {
            name,
            wallet_address: walletAddress,
        })
    }

    getPendingReviews(walletAddress) {
        return this.request('GET', `/institutions/${walletAddress}/pending-reviews`)
    }

    // ── Health ───────────────────────────────────────────────────────────
    async health() {
        try {
            return await this.request('GET', '/health')
        } catch {
            return { status: 'unavailable' }
        }
    }
}

const api = new APIClient()
