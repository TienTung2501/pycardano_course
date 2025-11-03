import type { AppProps } from 'next/app'
import { MeshProvider } from '@meshsdk/react'
import '../styles/globals.css'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <MeshProvider>
      <Component {...pageProps} />
    </MeshProvider>
  )
}
