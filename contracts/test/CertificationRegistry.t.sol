// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/CertificationNFT.sol";
import "../src/CertificationRegistry.sol";

contract CertificationRegistryTest is Test {
    CertificationNFT private nft;
    CertificationRegistry private registry;

    address private admin = address(this);
    address private issuer = address(0xA11CE);
    address private learner = address(0xB0B);
    address private stranger = address(0xBAD);

    string private issuerDID = "did:ethr:arbitrum:0xA11CE";
    string private metadataCID = "bafy-metadata";
    string private artefactCID = "bafy-assessment";

    function setUp() public {
        nft = new CertificationNFT();
        registry = new CertificationRegistry(address(nft));
        nft.setRegistry(address(registry));
    }

    function testAdminCanAuthorizeIssuer() public {
        registry.addAuthorizedIssuer(issuer);

        assertTrue(registry.isAuthorizedIssuer(issuer));
        assertTrue(registry.authorizedIssuers(issuer));
        assertTrue(registry.hasRole(registry.ISSUER_ROLE(), issuer));
    }

    function testAuthorizedIssuerCanIssueAndVerifyCertificate() public {
        registry.addAuthorizedIssuer(issuer);

        vm.prank(issuer);
        uint256 tokenId = registry.issueCertificate(
            learner,
            issuerDID,
            metadataCID,
            artefactCID
        );

        assertEq(tokenId, 1);
        assertEq(nft.ownerOf(tokenId), learner);
        assertEq(nft.tokenURI(tokenId), metadataCID);
        assertEq(registry.artefactCID(tokenId), artefactCID);

        (
            bool valid,
            string memory returnedMetadataCID,
            string memory returnedArtefactCID,
            string memory returnedIssuerDID,
            uint256 timestamp
        ) = registry.verifyCertificate(tokenId);

        assertTrue(valid);
        assertEq(returnedMetadataCID, metadataCID);
        assertEq(returnedArtefactCID, artefactCID);
        assertEq(returnedIssuerDID, issuerDID);
        assertGt(timestamp, 0);
    }

    function testUnauthorizedIssuerCannotIssue() public {
        vm.prank(stranger);
        vm.expectRevert("Issuer not authorized");
        registry.issueCertificate(learner, issuerDID, metadataCID, artefactCID);
    }

    function testAuthorizedIssuerCanRevokeWithReason() public {
        registry.addAuthorizedIssuer(issuer);

        vm.startPrank(issuer);
        uint256 tokenId = registry.issueCertificate(
            learner,
            issuerDID,
            metadataCID,
            artefactCID
        );

        registry.revokeCertificate(tokenId, "Academic misconduct");
        vm.stopPrank();

        assertTrue(registry.isRevoked(tokenId));
        assertEq(registry.revocationReason(tokenId), "Academic misconduct");

        (bool valid, , , , ) = registry.verifyCertificate(tokenId);
        assertFalse(valid);
    }

    function testNFTIsSoulbound() public {
        registry.addAuthorizedIssuer(issuer);

        vm.prank(issuer);
        uint256 tokenId = registry.issueCertificate(
            learner,
            issuerDID,
            metadataCID,
            artefactCID
        );

        vm.prank(learner);
        vm.expectRevert("SkillCert: non-transferable");
        nft.transferFrom(learner, stranger, tokenId);
    }
}
