/**
 * js/verifier.js - Anonymous public certificate registry and secure verification.
 */

class VerificationInterface {
    init() {
        this.renderContent()
        this.loadStats()
    }

    renderContent() {
        const container = document.getElementById('verifier-content')
        container.innerHTML = `
            <div class="space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4" id="registry-stats">
                    <div class="card"><p class="text-sm text-gray-500">Total Certificates</p><p class="text-2xl font-bold">...</p></div>
                    <div class="card"><p class="text-sm text-gray-500">Institutions</p><p class="text-2xl font-bold">...</p></div>
                    <div class="card"><p class="text-sm text-gray-500">Courses</p><p class="text-2xl font-bold">...</p></div>
                    <div class="card"><p class="text-sm text-gray-500">Last 7 Days</p><p class="text-2xl font-bold">...</p></div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Verify Certificate</h3>
                        <p class="card-subtitle">Token ID and verification code are both required. Public registry stats never reveal learner details.</p>
                    </div>
                    <form id="verify-form" onsubmit="verifier.verifyToken(event)">
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="form-group">
                                <label>Certificate Token ID</label>
                                <input type="number" id="token-id" required />
                            </div>
                            <div class="form-group">
                                <label>Verification Code</label>
                                <input type="text" id="verification-code" placeholder="SC-2026-ABC123XYZ" required />
                            </div>
                            <div class="form-group">
                                <label>QR Payload</label>
                                <input type="text" id="qr-payload" placeholder="Optional scanned QR value" />
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary w-full">Verify</button>
                    </form>
                </div>

                <div id="result-container" class="hidden"></div>
            </div>
        `
    }

    async loadStats() {
        try {
            const stats = await api.registryStats()
            document.getElementById('registry-stats').innerHTML = `
                <div class="card"><p class="text-sm text-gray-500">Total Certificates</p><p class="text-2xl font-bold">${stats.total_certificates_issued}</p></div>
                <div class="card"><p class="text-sm text-gray-500">Institutions</p><p class="text-2xl font-bold">${stats.institutions}</p></div>
                <div class="card"><p class="text-sm text-gray-500">Courses</p><p class="text-2xl font-bold">${stats.courses}</p></div>
                <div class="card"><p class="text-sm text-gray-500">Last 7 Days</p><p class="text-2xl font-bold">${stats.last_7_days}</p></div>
            `
        } catch (err) {
            console.warn('Registry stats unavailable:', err.message)
        }
    }

    async verifyToken(e) {
        e.preventDefault()
        const tokenId = document.getElementById('token-id').value
        const code = document.getElementById('verification-code').value.trim()
        const qrPayload = document.getElementById('qr-payload').value.trim() || null
        const btn = e.target.querySelector('button[type="submit"]')
        btn.disabled = true
        btn.textContent = 'Verifying...'

        try {
            const result = await api.verifyWithCode(tokenId, code, qrPayload)
            this.showResult(result)
        } catch (err) {
            this.showError(err.message)
        } finally {
            btn.disabled = false
            btn.textContent = 'Verify'
        }
    }

    showResult(result) {
        const container = document.getElementById('result-container')
        container.classList.remove('hidden')
        if (!result.valid) {
            container.innerHTML = `<div class="alert alert-error">Certificate not found or code incorrect.</div>`
            return
        }
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title"><span class="badge badge-success">VERIFIED</span></h3>
                </div>
                <div class="space-y-3">
                    <p><strong>Token ID:</strong> ${result.token_id}</p>
                    <p><strong>Learner Wallet:</strong> ${escapeHtml(result.learner_wallet)}</p>
                    <p><strong>Institution:</strong> ${escapeHtml(result.institution_name)}</p>
                    <p><strong>Course:</strong> ${escapeHtml(result.course_name || '')}</p>
                    <p><strong>Date Issued:</strong> ${escapeHtml(result.date_issued || '')}</p>
                    <p><strong>Score:</strong> ${Number(result.score_percentage || 0).toFixed(1)}%</p>
                </div>
            </div>
        `
    }

    showError(message) {
        const container = document.getElementById('result-container')
        container.classList.remove('hidden')
        container.innerHTML = `<div class="alert alert-error">${escapeHtml(message)}</div>`
    }
}

const verifier = new VerificationInterface()
