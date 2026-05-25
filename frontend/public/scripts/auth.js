const auth = {
    saveSession(result) {
        localStorage.setItem('skillcert-access-token', result.access_token)
        localStorage.setItem('skillcert-refresh-token', result.refresh_token)
        localStorage.setItem('skillcert-user', JSON.stringify(result.user))
    },

    user() {
        try {
            return JSON.parse(localStorage.getItem('skillcert-user') || 'null')
        } catch {
            return null
        }
    },

    isAuthenticated() {
        return !!localStorage.getItem('skillcert-access-token')
    },

    async syncSession() {
        if (!this.isAuthenticated()) return null
        try {
            const result = await api.currentUser()
            localStorage.setItem('skillcert-user', JSON.stringify(result.user))
            return result.user
        } catch (err) {
            this.clearSession()
            throw err
        }
    },

    clearSession() {
        localStorage.removeItem('skillcert-access-token')
        localStorage.removeItem('skillcert-refresh-token')
        localStorage.removeItem('skillcert-user')
        localStorage.removeItem('skillcert-learner')
        localStorage.removeItem('skillcert-preview-wallet')
    },

    logout() {
        this.clearSession()
        window.location.href = '/auth/login.html'
    },

    protect() {
        if (!this.isAuthenticated()) {
            window.location.href = '/auth/login.html'
        }
    },
}

window.auth = auth

async function handleRegister(event) {
    event.preventDefault()
    const form = event.target
    const payload = {
        email: form.email.value.trim(),
        password: form.password.value,
        wallet_address: form.wallet.value.trim(),
        full_name: form.full_name.value.trim(),
        programme: form.programme.value.trim() || 'General',
        role: form.role.value,
    }
    try {
        const result = await api.registerAccount(payload)
        auth.saveSession(result)
        redirectAfterAuth(result.user)
    } catch (err) {
        document.getElementById('auth-error').textContent = friendlyAuthError(err)
    }
}

async function handleLogin(event) {
    event.preventDefault()
    const form = event.target
    try {
        const result = await api.login(form.email.value.trim(), form.password.value)
        auth.saveSession(result)
        redirectAfterAuth(result.user)
    } catch (err) {
        document.getElementById('auth-error').textContent = friendlyAuthError(err)
    }
}

async function handleForgotPassword(event) {
    event.preventDefault()
    document.getElementById('auth-error').textContent = 'Password recovery is accepted in preview mode.'
}

function friendlyAuthError(err) {
    const message = err?.message || 'Authentication failed'
    if (message.includes('Invalid email or password')) {
        return 'Invalid email or password.'
    }
    if (message.includes('Account already exists')) {
        return 'That email or wallet is already registered. Login instead, or use a different wallet address.'
    }
    if (message.includes('Failed to fetch')) {
        return 'Backend is not reachable. Make sure the backend is running on localhost:8000.'
    }
    return message
}

function redirectAfterAuth(user) {
    const tab = user?.role === 'issuer' ? 'issuer' : 'learner'
    window.location.href = `/#${tab}`
}
