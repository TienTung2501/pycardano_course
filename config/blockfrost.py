# config/blockfrost.py
# Tạo và tái sử dụng kết nối BlockFrostChainContext (giảm thời gian khởi tạo)

from pycardano import BlockFrostChainContext
from config.settings import BLOCKFROST_PROJECT_ID, NETWORK

# Cache context để không phải khởi tạo lại mỗi lần gọi
_context_cache = None

def get_blockfrost_context() -> BlockFrostChainContext:
    """
    Trả về BlockFrostChainContext đã được khởi tạo (singleton pattern).
    """
    global _context_cache
    if _context_cache:
        return _context_cache

    context = BlockFrostChainContext(
        project_id=BLOCKFROST_PROJECT_ID,
        network=NETWORK
    )

    _context_cache = context
    print(f"🔗 Đã khởi tạo Blockfrost context ({NETWORK.name}) thành công.")
    return context
