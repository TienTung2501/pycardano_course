import { useState } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import { useWallet } from '@meshsdk/react'

export default function Home() {
  const { wallet, connected, connect, disconnect } = useWallet()
  const [walletAddress, setWalletAddress] = useState<string>('')

  const handleConnect = async () => {
    try {
      await connect('nami') // or 'eternl', 'flint', etc.
      if (wallet) {
        const address = await wallet.getChangeAddress()
        setWalletAddress(address)
      }
    } catch (error) {
      console.error('Failed to connect wallet:', error)
    }
  }

  const handleDisconnect = () => {
    disconnect()
    setWalletAddress('')
  }

  return (
    <>
      <Head>
        <title>CIP-68 NFT Platform</title>
        <meta name="description" content="CIP-68 Dynamic NFT Platform - Educational Example" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-md">
          <div className="container mx-auto px-4 py-4">
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold text-cardano-blue dark:text-white">
                🎨 CIP-68 NFT Platform
              </h1>
              
              <div className="flex items-center gap-4">
                {connected ? (
                  <>
                    <span className="text-sm text-gray-600 dark:text-gray-300">
                      {walletAddress.slice(0, 15)}...
                    </span>
                    <button onClick={handleDisconnect} className="btn-secondary">
                      Disconnect
                    </button>
                  </>
                ) : (
                  <button onClick={handleConnect} className="btn-primary">
                    Connect Wallet
                  </button>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-4 py-8">
          {/* Hero Section */}
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4 text-gray-800 dark:text-white">
              Dynamic NFTs on Cardano
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
              Create, update, and manage CIP-68 NFTs with updatable metadata
            </p>
            
            {!connected && (
              <div className="bg-yellow-100 dark:bg-yellow-900 border-l-4 border-yellow-500 p-4 mb-8 max-w-2xl mx-auto">
                <p className="text-yellow-700 dark:text-yellow-200">
                  ⚠️ Please connect your wallet to interact with the platform
                </p>
              </div>
            )}
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <div className="card">
              <div className="text-4xl mb-4">🎨</div>
              <h3 className="text-xl font-bold mb-2">Mint NFTs</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Create new CIP-68 NFT pairs with reference and user tokens
              </p>
              <Link href="/mint" className="text-blue-600 hover:text-blue-700 font-semibold">
                Go to Mint →
              </Link>
            </div>

            <div className="card">
              <div className="text-4xl mb-4">📝</div>
              <h3 className="text-xl font-bold mb-2">View NFTs</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Browse your NFT collection and view metadata
              </p>
              <Link href="/gallery" className="text-blue-600 hover:text-blue-700 font-semibold">
                View Gallery →
              </Link>
            </div>

            <div className="card">
              <div className="text-4xl mb-4">✏️</div>
              <h3 className="text-xl font-bold mb-2">Update Metadata</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Update NFT metadata dynamically (CIP-68 feature)
              </p>
              <Link href="/update" className="text-blue-600 hover:text-blue-700 font-semibold">
                Update NFT →
              </Link>
            </div>
          </div>

          {/* How It Works */}
          <div className="card max-w-4xl mx-auto">
            <h3 className="text-2xl font-bold mb-4">📚 How CIP-68 Works</h3>
            
            <div className="space-y-4">
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                  1
                </div>
                <div>
                  <h4 className="font-bold mb-1">Reference Token (100)</h4>
                  <p className="text-gray-600 dark:text-gray-400">
                    Locked at script address with inline datum containing metadata
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                  2
                </div>
                <div>
                  <h4 className="font-bold mb-1">User Token (222)</h4>
                  <p className="text-gray-600 dark:text-gray-400">
                    Sent to your wallet - proves ownership and enables updates
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                  3
                </div>
                <div>
                  <h4 className="font-bold mb-1">Update Mechanism</h4>
                  <p className="text-gray-600 dark:text-gray-400">
                    Include user token to prove ownership → spend reference token → create new output with updated datum
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Educational Note */}
          <div className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
            <p>Educational project demonstrating CIP-68 implementation</p>
            <p className="mt-2">
              <a 
                href="https://cips.cardano.org/cips/cip68/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700"
              >
                Learn more about CIP-68 →
              </a>
            </p>
          </div>
        </main>

        {/* Footer */}
        <footer className="bg-white dark:bg-gray-800 mt-12 py-6">
          <div className="container mx-auto px-4 text-center text-gray-600 dark:text-gray-400">
            <p>Built with Next.js, Mesh SDK, and PyCardano</p>
            <p className="mt-2 text-sm">Network: Preview Testnet</p>
          </div>
        </footer>
      </div>
    </>
  )
}
