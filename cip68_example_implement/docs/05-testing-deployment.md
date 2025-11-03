# Module 5: Testing, Deployment & Best Practices

## 5.1. Overview

Module cuối cùng này cover:
- Testing strategies (contracts + off-chain + frontend)
- Deployment procedures
- Security best practices
- Production considerations
- Troubleshooting guide

---

## 5.2. Testing Strategy

### 5.2.1. Smart Contract Testing (Aiken)

**Unit Tests:**

```aiken
// validators/update_metadata.ak
test update_with_valid_owner() {
  let datum = CIP68Datum {
    image_url: "ipfs://old",
    description: "Old description"
  }
  
  let new_datum = CIP68Datum {
    image_url: "ipfs://new",
    description: "New description"
  }
  
  let ctx = // Build mock ScriptContext
  
  update_metadata(policy_id, datum, 0, ctx) == True
}

test update_without_owner_token_fails() {
  // Should fail if user token not in inputs
  let ctx = // Build mock context without user token
  
  update_metadata(policy_id, datum, 0, ctx) == False
}
```

**Run tests:**
```bash
cd contracts
aiken check
```

### 5.2.2. Off-chain Testing (Python)

**Unit Tests:**

Create `tests/test_helpers.py`:
```python
import pytest
from off_chain.utils.helpers import build_token_name, create_cip68_datum

def test_build_token_name():
    # Test reference token
    ref_name = build_token_name(100, "Dragon001")
    assert ref_name == "100Dragon001"
    
    # Test user token
    user_name = build_token_name(222, "Dragon001")
    assert user_name == "222Dragon001"

def test_create_cip68_datum():
    datum = create_cip68_datum(
        image_url="ipfs://QmTest",
        description="Test NFT"
    )
    
    assert datum.CONSTR_ID == 0
    assert datum.image_url == b"ipfs://QmTest"
    assert datum.description == b"Test NFT"
```

**Integration Tests:**

Create `tests/test_mint.py`:
```python
import pytest
from off_chain.mint_nft import mint_cip68_nft

@pytest.mark.integration
def test_mint_nft_end_to_end():
    """
    Full mint flow test on Preview testnet
    Requires: Test ADA, valid Blockfrost API key
    """
    # Setup
    name = f"Test{int(time.time())}"
    
    # Execute
    tx_hash = mint_cip68_nft(
        name=name,
        image="ipfs://QmTest",
        description="Integration test NFT",
        submit=True
    )
    
    # Verify
    assert tx_hash is not None
    assert len(tx_hash) == 64  # Valid TX hash
    
    # Wait for confirmation
    time.sleep(30)
    
    # Query to verify
    # ... check that tokens exist on chain
```

**Run tests:**
```bash
cd off_chain

# Unit tests only
pytest tests/ -v

# Include integration tests
pytest tests/ -v --integration

# With coverage
pytest tests/ --cov=off_chain --cov-report=html
```

### 5.2.3. Frontend Testing

**Component Tests (Jest + React Testing Library):**

Create `frontend/__tests__/MintPage.test.tsx`:
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import MintPage from '../pages/mint'

describe('Mint Page', () => {
  it('renders mint form', () => {
    render(<MintPage />)
    
    expect(screen.getByText('Mint CIP-68 NFT')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/NFT Name/i)).toBeInTheDocument()
  })
  
  it('validates required fields', () => {
    render(<MintPage />)
    
    const submitButton = screen.getByText('Mint NFT')
    fireEvent.click(submitButton)
    
    expect(screen.getByText(/fill in all fields/i)).toBeInTheDocument()
  })
})
```

**E2E Tests (Playwright):**

Create `frontend/e2e/mint.spec.ts`:
```typescript
import { test, expect } from '@playwright/test'

test('complete mint flow', async ({ page }) => {
  await page.goto('http://localhost:3000')
  
  // Connect wallet (mocked)
  await page.click('text=Connect Wallet')
  
  // Navigate to mint
  await page.click('text=Go to Mint')
  
  // Fill form
  await page.fill('input[name="name"]', 'E2ETestNFT')
  await page.fill('input[name="image"]', 'ipfs://QmTest123')
  await page.fill('textarea[name="description"]', 'E2E test NFT')
  
  // Submit
  await page.click('button:has-text("Mint NFT")')
  
  // Verify success (or appropriate message)
  await expect(page.locator('text=/success|in progress/i')).toBeVisible()
})
```

---

## 5.3. Deployment

### 5.3.1. Smart Contracts

**Build and Deploy:**

```bash
cd contracts

# Build contracts
aiken build

# Generates plutus.json

# Copy to off_chain
cp plutus.json ../off_chain/

# Version control
git add plutus.json
git commit -m "Update contract build"
```

**Parameter Application:**

Parameters applied at runtime in Python scripts:
```python
# In mint_nft.py
parameterized_validator = apply_params_to_script(
    "update_metadata.update_metadata",
    policy_id.hex()  # Apply policy ID
)
```

**Contract Verification:**

```bash
# Check validator hash
aiken blueprint hash -v update_metadata.update_metadata

# Verify on-chain script matches
# Compare with script address on explorer
```

### 5.3.2. Off-chain Scripts

**Environment Setup:**

```bash
# Production .env
NETWORK=preprod  # or mainnet
BLOCKFROST_PROJECT_ID=preprod_api_key
```

**Installation:**

```bash
cd off_chain

# Create production venv
python -m venv venv_prod
source venv_prod/bin/activate  # Linux/Mac
# or venv_prod\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Freeze exact versions
pip freeze > requirements-lock.txt
```

**Wallet Management:**

```bash
# Generate production wallets securely
python -c "from utils.helpers import generate_or_load_wallet; generate_or_load_wallet('prod_issuer.mnemonic')"

# Backup mnemonics OFFLINE
# Use hardware wallet for large values
```

### 5.3.3. Frontend

**Build:**

```bash
cd frontend

# Install
npm ci  # Use lockfile

# Build
npm run build

# Test production build
npm run start
```

**Deploy to Vercel:**

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

**Environment Variables (Vercel Dashboard):**
- `NEXT_PUBLIC_NETWORK=preprod`
- `NEXT_PUBLIC_BLOCKFROST_API_KEY=preprod_xxx`

**Custom Domain:**
```bash
# Add domain
vercel domains add cip68-example.com
```

---

## 5.4. Security Best Practices

### 5.4.1. Key Management

**DO:**
- ✅ Use hardware wallets for mainnet
- ✅ Store mnemonics offline (paper backup)
- ✅ Encrypt sensitive files
- ✅ Use different keys per environment
- ✅ Rotate keys periodically

**DON'T:**
- ❌ Commit mnemonics to git
- ❌ Share keys via email/chat
- ❌ Use testnet keys on mainnet
- ❌ Store keys in plain text

**Example: Encrypt mnemonic**
```bash
# Encrypt
gpg -c issuer.mnemonic
# Creates issuer.mnemonic.gpg

# Decrypt
gpg issuer.mnemonic.gpg
```

### 5.4.2. Transaction Safety

**Validation Checklist:**
- [ ] Verify recipient addresses
- [ ] Check transaction amounts
- [ ] Review fee (should be < 1 ADA typically)
- [ ] Confirm network (preview/preprod/mainnet)
- [ ] Test on testnet first
- [ ] Start with small amounts

**Example validation:**
```python
def validate_transaction(tx):
    # Check fee is reasonable
    assert tx.transaction_body.fee < 1_000_000, "Fee too high"
    
    # Check outputs
    for output in tx.transaction_body.outputs:
        # Verify address network
        assert output.address.network == expected_network
        
        # Check min ADA
        assert output.amount.coin >= MIN_ADA
    
    return True
```

### 5.4.3. Smart Contract Security

**Validator Security:**
- Check all inputs satisfy constraints
- Validate datum structure
- Ensure token conservation
- Prevent double satisfaction
- Handle edge cases

**Example secure checks:**
```aiken
fn update_metadata(
  policy_id: PolicyId,
  datum: CIP68Datum,
  redeemer: Void,
  ctx: ScriptContext
) -> Bool {
  // 1. Check datum is valid
  expect datum_valid = validate_datum(datum)
  
  // 2. Check ref token in inputs
  expect ref_token_found = has_ref_token(ctx.inputs, policy_id)
  
  // 3. Check ref token in outputs
  expect ref_token_preserved = has_ref_token(ctx.outputs, policy_id)
  
  // 4. Check user token proves ownership
  expect user_token_found = has_user_token(ctx.inputs, policy_id)
  
  // All checks must pass
  datum_valid && ref_token_found && 
  ref_token_preserved && user_token_found
}
```

### 5.4.4. API Security

**If building backend API:**

```typescript
// Rate limiting
import rateLimit from 'express-rate-limit'

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
})

app.use('/api/', limiter)

// Input validation
import { body, validationResult } from 'express-validator'

app.post('/api/mint',
  body('name').isAlphanumeric().isLength({ min: 3, max: 20 }),
  body('image').isURL(),
  body('description').isLength({ max: 500 }),
  async (req, res) => {
    const errors = validationResult(req)
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() })
    }
    
    // Process...
  }
)

// CORS
import cors from 'cors'

app.use(cors({
  origin: 'https://your-frontend.vercel.app',
  credentials: true
}))
```

---

## 5.5. Monitoring & Logging

### 5.5.1. Transaction Monitoring

**Track transactions:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transactions.log'),
        logging.StreamHandler()
    ]
)

def mint_nft(...):
    logging.info(f"Starting mint for {name}")
    
    try:
        tx_hash = submit_transaction(...)
        logging.info(f"Success: {tx_hash}")
        
        # Monitor confirmation
        confirmed = wait_for_confirmation(tx_hash, timeout=300)
        logging.info(f"Confirmed in block: {confirmed.block}")
        
    except Exception as e:
        logging.error(f"Failed: {e}", exc_info=True)
```

**Log structure:**
```
2024-11-03 10:15:23 - INFO - Starting mint for Dragon001
2024-11-03 10:15:45 - INFO - Transaction built: 2.3KB, fee: 0.23 ADA
2024-11-03 10:15:47 - INFO - Success: a1b2c3d4...
2024-11-03 10:16:15 - INFO - Confirmed in block: 12345678
```

### 5.5.2. Error Tracking

**Sentry integration:**
```python
import sentry_sdk

sentry_sdk.init(
    dsn="your_sentry_dsn",
    environment="production"
)

try:
    mint_nft(...)
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```

---

## 5.6. Performance Optimization

### 5.6.1. Transaction Batching

```python
def mint_multiple_nfts(nfts: List[NFTData]):
    """Mint multiple NFTs in single transaction"""
    
    builder = TransactionBuilder(context)
    
    for nft in nfts:
        # Add mints
        builder.mint = MultiAsset({
            policy_id: Asset({
                build_token_name(100, nft.name): 1,
                build_token_name(222, nft.name): 1,
            })
        })
        
        # Add outputs
        builder.add_output(...)  # Reference token
        builder.add_output(...)  # User token
    
    # Single transaction for all NFTs
    signed_tx = builder.build_and_sign(...)
    return context.submit_tx(signed_tx)
```

### 5.6.2. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=10)
def get_protocol_params(network: str):
    """Cache protocol params for 5 minutes"""
    context = get_blockfrost_context()
    return context.protocol_param

@lru_cache(maxsize=100)
def load_plutus_script(name: str):
    """Cache loaded scripts"""
    with open(f"../contracts/plutus.json") as f:
        # Load and cache
    return script
```

---

## 5.7. Production Checklist

### Before Mainnet Launch:

**Smart Contracts:**
- [ ] All tests passing
- [ ] Security audit completed
- [ ] Edge cases handled
- [ ] Gas optimization done
- [ ] Validator logic verified

**Off-chain Scripts:**
- [ ] Tested on preprod
- [ ] Error handling comprehensive
- [ ] Logging implemented
- [ ] Monitoring setup
- [ ] Backup strategy defined

**Frontend:**
- [ ] All features tested
- [ ] Responsive on all devices
- [ ] Error messages clear
- [ ] Loading states implemented
- [ ] Performance optimized

**Infrastructure:**
- [ ] Production environment setup
- [ ] API keys secured
- [ ] Rate limiting configured
- [ ] Backup nodes available
- [ ] Disaster recovery plan

**Documentation:**
- [ ] User guide complete
- [ ] API documentation
- [ ] Troubleshooting guide
- [ ] Contact information

---

## 5.8. Troubleshooting Guide

### Issue: Transaction keeps failing

**Diagnosis:**
```python
# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Print transaction details
print(f"Inputs: {len(tx.transaction_body.inputs)}")
print(f"Outputs: {len(tx.transaction_body.outputs)}")
print(f"Fee: {tx.transaction_body.fee}")
print(f"Size: {len(tx.to_cbor())} bytes")
```

**Common causes:**
- Insufficient UTxOs
- Fee too low
- Invalid script
- Protocol params changed

### Issue: Script evaluation fails

**Check:**
1. Redeemer matches expected type
2. Datum structure correct
3. All validator conditions met
4. Required tokens present

**Debug:**
```bash
# View transaction in CBOR
cardano-cli transaction view --tx-body-file tx.cbor

# Check script hash
aiken blueprint hash -v validator_name
```

### Issue: NFT not visible in wallet

**Causes:**
- Transaction not confirmed yet
- Wallet not synced
- Token metadata not registered
- Wrong network

**Solution:**
```bash
# Check on explorer
https://preview.cardanoscan.io/transaction/{tx_hash}

# Verify token exists
python query_nft.py --policy {policy_id}

# Force wallet resync
```

---

## 5.9. Maintenance

### Regular Tasks:

**Weekly:**
- Review error logs
- Check transaction success rate
- Monitor ADA balances
- Update dependencies (security patches)

**Monthly:**
- Full backup of keys/mnemonics
- Review and rotate API keys
- Performance analysis
- Cost optimization

**Quarterly:**
- Security audit
- Dependency updates (major versions)
- Documentation review
- User feedback analysis

---

## 5.10. Resources

### Official Documentation:
- [Cardano Docs](https://docs.cardano.org/)
- [CIP-68 Specification](https://cips.cardano.org/cips/cip68/)
- [PyCardano Docs](https://pycardano.readthedocs.io/)
- [Aiken Documentation](https://aiken-lang.org/)
- [Mesh SDK Docs](https://meshjs.dev/)

### Community:
- [Cardano Forum](https://forum.cardano.org/)
- [Cardano Stack Exchange](https://cardano.stackexchange.com/)
- [IOHK Technical Discord](https://discord.gg/cardano)

### Tools:
- [Cardano Explorer](https://cardanoscan.io/)
- [Pool.pm](https://pool.pm/) - Token explorer
- [Cardano Testnet Faucet](https://docs.cardano.org/cardano-testnets/tools/faucet/)

---

## 5.11. Next Steps

**Congratulations!** 🎉 You've completed the CIP-68 NFT course.

**Continue Learning:**
1. Build more complex validators
2. Integrate with DeFi protocols
3. Explore other CIPs (CIP-25, CIP-67, etc.)
4. Contribute to open source

**Project Ideas:**
- Dynamic NFT marketplace
- NFT gaming platform
- Achievement/certificate system
- Real-world asset tokenization

---

**Course Complete!** Check the [main README](../README.md) for additional resources.
