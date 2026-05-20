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
        this.institution = this.loadAuthenticatedInstitution()
        this.pendingReviews = []
        this.courses = []
    }

    init() {
        this.renderContent()
        wallet.onStateChanged(() => this.renderContent())
    }

    renderContent() {
        const container = document.getElementById('institution-content')
        const user = auth.user()

        if (!auth.isAuthenticated()) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <p class="text-gray-600 mb-4">Login with an Institution account to create courses.</p>
                    <a class="btn btn-primary" href="/auth/login.html">Login</a>
                    <a class="btn btn-secondary" href="/auth/register.html">Register Institution</a>
                </div>
            `
            return
        }

        if (user?.role !== 'INSTITUTION') {
            container.innerHTML = `
                <div class="text-center py-12">
                    <p class="text-gray-600 mb-4">Your current account is not an Institution account.</p>
                    <button class="btn btn-secondary" onclick="auth.logout()">Logout</button>
                    <a class="btn btn-primary" href="/auth/register.html">Create Institution Account</a>
                </div>
            `
            return
        }

        if (!this.institution) {
            this.institution = this.loadAuthenticatedInstitution()
        }

        this.renderDashboard()
    }

    loadAuthenticatedInstitution() {
        const user = auth.user()
        if (!user || user.role !== 'INSTITUTION') return null
        return {
            wallet: user.wallet_address,
            did: `did:ethr:arbitrum:${user.wallet_address}`,
            name: user.email || 'Institution',
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
            <div class="max-w-md mx-auto text-center py-12">
                <p class="text-gray-600 mb-4">Institution registration now happens on the dedicated auth page.</p>
                <a class="btn btn-primary" href="/auth/register.html">Register Institution</a>
            </div>
        `
    }

    async registerInstitution() {
        window.location.href = '/auth/register.html'
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
                        <h3 class="card-title">Courses, Codes, and Materials</h3>
                        <p class="card-subtitle">Create courses, generate enrollment codes, upload materials, and create 30-question assessment templates.</p>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <form class="card" onsubmit="institutionDashboard.createCourse(event)">
                            <h4 class="font-semibold mb-4">Create Course</h4>
                            <div class="form-group">
                                <label>Course Title</label>
                                <input id="course-title" required />
                            </div>
                            <div class="form-group">
                                <label>Description</label>
                                <textarea id="course-description" required></textarea>
                            </div>
                            <button class="btn btn-primary w-full" type="submit">Create Course</button>
                        </form>

                        <form class="card" onsubmit="institutionDashboard.generateCodes(event)">
                            <h4 class="font-semibold mb-4">Generate Codes</h4>
                            <div class="form-group">
                                <label>Course ID</label>
                                <input id="code-course-id" required />
                            </div>
                            <div class="form-group">
                                <label>Count</label>
                                <input id="code-count" type="number" min="1" max="500" value="5" />
                            </div>
                            <div class="form-group">
                                <label>Quota Per Code</label>
                                <input id="code-quota" type="number" min="1" max="1000" value="1" />
                            </div>
                            <button class="btn btn-primary w-full" type="submit">Generate</button>
                        </form>

                        <form class="card" onsubmit="institutionDashboard.createTemplate(event)">
                            <h4 class="font-semibold mb-4">Create Assessment</h4>
                            <div class="form-group">
                                <label>Course ID</label>
                                <input id="template-course-id" required />
                            </div>
                            <div class="form-group">
                                <label>Material ID</label>
                                <input id="template-material-id" required />
                            </div>
                            <div class="form-group">
                                <label>Assessment Title</label>
                                <input id="template-title" required />
                            </div>
                            <button class="btn btn-primary w-full" type="submit">Create 30-Question Template</button>
                        </form>
                    </div>
                    <div id="course-result" class="mt-4"></div>

                    <div class="card mt-4">
                        <div class="card-header">
                            <div class="flex items-center justify-between gap-3">
                                <div>
                                    <h3 class="card-title">Courses Created</h3>
                                    <p class="card-subtitle">Courses, enrollment counts, and assessment template counts for this institution.</p>
                                </div>
                                <button class="btn btn-sm btn-secondary" onclick="institutionDashboard.loadCourses()">Refresh</button>
                            </div>
                        </div>
                        <div id="institution-course-list">
                            <p class="text-sm text-gray-600">Loading courses...</p>
                        </div>
                    </div>

                    <div class="card mt-4">
                        <div class="card-header">
                            <h3 class="card-title">Upload Learning Material</h3>
                            <p class="card-subtitle">Paste text material for AI-generated learner assessments.</p>
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
        await this.loadCourses()
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

    async createCourse(e) {
        e.preventDefault()
        try {
            const result = await api.createCourse({
                title: document.getElementById('course-title').value.trim(),
                description: document.getElementById('course-description').value.trim(),
            })
            document.getElementById('course-result').innerHTML = `
                <div class="alert alert-success">Course created. Course ID: <span class="font-mono">${escapeHtml(result.course_id)}</span></div>
            `
            document.getElementById('course-title').value = ''
            document.getElementById('course-description').value = ''
            await this.loadCourses()
            showSuccess('Course created.')
        } catch (err) {
            showError(err.message)
        }
    }

    async generateCodes(e) {
        e.preventDefault()
        try {
            const courseId = document.getElementById('code-course-id').value.trim()
            const result = await api.generateCourseCodes(courseId, {
                count: Number(document.getElementById('code-count').value || 1),
                quota: Number(document.getElementById('code-quota').value || 1),
                expires_in_days: 30,
            })
            document.getElementById('course-result').innerHTML = `
                <div class="alert alert-success">
                    <p class="font-medium">Codes generated</p>
                    <p class="font-mono text-sm">${result.codes.map(escapeHtml).join('<br>')}</p>
                </div>
            `
            await this.loadCourses()
        } catch (err) {
            showError(err.message)
        }
    }

    async createTemplate(e) {
        e.preventDefault()
        try {
            const courseId = document.getElementById('template-course-id').value.trim()
            const result = await api.createAssessmentTemplate(courseId, {
                course_id: courseId,
                material_id: document.getElementById('template-material-id').value.trim(),
                title: document.getElementById('template-title').value.trim(),
                description: 'Institution-created assessment template',
            })
            document.getElementById('course-result').innerHTML = `
                <div class="alert alert-success">Assessment template created. ID: <span class="font-mono">${escapeHtml(result.assessment_template_id)}</span></div>
            `
            document.getElementById('template-title').value = ''
            await this.loadCourses()
        } catch (err) {
            showError(err.message)
        }
    }

    async loadCourses() {
        const container = document.getElementById('institution-course-list')
        if (!container) return

        container.innerHTML = `<div class="flex items-center gap-2 text-sm text-gray-600">${getLoadingSpinner()} Loading courses...</div>`
        try {
            const result = await api.institutionCourses()
            this.courses = result.courses || []

            if (!this.courses.length) {
                container.innerHTML = '<p class="text-sm text-gray-600">No courses created yet.</p>'
                return
            }

            container.innerHTML = `
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead>
                            <tr class="text-left border-b border-gray-200">
                                <th class="py-2 pr-3">Course</th>
                                <th class="py-2 pr-3">Created</th>
                                <th class="py-2 pr-3">Programme</th>
                                <th class="py-2 pr-3">Material IDs</th>
                                <th class="py-2 pr-3">Course Codes</th>
                                <th class="py-2 pr-3">Course ID</th>
                                <th class="py-2 pr-3">Status</th>
                                <th class="py-2 pr-3">Learners</th>
                                <th class="py-2 pr-3">Assessments</th>
                                <th class="py-2">Use</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this.courses.map(course => {
                                const programmes = this.uniqueValues((course.materials || []).map(material => material.programme))
                                const materialIds = this.uniqueValues((course.materials || []).map(material => material.material_id))
                                const codes = course.codes || []
                                return `
                                <tr class="border-b border-gray-100 align-top">
                                    <td class="py-3 pr-3">
                                        <p class="font-medium text-gray-900">${escapeHtml(course.title)}</p>
                                        <p class="text-xs text-gray-600">${escapeHtml(course.description || '')}</p>
                                    </td>
                                    <td class="py-3 pr-3 text-xs">${escapeHtml(formatDate(course.created_at))}</td>
                                    <td class="py-3 pr-3 text-xs">${programmes.length ? programmes.map(escapeHtml).join('<br>') : '<span class="text-gray-400">Not linked</span>'}</td>
                                    <td class="py-3 pr-3 font-mono text-xs">${materialIds.length ? materialIds.map(escapeHtml).join('<br>') : '<span class="text-gray-400 font-sans">None</span>'}</td>
                                    <td class="py-3 pr-3">
                                        ${codes.length ? codes.map(code => `
                                            <div class="mb-2">
                                                <p class="font-mono text-xs">${escapeHtml(code.code)}</p>
                                                <p class="text-xs text-gray-500">${Number(code.used_count || 0)}/${Number(code.quota || 0)} used • ${escapeHtml(code.status)}</p>
                                            </div>
                                        `).join('') : '<span class="text-xs text-gray-400">No codes</span>'}
                                    </td>
                                    <td class="py-3 pr-3 font-mono text-xs">${escapeHtml(course.course_id)}</td>
                                    <td class="py-3 pr-3"><span class="badge badge-success">${escapeHtml(course.status)}</span></td>
                                    <td class="py-3 pr-3">${Number(course.enrollments || 0)}</td>
                                    <td class="py-3 pr-3">${Number(course.assessments || 0)}</td>
                                    <td class="py-3">
                                        <button class="btn btn-sm btn-secondary" onclick="institutionDashboard.useCourse('${escapeHtml(course.course_id)}')">Fill ID</button>
                                    </td>
                                </tr>
                            `}).join('')}
                        </tbody>
                    </table>
                </div>
            `
        } catch (err) {
            container.innerHTML = '<p class="text-sm text-red-600">Could not load created courses. Login again if your session expired.</p>'
            showError(err.message)
        }
    }

    uniqueValues(values) {
        return [...new Set(values.filter(Boolean))]
    }

    useCourse(courseId) {
        const codeInput = document.getElementById('code-course-id')
        const templateInput = document.getElementById('template-course-id')
        if (codeInput) codeInput.value = courseId
        if (templateInput) templateInput.value = courseId
        showSuccess('Course ID filled into the forms.')
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
        auth.logout()
    }
}

const institutionDashboard = new InstitutionDashboard()
