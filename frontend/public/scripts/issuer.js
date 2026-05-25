/**
 * Issuer dashboard: courses, materials, assessment templates, learner history,
 * and certificate revocation.
 */

class IssuerDashboardController {
    constructor() {
        this.issuer = null
        this.courses = []
        this.materials = []
        this.history = null
    }

    init() {
        this.bootstrapFromAuth()
        this.renderContent()
    }

    bootstrapFromAuth() {
        const user = auth.user()
        if (!user || user.role !== 'issuer') {
            this.issuer = null
            return
        }
        this.issuer = {
            id: user.issuer_id,
            wallet: user.wallet_address,
            did: `did:ethr:arbitrum:${user.wallet_address}`,
            name: user.email,
        }
    }

    renderContent() {
        const container = document.getElementById('issuer-content')
        if (!this.issuer) {
            container.innerHTML = `
                <div class="card text-center">
                    <p class="text-gray-700 mb-4">Login with an issuer account to access this dashboard.</p>
                    <a class="btn btn-primary" href="/auth/login.html">Login</a>
                </div>
            `
            return
        }
        this.renderDashboard()
    }

    async renderDashboard() {
        const container = document.getElementById('issuer-content')
        container.innerHTML = `
            <div class="space-y-6">
                <div class="card">
                    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                        <div>
                            <h3 class="card-title">Issuer Dashboard</h3>
                            <p class="card-subtitle">Wallet: <span class="font-mono">${escapeHtml(this.issuer.wallet)}</span></p>
                        </div>
                        <button class="btn btn-sm btn-secondary" onclick="auth.logout()">Log Out</button>
                    </div>
                </div>

                <div class="flex flex-wrap gap-2 border-b border-gray-200">
                    ${this.tabButton('courses', 'Courses Created', true)}
                    ${this.tabButton('materials', 'Materials')}
                    ${this.tabButton('assessments', 'Assessments')}
                    ${this.tabButton('history', 'Previous History')}
                    ${this.tabButton('revoke', 'Revoke')}
                </div>

                <div id="tab-courses" class="space-y-4">${this.renderCoursesTab()}</div>
                <div id="tab-materials" class="space-y-4 hidden">${this.renderMaterialsTab()}</div>
                <div id="tab-assessments" class="space-y-4 hidden">${this.renderAssessmentsTab()}</div>
                <div id="tab-history" class="space-y-4 hidden">${this.renderHistoryTab()}</div>
                <div id="tab-revoke" class="space-y-4 hidden">${this.renderRevokeTab()}</div>
            </div>
        `
        await this.loadCourses()
    }

    tabButton(name, label, active = false) {
        return `
            <button
                id="tab-btn-${name}"
                class="issuer-tab-btn px-4 py-2 border-b-2 ${active ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-600 hover:text-gray-900'} font-medium"
                onclick="IssuerDashboard.showTab('${name}')"
            >
                ${label}
            </button>
        `
    }

    showTab(tabName) {
        document.querySelectorAll('[id^="tab-"]').forEach(tab => {
            if (!tab.classList.contains('issuer-tab-btn')) tab.classList.add('hidden')
        })
        document.querySelectorAll('.issuer-tab-btn').forEach(btn => {
            btn.classList.remove('border-indigo-600', 'text-indigo-600')
            btn.classList.add('border-transparent', 'text-gray-600')
        })
        document.getElementById(`tab-${tabName}`)?.classList.remove('hidden')
        const active = document.getElementById(`tab-btn-${tabName}`)
        if (active) {
            active.classList.add('border-indigo-600', 'text-indigo-600')
            active.classList.remove('border-transparent', 'text-gray-600')
        }
        if (tabName === 'history') this.loadHistory()
    }

    renderCoursesTab() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Create Course</h3>
                    <p class="card-subtitle">Courses are visible to learners, but materials stay hidden until assessment.</p>
                </div>
                <form onsubmit="IssuerDashboard.createCourse(event)">
                    <div class="form-group">
                        <label>Course Title</label>
                        <input id="course-title" required placeholder="e.g., Electrical Safety" />
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea id="course-description" required placeholder="Brief course description for learners"></textarea>
                    </div>
                    <button id="course-submit" class="btn btn-primary" type="submit">Create Course</button>
                </form>
            </div>
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Courses Created</h3>
                    <p class="card-subtitle">Track course codes, materials, templates, and enrollment counts.</p>
                </div>
                <div id="issuer-course-list"><p class="text-sm text-gray-600">Loading courses...</p></div>
            </div>
        `
    }

    renderMaterialsTab() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Upload Learning Material</h3>
                    <p class="card-subtitle">Material is used by the AI service to generate assessment questions.</p>
                </div>
                <form id="material-form" onsubmit="IssuerDashboard.submitMaterial(event)">
                    <div class="form-group">
                        <label>Programme</label>
                        <input type="text" id="material-programme" placeholder="e.g., Electrical Safety" required />
                    </div>
                    <div class="form-group">
                        <label>Title</label>
                        <input type="text" id="material-title" placeholder="e.g., Lockout Tagout Basics" required />
                    </div>
                    <div class="form-group">
                        <label>Topics</label>
                        <input type="text" id="material-topics" placeholder="Comma-separated topics" />
                    </div>
                    <div class="form-group">
                        <label>Material Content</label>
                        <textarea id="material-content" placeholder="Paste the course material..." required></textarea>
                    </div>
                    <button type="submit" id="material-submit" class="btn btn-primary">Save Material</button>
                </form>
                <div id="material-result" class="mt-4"></div>
            </div>
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Known Materials</h3>
                    <p class="card-subtitle">Materials currently linked to assessment templates.</p>
                </div>
                <div id="issuer-material-list"><p class="text-sm text-gray-600">No materials linked yet.</p></div>
            </div>
        `
    }

    renderAssessmentsTab() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Create Assessment Template</h3>
                    <p class="card-subtitle">Each template creates a separate 30-question assessment for a course.</p>
                </div>
                <form onsubmit="IssuerDashboard.createTemplate(event)">
                    <div class="form-group">
                        <label>Course</label>
                        <select id="template-course" required></select>
                    </div>
                    <div class="form-group">
                        <label>Template Title</label>
                        <input id="template-title" required placeholder="e.g., Final Safety Assessment" />
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea id="template-description" placeholder="Optional assessment description"></textarea>
                    </div>
                    <div class="form-group">
                        <label>Material ID</label>
                        <input id="template-material-id" required placeholder="mat_..." />
                    </div>
                    <button id="template-submit" class="btn btn-primary" type="submit">Create Assessment Template</button>
                </form>
            </div>
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Assessment Templates</h3>
                    <p class="card-subtitle">Learners use the template ID after enrolling in the course.</p>
                </div>
                <div id="issuer-template-list"><p class="text-sm text-gray-600">No templates yet.</p></div>
            </div>
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Generate Course Codes</h3>
                    <p class="card-subtitle">Learners need these codes to enroll.</p>
                </div>
                <form onsubmit="IssuerDashboard.generateCodes(event)" class="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <select id="code-course" required></select>
                    <input id="code-count" type="number" min="1" max="100" value="1" />
                    <input id="code-quota" type="number" min="1" max="1000" value="1" />
                    <button class="btn btn-secondary" type="submit">Generate Codes</button>
                </form>
                <div id="code-result" class="mt-4"></div>
            </div>
        `
    }

    renderHistoryTab() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Learners & Previous History</h3>
                    <p class="card-subtitle">Enrollment and assessment records for your courses.</p>
                </div>
                <div id="issuer-history-list"><p class="text-sm text-gray-600">Open this tab to load history.</p></div>
            </div>
        `
    }

    renderRevokeTab() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Revoke Certificate</h3>
                    <p class="card-subtitle">Flag a certificate as revoked on-chain.</p>
                </div>
                <form id="revoke-form" onsubmit="IssuerDashboard.revokeCertificate(event)">
                    <div class="form-group">
                        <label>Token ID</label>
                        <input type="number" id="revoke-tokenid" placeholder="e.g., 42" required />
                    </div>
                    <div class="form-group">
                        <label>Reason</label>
                        <textarea id="revoke-reason" placeholder="Why is this certificate being revoked?" required></textarea>
                    </div>
                    <button type="submit" class="btn btn-danger">Revoke Certificate</button>
                </form>
            </div>
        `
    }

    async loadCourses() {
        try {
            const [courseResult, materialResult] = await Promise.all([
                api.issuerCourses(),
                api.issuerMaterials(),
            ])
            this.courses = courseResult.courses || []
            this.materials = materialResult.materials || []
            this.renderCourseList()
            this.renderMaterialList()
            this.renderTemplateList()
            this.populateCourseSelects()
        } catch (err) {
            showError(err.message)
        }
    }

    renderCourseList() {
        const box = document.getElementById('issuer-course-list')
        if (!box) return
        if (!this.courses.length) {
            box.innerHTML = '<p class="text-sm text-gray-600">No courses created yet.</p>'
            return
        }
        box.innerHTML = `
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="text-left text-gray-500 border-b border-gray-200">
                            <th class="py-2 pr-3">Course</th>
                            <th class="py-2 pr-3">Date</th>
                            <th class="py-2 pr-3">Status</th>
                            <th class="py-2 pr-3">Learners</th>
                            <th class="py-2 pr-3">Assessments</th>
                            <th class="py-2 pr-3">Codes</th>
                            <th class="py-2 pr-3">Materials / Programme</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.courses.map(course => {
                            const materials = course.materials || []
                            const templates = course.templates || []
                            return `
                                <tr class="border-b border-gray-100 align-top">
                                    <td class="py-3 pr-3 min-w-64">
                                        <p class="font-semibold text-gray-900">${escapeHtml(course.title)}</p>
                                        <p class="text-xs text-gray-600">${escapeHtml(course.description)}</p>
                                        <p class="text-xs text-gray-500 mt-1">ID: <span class="font-mono">${escapeHtml(course.course_id)}</span></p>
                                    </td>
                                    <td class="py-3 pr-3 whitespace-nowrap">${escapeHtml(this.formatDate(course.created_at))}</td>
                                    <td class="py-3 pr-3"><span class="badge badge-success">${escapeHtml(course.status || 'ACTIVE')}</span></td>
                                    <td class="py-3 pr-3">${Number(course.enrollments || 0)}</td>
                                    <td class="py-3 pr-3">${Number(course.assessments || templates.length || 0)}</td>
                                    <td class="py-3 pr-3 min-w-48">
                                        ${(course.codes || []).length
                                            ? (course.codes || []).map(c => `<span class="font-mono badge badge-info mb-1">${escapeHtml(c.code)}</span>`).join(' ')
                                            : '<span class="text-gray-400">None</span>'}
                                    </td>
                                    <td class="py-3 pr-3 min-w-56">
                                        ${materials.length ? materials.map(material => `
                                            <div class="mb-2">
                                                <p class="font-mono text-xs">${escapeHtml(material.material_id)}</p>
                                                <p class="text-xs text-gray-600">${escapeHtml(material.programme || 'Programme unavailable')}</p>
                                            </div>
                                        `).join('') : '<span class="text-gray-400">No linked material</span>'}
                                    </td>
                                </tr>
                            `
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `
    }

    formatDate(value) {
        if (!value) return 'N/A'
        const date = new Date(value)
        if (Number.isNaN(date.getTime())) return value
        return date.toLocaleDateString()
    }

    renderMaterialList() {
        const box = document.getElementById('issuer-material-list')
        if (!box) return
        if (!this.materials.length) {
            box.innerHTML = '<p class="text-sm text-gray-600">No materials uploaded yet.</p>'
            return
        }
        box.innerHTML = this.materials.map(material => `
            <div class="border border-gray-200 rounded-lg p-3 mb-2">
                <p class="font-medium">${escapeHtml(material.title)}</p>
                <p class="text-xs text-gray-600">${escapeHtml(material.programme || '')}</p>
                <p class="text-xs font-mono text-gray-500">${escapeHtml(material.material_id)}</p>
                <button class="btn btn-sm btn-secondary mt-2" onclick="IssuerDashboard.useMaterial('${escapeHtml(material.material_id)}')">Use for Assessment</button>
            </div>
        `).join('')
    }

    renderTemplateList() {
        const box = document.getElementById('issuer-template-list')
        if (!box) return
        const templates = this.courses.flatMap(course => (course.templates || []).map(template => ({ ...template, course_title: course.title })))
        if (!templates.length) {
            box.innerHTML = '<p class="text-sm text-gray-600">No assessment templates yet.</p>'
            return
        }
        box.innerHTML = templates.map(template => `
            <div class="border border-gray-200 rounded-lg p-3 mb-2">
                <p class="font-medium">${escapeHtml(template.title)}</p>
                <p class="text-xs text-gray-600">${escapeHtml(template.course_title)} | Material: <span class="font-mono">${escapeHtml(template.material_id)}</span></p>
                <p class="text-xs text-gray-500">Template ID: <span class="font-mono">${escapeHtml(template.assessment_template_id)}</span></p>
            </div>
        `).join('')
    }

    populateCourseSelects() {
        const options = this.courses.map(course => `<option value="${escapeHtml(course.course_id)}">${escapeHtml(course.title)}</option>`).join('')
        ;['template-course', 'code-course'].forEach(id => {
            const select = document.getElementById(id)
            if (select) select.innerHTML = options || '<option value="">Create a course first</option>'
        })
    }

    useMaterial(materialId) {
        this.showTab('assessments')
        const input = document.getElementById('template-material-id')
        if (input) input.value = materialId
    }

    async createCourse(event) {
        event.preventDefault()
        const button = document.getElementById('course-submit')
        button.disabled = true
        try {
            await api.createCourse({
                title: document.getElementById('course-title').value.trim(),
                description: document.getElementById('course-description').value.trim(),
            })
            event.target.reset()
            showSuccess('Course created.')
            await this.loadCourses()
        } catch (err) {
            showError(err.message)
        } finally {
            button.disabled = false
        }
    }

    async submitMaterial(event) {
        event.preventDefault()
        const button = document.getElementById('material-submit')
        const resultBox = document.getElementById('material-result')
        button.disabled = true
        button.textContent = 'Saving...'
        try {
            const result = await api.ingestMaterial({
                issuer_id: this.issuer.did,
                programme: document.getElementById('material-programme').value.trim(),
                title: document.getElementById('material-title').value.trim(),
                content: document.getElementById('material-content').value.trim(),
                difficulty_level: 'backend-controlled',
                topics: document.getElementById('material-topics').value.split(',').map(t => t.trim()).filter(Boolean),
            })
            resultBox.innerHTML = `
                <div class="alert alert-success">
                    Material saved. Material ID:
                    <span class="font-mono">${escapeHtml(result.material_id)}</span>
                </div>
            `
            event.target.reset()
            showSuccess('Material saved.')
            await this.loadCourses()
        } catch (err) {
            showError(err.message)
        } finally {
            button.disabled = false
            button.textContent = 'Save Material'
        }
    }

    async createTemplate(event) {
        event.preventDefault()
        const button = document.getElementById('template-submit')
        button.disabled = true
        try {
            const courseId = document.getElementById('template-course').value
            await api.createAssessmentTemplate(courseId, {
                course_id: courseId,
                title: document.getElementById('template-title').value.trim(),
                description: document.getElementById('template-description').value.trim(),
                material_id: document.getElementById('template-material-id').value.trim(),
            })
            event.target.reset()
            showSuccess('Assessment template created.')
            await this.loadCourses()
        } catch (err) {
            showError(err.message)
        } finally {
            button.disabled = false
        }
    }

    async generateCodes(event) {
        event.preventDefault()
        const courseId = document.getElementById('code-course').value
        const resultBox = document.getElementById('code-result')
        try {
            const result = await api.generateCourseCodes(courseId, {
                count: Number(document.getElementById('code-count').value || 1),
                quota: Number(document.getElementById('code-quota').value || 1),
                expires_in_days: 30,
            })
            resultBox.innerHTML = `
                <div class="alert alert-success">
                    ${(result.codes || []).map(code => `<span class="font-mono badge badge-info">${escapeHtml(code)}</span>`).join(' ')}
                </div>
            `
            showSuccess('Course code generated.')
            await this.loadCourses()
        } catch (err) {
            showError(err.message)
        }
    }

    async loadHistory() {
        const box = document.getElementById('issuer-history-list')
        if (!box) return
        box.innerHTML = '<p class="text-sm text-gray-600">Loading history...</p>'
        try {
            const result = await api.issuerLearners()
            this.history = result
            const learners = result.learners || []
            box.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                    <div class="border border-gray-200 rounded-lg p-3"><p class="text-xs text-gray-500">Total Learners</p><p class="text-xl font-bold">${result.stats?.total_learners || 0}</p></div>
                    <div class="border border-gray-200 rounded-lg p-3"><p class="text-xs text-gray-500">Average Score</p><p class="text-xl font-bold">${result.stats?.avg_score ?? 'N/A'}</p></div>
                    <div class="border border-gray-200 rounded-lg p-3"><p class="text-xs text-gray-500">Completion Rate</p><p class="text-xl font-bold">${result.stats?.completion_rate || 0}%</p></div>
                </div>
                ${learners.length ? learners.map(row => `
                    <div class="border border-gray-200 rounded-lg p-3 mb-2">
                        <p class="font-mono text-sm">${escapeHtml(row.learner_wallet_address || '')}</p>
                        <p class="text-sm text-gray-700">${escapeHtml(row.course_name || '')} ${row.assessment_name ? `| ${escapeHtml(row.assessment_name)}` : ''}</p>
                        <p class="text-xs text-gray-500">Score: ${row.score ?? 'N/A'} | Status: ${escapeHtml(row.status || '')} | Date: ${escapeHtml(row.date_taken || 'N/A')}</p>
                    </div>
                `).join('') : '<p class="text-sm text-gray-600">No learner history yet.</p>'}
            `
        } catch (err) {
            box.innerHTML = '<p class="text-sm text-red-600">Could not load learner history.</p>'
            showError(err.message)
        }
    }

    async revokeCertificate(event) {
        event.preventDefault()
        try {
            await api.revokeCertificate(
                Number(document.getElementById('revoke-tokenid').value),
                this.issuer.wallet,
                document.getElementById('revoke-reason').value.trim(),
            )
            event.target.reset()
            showSuccess('Certificate revoked.')
        } catch (err) {
            showError(err.message)
        }
    }
}

const IssuerDashboard = new IssuerDashboardController()
