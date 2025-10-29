import { FormEvent, useEffect, useState } from 'react';
import { api, BACKEND_URL } from '../utils/api';
import Link from 'next/link';

// Minimal CIP-30 helpers
function getWallet() {
  // try Nami/Eternl/Flint
  const w: any = (globalThis as any).cardano;
  return w?.nami || w?.eternl || w?.flint || null;
}

async function connectWallet() {
  const w = getWallet();
  if (!w) throw new Error('No CIP-30 wallet found (Nami/Eternl/Flint).');
  const api = await w.enable();
  return api;
}

export default function MintPage() {
  const [connected, setConnected] = useState(false);
  const [addr, setAddr] = useState<string>('');
  const [name, setName] = useState('CIP68_DEMO');
  const [description, setDescription] = useState('Minted from UI');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    // noop
  }, []);

  async function onConnect() {
    setMsg(null);
    try {
      const wapi = await connectWallet();
      const addrs: string[] = await wapi.getUsedAddresses();
      if (!addrs || addrs.length === 0) throw new Error('No used addresses from wallet');
      // bech32
      setAddr(addrs[0]);
      setConnected(true);
    } catch (e: any) {
      setMsg(e.message);
    }
  }

  async function onMint(e: FormEvent) {
    e.preventDefault();
    setLoading(true); setMsg(null);
    try {
      if (!connected || !addr) throw new Error('Connect wallet first');
      const metadata = { name, description, version: 1 };

      // 1) Build unsigned tx (with scripts/redeemers)
      const built = await api<{ unsigned_tx_cbor: string; details: { policy_id: string; user_token: string; reference_token: string } }>(
        '/mint/prepare', { method: 'POST', body: JSON.stringify({ user_address: addr, metadata }) }
      );

      const wapi = await connectWallet();
      // 2) Sign with wallet (user witness only)
  const userWitnessCbor: string = await wapi.signTx(built.unsigned_tx_cbor, true);

      // 3) Send witness back to backend for issuer sign + submit
      const finalized = await api<{ tx_id: string }>(
        '/tx/finalize', { method: 'POST', body: JSON.stringify({ tx_cbor: built.unsigned_tx_cbor, user_witness_cbor: userWitnessCbor }) }
      );

      setMsg(`Minted! tx=${finalized.tx_id}, policy=${built.details.policy_id}, userTN=${built.details.user_token}`);
    } catch (e: any) {
      setMsg(`Mint failed: ${e.message}`);
    } finally { setLoading(false); }
  }

  return (
    <div style={{ maxWidth: 900, margin: '2rem auto', fontFamily: 'system-ui, Arial' }}>
      <h1>Mint CIP-68 NFT</h1>
      <nav style={{ marginBottom: 16 }}>
        <Link href="/">Home</Link> | <Link href="/nfts">My NFTs</Link>
      </nav>

      {!connected ? (
        <button onClick={onConnect}>Connect Wallet</button>
      ) : (
        <p><b>Wallet:</b> {addr}</p>
      )}

      <form onSubmit={onMint} style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <input placeholder="name" value={name} onChange={e => setName(e.target.value)} />
          <input placeholder="description" value={description} onChange={e => setDescription(e.target.value)} style={{ width: 360 }} />
          <button type="submit" disabled={!connected || loading}>Mint</button>
        </div>
      </form>

      {msg && <pre style={{ background: '#f5f5f5', padding: 12, marginTop: 16 }}>{msg}</pre>}
    </div>
  );
}
