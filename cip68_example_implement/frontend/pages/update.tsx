import { useState } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { useWallet } from '@meshsdk/react'

export default function UpdatePage() {
  const router = useRouter()
  const { wallet, connected } = useWallet()
  
  const [formData, setFormData] = useState({
    name: (router.query.name as string) || '',
    policyId: (router.query.policy as string) || '',
    newImage: '',
    newDescription: '',
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

  const handleUpdate = async () => {
    if (!connected || !wallet) {
      setError('Please connect your wallet first')
      return
    }

    if (!formData.name || !formData.policyId || !formData.newImage || !formData.newDescription) {
      setError('Please fill in all fields')
      return
    }

    setLoading(true)
    setError('')
    setTxHash('')

    try {
      // In production, this would:
      // 1. Find reference token UTxO at script address
      // 2. Find user token UTxO in wallet (prove ownership)
      // 3. Build transaction to spend reference UTxO
      // 4. Create new output with updated datum
      // 5. Include validator script and redeemer
      // 6. Sign and submit
      
      setError('Frontend update implementation in progress. Please use Python script for now.')
      
      // Uncomment when full implementation is ready:
      /*
      const response = await fetch('/api/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          policyId: formData.policyId,
          newImage: formData.newImage,
          newDescription: formData.newDescription,
        }),
      })
      
      if (!response.ok) throw new Error('Update failed')
      
      const data = await response.json()
      setTxHash(data.txHash)
      */
      
    } catch (err: any) {
      setError(err.message || 'Failed to update NFT')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Head>
        <title>Update NFT - CIP-68 Platform</title>
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
            <h1 className="text-3xl font-bold mb-6">✏️ Update NFT Metadata</h1>

            {!connected && (
              <div className="bg-yellow-100 dark:bg-yellow-900 border-l-4 border-yellow-500 p-4 mb-6">
                <p className="text-yellow-700 dark:text-yellow-200">
                  Please connect your wallet to update NFTs
                </p>
              </div>
            )}

            <div className="space-y-4">
              {/* NFT Name */}
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
                  The name of the NFT to update
                </p>
              </div>

              {/* Policy ID */}
              <div>
                <label className="block text-sm font-bold mb-2">Policy ID</label>
                <input
                  type="text"
                  name="policyId"
                  value={formData.policyId}
                  onChange={handleInputChange}
                  placeholder="Policy ID (hex string)"
                  className="input"
                  disabled={!connected}
                />
                <p className="text-xs text-gray-500 mt-1">
                  The policy ID of your NFT
                </p>
              </div>

              {/* New Image URL */}
              <div>
                <label className="block text-sm font-bold mb-2">New Image URL</label>
                <input
                  type="text"
                  name="newImage"
                  value={formData.newImage}
                  onChange={handleInputChange}
                  placeholder="ipfs://QmNewImageHash..."
                  className="input"
                  disabled={!connected}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Updated image URL (IPFS or HTTP)
                </p>
              </div>

              {/* New Description */}
              <div>
                <label className="block text-sm font-bold mb-2">New Description</label>
                <textarea
                  name="newDescription"
                  value={formData.newDescription}
                  onChange={handleInputChange}
                  placeholder="Updated description..."
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
                    ✓ Metadata Updated Successfully!
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

              {/* Update Button */}
              <button
                onClick={handleUpdate}
                disabled={!connected || loading}
                className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Updating...' : 'Update Metadata'}
              </button>

              {/* Info Box */}
              <div className="bg-blue-50 dark:bg-blue-900 border-l-4 border-blue-500 p-4 mt-6">
                <h3 className="font-bold mb-2">ℹ️ How updating works:</h3>
                <ul className="list-disc list-inside text-sm space-y-1 text-gray-700 dark:text-gray-300">
                  <li>You must own the user token (222) to prove ownership</li>
                  <li>Reference token (100) is spent from script address</li>
                  <li>New datum with updated metadata is created</li>
                  <li>Reference token is returned to script with new datum</li>
                  <li>User token is returned to your wallet</li>
                </ul>
              </div>

              {/* Alternative Method */}
              <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded">
                <h3 className="font-bold mb-2">💡 Alternative: Use Python Script</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                  For full functionality, use the command-line tool:
                </p>
                <pre className="bg-black text-green-400 p-3 rounded text-xs overflow-x-auto">
                  python update_nft.py \<br/>
                  {'  '}--name "{formData.name || 'YourName'}" \<br/>
                  {'  '}--policy "{formData.policyId || 'your_policy_id'}" \<br/>
                  {'  '}--image "{formData.newImage || 'ipfs://...'}" \<br/>
                  {'  '}--desc "{formData.newDescription || 'New description'}"
                </pre>
              </div>

              {/* Warning */}
              <div className="bg-yellow-50 dark:bg-yellow-900 border-l-4 border-yellow-500 p-4">
                <p className="text-sm text-yellow-700 dark:text-yellow-200">
                  ⚠️ <strong>Important:</strong> Updating requires spending the reference token
                  from the script. Make sure you have enough ADA for transaction fees and collateral.
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  )
}
