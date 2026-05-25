/**
 * js/app.js — Main app initialization and wallet UI
 */

// ── Wallet button in navbar ──────────────────────────────────────────────────

function renderWalletButton() {
    const container = document.getElementById('wallet-container')
    const state = {
        account: wallet.getAccount(),
        chainId: wallet.getChainId(),
        isConnected: wallet.isConnected(),
        isCorrectChain: wallet.isCorrectChain(),
    }

    if (!state.isConnected) {
        container.innerHTML = `
            <button class="btn btn-primary" onclick="wallet.connect().catch(e => showError(e.message))">
                Connect Wallet
            </button>
        `
        return
    }

    if (!state.isCorrectChain) {
        container.innerHTML = `
            <div class="flex items-center gap-2">
                <span class="text-xs text-amber-600">Wrong network</span>
                <button class="btn btn-sm btn-secondary" onclick="wallet.switchToArbitrum().catch(e => showError(e.message))">
                    Switch to Arbitrum
                </button>
            </div>
        `
        return
    }

    container.innerHTML = `
        <div class="flex items-center gap-2">
            <span class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-green-50 text-green-700 text-sm font-mono">
                <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                ${shortenAddress(state.account)}
            </span>
            <button class="px-2 py-1.5 rounded-lg hover:bg-gray-100 transition text-gray-600" onclick="wallet.disconnect(); renderWalletButton()" title="Disconnect">
                ✕
            </button>
        </div>
    `
}

wallet.onStateChanged(() => {
    renderWalletButton()
})

function openAppTab(tabName) {
    const tabButtons = document.querySelectorAll('.nav-tab')
    const tabContents = document.querySelectorAll('.tab-content')

    tabButtons.forEach(btn => {
        const active = btn.dataset.tab === tabName
        btn.classList.toggle('active', active)
    })

    tabContents.forEach(content => {
        const active = content.id === `${tabName}-tab`
        content.classList.toggle('hidden', !active)
    })
}

// ── Initialize everything ───────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 SkillCert initializing...')

    if (!auth.isAuthenticated()) {
        window.location.href = '/auth/login.html'
        return
    }

    let user
    try {
        user = await auth.syncSession()
    } catch (err) {
        console.warn('Session sync failed:', err.message)
        window.location.href = '/auth/login.html'
        return
    }

    // Render wallet button
    renderWalletButton()

    // Initialize portals
    learnerPortal.init()
    IssuerDashboard.init()
    verifier.init()

    // Open the correct dashboard for the authenticated role.
    const hashTab = window.location.hash.replace('#', '')
    const allowedTabs = user?.role === 'issuer'
        ? ['issuer', 'verifier']
        : ['learner', 'verifier']
    if (hashTab && allowedTabs.includes(hashTab)) {
        openAppTab(hashTab)
    } else if (user?.role === 'issuer') {
        openAppTab('issuer')
    } else {
        openAppTab('learner')
    }

    // Try to auto-connect if previously connected
    const wasConnected = localStorage.getItem('skillcert-wallet-connected')
    if (wasConnected) {
        wallet.connect().catch(err => {
            console.warn('Auto-connect failed:', err.message)
        })
    }

    // Log API health
    api.health().then(health => {
        console.log('API health:', health.status)
    }).catch(err => {
        console.warn('API unavailable:', err.message)
        showWarning('Backend API is unavailable. Some features may not work.')
    })

    console.log('✓ SkillCert ready')
})

// Save wallet connection state
wallet.onStateChanged((state) => {
    if (state.isConnected) {
        localStorage.setItem('skillcert-wallet-connected', 'true')
    } else {
        localStorage.removeItem('skillcert-wallet-connected')
    }
})
