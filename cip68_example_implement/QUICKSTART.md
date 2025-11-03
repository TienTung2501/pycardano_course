# 🚀 Quick Start Guide

Get started with CIP-68 NFT development in 15 minutes!

## ⚡ Prerequisites

- Python 3.9+
- Node.js 18+
- Aiken compiler
- Cardano wallet (Nami, Eternl, or Flint)
- ~10 test ADA from faucet

## 📦 Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd cip68_example_implement
```

### 2. Setup Smart Contracts
```bash
cd contracts

# Install Aiken if not installed
# See: https://aiken-lang.org/installation-instructions

# Build contracts
aiken build

# Verify plutus.json generated
ls plutus.json
```

### 3. Setup Python Environment
```bash
cd ../off_chain

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your Blockfrost API key
```

### 4. Setup Frontend (Optional)
```bash
cd ../frontend

# Install dependencies
npm install

# Configure
cp .env.local.example .env.local
# Edit .env.local
```

## 🎯 Your First CIP-68 NFT

### Step 1: Get Test ADA

Visit [Cardano Testnet Faucet](https://docs.cardano.org/cardano-testnets/tools/faucet/)

The scripts will auto-generate a wallet on first run. You'll see:
```
No wallet found. Generating new wallet...
Mnemonic: word1 word2 word3 ... word24

⚠️ SAVE THIS MNEMONIC SAFELY!

Address: addr_test1qq...
```

Send ~10 tADA to this address.

### Step 2: Mint Your First NFT

```bash
cd off_chain

python mint_nft.py \
  --name "MyFirstNFT" \
  --image "ipfs://QmYx6GsYAKnNzZ9A6NvEKV9nf1VaDzJrqDR4kmCKp8JvCE" \
  --desc "My first CIP-68 NFT!"
```

**Expected Output:**
```
============================================================
CIP-68 NFT Minting (PPBL Approach - Native Script)
============================================================

[1] Connecting to Cardano network...
    Network: preview

[2] Loading wallets...
    Issuer: addr_test1qp0w79aen4...
    User:   addr_test1qqdpq8qm24...

[3] Setting up minting policy (Native Script)...
    Policy ID: 7fd86d5ade2db175...

[4] Building token names...
    Reference token: 100MyFirstNFT
    User token:      222MyFirstNFT

...

[9] Submitting transaction...
    ✓ Transaction submitted!
    TX Hash: a1b2c3d4e5f6...
    
    View on explorer:
    https://preview.cardanoscan.io/transaction/a1b2c3d4e5f6...

============================================================
```

**Save the Policy ID!** You'll need it for querying and updating.

### Step 3: Query Your NFT

```bash
python query_nft.py --policy "YOUR_POLICY_ID"
```

**Output:**
```
NFT #1: MyFirstNFT
────────────────────────────────────────

Policy ID: 7fd86d5a...

Tokens:
  Reference (100): 100MyFirstNFT
  User (222):      222MyFirstNFT

Ownership: ✓ You own this NFT

Metadata:
  Image URL:   ipfs://QmYx6...
  Description: My first CIP-68 NFT!
```

### Step 4: Update Metadata

```bash
python update_nft.py \
  --name "MyFirstNFT" \
  --policy "YOUR_POLICY_ID" \
  --image "ipfs://QmNewImageHash" \
  --desc "Updated: My NFT just got better!"
```

### Step 5: (Optional) Burn NFT

```bash
python burn_nft.py \
  --name "MyFirstNFT" \
  --policy "YOUR_POLICY_ID"
```

This will:
- Burn both tokens (100 + 222)
- Reclaim locked ADA (~4-5 ADA)
- Return to your wallet

## 🌐 Run Frontend

```bash
cd frontend
npm run dev
```

Open http://localhost:3000

**Note:** Frontend is UI mockup. Use Python scripts for actual transactions.

## 📚 Next Steps

1. **Read Documentation:**
   - [Module 1: CIP-68 Introduction](docs/01-introduction.md)
   - [Module 2: Smart Contracts](docs/02-smart-contracts.md)
   - [Module 3: Off-chain Scripts](docs/03-offchain-pycardano.md)

2. **Try Examples:**
   - Gaming NFT (Dragon)
   - Achievement Badge
   - Virtual Real Estate
   - See [examples/README.md](examples/README.md)

3. **Build Your Own:**
   - Design custom metadata
   - Create collection series
   - Implement dynamic updates

## 🐛 Common Issues

### "Address does not have any UTxOs"
→ Send test ADA to the generated address

### "plutus.json not found"
→ Run `aiken build` in contracts directory

### "Failed to connect to Blockfrost"
→ Check your API key in `.env`

### Transaction fails
→ Ensure you have enough ADA (min 10 tADA)
→ Check network is set to `preview` in `.env`

## 💡 Tips

**Development:**
- Always test on Preview testnet first
- Save your mnemonics securely
- Keep policy IDs for reference
- Check transactions on explorer

**Production:**
- Switch to Preprod for final testing
- Use hardware wallet for mainnet
- Conduct security audit
- Monitor transactions

## 🎓 Learning Path

### Beginner (Day 1-2):
- [x] Install tools
- [x] Mint first NFT
- [x] Query NFT
- [x] Update metadata
- [ ] Read Module 1 & 2

### Intermediate (Day 3-5):
- [ ] Understand validator logic
- [ ] Modify datum structure
- [ ] Create custom metadata
- [ ] Build collection series
- [ ] Read Module 3 & 4

### Advanced (Week 2+):
- [ ] Write custom validators
- [ ] Implement complex datums
- [ ] Build production dApp
- [ ] Security hardening
- [ ] Read Module 5

## 📞 Get Help

- **Documentation:** Check [docs/](docs/) folder
- **Examples:** See [examples/](examples/) folder
- **Issues:** Common problems in each module
- **Community:** Cardano forums and Discord

## ✅ Checklist

Before you start coding:
- [ ] Aiken installed and working
- [ ] Python 3.9+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Blockfrost API key configured
- [ ] Test ADA received
- [ ] Wallet mnemonic backed up

## 🎉 Success!

You now have:
- ✅ Working CIP-68 NFT platform
- ✅ Minted your first dynamic NFT
- ✅ Updated its metadata
- ✅ Learned the basics

**Continue learning** with the full course modules!

---

**Happy Building!** 🚀
