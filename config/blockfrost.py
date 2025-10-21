# config/blockfrost.py

from pycardano import BlockFrostChainContext, Network
from blockfrost import ApiUrls
from config.settings import BLOCKFROST_PROJECT_ID, NETWORK

_context_cache = None


def get_blockfrost_context() -> BlockFrostChainContext:
    """
    Trả về BlockFrostChainContext tương ứng với network hiện tại.
    Dùng cache để tránh khởi tạo lại nhiều lần.
    """
    global _context_cache
    if _context_cache:
        return _context_cache

    if NETWORK == "PREVIEW":
        base_url = ApiUrls.preview.value
        network_enum = Network.TESTNET
    elif NETWORK == "PREPROD":
        base_url = ApiUrls.preprod.value
        network_enum = Network.TESTNET
    elif NETWORK == "MAINNET":
        base_url = ApiUrls.mainnet.value
        network_enum = Network.MAINNET
    else:
        raise ValueError("❌ Network không hợp lệ trong config/settings.py")

    project_id = BLOCKFROST_PROJECT_ID
    context = BlockFrostChainContext(project_id=project_id, base_url=base_url)
    _context_cache = context

    print(f"🔗 Đã khởi tạo Blockfrost context cho {NETWORK} thành công.")
    return context


def get_network_enum() -> Network:
    """
    Trả về enum Network của PyCardano tương ứng với network hiện tại.
    """
    if NETWORK == "MAINNET":
        return Network.MAINNET
    return Network.TESTNET
