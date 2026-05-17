// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "./CertificationNFT.sol";

contract CertificationRegistry is AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant ISSUER_ROLE = keccak256("ISSUER_ROLE");

    CertificationNFT public nftContract;

    mapping(uint256 => bool) public isRevoked;
    mapping(uint256 => string) public artefactCID;

    event CertificateIssued(
        uint256 indexed tokenId,
        address indexed learner,
        string institutionDID,
        string metadataCID,
        uint256 ts
    );

    event CertificateRevoked(
        uint256 indexed tokenId,
        address indexed revokedBy,
        uint256 ts
    );

    constructor(address _nftContract) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);

        nftContract = CertificationNFT(_nftContract);
    }

    /// Issue an NFT certificate after confirmed AI assessment pass
    function issueCertificate(
        address learner,
        string calldata institutionDID,
        string calldata metadataCID,
        string calldata assessmentCID
    ) external onlyRole(ISSUER_ROLE) returns (uint256 tokenId) {
        tokenId = nftContract.mint(learner, metadataCID);

        artefactCID[tokenId] = assessmentCID;

        emit CertificateIssued(
            tokenId,
            learner,
            institutionDID,
            metadataCID,
            block.timestamp
        );
    }

    /// Revoke a certificate — token remains on-chain but flagged invalid
    function revokeCertificate(uint256 tokenId)
        external
        onlyRole(ISSUER_ROLE)
    {
        require(!isRevoked[tokenId], "Already revoked");

        isRevoked[tokenId] = true;

        emit CertificateRevoked(tokenId, msg.sender, block.timestamp);
    }

    /// Public, gas-free verification query
    function verifyCertificate(uint256 tokenId)
        external
        view
        returns (bool valid, string memory metaCID)
    {
        valid = !isRevoked[tokenId] && nftContract.exists(tokenId);
        metaCID = nftContract.tokenURI(tokenId);
    }
}