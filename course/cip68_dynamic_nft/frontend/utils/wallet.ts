export type CIP30 = {
  enable: () => Promise<any>;
  isEnabled: () => Promise<boolean>;
  getNetworkId: () => Promise<number>;
  getChangeAddress: () => Promise<string>;
  getUsedAddresses: () => Promise<string[]>;
  getUtxos: () => Promise<string[]>;
  signTx: (tx: string, partialSign?: boolean) => Promise<string>;
};

export function getWallet(): any | null {
  const anyWin = typeof window !== 'undefined' ? (window as any) : undefined;
  if (!anyWin || !anyWin.cardano) return null;
  return anyWin.cardano.nami || anyWin.cardano.eternl || anyWin.cardano.flint || anyWin.cardano.gerowallet || null;
}

export async function enableWallet(): Promise<CIP30> {
  const w = getWallet();
  if (!w) throw new Error('No CIP-30 wallet found (Nami/Eternl/Flint/Gero)');
  return await w.enable();
}
