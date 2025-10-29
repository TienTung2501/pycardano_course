import { FormEvent, useEffect, useState } from 'react';
import { api } from '../utils/api';

type AddressesResp = { issuer: string; user: string };

type MintResp = { tx_id: string; token_names: { reference_token: string; user_token: string; policy_id: string } };

type SimpleTxResp = { tx_id: string };

type StoreResp = { store_address: string; utxo_count: number };

export default function Home() {
  const [issuer, setIssuer] = useState('');
  const [user, setUser] = useState('');
  const [store, setStore] = useState<StoreResp | null>(null);
  const [mintName, setMintName] = useState('CIP68_DEMO');
  const [mintDesc, setMintDesc] = useState('Minted via UI');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const a = await api<AddressesResp>('/addresses');
        setIssuer(a.issuer);
        setUser(a.user);
        const s = await api<StoreResp>('/store');
        setStore(s);
      } catch (e: any) {
        setMessage(`Load failed: ${e.message}`);
      }
    })();
  }, []);

  async function onMint(e: FormEvent) {
    e.preventDefault();
    setLoading(true); setMessage(null);
    try {
      const metadata = { name: mintName, description: mintDesc, version: 1 };
      const r = await api<MintResp>('/mint', { method: 'POST', body: JSON.stringify({ metadata }) });
      setMessage(`Minted! tx=${r.tx_id}, policy=${r.token_names.policy_id}, userTN=${r.token_names.user_token}`);
      const s = await api<StoreResp>('/store');
      setStore(s);
    } catch (e: any) {
      setMessage(`Mint failed: ${e.message}`);
    } finally { setLoading(false); }
  }

  async function onUpdate(e: FormEvent) {
    e.preventDefault();
    setLoading(true); setMessage(null);
    try {
      const metadata = { name: mintName + ' (updated)', description: 'Updated via UI', version: 2 };
      const r = await api<SimpleTxResp>('/update', { method: 'POST', body: JSON.stringify({ metadata }) });
      setMessage(`Updated! tx=${r.tx_id}`);
      const s = await api<StoreResp>('/store');
      setStore(s);
    } catch (e: any) {
      setMessage(`Update failed: ${e.message}`);
    } finally { setLoading(false); }
  }

  async function onRemove(e: FormEvent) {
    e.preventDefault();
    setLoading(true); setMessage(null);
    try {
      const r = await api<{ tx_id: string; consumed: number }>('/remove', { method: 'POST', body: JSON.stringify({}) });
      setMessage(`Removed! tx=${r.tx_id}, consumed=${r.consumed}`);
      const s = await api<StoreResp>('/store');
      setStore(s);
    } catch (e: any) {
      setMessage(`Remove failed: ${e.message}`);
    } finally { setLoading(false); }
  }

  async function onBurn(e: FormEvent) {
    e.preventDefault();
    setLoading(true); setMessage(null);
    try {
      const r = await api<SimpleTxResp>('/burn', { method: 'POST', body: JSON.stringify({}) });
      setMessage(`Burned! tx=${r.tx_id}`);
    } catch (e: any) {
      setMessage(`Burn failed: ${e.message}`);
    } finally { setLoading(false); }
  }

  return (
    <div style={{ maxWidth: 900, margin: '2rem auto', fontFamily: 'system-ui, Arial' }}>
      <h1>CIP-68 Dynamic NFT</h1>
      <p><b>Issuer:</b> {issuer || '…'}</p>
      <p><b>User:</b> {user || '…'}</p>
      <p><b>Store:</b> {store ? `${store.store_address} (UTxOs: ${store.utxo_count})` : '…'}</p>

      <hr />

      <form onSubmit={onMint} style={{ marginBottom: '1rem' }}>
        <h2>Mint</h2>
        <div style={{ display: 'flex', gap: 12 }}>
          <input value={mintName} onChange={e => setMintName(e.target.value)} placeholder="name" />
          <input value={mintDesc} onChange={e => setMintDesc(e.target.value)} placeholder="description" style={{ width: 360 }} />
          <button type="submit" disabled={loading}>Mint</button>
        </div>
      </form>

      <form onSubmit={onUpdate} style={{ marginBottom: '1rem' }}>
        <h2>Update metadata</h2>
        <button type="submit" disabled={loading}>Update</button>
      </form>

      <form onSubmit={onRemove} style={{ marginBottom: '1rem' }}>
        <h2>Remove (spend store UTxOs)</h2>
        <button type="submit" disabled={loading}>Remove</button>
      </form>

      <form onSubmit={onBurn}>
        <h2>Burn (user+ref tokens)</h2>
        <button type="submit" disabled={loading}>Burn</button>
      </form>

      {message && (
        <pre style={{ background: '#f5f5f5', padding: 12, marginTop: 16 }}>{message}</pre>
      )}
    </div>
  );
}
