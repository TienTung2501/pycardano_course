import ipfshttpclient
from config.settings import IPFS_API

def upload_to_ipfs(file_path):
    with ipfshttpclient.connect(IPFS_API) as client:
        res = client.add(file_path)
        cid = res["Hash"]
        print(f"📦 Uploaded to IPFS: {cid}")
        return cid
