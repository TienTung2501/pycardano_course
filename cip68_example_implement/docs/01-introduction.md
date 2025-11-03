# Module 1: Giới thiệu CIP-68

## 1.1. CIP-68 là gì?

**CIP-68** (Cardano Improvement Proposal 68) là một tiêu chuẩn để tạo **NFT động** (Dynamic NFTs) trên Cardano blockchain.

### Vấn đề với NFT truyền thống (CIP-25)

NFT truyền thống sử dụng CIP-25 có **metadata tĩnh** được lưu trong transaction metadata khi mint:

```json
{
  "721": {
    "policy_id": {
      "token_name": {
        "name": "My NFT",
        "image": "ipfs://...",
        "attributes": {...}
      }
    }
  }
}
```

**Hạn chế:**
- ❌ Metadata KHÔNG thể thay đổi sau khi mint
- ❌ Không phù hợp cho game items (stats thay đổi)
- ❌ Không phù hợp cho dynamic content (evolving art)
- ❌ Không thể update thông tin mới

### Giải pháp: CIP-68

CIP-68 giải quyết bằng cách:
- ✅ Lưu metadata trong **UTxO datum** (có thể spend và recreate)
- ✅ Cho phép **update** metadata bất cứ lúc nào
- ✅ Tách riêng **ownership** và **metadata storage**

---

## 1.2. Kiến trúc Reference Token Pair

CIP-68 sử dụng **2 tokens** cho mỗi NFT:

### Token 1: Reference Token (Label 100)
- **Asset name**: `"100" + token_name`
- **Purpose**: Lưu trữ metadata
- **Location**: Locked tại script address
- **Datum**: Chứa metadata (image, description, attributes...)
- **Quantity**: Luôn là 1
- **Không transfer**: Chỉ dùng để reference

### Token 2: User Token (Label 222)
- **Asset name**: `"222" + token_name`
- **Purpose**: Ownership
- **Location**: User wallet
- **Datum**: Không có
- **Quantity**: 1 (NFT) hoặc nhiều (FT)
- **Có thể transfer**: Normal token behavior

### Diagram

```
┌─────────────────────────────────────────────┐
│           CIP-68 NFT Architecture           │
└─────────────────────────────────────────────┘

┌─────────────────┐         ┌──────────────────┐
│  Policy ID      │         │   Token Name     │
│  (Same for both)│         │                  │
└────────┬────────┘         └────────┬─────────┘
         │                           │
         ├───────────┬───────────────┤
         │           │               │
         ▼           ▼               ▼
┌────────────┐ ┌─────────────┐ ┌──────────────┐
│ Reference  │ │ User Token  │ │ Same policy  │
│ Token (100)│ │ Token (222) │ │ Different    │
│            │ │             │ │ asset names  │
└──────┬─────┘ └──────┬──────┘ └──────────────┘
       │              │
       │              │
       ▼              ▼
┌─────────────┐ ┌────────────┐
│ At Script   │ │ In User    │
│ Address     │ │ Wallet     │
│             │ │            │
│ Has inline  │ │ No datum   │
│ datum with  │ │            │
│ metadata    │ │ Transferable│
└─────────────┘ └────────────┘
```

---

## 1.3. Ví dụ cụ thể

### NFT Game Character

Giả sử bạn tạo một game character NFT:

**Ban đầu (Mint):**
```
Reference Token (100):
  - Asset: policy_id + "100CharacterAlpha"
  - Locked at: Script address
  - Datum: {
      image_url: "ipfs://character_level1.png",
      description: "Level 1 Warrior, HP: 100"
    }

User Token (222):
  - Asset: policy_id + "222CharacterAlpha"
  - In wallet: addr1...xyz
  - Ownership proof
```

**Sau khi level up (Update):**
```
Reference Token (100):
  - Asset: SAME (policy_id + "100CharacterAlpha")
  - Still at: Script address
  - NEW Datum: {
      image_url: "ipfs://character_level5.png",
      description: "Level 5 Warrior, HP: 500"
    }

User Token (222):
  - Asset: SAME (không đổi)
  - Still in wallet: addr1...xyz
```

**Cách update hoạt động:**
1. Spend Reference Token UTxO (với validator approval)
2. Create new UTxO với same token NHƯNG datum mới
3. User token không bị ảnh hưởng

---

## 1.4. So sánh CIP-25 vs CIP-68

| Feature | CIP-25 (Traditional) | CIP-68 (Dynamic) |
|---------|---------------------|------------------|
| Metadata storage | Transaction metadata | UTxO datum |
| Can update? | ❌ No | ✅ Yes |
| Tokens per NFT | 1 | 2 (100 + 222) |
| Complexity | Simple | Medium |
| Gas fees | Low | Medium |
| Use cases | Static art, collectibles | Games, dynamic content |
| Ownership | Token itself | 222 token |
| Metadata reference | 100 token at script |

---

## 1.5. Use Cases thực tế

### 1. **Gaming NFTs**
- Character stats thay đổi (level, HP, equipment)
- In-game items với durability
- Evolving pets/creatures

### 2. **Dynamic Art**
- NFT thay đổi theo thời gian
- NFT phản ứng với external data (weather, stock price)
- Generative art evolves

### 3. **Membership/Access Tokens**
- Update privilege levels
- Thêm/bớt access rights
- Dynamic metadata cho passes

### 4. **Real World Assets**
- Update property details
- Maintenance records
- Certification updates

### 5. **Social Identity**
- Profile pictures với stats
- Achievement badges
- Reputation scores

---

## 1.6. Workflow tổng quát

### Mint (Tạo NFT mới)
```
1. Generate policy (Native Script - signature based)
2. Create transaction:
   - Mint 2 tokens (100 + 222)
   - Send 100 to script address WITH datum
   - Send 222 to user wallet
3. Sign and submit
```

### Update (Thay đổi metadata)
```
1. Build transaction:
   - Spend reference token UTxO (input)
   - Recreate UTxO with NEW datum (output)
   - Attach Plutus validator redeemer
   - Include user token as proof
2. Validator checks:
   - User token exists
   - Reference token returned to script
   - Datum structure valid
3. Sign and submit
```

### Transfer Ownership
```
1. Just transfer 222 token to new owner
2. Reference token stays at script
3. New owner can now update metadata
```

### Burn
```
1. Burn both tokens (100 + 222)
2. Spend reference token UTxO
3. Mint negative amounts
```

---

## 1.7. Điểm chú ý

### ⚠️ Lưu ý quan trọng:

1. **Reference token KHÔNG phải NFT thực sự**
   - User token (222) mới là NFT ownership
   - Reference token chỉ để lưu metadata

2. **Policy ID phải GIỐNG NHAU**
   - Cả 100 và 222 dùng cùng policy
   - Chỉ khác asset name

3. **Datum structure**
   - Phải match với validator expects
   - Thường là: constructor 0 với fields

4. **Gas fees**
   - Update cần Plutus execution → phí cao hơn transfer
   - Mint với native script → phí thấp

5. **Security**
   - Validator phải check owner token exists
   - Prevent unauthorized updates

---

## 1.8. Chuẩn bị cho Module 2

Trong module tiếp theo, chúng ta sẽ:
- Viết Aiken validator để kiểm soát việc update
- Hiểu cách validator check owner token
- Test validator logic

**Yêu cầu:**
- Đã cài đặt Aiken compiler
- Hiểu cơ bản về Plutus validators
- Biết cách test với Aiken

---

## 📚 Tài liệu tham khảo

- [CIP-68 Official Specification](https://cips.cardano.org/cips/cip68/)
- [Cardano NFT Standards Overview](https://developers.cardano.org/docs/native-tokens/minting-nfts/)
- [PPBL CIP-68 Examples](https://plutuspbl.io/)

---

**Next:** [Module 2: Smart Contracts với Aiken](./02-smart-contracts.md)
