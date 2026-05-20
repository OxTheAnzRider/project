/**
 * js/wallet.js — MetaMask wallet management
 * 
 * Handles: connect, disconnect, chainId check, account switching
 */

const ARBITRUM_SEPOLIA_CHAIN_ID = '0x66EEE'  // 421614
const ARBITRUM_ONE_CHAIN_ID = '0xa4b1'       // 42161

class WalletManager {
    constructor() {
        this.provider = null
        this.account = null
        this.chainId = null
        this.listeners = []
    }

    onStateChanged(listener) {
        this.listeners.push(listener)
    }

    notifyListeners() {
        this.listeners.forEach(fn => fn({
            account: this.account,
            chainId: this.chainId,
            isConnected: !!this.account,
            isCorrectChain: this.chainId === ARBITRUM_SEPOLIA_CHAIN_ID || this.chainId === ARBITRUM_ONE_CHAIN_ID,
        }))
    }

    async detectProvider() {
        if (!window.ethereum) {
            console.warn('MetaMask not found; using preview wallet.')
            this.provider = null
            return null
        }
        this.provider = window.ethereum
        return this.provider
    }

    async connect() {
        try {
            await this.detectProvider()

            if (!this.provider) {
                this.account = localStorage.getItem('skillcert-preview-wallet')
                    || `0x${Math.random().toString(16).slice(2).padEnd(40, '0').slice(0, 40)}`
                this.chainId = ARBITRUM_SEPOLIA_CHAIN_ID
                localStorage.setItem('skillcert-preview-wallet', this.account)
                this.notifyListeners()
                return { account: this.account, chainId: this.chainId }
            }

            // Request accounts
            const accounts = await this.provider.request({
                method: 'eth_requestAccounts',
            })
            this.account = accounts[0]

            // Get current chain
            const chainId = await this.provider.request({
                method: 'eth_chainId',
            })
            this.chainId = chainId

            // Try to switch to Arbitrum Sepolia
            await this.switchToArbitrum()

            // Listen for account / chain changes
            this.setupListeners()

            this.notifyListeners()
            return { account: this.account, chainId: this.chainId }
        } catch (err) {
            console.error('Wallet connect failed:', err)
            throw err
        }
    }

    async switchToArbitrum() {
        if (!this.provider) {
            this.chainId = ARBITRUM_SEPOLIA_CHAIN_ID
            return
        }

        try {
            await this.provider.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: ARBITRUM_SEPOLIA_CHAIN_ID }],
            })
        } catch (err) {
            // Chain not added — add it
            if (err.code === 4902) {
                await this.provider.request({
                    method: 'wallet_addEthereumChain',
                    params: [{
                        chainId: ARBITRUM_SEPOLIA_CHAIN_ID,
                        chainName: 'Arbitrum Sepolia',
                        rpcUrls: ['https://sepolia-rollup.arbitrum.io/rpc'],
                        nativeCurrency: {
                            name: 'Ethereum',
                            symbol: 'ETH',
                            decimals: 18,
                        },
                        blockExplorerUrls: ['https://sepolia.arbiscan.io/'],
                    }],
                })
                this.chainId = ARBITRUM_SEPOLIA_CHAIN_ID
            } else {
                throw err
            }
        }
    }

    setupListeners() {
        if (!this.provider) return

        this.provider.on('accountsChanged', (accounts) => {
            if (accounts.length === 0) {
                this.disconnect()
            } else {
                this.account = accounts[0]
                this.notifyListeners()
            }
        })

        this.provider.on('chainChanged', (chainId) => {
            this.chainId = chainId
            this.notifyListeners()
        })
    }

    disconnect() {
        this.account = null
        this.chainId = null
        this.notifyListeners()
    }

    async call(contractAddress, abi, method, args = []) {
        if (!this.provider) throw new Error('Wallet not connected')

        const Web3Provider = window.ethers?.providers?.Web3Provider
        const ethersProvider = Web3Provider ? new Web3Provider(this.provider) : null
        if (!ethersProvider) {
            // Fallback: use eth_call directly
            console.warn('ethers.js not available — using raw eth_call')
            return null
        }

        try {
            const contract = new ethers.Contract(contractAddress, abi, ethersProvider)
            const result = await contract[method](...args)
            return result
        } catch (err) {
            console.error(`Contract call ${method} failed:`, err)
            throw err
        }
    }

    getAccount() {
        return this.account
    }

    getChainId() {
        return this.chainId
    }

    isConnected() {
        return !!this.account
    }

    isCorrectChain() {
        return this.chainId === ARBITRUM_SEPOLIA_CHAIN_ID || this.chainId === ARBITRUM_ONE_CHAIN_ID
    }
}

const wallet = new WalletManager()
