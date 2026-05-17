/**
 * js/verifier.js — Public certificate verification interface
 * 
 * No wallet required — anyone can query a certificate on-chain by token ID.
 * FR-06: Public verification endpoint
 */

class VerificationInterface {
    init() {
        this.renderContent()
    }

    renderContent() {
        const container = document.getElementById('verifier-content')
        container.innerHTML = `
            <div class="space-y-6">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Verify Certificate (FR-06)</h3>
                        <p class="card-subtitle">Check certificate authenticity on-chain — no login required</p>
                    </div>

                    <form id="verify-form" onsubmit="verifier.verifyToken(event)">
                        <div class="form-group">
                            <label>Certificate Token ID</label>
                            <input type="number" id="token-id" placeholder="e.g., 42" required />
                            <div class="form-hint">Find this on your certificate</div>
                        </div>
                        <button type="submit" class="btn btn-primary w-full">Verify</button>
                    </form>
                </div>

                <div id="result-container" class="hidden"></div>
            </div>
        `
    }

    async verifyToken(e) {
        e.preventDefault()
        const tokenId = parseInt(document.getElementById('token-id').value)

        const btn = e.target.querySelector('button[type="submit"]')
        btn.disabled = true
        btn.textContent = 'Verifying...'

        try {
            const result = await api.verifyCertificate(tokenId)
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

        const status = result.valid 
            ? '<span class="badge badge-success">✓ VALID</span>'
            : '<span class="badge badge-danger">✗ INVALID</span>'

        const revocationNotice = result.is_revoked
            ? `<div class="alert alert-warning">
                 <strong>Revoked:</strong> ${result.revocation_reason || 'No reason provided'}
               </div>`
            : ''

        const programmeInfo = result.programme 
            ? `<p class="text-sm"><strong>Programme:</strong> ${escapeHtml(result.programme)}</p>`
            : ''

        const txLink = result.tx_hash 
            ? `<a href="https://sepolia.arbiscan.io/tx/${result.tx_hash}" target="_blank" class="text-indigo-600 hover:underline text-xs">View on Arbiscan</a>`
            : ''

        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Verification Result ${status}</h3>
                </div>

                ${revocationNotice}

                <div class="space-y-3">
                    <div>
                        <p class="text-xs text-gray-600">Token ID</p>
                        <p class="font-mono font-semibold">${result.token_id}</p>
                    </div>

                    ${programmeInfo}

                    ${result.institution_name ? `
                        <div>
                            <p class="text-xs text-gray-600">Issued by</p>
                            <p class="font-semibold">${escapeHtml(result.institution_name)}</p>
                        </div>
                    ` : ''}

                    ${result.issued_at ? `
                        <div>
                            <p class="text-xs text-gray-600">Issued at</p>
                            <p class="font-semibold">${new Date(result.issued_at * 1000).toLocaleDateString()}</p>
                        </div>
                    ` : ''}

                    ${result.metadata_cid ? `
                        <div>
                            <p class="text-xs text-gray-600">Metadata (IPFS)</p>
                            <a href="${formatIPFSUrl(result.metadata_cid)}" target="_blank" class="text-indigo-600 hover:underline text-xs break-all">
                                ${shortenAddress(result.metadata_cid)}
                            </a>
                        </div>
                    ` : ''}

                    ${txLink ? `
                        <div class="text-xs">
                            ${txLink}
                        </div>
                    ` : ''}
                </div>

                <div class="mt-4 p-3 bg-gray-50 rounded-lg text-xs text-gray-600">
                    <p><strong>On-chain Verification:</strong> This certificate was verified directly from the Arbitrum Sepolia blockchain.</p>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">What This Means</h3>
                </div>

                ${result.valid ? `
                    <div class="space-y-2 text-sm">
                        <p>✓ This certificate is <strong>authentic</strong> and was issued by an accredited institution.</p>
                        <p>✓ The certificate is <strong>soulbound</strong> — it cannot be transferred and is permanently linked to its recipient.</p>
                        <p>✓ The issuance was <strong>verified by AI</strong> and confirmed by human assessors.</p>
                        <p>✓ The assessment evidence is <strong>tamper-proof</strong> and anchored on the blockchain.</p>
                    </div>
                ` : `
                    <div class="space-y-2 text-sm text-red-700">
                        <p>✗ This certificate is not found on the blockchain or has been revoked.</p>
                        <p>✗ Do not accept this credential as valid.</p>
                    </div>
                `}
            </div>

            <button class="btn btn-secondary w-full mt-4" onclick="verifier.resetForm()">
                Verify Another
            </button>
        `
    }

    showError(message) {
        const container = document.getElementById('result-container')
        container.classList.remove('hidden')
        container.innerHTML = `
            <div class="alert alert-error">
                <strong>Verification Failed:</strong> ${escapeHtml(message)}
            </div>
        `
    }

    resetForm() {
        document.getElementById('token-id').value = ''
        document.getElementById('result-container').classList.add('hidden')
        document.getElementById('token-id').focus()
    }
}

const verifier = new VerificationInterface()