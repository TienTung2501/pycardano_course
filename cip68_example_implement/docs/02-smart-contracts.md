# Module 2: Smart Contracts với Aiken

## 2.1. Tổng quan Validator

Trong CIP-68, Plutus validator CHỈ dùng cho **UPDATE metadata**, KHÔNG dùng cho minting.

### Vai trò của validator:

✅ Kiểm soát việc spend reference token UTxO  
✅ Đảm bảo owner token (222) exists trong transaction  
✅ Verify datum structure hợp lệ  
✅ Đảm bảo reference token được return về script address  

---

## 2.2. Datum Structure

```aiken
// Datum đơn giản - chỉ 2 fields
pub type CIP68Datum {
  image_url: ByteArray,
  description: ByteArray,
}
```

**Trong CBOR/JSON:**
```json
{
  "constructor": 0,
  "fields": [
    {"bytes": "68747470733a2f2f..."},  // image_url (hex)
    {"bytes": "6465736372697074696f6e"}  // description (hex)
  ]
}
```

---

## 2.3. Redeemer Structure

```aiken
pub type UpdateRedeemer {
  new_image_url: ByteArray,
  new_description: ByteArray,
  token_name: ByteArray,
}
```

---

## 2.4. Validator Code (Simplified)

```aiken
use aiken/builtin.{append_bytearray}
use aiken/collection/list
use cardano/assets.{AssetName, PolicyId, quantity_of}
use cardano/transaction.{InlineDatum, Input, OutputReference, Transaction}

pub type CIP68Datum {
  image_url: ByteArray,
  description: ByteArray,
}

pub type UpdateRedeemer {
  new_image_url: ByteArray,
  new_description: ByteArray,
  token_name: ByteArray,
}

validator update_metadata(reference_token_policy: PolicyId) {
  spend(
    _old_datum: Option<CIP68Datum>,
    redeemer: UpdateRedeemer,
    oref: OutputReference,
    tx: Transaction,
  ) {
    let UpdateRedeemer { new_image_url, new_description, token_name } = redeemer
    let Transaction { inputs, outputs, .. } = tx

    // Construct asset names
    let ref_token_name: AssetName = append_bytearray("100", token_name)
    let user_token_name: AssetName = append_bytearray("222", token_name)

    // Find the input being spent (reference token)
    let reference_input = 
      list.find(inputs, fn(input) { input.output_reference == oref })
    
    expect Some(ref_input) = reference_input

    // Find outputs back to script address with reference token
    let reference_outputs = 
      list.filter(
        outputs,
        fn(output) {
          output.address == ref_input.output.address &&
          quantity_of(output.value, reference_token_policy, ref_token_name) == 1
        },
      )

    // Find owner token (222) in inputs - proves ownership
    let owner_token_inputs = 
      list.filter(
        inputs,
        fn(input) {
          quantity_of(input.output.value, reference_token_policy, user_token_name) == 1
        },
      )

    // Find owner token in outputs - must be returned
    let owner_token_outputs = 
      list.filter(
        outputs,
        fn(output) {
          quantity_of(output.value, reference_token_policy, user_token_name) == 1
        },
      )

    // Validate conditions
    when (reference_outputs, owner_token_inputs, owner_token_outputs) is {
      ([reference_output], [owner_input], [owner_output]) -> {
        // Check new datum is correct
        expect InlineDatum(new_datum_data) = reference_output.datum
        expect new_datum: CIP68Datum = new_datum_data
        
        // Verify all conditions
        and {
          // New datum has correct values
          new_datum.image_url == new_image_url,
          new_datum.description == new_description,
          
          // Reference token input has correct token
          quantity_of(ref_input.output.value, reference_token_policy, ref_token_name) == 1,
          
          // Reference token output has correct token
          quantity_of(reference_output.value, reference_token_policy, ref_token_name) == 1,
          
          // Owner token stays with same owner
          owner_input.output.address == owner_output.address,
        }
      }
      _ -> False
    }
  }

  else(_) {
    fail
  }
}
```

---

## 2.5. Giải thích Logic

### Step 1: Extract redeemer data
```aiken
let UpdateRedeemer { new_image_url, new_description, token_name } = redeemer
```

### Step 2: Construct token names
```aiken
let ref_token_name = "100" + token_name
let user_token_name = "222" + token_name
```

### Step 3: Find reference token input
- Input đang được spend phải chứa reference token (100)

### Step 4: Find reference token output
- Output về script address phải chứa reference token (100)
- Có inline datum mới

### Step 5: Verify owner token
- **Input**: Owner token (222) phải có trong inputs (proves ownership)
- **Output**: Owner token phải return về address cũ (không đổi owner)

### Step 6: Validate datum
- Datum mới phải match với redeemer
- Structure phải đúng (CIP68Datum)

---

## 2.6. Test Cases

### Test 1: Successful Update
```aiken
test test_update_success() {
  let policy_id = mock_policy_id(0)
  let wallet_addr = mock_pub_key_address(0, None)
  let script_addr = mock_script_address(1, None)
  
  let old_datum = CIP68Datum {
    image_url: "old_url",
    description: "old_desc",
  }
  
  let new_datum = CIP68Datum {
    image_url: "new_url",
    description: "new_desc",
  }
  
  let redeemer = UpdateRedeemer {
    new_image_url: "new_url",
    new_description: "new_desc",
    token_name: "MyNFT",
  }
  
  let tx = mock_update_tx(
    old_datum,
    new_datum,
    redeemer,
    wallet_addr,
    script_addr,
    policy_id,
  )
  
  let output_ref = mock_utxo_ref(1, 0)
  
  update_metadata.spend(
    policy_id,
    Some(old_datum),
    redeemer,
    output_ref,
    tx,
  )
}
```

### Test 2: Missing Owner Token (Should Fail)
```aiken
test test_update_no_owner_token() fail {
  // Transaction WITHOUT owner token (222)
  // Should fail validation
  ...
}
```

### Test 3: Wrong Datum (Should Fail)
```aiken
test test_update_wrong_datum() fail {
  // Datum doesn't match redeemer
  // Should fail
  ...
}
```

---

## 2.7. Build và Deploy

### Build với Aiken
```bash
cd contracts
aiken build
```

Output: `plutus.json` chứa compiled validator

### Extract validator CBOR
```bash
# Lấy compiled code từ plutus.json
cat plutus.json | jq '.validators[0].compiledCode' -r > update_metadata.cbor
```

### Generate script address
```python
from pycardano import PlutusV3Script, Address, Network

# Load validator
with open('plutus.json', 'r') as f:
    blueprint = json.load(f)
    
cbor_hex = blueprint['validators'][0]['compiledCode']
script = PlutusV3Script(bytes.fromhex(cbor_hex))

# Get script hash
script_hash = plutus_script_hash(script)

# Create address
script_addr = Address(script_hash, network=Network.TESTNET)
print(f"Script address: {script_addr}")
```

---

## 2.8. Apply Parameters

Validator cần `reference_token_policy` parameter - đây là policy ID của tokens.

**Sau khi mint:**
```bash
# Policy ID được tạo từ native script
policy_id="abc123..."

# Apply parameter bằng Aiken
aiken blueprint apply \
  -o plutus.json \
  -v update_metadata.update_metadata \
  $policy_id
```

**Hoặc dùng PyCardano:**
```python
import cbor2
from pycardano import PlutusData

# Policy ID as PlutusData
@dataclass
class PolicyIdParam(PlutusData):
    policy_id: bytes

param = PolicyIdParam(policy_id=bytes.fromhex(policy_id_hex))

# Apply với Aiken CLI
subprocess.run([
    'aiken', 'blueprint', 'apply',
    '-o', 'plutus_with_params.json',
    '-v', 'update_metadata.update_metadata',
    cbor2.dumps(param).hex()
])
```

---

## 2.9. Security Considerations

### ✅ Validator đảm bảo:

1. **Owner verification**: Owner token (222) PHẢI có trong inputs
2. **Reference token preserved**: Token 100 returned về script
3. **Datum integrity**: New datum match redeemer
4. **Address consistency**: Owner token không đổi address

### ⚠️ Lưu ý:

- Validator KHÔNG check ai là owner (address bất kỳ có 222 token đều OK)
- Nếu cần restrict owner, thêm check signature trong validator
- Datum structure CÓ THỂ mở rộng (thêm fields)

---

## 2.10. Mở rộng Datum

### Thêm fields:
```aiken
pub type CIP68DatumExtended {
  image_url: ByteArray,
  description: ByteArray,
  attributes: List<(ByteArray, ByteArray)>,  // Key-value pairs
  version: Int,
}
```

### Nested structures:
```aiken
pub type GameCharacter {
  image_url: ByteArray,
  description: ByteArray,
  level: Int,
  health: Int,
  mana: Int,
  equipment: List<ByteArray>,
}
```

---

## 2.11. Homework / Practice

1. **Thêm field `version` vào datum**
   - Update validator để check version increment
   
2. **Implement burn logic**
   - Validator cho phép burn cả 2 tokens
   
3. **Add owner restriction**
   - Chỉ specific address có thể update

---

**Next:** [Module 3: Off-chain Scripts với PyCardano](./03-offchain-pycardano.md)
