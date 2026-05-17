// SPDX-License-Identifier: MITpragma solidity ^0.8.20;
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";


//@audit add more layer of security
contract CertificationNFT is ERC721URIStorage, Ownable { 

    uint256 private _tokenIdCounter;
    address public registry;
     
    modifier onlyRegistry() { 
       require(msg.sender == registry, 'Caller is not the registry');
        _;
    }

    constructor() ERC721('SkillCert', 'SCRT') Ownable(msg.sender) {} 
      
      
    function setRegistry(address _registry) external onlyOwner {
        registry = _registry;
    }
     
    function mint(address to, string calldata uri) external onlyRegistry returns (uint256) { 
       uint256 tokenId = ++_tokenIdCounter;
       _safeMint(to, tokenId);
       _setTokenURI(tokenId, uri);
     return tokenId;
    }
          
          
    function exists(uint256 tokenId) external view returns (bool) {
     return _ownerOf(tokenId) != address(0);
    }  
     
    // Soulbound: prevent all post-mint transfers    
    function _update(address to, uint256 tokenId, address auth) internal override returns (address) { 
     address from = _ownerOf(tokenId);     
     require(from == address(0), 'SkillCert: non-transferable');
     return super._update(to, tokenId, auth);
    }
}
//@audit cross check the parenthesis error