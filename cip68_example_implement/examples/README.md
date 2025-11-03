# CIP-68 NFT Examples

This directory contains example metadata files, transaction samples, and usage scenarios for the CIP-68 NFT platform.

## 📁 Contents

### Metadata Examples

1. **metadata-dragon.json** - Gaming NFT
   - Collectible dragon with attributes
   - Rarity, power, element traits
   - Part of a collection series

2. **metadata-achievement.json** - Achievement Badge
   - Educational certificate/badge
   - Tracks completion status
   - Dynamically updatable progress

3. **metadata-realestate.json** - Virtual Real Estate
   - Metaverse land plot
   - Location and development data
   - Dynamic property values

### Transaction Examples

Below are real-world transaction scenarios.

---

## 🎮 Example 1: Gaming NFT (Dragon)

### Scenario
Create a collectible dragon NFT for a blockchain game. The dragon's stats can be updated as it levels up in the game.

### Initial Mint

**Command:**
```bash
python mint_nft.py \
  --name "Dragon001" \
  --image "ipfs://QmYx6GsYAKnNzZ9A6NvEKV9nf1VaDzJrqDR4kmCKp8JvCE" \
  --desc "A rare legendary fire dragon with immense power."
```

**Output:**
```
Policy ID: 7fd86d5ade2db175fd2e491e117ac1fed4989c6ae5bf48c1be0a6b37
Reference token: 7fd86d5a...100Dragon001
User token:      7fd86d5a...222Dragon001
TX Hash: a1b2c3d4e5f6789...
```

**Explorer:** https://preview.cardanoscan.io/transaction/a1b2c3d4e5f6789...

### Update After Leveling Up

**Command:**
```bash
python update_nft.py \
  --name "Dragon001" \
  --policy "7fd86d5ade2db175fd2e491e117ac1fed4989c6ae5bf48c1be0a6b37" \
  --image "ipfs://QmNewImageWithStrongerDragon" \
  --desc "Legendary fire dragon - EVOLVED! Power level increased to 100."
```

**Output:**
```
Metadata updated!
TX Hash: f9e8d7c6b5a4321...
```

---

## 🏆 Example 2: Achievement Badge

### Scenario
Issue a completion certificate for a course. The badge dynamically updates as the student progresses through modules.

### Initial Issuance

**Command:**
```bash
python mint_nft.py \
  --name "CourseBadge2024" \
  --image "ipfs://QmPK3Xqvs8fDqAb8Gk4RFxCj9YhN3mVs2pQwXzKjL5vRtY" \
  --desc "CIP-68 Course - Module 1 completed"
```

### Update on Course Completion

**Command:**
```bash
python update_nft.py \
  --name "CourseBadge2024" \
  --policy "abc123..." \
  --image "ipfs://QmCompletedBadgeGoldVersion" \
  --desc "CIP-68 Course - ALL MODULES COMPLETED! ⭐"
```

**Use Cases:**
- Educational certificates
- Professional credentials
- Skill tracking
- Progress rewards

---

## 🏠 Example 3: Virtual Real Estate

### Scenario
Tokenize virtual land. Metadata updates when buildings are constructed or property value changes.

### Initial Mint

**Command:**
```bash
python mint_nft.py \
  --name "Plot42District7" \
  --image "ipfs://QmT8vZxQvC2hKf9xDjRb5mNp3wYqL7sVkX2JnM4RzPtGhB" \
  --desc "1000 sqm virtual land plot in District 7"
```

### Update After Development

**Command:**
```bash
python update_nft.py \
  --name "Plot42District7" \
  --policy "def456..." \
  --image "ipfs://QmUpdatedImageWithBuildings" \
  --desc "1000 sqm plot - Now featuring luxury villa! Value: 75000 ADA"
```

**Use Cases:**
- Metaverse land
- Virtual property management
- Real-world asset tokenization
- Dynamic valuations

---

## 📊 Transaction Details

### Typical Transaction Structure

**Mint Transaction:**
```
Inputs:
  - User wallet UTxO (for fees + min ADA)

Outputs:
  - Reference token (100) → Script address
    Amount: 3 ADA
    Datum: CIP68Datum {
      image_url: "ipfs://...",
      description: "..."
    }
  
  - User token (222) → User wallet
    Amount: 2 ADA

  - Change → User wallet

Minting:
  - Policy: Native script (signature-based)
  - Assets: 
    * 100Dragon001: +1
    * 222Dragon001: +1

Fee: ~0.23 ADA
Size: ~1.8 KB
```

**Update Transaction:**
```
Inputs:
  - Reference token UTxO (from script)
  - User token UTxO (from wallet)
  - Fee UTxO (from wallet)

Outputs:
  - Reference token (100) → Script address
    Amount: 3 ADA
    Datum: NEW CIP68Datum {
      image_url: "ipfs://new...",
      description: "updated..."
    }
  
  - User token (222) → User wallet
    Amount: 2 ADA

  - Change → User wallet

Script Execution:
  - Validator: update_metadata
  - Redeemer: Unit (Constructor 0)

Collateral: 5 ADA (returned if successful)
Fee: ~0.45 ADA
Size: ~2.5 KB
```

---

## 🔍 Querying Examples

### Query All NFTs of a Policy

**Command:**
```bash
python query_nft.py --policy "7fd86d5ade2db175fd2e491e117ac1fed4989c6ae5bf48c1be0a6b37"
```

**Output:**
```
================================================================================
CIP-68 NFT Information
================================================================================

────────────────────────────────────────────────────────────────────────────────
NFT #1: Dragon001
────────────────────────────────────────────────────────────────────────────────

Policy ID:
  7fd86d5ade2db175fd2e491e117ac1fed4989c6ae5bf48c1be0a6b37

Tokens:
  Reference (100): 313030447261676f6e303031
  User (222):      323232447261676f6e303031

Ownership:
  ✓ You own this NFT

Reference Token UTxO:
  a1b2c3d4e5f6789...#0
  Locked ADA: 3.00

Metadata:
  Image URL:   ipfs://QmYx6GsYAKnNzZ9A6NvEKV9nf1VaDzJrqDR4kmCKp8JvCE
  Description: A rare legendary fire dragon with immense power.

Full Asset ID:
  Reference: 7fd86d5a...313030447261676f6e303031
  User:      7fd86d5a...323232447261676f6e303031

================================================================================
```

### Filter by Name

**Command:**
```bash
python query_nft.py --policy "7fd86d5a..." --name "Dragon"
```

### Check Ownership

**Command:**
```bash
python query_nft.py \
  --policy "7fd86d5a..." \
  --owner "addr_test1qqdpq8qm24gh27mkjkrmpc5nkdnm8lexejxsqqk7t6lsch..."
```

---

## 🔥 Burning Example

### Scenario
Remove an NFT and reclaim locked ADA.

**Command:**
```bash
python burn_nft.py \
  --name "Dragon001" \
  --policy "7fd86d5ade2db175fd2e491e117ac1fed4989c6ae5bf48c1be0a6b37"
```

**Output:**
```
NFT burned:
- Policy ID: 7fd86d5a...
- Name: Dragon001
- Reference token: BURNED
- User token: BURNED
- ADA reclaimed: ~4.77 ADA

TX Hash: 9876543210fedcba...
```

---

## 💡 Best Practices from Examples

### 1. Naming Convention
```
✅ Good: "Dragon001", "Plot42District7", "CourseBadge2024"
❌ Bad:  "my nft", "test123", "aaa"

- Use alphanumeric characters
- No spaces (use camelCase or underscores)
- Descriptive and unique
```

### 2. Image URLs
```
✅ Good: "ipfs://QmYx6GsYAKnNzZ9A6NvEKV9nf1VaDzJrqDR4kmCKp8JvCE"
❌ Bad:  "http://myserver.com/image.jpg" (can go offline)

- Prefer IPFS for permanence
- Use content-addressed storage
- Verify hash before minting
```

### 3. Descriptions
```
✅ Good: Clear, concise, informative
❌ Bad:  Too long (>500 chars), generic ("An NFT")

- Explain what makes it unique
- Include key attributes
- Keep under 200 characters for display
```

### 4. Metadata Structure
```json
{
  "name": "Clear, unique name",
  "image": "Permanent storage (IPFS)",
  "description": "Concise but informative",
  "attributes": [
    // Structured traits for filtering
  ],
  "dynamic_properties": {
    // Fields that will be updated
  }
}
```

---

## 📸 Screenshots

*Note: Add screenshots to this directory:*

- `screenshot-wallet-connect.png` - Wallet connection UI
- `screenshot-mint-form.png` - Mint NFT form
- `screenshot-gallery.png` - NFT gallery view
- `screenshot-explorer.png` - Transaction on explorer
- `screenshot-update-success.png` - Successful update

---

## 🎓 Learning Exercises

### Exercise 1: Create Your Own NFT
1. Design metadata for a custom use case
2. Mint the NFT on Preview testnet
3. Update its metadata
4. Query to verify changes

### Exercise 2: Collection Series
1. Mint 5 NFTs as a collection
2. Ensure consistent naming (e.g., "Series1_001" to "Series1_005")
3. Query all NFTs of the policy
4. Update one NFT's metadata

### Exercise 3: Dynamic Game Item
1. Create a game item NFT (weapon, armor, etc.)
2. Simulate "leveling up" by updating stats
3. Track changes via query
4. Burn the NFT when "consumed"

---

## 📚 Additional Resources

- [IPFS Upload Guide](https://docs.ipfs.io/how-to/command-line-quick-start/)
- [Pinata IPFS Service](https://pinata.cloud/)
- [NFT.Storage](https://nft.storage/)
- [Cardano Token Registry](https://github.com/cardano-foundation/cardano-token-registry)

---

**Happy Minting!** 🎨
