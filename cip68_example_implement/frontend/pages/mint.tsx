import { useState } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import { useWallet } from '@meshsdk/react'
import { Transaction, ForgeScript, AssetMetadata } from '@meshsdk/core'

export default function MintPage() {
  const { wallet, connected } = useWallet()
  
  const [formData, setFormData] = useState({
    name: '',
    image: '',
    description: '',
  })
  const [loading, setLoading] = useState(false)
  const [txHash, setTxHash] = useState('')
  const [error, setError] = useState('')

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleMint = async () => {
    if (!connected || !wallet) {
      setError('Please connect your wallet first')
      return
    }

    if (!formData.name || !formData.image || !formData.description) {
      setError('Please fill in all fields')
      return
    }

    setLoading(true)
    setError('')
    setTxHash('')

    try {
      // Get wallet address
      const address = await wallet.getChangeAddress()
      
      // Create asset metadata (CIP-68 format)
      const metadata: AssetMetadata = {
        name: formData.name,
        image: formData.image,
        description: formData.description,
      }

      // Build minting transaction
      // Note: This is simplified. In production, you'd need to:
      // 1. Load the parameterized validator script
      // 2. Create proper datum with image_url and description
      // 3. Send reference token (100) to script address
      // 4. Send user token (222) to user wallet
      
      const tx = new Transaction({ initiator: wallet })
      
      // For educational purposes, showing the concept
      // Real implementation would use the validator address and proper asset names
      
      const forgingScript: ForgeScript = {
        type: 'all',
        scripts: [
          {
            type: 'sig',
            keyHash: 'your_policy_key_hash', // Would come from policy keys
          },
        ],
      }

      // This is a simplified example
      // Production code should follow the PPBL approach from Python scripts
      
      setError('Frontend minting implementation in progress. Please use Python scripts for now.')
      
      // Uncomment when full implementation is ready:
      /*
      const unsignedTx = await tx
        .mintAsset(forgingScript, {
          assetName: '100' + formData.name,
          assetQuantity: '1',
        })
        .mintAsset(forgingScript, {
          assetName: '222' + formData.name,
          assetQuantity: '1',
        })
        .setMetadata(721, {
          [policyId]: {
            [formData.name]: metadata,
          },
        })
        .build()

      const signedTx = await wallet.signTx(unsignedTx)
      const txHashResult = await wallet.submitTx(signedTx)
      
      setTxHash(txHashResult)
      */
      
    } catch (err: any) {
      setError(err.message || 'Failed to mint NFT')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Head>
        <title>Mint NFT - CIP-68 Platform</title>
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        <header className="bg-white dark:bg-gray-800 shadow-md">
          <div className="container mx-auto px-4 py-4">
            <Link href="/" className="text-2xl font-bold text-cardano-blue dark:text-white">
              ← Back to Home
            </Link>
          </div>
        </header>

        <main className="container mx-auto px-4 py-8 max-w-2xl">
          <div className="card">
            <h1 className="text-3xl font-bold mb-6">🎨 Mint CIP-68 NFT</h1>

            {!connected && (
              <div className="bg-yellow-100 dark:bg-yellow-900 border-l-4 border-yellow-500 p-4 mb-6">
                <p className="text-yellow-700 dark:text-yellow-200">
                  Please connect your wallet to mint NFTs
                </p>
              </div>
            )}

            <div className="space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-bold mb-2">NFT Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="e.g., Dragon001"
                  className="input"
                  disabled={!connected}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Unique identifier for your NFT
                </p>
              </div>

              {/* Image URL */}
              <div>
                <label className="block text-sm font-bold mb-2">Image URL</label>
                <input
                  type="text"
                  name="image"
                  value={formData.image}
                  onChange={handleInputChange}
                  placeholder="ipfs://QmYourImageHash..."
                  className="input"
                  disabled={!connected}
                />
                <p className="text-xs text-gray-500 mt-1">
                  IPFS or HTTP URL to your NFT image
                </p>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-bold mb-2">Description</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="Describe your NFT..."
                  rows={4}
                  className="input"
                  disabled={!connected}
                />
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-red-100 dark:bg-red-900 border-l-4 border-red-500 p-4">
                  <p className="text-red-700 dark:text-red-200">{error}</p>
                </div>
              )}

              {/* Success Message */}
              {txHash && (
                <div className="bg-green-100 dark:bg-green-900 border-l-4 border-green-500 p-4">
                  <p className="text-green-700 dark:text-green-200 font-bold mb-2">
                    ✓ NFT Minted Successfully!
                  </p>
                  <p className="text-sm">Transaction: {txHash}</p>
                  <a
                    href={`https://preview.cardanoscan.io/transaction/${txHash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-green-600 hover:text-green-700 text-sm"
                  >
                    View on Explorer →
                  </a>
                </div>
              )}

              {/* Mint Button */}
              <button
                onClick={handleMint}
                disabled={!connected || loading}
                className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Minting...' : 'Mint NFT'}
              </button>

              {/* Info Box */}
              <div className="bg-blue-50 dark:bg-blue-900 border-l-4 border-blue-500 p-4 mt-6">
                <h3 className="font-bold mb-2">ℹ️ What happens when you mint:</h3>
                <ul className="list-disc list-inside text-sm space-y-1 text-gray-700 dark:text-gray-300">
                  <li>Reference token (100{formData.name || 'YourName'}) sent to script with metadata</li>
                  <li>User token (222{formData.name || 'YourName'}) sent to your wallet</li>
                  <li>Metadata stored on-chain in datum</li>
                  <li>~5 ADA locked (3 ADA at script, 2 ADA with user token)</li>
                </ul>
              </div>

              {/* Alternative Method */}
              <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded">
                <h3 className="font-bold mb-2">💡 Alternative: Use Python Script</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                  For full functionality, use the command-line tool:
                </p>
                <pre className="bg-black text-green-400 p-3 rounded text-xs overflow-x-auto">
                  python mint_nft.py \<br/>
                  {'  '}--name "{formData.name || 'YourName'}" \<br/>
                  {'  '}--image "{formData.image || 'ipfs://...'}" \<br/>
                  {'  '}--desc "{formData.description || 'Your description'}"
                </pre>
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  )
}
