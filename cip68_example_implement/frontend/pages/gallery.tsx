import { useState, useEffect } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import { useWallet } from '@meshsdk/react'
import Image from 'next/image'

interface NFTData {
  name: string
  policyId: string
  refTokenName: string
  userTokenName: string
  metadata: {
    image_url: string
    description: string
  }
  owned: boolean
}

export default function GalleryPage() {
  const { wallet, connected } = useWallet()
  const [nfts, setNfts] = useState<NFTData[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [policyId, setPolicyId] = useState('')

  const fetchNFTs = async () => {
    if (!policyId) {
      setError('Please enter a Policy ID')
      return
    }

    setLoading(true)
    setError('')

    try {
      // In production, this would call a backend API
      // that runs the query_nft.py script
      
      const response = await fetch(`/api/nfts?policy=${policyId}`)
      if (!response.ok) throw new Error('Failed to fetch NFTs')
      
      const data = await response.json()
      setNfts(data.nfts || [])
      
      if (data.nfts.length === 0) {
        setError('No NFTs found for this Policy ID')
      }
    } catch (err: any) {
      setError('API endpoint not implemented. Use Python script: python query_nft.py --policy YOUR_POLICY_ID')
      // Mock data for demonstration
      setNfts([
        {
          name: 'Dragon001',
          policyId: policyId,
          refTokenName: '100Dragon001',
          userTokenName: '222Dragon001',
          metadata: {
            image_url: 'ipfs://QmExample123',
            description: 'A legendary fire dragon'
          },
          owned: true,
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const convertIpfsUrl = (url: string): string => {
    if (url.startsWith('ipfs://')) {
      return `https://ipfs.io/ipfs/${url.replace('ipfs://', '')}`
    }
    return url
  }

  return (
    <>
      <Head>
        <title>NFT Gallery - CIP-68 Platform</title>
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        <header className="bg-white dark:bg-gray-800 shadow-md">
          <div className="container mx-auto px-4 py-4">
            <Link href="/" className="text-2xl font-bold text-cardano-blue dark:text-white">
              ← Back to Home
            </Link>
          </div>
        </header>

        <main className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto mb-8">
            <h1 className="text-3xl font-bold mb-6">📝 NFT Gallery</h1>

            {/* Query Form */}
            <div className="card mb-6">
              <label className="block text-sm font-bold mb-2">Policy ID</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={policyId}
                  onChange={(e) => setPolicyId(e.target.value)}
                  placeholder="Enter Policy ID to view NFTs..."
                  className="input flex-1"
                />
                <button
                  onClick={fetchNFTs}
                  disabled={loading}
                  className="btn-primary disabled:opacity-50"
                >
                  {loading ? 'Loading...' : 'Query'}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Enter the Policy ID from your minted NFTs
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-yellow-100 dark:bg-yellow-900 border-l-4 border-yellow-500 p-4 mb-6">
                <p className="text-yellow-700 dark:text-yellow-200">{error}</p>
              </div>
            )}
          </div>

          {/* NFT Grid */}
          {nfts.length > 0 && (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {nfts.map((nft, index) => (
                <div key={index} className="card hover:shadow-lg transition-shadow">
                  {/* NFT Image */}
                  <div className="relative h-48 bg-gray-200 dark:bg-gray-700 rounded-lg mb-4 overflow-hidden">
                    {nft.metadata.image_url.startsWith('ipfs://') || 
                     nft.metadata.image_url.startsWith('http') ? (
                      <img
                        src={convertIpfsUrl(nft.metadata.image_url)}
                        alt={nft.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full text-gray-400">
                        🖼️ No Image
                      </div>
                    )}
                  </div>

                  {/* NFT Info */}
                  <h3 className="text-xl font-bold mb-2">{nft.name}</h3>
                  
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    {nft.metadata.description}
                  </p>

                  {/* Ownership Badge */}
                  {nft.owned && (
                    <div className="inline-block bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-200 text-xs px-2 py-1 rounded mb-3">
                      ✓ You own this NFT
                    </div>
                  )}

                  {/* Token Info */}
                  <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1 mb-4">
                    <div className="truncate">
                      <span className="font-semibold">Policy:</span> {nft.policyId.slice(0, 20)}...
                    </div>
                    <div>
                      <span className="font-semibold">Reference:</span> {nft.refTokenName}
                    </div>
                    <div>
                      <span className="font-semibold">User:</span> {nft.userTokenName}
                    </div>
                  </div>

                  {/* Actions */}
                  {nft.owned && (
                    <div className="flex gap-2">
                      <Link
                        href={`/update?policy=${nft.policyId}&name=${nft.name}`}
                        className="btn-primary text-sm py-1 px-3 flex-1 text-center"
                      >
                        Update
                      </Link>
                      <button className="btn-secondary text-sm py-1 px-3">
                        Burn
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!loading && nfts.length === 0 && !error && (
            <div className="text-center text-gray-500 dark:text-gray-400 py-12">
              <div className="text-6xl mb-4">🔍</div>
              <p className="text-xl mb-2">No NFTs to display</p>
              <p className="text-sm">Enter a Policy ID to view NFTs</p>
            </div>
          )}

          {/* Alternative Method */}
          {policyId && (
            <div className="max-w-4xl mx-auto mt-8">
              <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded">
                <h3 className="font-bold mb-2">💡 Alternative: Use Python Script</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                  Query NFTs using the command-line tool:
                </p>
                <pre className="bg-black text-green-400 p-3 rounded text-xs overflow-x-auto">
                  python query_nft.py --policy {policyId}
                  {connected && '\n  --owner YOUR_WALLET_ADDRESS'}
                </pre>
              </div>
            </div>
          )}
        </main>
      </div>
    </>
  )
}
