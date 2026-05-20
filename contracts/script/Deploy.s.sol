// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/CertificationNFT.sol";
import "../src/CertificationRegistry.sol";

contract Deploy is Script {
    function run() external {
        uint256 deployerKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address initialIssuer = vm.envOr("INITIAL_ISSUER", address(0));

        vm.startBroadcast(deployerKey);

        CertificationNFT nft = new CertificationNFT();
        CertificationRegistry registry = new CertificationRegistry(address(nft));
        nft.setRegistry(address(registry));

        if (initialIssuer != address(0)) {
            address[] memory initialIssuers = new address[](1);
            initialIssuers[0] = initialIssuer;
            registry.setAuthorizedIssuers(initialIssuers);
        }

        vm.stopBroadcast();
    }
}
