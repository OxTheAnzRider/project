# SkillCert Contracts

Foundry contracts for the SkillCert certificate registry and soulbound NFT.

## Build

```bash
forge build
```

## Test

```bash
forge test
```

## Deploy

Set the deployer private key and, optionally, the backend issuer wallet that
will sign certificate issuance transactions:

```bash
export DEPLOYER_PRIVATE_KEY=...
export INITIAL_ISSUER=0xYourBackendIssuerWallet
```

Deploy:

```bash
forge script script/Deploy.s.sol:Deploy \
  --rpc-url $ARBITRUM_RPC_URL \
  --broadcast
```

The deploy script:

1. Deploys `CertificationNFT`.
2. Deploys `CertificationRegistry`.
3. Calls `CertificationNFT.setRegistry(registryAddress)`.
4. Optionally authorizes `INITIAL_ISSUER`.

## Backend ABI Compatibility

`CertificationRegistry` exposes the interface expected by
`backend/app/services/blockchain.py`:

```solidity
issueCertificate(address learner, string institutionDID, string metadataCID, string assessmentCID)
revokeCertificate(uint256 tokenId, string reason)
verifyCertificate(uint256 tokenId)
```

`verifyCertificate` returns:

```solidity
(bool valid, string metaCID, string assessmentArtefactCID, string institutionDID, uint256 timestamp)
```

After redeploying, update backend `.env`:

```bash
REGISTRY_CONTRACT_ADDRESS=0x...
NFT_CONTRACT_ADDRESS=0x...
ARBITRUM_RPC_URL=...
DEPLOYER_PRIVATE_KEY=...
```

The backend signing key must be authorized in the registry with
`addAuthorizedIssuer` or through `INITIAL_ISSUER` during deployment.
