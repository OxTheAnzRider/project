/**
 * js/institution.js — Institution dashboard: material ingestion and certificate admin
 * 
 * Screens:
 *   1. Registration (FR-02)
 *   2. Material ingestion
 *   3. Revocation interface
 */

class InstitutionDashboard {
    constructor() {
        this.institution = null
        this.pendingReviews = []
    }

    init() {
        this.renderContent()
        wallet.onStateChanged(() => this.renderContent())
    }

    renderContent() {
        const container = document.getElementById('institution-content')

        if (!wallet.isConnected()) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <p class="text-gray-600 mb-4">Connect your wallet to access the institution dashboard</p>
                    <button class="btn btn-primary" onclick="institutionDashboard.connectWallet()">
                        Connect Wallet
                    </button>
                </div>
            `
            return
        }

        if (!this.institution) {
            this.renderRegistration()
        } else {
            this.renderDashboard()
        }
    }

    async connectWallet() {
        try {
            const { account } = await wallet.connect()
            showSuccess(`Connected: ${shortenAddress(account)}`)
        } catch (err) {
            showError(err.message)
        }
    }

    renderRegistration() {
        const container = document.getElementById('institution-content')
        container.innerHTML = `
            <div class="max-w-md mx-auto space-y-4">
                <h3 class="text-lg font-semibold mb-4">Register Institution (FR-02)</h3>
                <div class="form-group">
                    <label>Institution Name</label>
                    <input type="text" id="inst-name" placeholder="e.g., Lagos Technical Institute" />
                </div>
                <p class="text-xs text-gray-500">
                    Institution address: <span class="font-mono">${shortenAddress(wallet.getAccount())}</span>
                </p>
                <button class="btn btn-primary w-full" id="inst-submit" onclick="institutionDashboard.registerInstitution()">
                    Register
                </button>
                <p class="text-xs text-gray-500 text-center">
                    Next: Admin will grant ISSUER_ROLE via smart contract
                </p>
            </div>
        `
    }

    async registerInstitution() {
        const name = document.getElementById('inst-name').value.trim()
        if (!name) {
            showError('Please enter institution name')
            return
        }

        const btn = document.getElementById('inst-submit')
        btn.disabled = true

        try {
            const result = await api.registerInstitution(name, wallet.getAccount())
            this.institution = {
                wallet: wallet.getAccount(),
                did: result.did,
                name,
            }
            showSuccess('Institution registered!')
            this.renderContent()
        } catch (err) {
            showError(err.message)
        } finally {
            btn.disabled = false
        }
    }

    async renderDashboard() {
        const container = document.getElementById('institution-content')
        container.innerHTML = `
            <div class="space-y-6">
                <!-- Welcome -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">${escapeHtml(this.institution.name)}</h3>
                        <p class="card-subtitle">DID: <span class="font-mono text-xs">${shortenAddress(this.institution.did)}</span></p>
                    </div>
                    <button class="btn btn-sm btn-secondary" onclick="institutionDashboard.logOut()">Log Out</button>
                </div>

                <!-- Tabs for Material, Pending, Revoke -->
                <div class="flex gap-2 border-b border-gray-200">
                    <button class="px-4 py-2 border-b-2 border-indigo-600 text-indigo-600 font-medium" onclick="institutionDashboard.showTab('material')">
                        Upload Material
                    </button>
                    <button class="px-4 py-2 text-gray-600 hover:text-gray-900" onclick="institutionDashboard.showTab('pending')">
                        Pending Review (FR-04)
                    </button>
                    <button class="px-4 py-2 text-gray-600 hover:text-gray-900" onclick="institutionDashboard.showTab('revoke')">
                        Revoke Certificate (FR-07)
                    </button>
                </div>

                <!-- Material tab -->
                <div id="tab-material" class="card">
                    <div class="card-header">
                        <h3 class="card-title">Upload Learning Material</h3>
                        <p class="card-subtitle">Create source material for AI-generated learner assessments.</p>
                    </div>
                    <form id="material-form" onsubmit="institutionDashboard.submitMaterial(event)">
                        <div class="form-group">
                            <label>Programme</label>
                            <input type="text" id="material-programme" placeholder="e.g., Solar Installation Basics" required />
                        </div>
                        <div class="form-group">
                            <label>Title</label>
                            <input type="text" id="material-title" placeholder="e.g., Battery Safety and Wiring" required />
                        </div>
                        <div class="form-group">
                            <label>Difficulty</label>
                            <select id="material-difficulty">
                                <option value="beginner">Beginner</option>
                                <option value="intermediate" selected>Intermediate</option>
                                <option value="advanced">Advanced</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Topics</label>
                            <input type="text" id="material-topics" placeholder="Comma-separated topics" />
                        </div>
                        <div class="form-group">
                            <label>Material Content</label>
                            <textarea id="material-content" placeholder="Paste the lesson material learners should be assessed against..." required></textarea>
                        </div>
                        <button type="submit" id="material-submit" class="btn btn-primary w-full">Upload Material</button>
                    </form>
                    <div id="material-result" class="mt-4"></div>
                </div>

                <!-- Pending reviews tab -->
                <div id="tab-pending" class="hidden">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Assessments Awaiting Human Adjudication</h3>
                            <p class="card-subtitle">Cases where AI confidence is below threshold</p>
                        </div>
                        <div id="pending-list">
                            <p class="text-gray-600">No pending reviews at this time.</p>
                        </div>
                    </div>
                </div>

                <!-- Revoke tab -->
                <div id="tab-revoke" class="hidden">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Revoke Certificate</h3>
                            <p class="card-subtitle">Flag a certificate as revoked on-chain</p>
                        </div>
                        <form id="revoke-form" onsubmit="institutionDashboard.revokeCertificate(event)">
                            <div class="form-group">
                                <label>Token ID (on-chain)</label>
                                <input type="number" id="revoke-tokenid" placeholder="e.g., 42" />
                            </div>
                            <div class="form-group">
                                <label>Reason</label>
                                <textarea id="revoke-reason" placeholder="Why is this certificate being revoked?"></textarea>
                            </div>
                            <button type="submit" class="btn btn-danger w-full">Revoke Certificate</button>
                        </form>
                    </div>
                </div>
            </div>
        `

        // Load pending reviews
        await this.loadPendingReviews()
    }

    showTab(tabName) {
        document.querySelectorAll('[id^="tab-"]').forEach(tab => tab.classList.add('hidden'))
        document.getElementById(`tab-${tabName}`).classList.remove('hidden')
    }

    async loadPendingReviews() {
        try {
            const result = await api.getPendingReviews(this.institution.wallet)
            const list = document.getElementById('pending-list')

            if (!result.pending || result.pending.length === 0) {
                list.innerHTML = '<p class="text-gray-600">No pending reviews.</p>'
                return
            }

            list.innerHTML = result.pending.map(a => `
                <div class="border border-gray-200 rounded-lg p-4 mb-2">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="font-medium">${escapeHtml(a.learner_name)}</p>
                            <p class="text-xs text-gray-600">${a.programme}</p>
                        </div>
                        <button class="btn btn-sm btn-primary" onclick="institutionDashboard.showAdjudication(${a.id})">
                            Review
                        </button>
                    </div>
                </div>
            `).join('')
        } catch (err) {
            console.error('Failed to load pending reviews:', err)
        }
    }

    showAdjudication(assessmentId) {
        openModal('Adjudicate Assessment', `
            <form onsubmit="institutionDashboard.submitAdjudication(${assessmentId}, event)">
                <div class="form-group">
                    <label>Decision</label>
                    <select id="adj-outcome" required>
                        <option value="">-- Select --</option>
                        <option value="PASS">PASS</option>
                        <option value="FAIL">FAIL</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Notes</label>
                    <textarea id="adj-notes" placeholder="Any additional notes..."></textarea>
                </div>
                <button type="submit" class="btn btn-primary w-full">Confirm Adjudication</button>
            </form>
        `)
    }

    async submitAdjudication(assessmentId, e) {
        e.preventDefault()
        const outcome = document.getElementById('adj-outcome').value
        const notes = document.getElementById('adj-notes').value

        try {
            await api.adjudicateAssessment(assessmentId, outcome, this.institution.wallet, notes)
            closeModal()
            showSuccess(`Adjudication complete: ${outcome}`)
            await this.loadPendingReviews()
        } catch (err) {
            showError(err.message)
        }
    }

    async submitMaterial(e) {
        e.preventDefault()
        const programme = document.getElementById('material-programme').value.trim()
        const title = document.getElementById('material-title').value.trim()
        const difficulty = document.getElementById('material-difficulty').value
        const topics = document.getElementById('material-topics').value
            .split(',')
            .map(topic => topic.trim())
            .filter(Boolean)
        const content = document.getElementById('material-content').value.trim()
        const button = document.getElementById('material-submit')
        const resultBox = document.getElementById('material-result')

        if (!programme || !title || !content) {
            showError('Please fill programme, title, and material content.')
            return
        }

        button.disabled = true
        button.textContent = 'Uploading...'

        try {
            const result = await api.ingestMaterial({
                institution_id: this.institution.did,
                programme,
                title,
                content,
                difficulty_level: difficulty,
                topics,
            })

            resultBox.innerHTML = `
                <div class="alert alert-success">
                    <p class="font-medium">Material ready for assessment.</p>
                    <p class="text-sm mt-1">Material ID: <span class="font-mono">${escapeHtml(result.material_id)}</span></p>
                </div>
            `
            document.getElementById('material-form').reset()
            showSuccess('Material uploaded.')
        } catch (err) {
            showError(err.message)
        } finally {
            button.disabled = false
            button.textContent = 'Upload Material'
        }
    }

    async revokeCertificate(e) {
        e.preventDefault()
        const tokenId = document.getElementById('revoke-tokenid').value
        const reason = document.getElementById('revoke-reason').value

        if (!tokenId || !reason) {
            showError('Please fill all fields')
            return
        }

        try {
            await api.revokeCertificate(parseInt(tokenId), this.institution.wallet, reason)
            showSuccess(`Certificate ${tokenId} revoked`)
            document.getElementById('revoke-form').reset()
        } catch (err) {
            showError(err.message)
        }
    }

    logOut() {
        this.institution = null
        this.renderContent()
    }
}

const institutionDashboard = new InstitutionDashboard()
