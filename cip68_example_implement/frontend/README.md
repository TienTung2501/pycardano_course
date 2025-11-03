# CIP-68 NFT Frontend

Modern web interface for interacting with CIP-68 NFTs using Next.js and Mesh SDK.

## 🎨 Features

- **Wallet Connection**: Connect Cardano wallets (Nami, Eternl, Flint, etc.)
- **Mint NFTs**: Create new CIP-68 NFT pairs with metadata
- **View Gallery**: Browse and display your NFT collection
- **Update Metadata**: Modify NFT metadata dynamically
- **Responsive Design**: Mobile-friendly UI with Tailwind CSS

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- Cardano wallet extension (Nami, Eternl, or Flint)
- Test ADA from faucet

### Installation

```bash
# Install dependencies
npm install
# or
yarn install

# Run development server
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📁 Project Structure

```
frontend/
├── pages/
│   ├── _app.tsx          # App wrapper with MeshProvider
│   ├── index.tsx         # Home page
│   ├── mint.tsx          # Mint NFT page
│   ├── gallery.tsx       # NFT gallery page
│   └── update.tsx        # Update metadata page
├── styles/
│   └── globals.css       # Global styles + Tailwind
├── public/               # Static assets
├── package.json
├── tsconfig.json
├── next.config.js
└── tailwind.config.js
```

## 🔧 Configuration

### Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_NETWORK=preview
NEXT_PUBLIC_BLOCKFROST_API_KEY=your_api_key
```

### Supported Networks

- `preview` - Preview Testnet (default)
- `preprod` - Pre-production Testnet
- `mainnet` - Mainnet (use with caution)

## 📱 Pages Overview

### Home (`/`)

- Platform introduction
- Wallet connection
- Feature overview
- CIP-68 explanation

### Mint (`/mint`)

- NFT creation form
- Name, image URL, description inputs
- Minting transaction
- Success confirmation

**Note:** Currently shows UI mockup. For full functionality, use Python script:
```bash
python ../off_chain/mint_nft.py --name "YourNFT" --image "ipfs://..." --desc "..."
```

### Gallery (`/gallery`)

- Query NFTs by Policy ID
- Display NFT cards with images
- Show metadata (image, description)
- Ownership indicators
- Quick update/burn actions

### Update (`/update`)

- Update existing NFT metadata
- New image and description
- Transaction confirmation
- Explorer links

## 🎨 Design System

### Colors

```css
Primary: Cardano Blue (#0033AD)
Light: #3468D1
Background: Gradient blue-indigo
Dark Mode: Gray tones
```

### Components

**Buttons:**
- `.btn-primary` - Primary actions
- `.btn-secondary` - Secondary actions

**Cards:**
- `.card` - Content containers with shadow

**Inputs:**
- `.input` - Form inputs with focus states

## 🔌 Wallet Integration

### Supported Wallets

- **Nami** - Most popular Cardano wallet
- **Eternl** - Feature-rich wallet
- **Flint** - Lightweight wallet
- **Typhon** - Multi-platform wallet

### Usage

```typescript
import { useWallet } from '@meshsdk/react'

const { wallet, connected, connect, disconnect } = useWallet()

// Connect
await connect('nami')

// Get address
const address = await wallet.getChangeAddress()

// Sign transaction
const signedTx = await wallet.signTx(unsignedTx)
```

## 🛠️ Development

### Build for Production

```bash
npm run build
npm run start
```

### Linting

```bash
npm run lint
```

### Type Checking

```bash
npx tsc --noEmit
```

## ⚠️ Current Limitations

This frontend is an **educational example** and has some limitations:

### 1. Transaction Building

The Mesh SDK transaction building for CIP-68 is **not fully implemented**. The UI shows forms and flow, but actual blockchain interaction requires:

- Loading parameterized Plutus scripts
- Creating proper CIP-68 datums
- Building complex transactions with script inputs/outputs
- Handling collateral and execution units

**Recommended:** Use Python scripts for actual transactions:

```bash
# Mint
python ../off_chain/mint_nft.py --name "Dragon" --image "ipfs://..." --desc "..."

# Update
python ../off_chain/update_nft.py --name "Dragon" --policy "abc123..." --image "..." --desc "..."

# Query
python ../off_chain/query_nft.py --policy "abc123..."

# Burn
python ../off_chain/burn_nft.py --name "Dragon" --policy "abc123..."
```

### 2. Backend API

The gallery and query features require a backend API to:
- Run Python query scripts
- Decode on-chain data
- Format responses

**Future Enhancement:** Build Express.js or Next.js API routes that call Python scripts.

### 3. IPFS Integration

Image uploads to IPFS are not implemented. Users must:
- Upload images to Pinata, NFT.Storage, or similar
- Get IPFS hash manually
- Paste into form

## 🔮 Future Enhancements

### Phase 1: Backend Integration
```typescript
// API route: /api/mint
export default async function handler(req, res) {
  const { name, image, description } = req.body
  
  // Execute Python script
  const result = await execSync(
    `python ../off_chain/mint_nft.py --name "${name}" ...`
  )
  
  return res.json({ txHash: result })
}
```

### Phase 2: Full Mesh Implementation

Implement proper CIP-68 transactions in TypeScript:
```typescript
// Load validator script
const validator = await loadPlutusScript('update_metadata')

// Apply parameters
const parameterized = applyParams(validator, [policyId])

// Build datum
const datum = Data.to({
  constructor: 0,
  fields: [
    fromText(imageUrl),
    fromText(description)
  ]
})

// Build transaction
const tx = new Transaction({ initiator: wallet })
  .sendAssets(
    scriptAddress,
    [{ unit: refToken, quantity: '1' }],
    { inline: datum }
  )
  .sendAssets(
    userAddress,
    [{ unit: userToken, quantity: '1' }]
  )
```

### Phase 3: Enhanced Features

- **Image Upload**: Direct IPFS upload via Pinata API
- **Metadata Validation**: JSON schema validation
- **Transaction History**: Show past mints/updates
- **Batch Operations**: Mint/update multiple NFTs
- **Advanced Filtering**: Search by attributes
- **Analytics Dashboard**: Collection statistics

## 📚 Learning Resources

### Mesh SDK
- [Official Docs](https://meshjs.dev/)
- [Transaction Building](https://meshjs.dev/apis/transaction)
- [Wallet Integration](https://meshjs.dev/apis/wallets)

### Next.js
- [Getting Started](https://nextjs.org/docs)
- [API Routes](https://nextjs.org/docs/api-routes/introduction)
- [Deployment](https://nextjs.org/docs/deployment)

### Tailwind CSS
- [Documentation](https://tailwindcss.com/docs)
- [Components](https://tailwindui.com/)

## 🐛 Troubleshooting

### "Cannot find module '@meshsdk/react'"

**Solution:** Install dependencies
```bash
npm install
```

### Wallet not connecting

**Causes:**
- Wallet extension not installed
- Wrong network selected in wallet
- Browser compatibility issues

**Solution:**
- Install wallet extension (Nami, Eternl, etc.)
- Switch wallet to Preview testnet
- Try different browser (Chrome, Brave)

### "Failed to fetch NFTs"

**Cause:** Backend API not implemented

**Solution:** Use Python script directly:
```bash
python ../off_chain/query_nft.py --policy "your_policy_id"
```

## 🤝 Contributing

Educational project - contributions welcome!

**Areas:**
- Complete transaction building with Mesh SDK
- Add backend API routes
- Implement IPFS upload
- Improve error handling
- Add loading states and animations
- Create reusable components

## 📄 License

MIT - Educational Example

---

**Note:** This frontend demonstrates CIP-68 concepts with a modern UI. For production use:
1. Complete transaction implementation
2. Add comprehensive error handling
3. Implement security best practices
4. Add automated tests
5. Use production-grade IPFS service
