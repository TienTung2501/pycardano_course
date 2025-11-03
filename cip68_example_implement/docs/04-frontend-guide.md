# Module 4: Frontend Development với Next.js và Mesh SDK

## 4.1. Overview

Module này hướng dẫn build web interface cho CIP-68 NFT platform sử dụng:
- **Next.js** - React framework
- **Mesh SDK** - Cardano blockchain integration
- **Tailwind CSS** - Styling
- **TypeScript** - Type safety

---

## 4.2. Architecture

```
┌─────────────────┐
│   User Browser  │
│  (Wallet Ext)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Next.js App   │
│   (Frontend)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐  ┌────────────┐
│  Mesh  │  │  Backend   │
│  SDK   │  │ API (Opt)  │
└───┬────┘  └─────┬──────┘
    │             │
    ▼             ▼
┌─────────────────────┐
│  Cardano Blockchain │
│   (Preview/Preprod) │
└─────────────────────┘
```

---

## 4.3. Setup Project

### Bước 1: Initialize Next.js

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Mở http://localhost:3000

### Bước 2: Verify Dependencies

**package.json:**
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "@meshsdk/core": "^1.5.0",
    "@meshsdk/react": "^1.5.0",
    "axios": "^1.6.0"
  }
}
```

### Bước 3: Configure Environment

**.env.local:**
```bash
NEXT_PUBLIC_NETWORK=preview
NEXT_PUBLIC_BLOCKFROST_API_KEY=your_api_key
```

---

## 4.4. Wallet Integration

### Setup MeshProvider

**pages/_app.tsx:**
```typescript
import { MeshProvider } from '@meshsdk/react'
import '../styles/globals.css'

export default function App({ Component, pageProps }) {
  return (
    <MeshProvider>
      <Component {...pageProps} />
    </MeshProvider>
  )
}
```

### Connect Wallet

```typescript
import { useWallet } from '@meshsdk/react'

export default function HomePage() {
  const { wallet, connected, connect, disconnect } = useWallet()
  
  const handleConnect = async () => {
    await connect('nami') // hoặc 'eternl', 'flint'
    
    if (wallet) {
      const address = await wallet.getChangeAddress()
      console.log('Connected:', address)
    }
  }
  
  return (
    <div>
      {connected ? (
        <button onClick={disconnect}>Disconnect</button>
      ) : (
        <button onClick={handleConnect}>Connect Wallet</button>
      )}
    </div>
  )
}
```

### Get Wallet Info

```typescript
// Get addresses
const changeAddress = await wallet.getChangeAddress()
const rewardAddress = await wallet.getRewardAddresses()

// Get UTxOs
const utxos = await wallet.getUtxos()

// Get assets
const assets = await wallet.getAssets()

// Get balance
const balance = await wallet.getBalance()
```

---

## 4.5. Display NFT Gallery

### Query NFTs

**Approach 1: Direct blockchain query (complex)**
```typescript
import { BlockfrostProvider } from '@meshsdk/core'

const provider = new BlockfrostProvider('your_api_key')

// Get assets at address
const assets = await provider.fetchAddressUTxOs(address)

// Filter CIP-68 tokens
const cip68Tokens = assets.filter(utxo => {
  // Check for 100/222 prefix in asset names
  return utxo.output.amount.some(asset => 
    asset.unit.startsWith('313030') || // "100"
    asset.unit.startsWith('323232')    // "222"
  )
})
```

**Approach 2: Backend API (recommended)**
```typescript
// Call backend that runs Python query script
const response = await fetch(`/api/nfts?policy=${policyId}`)
const data = await response.json()

setNfts(data.nfts)
```

### Display Cards

```typescript
interface NFT {
  name: string
  policyId: string
  metadata: {
    image_url: string
    description: string
  }
}

function NFTCard({ nft }: { nft: NFT }) {
  const imageUrl = nft.metadata.image_url.startsWith('ipfs://')
    ? `https://ipfs.io/ipfs/${nft.metadata.image_url.replace('ipfs://', '')}`
    : nft.metadata.image_url
  
  return (
    <div className="card">
      <img src={imageUrl} alt={nft.name} />
      <h3>{nft.name}</h3>
      <p>{nft.metadata.description}</p>
      <button>Update</button>
    </div>
  )
}
```

---

## 4.6. Build Transactions

### Overview

Mesh SDK cung cấp transaction builder, nhưng CIP-68 requires:
1. Load Plutus scripts
2. Apply parameters
3. Create complex datums
4. Handle script inputs/outputs

### Basic Transaction

```typescript
import { Transaction } from '@meshsdk/core'

const tx = new Transaction({ initiator: wallet })

// Add inputs (auto-selected from wallet)
// Add outputs
tx.sendLovelace(address, '2000000')

// Build and sign
const unsignedTx = await tx.build()
const signedTx = await wallet.signTx(unsignedTx)

// Submit
const txHash = await wallet.submitTx(signedTx)
```

### CIP-68 Minting (Simplified Concept)

```typescript
// Note: This is conceptual. Full implementation needs:
// - Proper native script loading
// - Correct asset naming (100 + name)
// - Datum creation and inline datum
// - Script address calculation

const forgingScript = {
  type: 'all',
  scripts: [
    {
      type: 'sig',
      keyHash: policyKeyHash,
    },
  ],
}

const tx = new Transaction({ initiator: wallet })

// Mint reference token (100)
tx.mintAsset(forgingScript, {
  assetName: '100' + nftName,
  assetQuantity: '1',
})

// Mint user token (222)
tx.mintAsset(forgingScript, {
  assetName: '222' + nftName,
  assetQuantity: '1',
})

// Send reference token to script
tx.sendAssets(
  scriptAddress,
  [{ unit: policyId + '100' + nftName, quantity: '1' }],
  { inline: datum } // Datum với metadata
)

// Send user token to wallet
tx.sendAssets(
  userAddress,
  [{ unit: policyId + '222' + nftName, quantity: '1' }]
)

const unsignedTx = await tx.build()
const signedTx = await wallet.signTx(unsignedTx)
const txHash = await wallet.submitTx(signedTx)
```

### CIP-68 Update (Conceptual)

```typescript
// Find reference token UTxO at script
const scriptUtxos = await provider.fetchAddressUTxOs(scriptAddress)
const refUtxo = scriptUtxos.find(utxo => 
  // Has reference token (100)
)

// Find user token in wallet
const walletUtxos = await wallet.getUtxos()
const userUtxo = walletUtxos.find(utxo =>
  // Has user token (222)
)

const tx = new Transaction({ initiator: wallet })

// Spend reference UTxO from script
tx.redeemValue({
  value: refUtxo,
  script: validator,
  redeemer: { data: { constructor: 0, fields: [] } }
})

// Add user token as input (prove ownership)
tx.setTxInputs([userUtxo])

// Create new output với updated datum
tx.sendAssets(
  scriptAddress,
  [{ unit: refToken, quantity: '1' }],
  { inline: newDatum }
)

// Return user token
tx.sendAssets(
  userAddress,
  [{ unit: userToken, quantity: '1' }]
)

// Set collateral (for Plutus script)
tx.setCollateral([collateralUtxo])

const unsignedTx = await tx.build()
const signedTx = await wallet.signTx(unsignedTx)
const txHash = await wallet.submitTx(signedTx)
```

---

## 4.7. Current Implementation Status

### ✅ Implemented

- Wallet connection (Nami, Eternl, Flint)
- UI pages (Home, Mint, Gallery, Update)
- Responsive design
- Form validation
- Error handling

### ⚠️ Partially Implemented

- NFT querying (needs backend API)
- Transaction display (mock data)

### ❌ Not Implemented

- Full transaction building for CIP-68
- Datum creation in TypeScript
- Script loading and parameterization
- IPFS upload integration

### 💡 Recommended Approach

**For Production:**

1. **Backend API** - Build Express.js API that calls Python scripts:
   ```typescript
   // pages/api/mint.ts
   export default async function handler(req, res) {
     const { name, image, description } = req.body
     
     // Execute Python script
     const result = execSync(
       `cd ../off_chain && python mint_nft.py --name "${name}" --image "${image}" --desc "${description}"`
     )
     
     return res.json({ txHash: result.toString() })
   }
   ```

2. **Hybrid Approach** - Use frontend for UX, Python for blockchain:
   - Frontend: Form input, validation, display
   - Python scripts: Actual transaction building
   - API: Bridge between them

---

## 4.8. Best Practices

### Error Handling

```typescript
try {
  const txHash = await wallet.submitTx(signedTx)
  setSuccess(true)
} catch (error) {
  if (error.message.includes('BadInputs')) {
    setError('UTxO already spent. Please refresh.')
  } else if (error.message.includes('FeeTooSmall')) {
    setError('Insufficient ADA for transaction fee.')
  } else {
    setError('Transaction failed: ' + error.message)
  }
}
```

### Loading States

```typescript
const [loading, setLoading] = useState(false)

const handleSubmit = async () => {
  setLoading(true)
  try {
    await submitTransaction()
  } finally {
    setLoading(false)
  }
}

return (
  <button disabled={loading}>
    {loading ? 'Processing...' : 'Submit'}
  </button>
)
```

### Type Safety

```typescript
// Define types
interface NFTMetadata {
  image_url: string
  description: string
}

interface NFT {
  name: string
  policyId: string
  metadata: NFTMetadata
}

// Use types
const [nfts, setNfts] = useState<NFT[]>([])
```

---

## 4.9. Styling với Tailwind

### Utility Classes

```jsx
{/* Card */}
<div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">

{/* Button */}
<button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">

{/* Input */}
<input className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500">

{/* Grid */}
<div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
```

### Responsive Design

```jsx
{/* Mobile: stack, Desktop: grid */}
<div className="flex flex-col md:flex-row gap-4">

{/* Mobile: hidden, Desktop: show */}
<div className="hidden md:block">

{/* Mobile: full width, Desktop: max width */}
<div className="w-full md:max-w-2xl mx-auto">
```

### Dark Mode

```jsx
{/* Auto dark mode support */}
<div className="bg-white dark:bg-gray-800">
<p className="text-gray-900 dark:text-gray-100">
```

---

## 4.10. Deployment

### Build for Production

```bash
npm run build
npm run start
```

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Environment Variables

Set in Vercel dashboard:
- `NEXT_PUBLIC_NETWORK`
- `NEXT_PUBLIC_BLOCKFROST_API_KEY`

---

## 4.11. Testing

### Manual Testing Checklist

- [ ] Wallet connects successfully
- [ ] Forms validate inputs
- [ ] Error messages display correctly
- [ ] Success states show transaction hash
- [ ] Explorer links work
- [ ] Responsive on mobile
- [ ] Dark mode works

### E2E Testing (Future)

```typescript
// Playwright or Cypress
describe('Mint NFT', () => {
  it('should mint NFT successfully', async () => {
    await page.goto('/mint')
    await page.fill('[name="name"]', 'TestNFT')
    await page.fill('[name="image"]', 'ipfs://...')
    await page.click('button:has-text("Mint")')
    await expect(page).toContainText('Success')
  })
})
```

---

## 4.12. Common Issues

### Issue 1: "wallet.signTx is not a function"

**Cause:** Wallet not connected

**Solution:** Check `connected` before calling wallet methods

### Issue 2: CORS errors

**Cause:** Backend API on different domain

**Solution:** Configure CORS in backend or use Next.js API routes

### Issue 3: Transaction fails silently

**Cause:** Missing error handling

**Solution:** Wrap in try/catch and log errors

---

**Next:** [Module 5: Testing & Deployment](./05-testing-deployment.md)
