// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "./CertificationNFT.sol";

contract CertificationRegistry is AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant ISSUER_ROLE = keccak256("ISSUER_ROLE");

    CertificationNFT public nftContract;

    struct CertificateRecord {
        string metadataCID;
        string artefactCID;
        string issuerDID;
        uint256 issuedAt;
    }

    mapping(address => bool) public authorizedIssuers;
    mapping(uint256 => bool) public isRevoked;
    mapping(uint256 => string) public revocationReason;
    mapping(uint256 => string) public artefactCID;
    mapping(uint256 => CertificateRecord) public certificateRecords;

    event IssuerAuthorized(address indexed issuer);
    event IssuerDeauthorized(address indexed issuer);

    event CertificateIssued(
        uint256 indexed tokenId,
        address indexed learner,
        string issuerDID,
        string metadataCID,
        string assessmentArtefactCID,
        uint256 timestamp
    );

    event CertificateRevoked(
        uint256 indexed tokenId,
        address indexed revokedBy,
        string reason,
        uint256 ts
    );

    constructor(address _nftContract) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);

        nftContract = CertificationNFT(_nftContract);
    }

    function setAuthorizedIssuers(address[] calldata issuers)
        external
        onlyRole(ADMIN_ROLE)
    {
        for (uint256 i = 0; i < issuers.length; i++) {
            authorizedIssuers[issuers[i]] = true;
            _grantRole(ISSUER_ROLE, issuers[i]);
            emit IssuerAuthorized(issuers[i]);
        }
    }

    function isAuthorizedIssuer(address account) external view returns (bool) {
        return authorizedIssuers[account];
    }

    function addAuthorizedIssuer(address issuer)
        external
        onlyRole(ADMIN_ROLE)
    {
        require(!authorizedIssuers[issuer], "Already authorized");
        authorizedIssuers[issuer] = true;
        _grantRole(ISSUER_ROLE, issuer);
        emit IssuerAuthorized(issuer);
    }

    function removeAuthorizedIssuer(address issuer)
        external
        onlyRole(ADMIN_ROLE)
    {
        require(authorizedIssuers[issuer], "Not authorized");
        authorizedIssuers[issuer] = false;
        _revokeRole(ISSUER_ROLE, issuer);
        emit IssuerDeauthorized(issuer);
    }

    /// Issue an NFT certificate after confirmed AI assessment pass
    function issueCertificate(
        address learner,
        string calldata issuerDID,
        string calldata metadataCID,
        string calldata assessmentCID
    ) external returns (uint256 tokenId) {
        require(authorizedIssuers[msg.sender], "Issuer not authorized");
        tokenId = nftContract.mint(learner, metadataCID);

        artefactCID[tokenId] = assessmentCID;
        certificateRecords[tokenId] = CertificateRecord({
            metadataCID: metadataCID,
            artefactCID: assessmentCID,
            issuerDID: issuerDID,
            issuedAt: block.timestamp
        });

        emit CertificateIssued(
            tokenId,
            learner,
            issuerDID,
            metadataCID,
            assessmentCID,
            block.timestamp
        );
    }

    /// Revoke a certificate — token remains on-chain but flagged invalid
    function revokeCertificate(uint256 tokenId, string calldata reason)
        external
    {
        require(authorizedIssuers[msg.sender], "Issuer not authorized");
        require(!isRevoked[tokenId], "Already revoked");
        require(nftContract.exists(tokenId), "Certificate does not exist");

        isRevoked[tokenId] = true;
        revocationReason[tokenId] = reason;

        emit CertificateRevoked(tokenId, msg.sender, reason, block.timestamp);
    }

    /// Public, gas-free verification query
    function verifyCertificate(uint256 tokenId)
        external
        view
        returns (
            bool valid,
            string memory metaCID,
            string memory assessmentArtefactCID,
            string memory issuerDID,
            uint256 timestamp
        )
    {
        valid = !isRevoked[tokenId] && nftContract.exists(tokenId);
        CertificateRecord memory record = certificateRecords[tokenId];
        metaCID = record.metadataCID;
        assessmentArtefactCID = record.artefactCID;
        issuerDID = record.issuerDID;
        timestamp = record.issuedAt;
    }
}
