# config/settings.py
# Nhiệm vụ: đọc file .env, cấu hình môi trường, và định nghĩa các biến toàn cục.

import os
from dotenv import load_dotenv
from pycardano import Network

# Nạp biến môi trường từ file .env
load_dotenv()

# Lấy các thông tin cấu hình từ .env
BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID")
BLOCKFROST_NETWORK = os.getenv("BLOCKFROST_NETWORK", "TESTNET").upper()
MNEMONIC = os.getenv("MNEMONIC")
IPFS_API = os.getenv("IPFS_API", "https://ipfs.infura.io:5001")
AI_MODEL_PATH = os.getenv("AI_MODEL_PATH", "models/face_model.pt")

# Xác định mạng lưới (mainnet hoặc testnet)
NETWORK = BLOCKFROST_NETWORK

# Kiểm tra cấu hình
if not BLOCKFROST_PROJECT_ID:
    raise ValueError("❌ Thiếu BLOCKFROST_PROJECT_ID trong file .env")

print(f"✅ Đã load cấu hình: {BLOCKFROST_NETWORK} / Blockfrost Project ID: {BLOCKFROST_PROJECT_ID[:5]}****")
