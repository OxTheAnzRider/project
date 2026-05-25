const API_HOST = window.location.hostname || 'localhost'
const API_BASE = window.API_BASE || `http://${API_HOST}:8000/api`

class APIClient {
    async request(method, endpoint, data = null) {
        const url = `${API_BASE}${endpoint}`
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        }
        const token = localStorage.getItem('skillcert-access-token')
        if (token) options.headers.Authorization = `Bearer ${token}`
        if (data) options.body = JSON.stringify(data)

        try {
            const resp = await fetch(url, options)
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({ message: resp.statusText }))
                throw new Error(err.message || err.detail || `HTTP ${resp.status}`)
            }
            return await resp.json()
        } catch (err) {
            console.error(`API ${method} ${endpoint}:`, err)
            throw err
        }
    }

    // ── Learners ─────────────────────────────────────────────────────────
    registerAccount(data) {
        return this.request('POST', '/auth/register', data)
    }

    login(email, password) {
        return this.request('POST', '/auth/login', { email, password })
    }

    currentUser() {
        return this.request('GET', '/auth/me')
    }

    logout(refreshToken) {
        return this.request('POST', '/auth/logout', { refresh_token: refreshToken })
    }

    listCourses() {
        return this.request('GET', '/courses')
    }

    enrollWithCode(code) {
        return this.request('POST', '/courses/enroll', { code })
    }

    myCourses() {
        return this.request('GET', '/courses/mine')
    }

    createCourse(data) {
        return this.request('POST', '/issuers/courses', data)
    }

    issuerCourses() {
        return this.request('GET', '/issuers/courses')
    }

    generateCourseCodes(courseId, data) {
        return this.request('POST', `/issuers/courses/${courseId}/codes`, data)
    }

    createAssessmentTemplate(courseId, data) {
        return this.request('POST', `/issuers/courses/${courseId}/templates`, data)
    }

    registryStats() {
        return this.request('GET', '/certificates/registry/stats')
    }

    verifyWithCode(tokenId, verificationCode, qrPayload = null) {
        return this.request('POST', '/certificates/verify', {
            token_id: Number(tokenId),
            verification_code: verificationCode,
            qr_payload: qrPayload,
        })
    }

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

    revokeCertificate(tokenId, issuerWallet, reason) {
        return this.request('POST', `/certificates/${tokenId}/revoke`, {
            issuer_wallet: issuerWallet,
            reason,
        })
    }

    getLearnerCertificates(did) {
        return this.request('GET', `/certificates/learner/${encodeURIComponent(did)}`)
    }

    // ── Issuers ─────────────────────────────────────────────────────
    registerIssuer(name, walletAddress) {
        return this.request('POST', '/issuers/register', {
            name,
            wallet_address: walletAddress,
        })
    }

    getPendingReviews(walletAddress) {
        return this.request('GET', `/issuers/${walletAddress}/pending-reviews`)
    }

    issuerLearners() {
        return this.request('GET', '/issuers/learners')
    }

    issuerMaterials() {
        return this.request('GET', '/issuers/materials')
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
