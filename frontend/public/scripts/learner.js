/**
 * js/learner.js - Learner portal for the Q1-Q5 assessment flow.
 */

class LearnerPortal {
    constructor() {
        this.learner = this.loadLearner()
        this.assessment = null
        this.currentQuestionIndex = 0
        this.answers = {}
        this.certificates = []
    }

    init() {
        this.renderContent()
        wallet.onStateChanged(() => this.renderContent())
    }

    loadLearner() {
        try {
            return JSON.parse(localStorage.getItem('skillcert-learner') || 'null')
        } catch {
            return null
        }
    }

    saveLearner(learner) {
        this.learner = learner
        localStorage.setItem('skillcert-learner', JSON.stringify(learner))
    }

    renderContent() {
        const container = document.getElementById('learner-content')

        if (!wallet.isConnected()) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <p class="text-gray-600 mb-4">Connect your wallet to register and take assessments.</p>
                    <button class="btn btn-primary" onclick="learnerPortal.connectWallet()">
                        Connect Wallet
                    </button>
                </div>
            `
            return
        }

        if (!this.learner || this.learner.wallet_address !== wallet.getAccount()) {
            this.renderRegistration()
            return
        }

        if (this.assessment) {
            this.renderAssessment()
            return
        }

        this.renderDashboard()
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
        const container = document.getElementById('learner-content')
        container.innerHTML = `
            <div class="max-w-xl mx-auto">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Register Learner</h3>
                        <p class="card-subtitle">Your profile is linked to the connected wallet.</p>
                    </div>
                    <form id="learner-registration-form" onsubmit="learnerPortal.registerLearner(event)">
                        <div class="form-group">
                            <label>Full Name</label>
                            <input type="text" id="learner-name" autocomplete="name" required />
                        </div>
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" id="learner-email" autocomplete="email" required />
                        </div>
                        <div class="form-group">
                            <label>Programme</label>
                            <input type="text" id="learner-programme" placeholder="e.g., Solar Installation Basics" required />
                        </div>
                        <p class="text-xs text-gray-500 mb-4">
                            Wallet: <span class="font-mono">${escapeHtml(wallet.getAccount())}</span>
                        </p>
                        <button type="submit" id="learner-register-btn" class="btn btn-primary w-full">
                            Register
                        </button>
                    </form>
                </div>
            </div>
        `
    }

    async registerLearner(event) {
        event.preventDefault()

        const fullName = document.getElementById('learner-name').value.trim()
        const email = document.getElementById('learner-email').value.trim()
        const programme = document.getElementById('learner-programme').value.trim()
        const button = document.getElementById('learner-register-btn')

        if (!fullName || !email || !programme) {
            showError('Please fill all learner registration fields.')
            return
        }

        button.disabled = true
        button.textContent = 'Registering...'

        try {
            const result = await api.registerLearner(fullName, email, wallet.getAccount(), programme)
            this.saveLearner({
                id: result.id,
                did: result.did,
                wallet_address: result.wallet_address,
                programme: result.programme,
            })
            showSuccess('Learner registered.')
            this.renderContent()
        } catch (err) {
            showError(err.message)
        } finally {
            button.disabled = false
            button.textContent = 'Register'
        }
    }

    renderDashboard() {
        const container = document.getElementById('learner-content')
        container.innerHTML = `
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 space-y-6">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Start Assessment</h3>
                            <p class="card-subtitle">Enter the material ID supplied by your institution.</p>
                        </div>
                        <form id="assessment-start-form" onsubmit="learnerPortal.startAssessment(event)">
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div class="form-group md:col-span-2">
                                    <label>Material ID</label>
                                    <input type="text" id="assessment-material-id" placeholder="mat_..." required />
                                </div>
                                <div class="form-group">
                                    <label>Questions</label>
                                    <input type="number" id="assessment-question-count" min="1" max="10" value="5" />
                                </div>
                            </div>
                            <div class="form-group">
                                <label>Difficulty</label>
                                <select id="assessment-difficulty">
                                    <option value="mixed">Mixed</option>
                                    <option value="easy">Easy</option>
                                    <option value="medium">Medium</option>
                                    <option value="hard">Hard</option>
                                </select>
                            </div>
                            <button type="submit" id="assessment-start-btn" class="btn btn-primary">
                                Start Assessment
                            </button>
                        </form>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Assessment Result</h3>
                            <p class="card-subtitle">Check a completed assessment by ID.</p>
                        </div>
                        <form class="flex flex-col md:flex-row gap-3" onsubmit="learnerPortal.lookupResult(event)">
                            <input class="flex-grow" type="text" id="lookup-assessment-id" placeholder="assessment_..." required />
                            <button type="submit" class="btn btn-secondary">Load Result</button>
                        </form>
                    </div>
                </div>

                <aside class="space-y-6">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Learner</h3>
                            <p class="card-subtitle">DID: <span class="font-mono text-xs">${escapeHtml(this.learner.did)}</span></p>
                        </div>
                        <p class="text-sm text-gray-600 mb-4">${escapeHtml(this.learner.programme)}</p>
                        <button class="btn btn-sm btn-secondary" onclick="learnerPortal.logOut()">Log Out</button>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Certificates</h3>
                            <p class="card-subtitle">Issued certificates for this learner.</p>
                        </div>
                        <div id="learner-certificates">
                            <button class="btn btn-sm btn-secondary" onclick="learnerPortal.loadCertificates()">Load Certificates</button>
                        </div>
                    </div>
                </aside>
            </div>
        `
    }

    async startAssessment(event) {
        event.preventDefault()

        const materialId = document.getElementById('assessment-material-id').value.trim()
        const numQuestions = Number(document.getElementById('assessment-question-count').value || 5)
        const difficulty = document.getElementById('assessment-difficulty').value
        const button = document.getElementById('assessment-start-btn')

        button.disabled = true
        button.textContent = 'Creating...'

        try {
            const result = await api.createAssessment({
                learner_id: this.learner.did,
                material_id: materialId,
                num_questions: numQuestions,
                difficulty,
            })

            this.assessment = {
                assessment_id: result.assessment_id,
                material_title: result.material_title,
                questions: result.questions || [],
                result: null,
            }
            this.currentQuestionIndex = 0
            this.answers = {}
            showSuccess('Assessment created.')
            this.renderAssessment()
        } catch (err) {
            showError(err.message)
        } finally {
            button.disabled = false
            button.textContent = 'Start Assessment'
        }
    }

    renderAssessment() {
        if (this.assessment.result) {
            this.renderResult(this.assessment.result)
            return
        }

        const container = document.getElementById('learner-content')
        const questions = this.assessment.questions
        const question = questions[this.currentQuestionIndex]
        const answeredCount = Object.keys(this.answers).length
        const percent = questions.length ? Math.round((answeredCount / questions.length) * 100) : 0

        container.innerHTML = `
            <div class="space-y-6">
                <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                    <div>
                        <h3 class="text-xl font-semibold text-gray-900">${escapeHtml(this.assessment.material_title || 'Assessment')}</h3>
                        <p class="text-sm text-gray-600">Assessment ID: <span class="font-mono">${escapeHtml(this.assessment.assessment_id)}</span></p>
                    </div>
                    <button class="btn btn-secondary" onclick="learnerPortal.cancelAssessment()">Exit</button>
                </div>

                <div class="card">
                    <div class="flex items-center justify-between mb-3">
                        <span class="badge badge-info">Question ${this.currentQuestionIndex + 1} of ${questions.length}</span>
                        <span class="text-sm text-gray-600">${answeredCount}/${questions.length} answered</span>
                    </div>
                    <div class="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-6">
                        <div class="h-full bg-indigo-600" style="width: ${percent}%"></div>
                    </div>

                    ${question ? this.renderQuestion(question) : '<p class="text-gray-600">No questions were generated.</p>'}
                </div>
            </div>
        `
    }

    renderQuestion(question) {
        const answer = this.answers[question.question_id] || ''
        const isFirst = this.currentQuestionIndex === 0
        const isLast = this.currentQuestionIndex === this.assessment.questions.length - 1

        return `
            <div class="space-y-5">
                <div>
                    <div class="flex flex-wrap gap-2 mb-3">
                        <span class="badge badge-info">${escapeHtml(question.type || 'question')}</span>
                        <span class="badge badge-warning">${escapeHtml(question.difficulty || 'mixed')}</span>
                        <span class="badge">${Number(question.points || 0)} pts</span>
                    </div>
                    <p class="text-lg font-medium text-gray-900">${escapeHtml(question.question)}</p>
                </div>

                <div class="form-group">
                    <label>Your Answer</label>
                    <textarea id="current-answer" placeholder="Write your answer here..." required>${escapeHtml(answer)}</textarea>
                </div>

                <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                    <div class="flex gap-2">
                        <button class="btn btn-secondary" onclick="learnerPortal.previousQuestion()" ${isFirst ? 'disabled' : ''}>
                            Previous
                        </button>
                        <button class="btn btn-primary" id="save-answer-btn" onclick="learnerPortal.saveCurrentAnswer()">
                            Save Answer
                        </button>
                        <button class="btn btn-secondary" onclick="learnerPortal.nextQuestion()" ${isLast ? 'disabled' : ''}>
                            Next
                        </button>
                    </div>
                    <button class="btn btn-success" id="grade-assessment-btn" onclick="learnerPortal.submitForGrading()" ${this.canSubmitForGrading() ? '' : 'disabled'}>
                        Submit for Grading
                    </button>
                </div>
            </div>
        `
    }

    canSubmitForGrading() {
        return this.assessment.questions.length > 0
            && Object.keys(this.answers).length === this.assessment.questions.length
    }

    async saveCurrentAnswer() {
        const question = this.assessment.questions[this.currentQuestionIndex]
        const answer = document.getElementById('current-answer').value.trim()
        const button = document.getElementById('save-answer-btn')

        if (!answer) {
            showError('Please write an answer before saving.')
            return false
        }

        button.disabled = true
        button.textContent = 'Saving...'

        try {
            const result = await api.submitAnswer(this.assessment.assessment_id, question.question_id, answer)
            this.answers[question.question_id] = answer
            showSuccess(`Answer saved (${result.progress}).`)
            this.renderAssessment()
            return true
        } catch (err) {
            showError(err.message)
            return false
        } finally {
            button.disabled = false
            button.textContent = 'Save Answer'
        }
    }

    previousQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.currentQuestionIndex -= 1
            this.renderAssessment()
        }
    }

    nextQuestion() {
        if (this.currentQuestionIndex < this.assessment.questions.length - 1) {
            this.currentQuestionIndex += 1
            this.renderAssessment()
        }
    }

    async submitForGrading() {
        if (!this.canSubmitForGrading()) {
            showError('Please save answers for every question before grading.')
            return
        }

        const button = document.getElementById('grade-assessment-btn')
        button.disabled = true
        button.textContent = 'Grading...'

        try {
            const result = await api.gradeAssessment(this.assessment.assessment_id)
            this.assessment.result = result
            showSuccess('Assessment graded.')
            this.renderResult(result)
        } catch (err) {
            showError(err.message)
        } finally {
            button.disabled = false
            button.textContent = 'Submit for Grading'
        }
    }

    async lookupResult(event) {
        event.preventDefault()
        const assessmentId = document.getElementById('lookup-assessment-id').value.trim()

        try {
            const result = await api.getAssessmentResult(assessmentId)
            this.assessment = {
                assessment_id: assessmentId,
                material_title: result.programme || 'Assessment Result',
                questions: [],
                result,
            }
            this.renderResult(result)
        } catch (err) {
            showError(err.message)
        }
    }

    renderResult(result) {
        const container = document.getElementById('learner-content')
        const passed = !!result.passed
        const percentage = Number(result.percentage || 0)
        const detailedResults = result.detailed_results || []

        container.innerHTML = `
            <div class="space-y-6">
                <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                    <div>
                        <h3 class="text-xl font-semibold text-gray-900">Assessment Result</h3>
                        <p class="text-sm text-gray-600">Assessment ID: <span class="font-mono">${escapeHtml(result.assessment_id)}</span></p>
                    </div>
                    <button class="btn btn-secondary" onclick="learnerPortal.finishResult()">Back to Dashboard</button>
                </div>

                <div class="card">
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div>
                            <p class="text-sm text-gray-500">Outcome</p>
                            <p class="text-2xl font-bold ${passed ? 'text-green-600' : 'text-red-600'}">${passed ? 'PASS' : 'FAIL'}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-500">Score</p>
                            <p class="text-2xl font-bold text-gray-900">${percentage.toFixed(1)}%</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-500">Certificate NFT ID</p>
                            <p class="text-2xl font-bold text-gray-900">${result.certificate_token_id ?? 'Not issued'}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-500">Transaction</p>
                            <p class="text-sm font-mono text-gray-700 break-all">${escapeHtml(result.certificate_tx_hash || 'Not available')}</p>
                        </div>
                    </div>
                    <div class="mt-6">
                        <p class="text-sm text-gray-500 mb-1">Feedback</p>
                        <p class="text-gray-800">${escapeHtml(result.overall_feedback || 'No feedback returned.')}</p>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Question Feedback</h3>
                        <p class="card-subtitle">Per-question scoring from the AI assessment service.</p>
                    </div>
                    ${this.renderDetailedResults(detailedResults)}
                </div>
            </div>
        `
    }

    renderDetailedResults(results) {
        if (!results.length) {
            return '<p class="text-gray-600">No per-question feedback was returned.</p>'
        }

        return `
            <div class="space-y-3">
                ${results.map((item, index) => `
                    <div class="border border-gray-200 rounded-lg p-4">
                        <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-2 mb-2">
                            <p class="font-medium text-gray-900">Q${index + 1}: ${escapeHtml(item.question || item.question_id || '')}</p>
                            <span class="badge badge-info">${Number(item.points_earned ?? item.score ?? 0)} / ${Number(item.max_points ?? item.points ?? 0)}</span>
                        </div>
                        <p class="text-sm text-gray-700">${escapeHtml(item.feedback || 'No feedback.')}</p>
                    </div>
                `).join('')}
            </div>
        `
    }

    async loadCertificates() {
        const container = document.getElementById('learner-certificates')
        container.innerHTML = `<div class="flex items-center gap-2 text-sm text-gray-600">${getLoadingSpinner()} Loading certificates...</div>`

        try {
            const result = await api.getLearnerCertificates(this.learner.did)
            this.certificates = result.certificates || []
            if (!this.certificates.length) {
                container.innerHTML = '<p class="text-sm text-gray-600">No certificates issued yet.</p>'
                return
            }

            container.innerHTML = this.certificates.map(cert => `
                <div class="border border-gray-200 rounded-lg p-3 mb-2">
                    <div class="flex items-start justify-between gap-3">
                        <div>
                            <p class="font-medium text-gray-900">Token #${escapeHtml(String(cert.token_id))}</p>
                            <p class="text-xs text-gray-600">${escapeHtml(cert.programme || 'Programme unavailable')}</p>
                        </div>
                        <span class="badge ${cert.is_revoked ? 'badge-danger' : 'badge-success'}">
                            ${cert.is_revoked ? 'Revoked' : 'Valid'}
                        </span>
                    </div>
                </div>
            `).join('')
        } catch (err) {
            container.innerHTML = '<p class="text-sm text-red-600">Could not load certificates.</p>'
            showError(err.message)
        }
    }

    finishResult() {
        this.assessment = null
        this.currentQuestionIndex = 0
        this.answers = {}
        this.renderDashboard()
    }

    cancelAssessment() {
        this.assessment = null
        this.currentQuestionIndex = 0
        this.answers = {}
        this.renderDashboard()
    }

    logOut() {
        this.learner = null
        this.assessment = null
        localStorage.removeItem('skillcert-learner')
        this.renderContent()
    }
}

const learnerPortal = new LearnerPortal()
