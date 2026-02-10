use aiken/collection/list
use aiken/primitive/bytearray
use cardano/assets.{PolicyId}
use cardano/transaction.{InlineDatum, OutputReference, Transaction}

// Reference Token: (100) - 0x000643b0 // nằm trong script để chứa datum có thể cập nhật
// User Token: (222) - 0x000de140 // nằm trong ví của người dùng để 
// đại diện cho quyên sở hữu tài sản

pub type MintRedeemer {
  /// Mint mới reference token và user token
  MintToken { token_name: ByteArray }
  /// Burn reference token và user token
  BurnToken { token_name: ByteArray }
}

pub type SpendRedeemer {
  /// Update metadata của reference token
  UpdateMetadata
  /// Burn reference token
  BurnReference
}

pub type CIP68Datum {
  /// Policy ID của token chứa thộng tin của token
  policy_id: ByteArray,
  /// Tên của token chứa thông tin của token
  asset_name: ByteArray,
  // policy Id và token name là thông tin để xác định token
  /// Owner public key hash - người có quyền update/burn 
  owner: ByteArray,
  /// Metadata fields theo CIP-68 standard
  metadata: Data,
  /// Version của metadata
  version: Int,
}

validator cip68_mint {
  mint(redeemer: MintRedeemer, policy_id: PolicyId, tx: Transaction) {
    let Transaction { mint, .. } = tx
    when redeemer is {
      MintToken { token_name } -> {
        // Tạo asset names theo CIP-68 standard
        let ref_token_name = #"000643b0" |> bytearray.concat(token_name)
        let user_token_name = #"000de140" |> bytearray.concat(token_name)
        // Kiểm tra mint đúng số lượng tokens
        let ref_token_amount =
          assets.quantity_of(mint, policy_id, ref_token_name)
        let user_token_amount =
          assets.quantity_of(mint, policy_id, user_token_name)
        // Phải mint đúng 1 reference token và 1 user token
        ref_token_amount == 1 && user_token_amount == 1
      }
      BurnToken { token_name } -> {
        // Tạo asset names theo CIP-68 standard
        let ref_token_name = #"000643b0" |> bytearray.concat(token_name)
        let user_token_name = #"000de140" |> bytearray.concat(token_name)
        // Kiểm tra burn đúng số lượng tokens
        let ref_token_amount =
          assets.quantity_of(mint, policy_id, ref_token_name)
        let user_token_amount =
          assets.quantity_of(mint, policy_id, user_token_name)
        // Phải burn đúng 1 reference token và 1 user token
        ref_token_amount == -1 && user_token_amount == -1
      }
    }
  }

  else(_) {
    fail
  }
}

validator cip68_store {
  spend(
    datum: Option<CIP68Datum>,
    redeemer: SpendRedeemer,
    own_ref: OutputReference,
    // tham chiếu đến utxo đang được chi tiêu(spend)
    tx: Transaction,
  ) {
    // lấy thông tin datum
    expect Some(current_datum) = datum
    let owner_pkh = current_datum.owner
    let datum_policy_id = current_datum.policy_id
    let datum_asset_name = current_datum.asset_name
    // hợp đồng store với thiết kế 
    // với update có các điều kiện cần đó là ký bởi owner
    // input khi chi tiêu phải có reference token
    // output gửi lại hợp đồng phải có reference token và datum mới
    // có các trường metadata được cập nhật, policy id và asset name giữ nguyên
    // Kiểm tra chữ ký của owner
    let must_be_signed = list.has(tx.extra_signatories, owner_pkh)
    // kết thúc kiểm tra chư ký
    when redeemer is {
      UpdateMetadata -> {
        // Tìm input của script
        expect Some(own_input) =
          list.find(tx.inputs, fn(input) { input.output_reference == own_ref })
        let script_address = own_input.output.address
        let ref_token_name = #"000643b0" |> bytearray.concat(datum_asset_name)
        // Kiểm tra input có chứa reference token
        // với đúng policy id và token name
        let input_has_ref_token =
          assets.quantity_of(
            own_input.output.value,
            datum_policy_id,
            ref_token_name,
          ) == 1
        // kiểm tra output gửi lại script phải chứa
        // reference token và datum mới có các trường
        // metadata được cập nhật và
        // đúng policy id và token name cũ không được thay đổi
        let has_valid_output =
          list.any(
            tx.outputs,
            fn(output) {
              when output.datum is {
                InlineDatum(data) -> {
                  expect new_datum: CIP68Datum = data
                  // Kiểm tra output có reference token
                  let output_has_ref_token =
                    assets.quantity_of(
                      output.value,
                      datum_policy_id,
                      ref_token_name,
                    ) == 1
                  // kiểm tra ràng buộc về thông tin sau khi update
                  output.address == script_address && output_has_ref_token && new_datum.policy_id == datum_policy_id && new_datum.asset_name == datum_asset_name && new_datum.owner == owner_pkh
                }
                _ -> False
              }
            },
          )
        must_be_signed && input_has_ref_token && has_valid_output
      }
      BurnReference -> must_be_signed
    }
  }

  else(_) {
    fail
  }
}
