/**
 * js/ui.js — UI helper functions
 * 
 * Alerts, modals, loading spinners, etc.
 */

// ── Alerts ───────────────────────────────────────────────────────────────────

function showAlert(message, type = 'info', duration = 5000) {
    const container = document.getElementById('alerts-container')
    const id = `alert-${Date.now()}`
    const alert = document.createElement('div')
    alert.id = id
    alert.className = `alert alert-${type}`
    alert.innerHTML = `
        <div class="flex items-center justify-between">
            <span>${escapeHtml(message)}</span>
            <button onclick="document.getElementById('${id}').remove()" class="ml-4 text-xl leading-none opacity-70 hover:opacity-100">×</button>
        </div>
    `
    container.appendChild(alert)

    if (duration > 0) {
        setTimeout(() => alert.remove(), duration)
    }
}

function showSuccess(message) {
    showAlert(message, 'success', 5000)
}

function showError(message) {
    showAlert(message, 'error', 7000)
}

function showWarning(message) {
    showAlert(message, 'warning', 5000)
}

function showInfo(message) {
    showAlert(message, 'info', 5000)
}

// ── Modal ────────────────────────────────────────────────────────────────────

function openModal(title, content) {
    const modal = document.getElementById('modal')
    const modalTitle = document.getElementById('modal-title')
    const modalContent = document.getElementById('modal-content')

    modalTitle.textContent = title
    modalContent.innerHTML = content

    modal.classList.remove('hidden')
    document.body.style.overflow = 'hidden'
}

function closeModal() {
    const modal = document.getElementById('modal')
    modal.classList.add('hidden')
    document.body.style.overflow = 'auto'
}

// Close modal on background click
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('modal')
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal()
        })
    }
})

// ── Loading ──────────────────────────────────────────────────────────────────

function getLoadingSpinner() {
    return '<div class="spinner"></div>'
}

function withLoading(button, fn) {
    return async function(...args) {
        const origText = button.textContent
        const origDisabled = button.disabled

        button.disabled = true
        button.innerHTML = `<span class="spinner"></span> ${origText.split('  ')[0]}`

        try {
            return await fn(...args)
        } finally {
            button.textContent = origText
            button.disabled = origDisabled
        }
    }
}

// ── Formatting ───────────────────────────────────────────────────────────────

function shortenAddress(addr) {
    if (!addr) return ''
    return `${addr.slice(0, 6)}…${addr.slice(-4)}`
}

function formatDate(timestamp) {
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })
}

function formatIPFSUrl(cid) {
    if (!cid) return '#'
    if (cid.startsWith('ipfs://')) cid = cid.slice(7)
    return `https://ipfs.io/ipfs/${cid}`
}

function escapeHtml(text) {
    const div = document.createElement('div')
    div.textContent = text
    return div.innerHTML
}

// ── Tab switching ────────────────────────────────────────────────────────────

function initTabs() {
    const tabButtons = document.querySelectorAll('.nav-tab')
    const tabContents = document.querySelectorAll('.tab-content')

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab

            // Update active button
            tabButtons.forEach(b => b.classList.remove('active'))
            btn.classList.add('active')

            // Update active content
            tabContents.forEach(content => {
                const contentId = `${tabName}-tab`
                if (content.id === contentId) {
                    content.classList.remove('hidden')
                } else {
                    content.classList.add('hidden')
                }
            })
        })
    })
}

// ── Charts (simple bar chart for SHAP) ────────────────────────────────────────

function renderShapChart(shapValues, container) {
    const sorted = Object.entries(shapValues)
        .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
        .slice(0, 10)  // Top 10

    const maxVal = Math.max(...sorted.map(([_, v]) => Math.abs(v)))

    let html = '<div class="space-y-2">'
    sorted.forEach(([name, val]) => {
        const pct = (Math.abs(val) / maxVal * 100)
        const color = val > 0 ? 'bg-green-500' : 'bg-red-500'
        html += `
            <div>
                <div class="text-xs font-mono text-gray-600">${name.replace(/_/g, ' ')}</div>
                <div class="flex items-center gap-2">
                    <div class="flex-grow bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div class="${color} h-full" style="width: ${pct}%"></div>
                    </div>
                    <span class="text-xs text-gray-600 font-mono w-12 text-right">${val.toFixed(4)}</span>
                </div>
            </div>
        `
    })
    html += '</div>'

    container.innerHTML = html
}

// ── Initialization ───────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', initTabs)