#!/usr/bin/env python3
"""
Query CIP-68 NFT Metadata

Retrieves and decodes full metadata from blockchain including:
- Name, Image, Description
- Attributes (trait/value pairs)  
- Media Type, Files

Usage:
    python query_nft.py --policy-id <POLICY_ID> --name <TOKEN_NAME>
    
Example:
    python query_nft.py --policy-id 1f32f479... --name DragonNFT
"""
import argparse
from pycardano import plutus_script_hash, Address

import config
from utils.helpers import (
    load_plutus_script,
    apply_params_to_script,
    hex_to_string,
)


def main():
    parser = argparse.ArgumentParser(description="Query CIP-68 NFT")
    parser.add_argument("--policy-id", required=True, help="Policy ID (hex)")
    parser.add_argument("--name", required=True, help="Token name (e.g., 'TestNFT001')")
    args = parser.parse_args()
    
    print("=" * 70)
    print("CIP-68 NFT Query")
    print("=" * 70)
    
    # Get blockchain context
    print("\n[1] Connecting to blockchain...")
    from pycardano import BlockFrostChainContext
    context = BlockFrostChainContext(
        project_id=config.BLOCKFROST_PROJECT_ID,
        base_url=config.BLOCKFROST_URL,
    )
    print(f"    Network: {config.NETWORK_NAME}")
    
    # Get script address
    print("\n[2] Getting script address...")
    print(f"    Policy ID: {args.policy_id}")
    
    # Apply policy ID to validator
    parameterized_validator = apply_params_to_script(
        config.UPDATE_VALIDATOR_TITLE,
        args.policy_id
    )
    
    script_hash = plutus_script_hash(parameterized_validator)
    script_addr = Address(script_hash, network=config.NETWORK)
    print(f"    Script address: {script_addr}")
    
    # Build token names
    from utils.helpers import build_token_name
    ref_token_name_bytes = build_token_name(config.LABEL_100, args.name)
    user_token_name_bytes = build_token_name(config.LABEL_222, args.name)
    
    print(f"\n[3] Looking for tokens:")
    print(f"    Reference (100): {ref_token_name_bytes.hex()}")
    print(f"    User (222):      {user_token_name_bytes.hex()}")
    
    # Query script address for reference token
    print(f"\n[4] Querying script address...")
    utxos = context.utxos(script_addr)
    
    found_ref = None
    for utxo in utxos:
        if not utxo.output.amount.multi_asset:
            continue
        
        for pid, assets in utxo.output.amount.multi_asset.items():
            if pid.payload.hex() != args.policy_id:
                continue
            
            for asset_name, qty in assets.items():
                if asset_name.payload == ref_token_name_bytes:
                    found_ref = utxo
                    print(f"    ✓ Found reference token!")
                    print(f"    UTxO: {utxo.input.transaction_id}#{utxo.input.index}")
                    break
    
    if not found_ref:
        print(f"    ✗ Reference token not found at script address")
        return
    
    # Decode datum
    print(f"\n[5] Decoding metadata from datum...")
    if found_ref.output.datum:
        try:
            import cbor2
            from pycardano.serialization import RawCBOR
            
            datum = found_ref.output.datum
            
            print(f"    Datum type: {type(datum)}")
            
            # If RawCBOR, decode it
            if isinstance(datum, RawCBOR):
                cbor_data = datum.cbor
                decoded = cbor2.loads(cbor_data)
                print(f"    Decoded CBOR: {decoded}")
                
                # CBOR structure for PlutusData Constructor:
                # CBORTag(121, [name, image, description, attributes, media_type, files])
                from cbor2 import CBORTag
                if isinstance(decoded, CBORTag):
                    fields = decoded.value
                    if isinstance(fields, list) and len(fields) >= 6:
                        name = fields[0]
                        image = fields[1]
                        description = fields[2]
                        attributes = fields[3]
                        media_type = fields[4]
                        files = fields[5]
                        
                        # Decode bytes
                        if isinstance(name, bytes):
                            name = name.decode('utf-8')
                        if isinstance(image, bytes):
                            image = image.decode('utf-8')
                        if isinstance(description, bytes):
                            description = description.decode('utf-8')
                        if isinstance(media_type, bytes):
                            media_type = media_type.decode('utf-8')
                        
                        print(f"\n    ✓ Metadata found:")
                        print(f"    Name:        {name}")
                        print(f"    Image:       {image}")
                        print(f"    Description: {description}")
                        print(f"    Media Type:  {media_type}")
                        
                        # Parse attributes
                        if isinstance(attributes, list) and len(attributes) > 0:
                            print(f"\n    Attributes:")
                            for attr in attributes:
                                if isinstance(attr, list) and len(attr) >= 2:
                                    trait_type = attr[0].decode('utf-8') if isinstance(attr[0], bytes) else attr[0]
                                    value = attr[1].decode('utf-8') if isinstance(attr[1], bytes) else attr[1]
                                    print(f"      - {trait_type}: {value}")
                        
                        # Parse files
                        if isinstance(files, list) and len(files) > 0:
                            print(f"\n    Files:")
                            for f in files:
                                file_str = f.decode('utf-8') if isinstance(f, bytes) else f
                                print(f"      - {file_str}")
                    else:
                        print(f"    Unexpected tag value: {fields}")
                elif isinstance(decoded, list) and len(decoded) >= 2:
                    image_url = decoded[0]
                    description = decoded[1]
                    
                    if isinstance(image_url, bytes):
                        image_url = image_url.decode('utf-8')
                    if isinstance(description, bytes):
                        description = description.decode('utf-8')
                    
                    print(f"\n    ✓ Metadata found:")
                    print(f"    Image URL:   {image_url}")
                    print(f"    Description: {description}")
                else:
                    print(f"    Unexpected decoded structure: {decoded}")
            
            # Datum structure: Constructor 0 with [image_url, description]
            elif hasattr(datum, 'fields') and len(datum.fields) >= 2:
                image_url = datum.fields[0]
                description = datum.fields[1]
                
                # Convert bytes to string
                if isinstance(image_url, bytes):
                    image_url = image_url.decode('utf-8')
                if isinstance(description, bytes):
                    description = description.decode('utf-8')
                
                print(f"    Image URL:   {image_url}")
                print(f"    Description: {description}")
            else:
                print(f"    Datum fields: {datum.fields if hasattr(datum, 'fields') else 'No fields'}")
        except Exception as e:
            print(f"    Error decoding datum: {e}")
    else:
        print(f"    No datum found")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()
