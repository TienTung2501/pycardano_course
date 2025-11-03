"""
wallet/generate_mnemonic.py

run script:py -m wallet.generate_mnemonic
Sinh một mnemonic mới (24 từ) bằng PyCardano và tự động ghi vào file .env
Dành cho môi trường học tập hoặc testnet.
"""

import os
from wallet.wallet_manager import WalletManager

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


def main():
    mnemonic = WalletManager.generate_new_mnemonic()

    print("\n✅ Mnemonic 24 từ mới (HÃY GIỮ BÍ MẬT):\n")
    print(mnemonic)
    print("\n⚠️ KHÔNG dùng mnemonic này cho ví thật hoặc mainnet.\n")

    # Ghi vào file .env
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = []

    updated = False
    for i, line in enumerate(lines):
        if line.startswith("MNEMONIC1="):
            lines[i] = f"MNEMONIC1={mnemonic}\n"
            updated = True
            break

    if not updated:
        lines.append(f"MNEMONIC1={mnemonic}\n")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"✅ Đã ghi mnemonic mới vào file {ENV_PATH}\n")


if __name__ == "__main__":
    main()
