from pycardano.backend.blockfrost import BlockFrostChainContext, ApiUrls
from pycardano.network import Network
from ..common.config import BLOCKFROST_PROJECT_ID

def mk_context() -> BlockFrostChainContext:
    # Preprod
    return BlockFrostChainContext(
        project_id=BLOCKFROST_PROJECT_ID,
        base_url=ApiUrls.preview.value,
    )

def network() -> Network:
    return Network.TESTNET