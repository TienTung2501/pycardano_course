import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '../utils/api';
import { enableWallet } from '../utils/wallet';

export default function NFTsPage() {
  const [addr, setAddr] = useState<string>('');
  const [items, setItems] = useState<any[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function connect() {
    setMsg(null);
    try {
      const w = await enableWallet();
      const used = await w.getUsedAddresses();
      if (!used.length) throw new Error('Wallet has no used addresses');
      setAddr(used[0]);
    } catch (e: any) {
      setMsg(e.message);
    }
  }

  async function reload() {
    if (!addr) return;
    setLoading(true);
    try {
      const res = await api<{ address: string; items: any[] }>(`/nfts?address=${addr}`);
      setItems(res.items || []);
    } catch (e: any) {
      setMsg(e.message);
    } finally { setLoading(false); }
  }

  useEffect(() => { if (addr) reload(); }, [addr]);

  async function doBurn(user_tx_hash?: string, user_index?: number) {
    setMsg(null); setLoading(true);
    try {
      // Prepare burn
      const prep = await api<{ unsigned_tx_cbor: string; details: any }>(
        '/burn/prepare', { method: 'POST', body: JSON.stringify({ user_address: addr }) }
      );
      const w = await enableWallet();
      const userWitness = await w.signTx(prep.unsigned_tx_cbor, true);
      const fin = await api<{ tx_id: string }>('/tx/finalize', { method: 'POST', body: JSON.stringify({ tx_cbor: prep.unsigned_tx_cbor, user_witness_cbor: userWitness }) });
      setMsg(`Burned. tx=${fin.tx_id}`);
      reload();
    } catch (e: any) {
      setMsg(e.message);
    } finally { setLoading(false); }
  }

  async function doUpdate(store_tx_hash?: string, store_index?: number) {
    const name = prompt('New name', 'Updated');
    if (!name) return;
    const description = prompt('Description', 'Updated by UI') || '';
    setMsg(null); setLoading(true);
    try {
      const r = await api<{ tx_id: string }>('/update', { method: 'POST', body: JSON.stringify({ metadata: { name, description, version: 2 } }) });
      setMsg(`Updated. tx=${r.tx_id}`);
      reload();
    } catch (e: any) { setMsg(e.message); } finally { setLoading(false); }
  }

  async function doRemove(store_tx_hash?: string, store_index?: number) {
    setMsg(null); setLoading(true);
    try {
      const r = await api<{ tx_id: string }>('/remove', { method: 'POST', body: JSON.stringify({}) });
      setMsg(`Removed. tx=${r.tx_id}`);
      reload();
    } catch (e: any) { setMsg(e.message); } finally { setLoading(false); }
  }

  return (
    <div style={{ maxWidth: 900, margin: '2rem auto', fontFamily: 'system-ui, Arial' }}>
      <h1>My CIP-68 NFTs</h1>
      <nav style={{ marginBottom: 16 }}>
        <Link href="/">Home</Link> | <Link href="/mint">Mint</Link>
      </nav>

      {!addr ? (
        <button onClick={connect}>Connect Wallet</button>
      ) : (
        <div><b>Wallet:</b> {addr} <button onClick={reload} disabled={loading}>Reload</button></div>
      )}

      {items.length === 0 ? <p style={{ opacity: 0.7 }}>No items</p> : (
        <div style={{ display: 'grid', gap: 12, marginTop: 16 }}>
          {items.map((it, idx) => (
            <div key={idx} style={{ border: '1px solid #ddd', padding: 12 }}>
              <div><b>Suffix:</b> {it.suffix_hex}</div>
              <div><b>User token:</b> {it.user_token_hex}</div>
              <div><b>Ref token:</b> {it.reference_token_hex}</div>
              {it.datum ? <pre style={{ background: '#fafafa', padding: 8 }}>{JSON.stringify(it.datum, null, 2)}</pre> : null}
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={() => doUpdate(it.store_utxo?.tx_hash, it.store_utxo?.index)} disabled={!it.store_utxo}>Update</button>
                <button onClick={() => doRemove(it.store_utxo?.tx_hash, it.store_utxo?.index)} disabled={!it.store_utxo}>Remove</button>
                <button onClick={() => doBurn(it.user_utxo?.tx_hash, it.user_utxo?.index)} disabled={!it.user_utxo}>Burn</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {msg && <pre style={{ background: '#f5f5f5', padding: 12, marginTop: 16 }}>{msg}</pre>}
    </div>
  );
}
