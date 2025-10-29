use aiken/collection/list
use aiken/crypto.{Blake2b_224, Hash, VerificationKey}

use cardano/script_context as sc
use cardano/script_context.{ScriptContext}
use cardano/transaction.{Transaction, OutputReference}
use cardano/assets as assets

use cip68_nft/types.{StoreAction}
use cip68_nft/utils

// Đặt tên validator: reference_store
validator reference_store(
  issuer: Hash<Blake2b_224, VerificationKey>,
) {
 spend(_datum: Option<Data>, rdmr: Option<StoreAction>, _own_ref: OutputReference, ctx: ScriptContext) -> Bool {
    
    // const PROJECT_VERSION = #"cip68_nfts_example_v1"  
    // let meta = MetaDatum::from_data(datum_data)
    let ScriptContext { transaction, info, .. } = ctx
    let Transaction { inputs, outputs, .. } = transaction

    // Own input reference từ ScriptInfo
    expect sc.Spending { output: own_ref, .. } = info
    // Tìm input khớp own_ref
    expect Some(own_in) =
      list.find(inputs, fn (i) { i.output_reference == own_ref })

    // Non-ADA assets trong own input (mong đợi đúng 1 ref asset)
    let ref_assets =
      own_in.output.value
        |> assets.without_lovelace()
        |> assets.flatten()

    expect 1 = list.length(ref_assets)
    expect Some((policy_id, tn_ref, _amt_in)) = list.head(ref_assets)

    // Issuer phải ký
    expect True = utils.is_signed_by(transaction, issuer)

   when rdmr is {
  // Update: trả về cùng script addr, giữ asset + datum hợp lệ
    Some(StoreAction.Update) -> {
      expect Some(out_ref) =
        list.find(outputs, fn (o) {
          o.address == own_in.output.address
            && utils.contains_asset(o.value, policy_id, tn_ref)
        })
      expect True = utils.check_output_utxo(out_ref)
      True
    }

    // Remove: cho rời khỏi script, nhưng output vẫn phải giữ shape datum + asset
    Some(StoreAction.Remove) -> {
      expect Some(out_any) =
        utils.find_output_by_asset(outputs, policy_id, tn_ref)
      expect True = utils.check_output_utxo(out_any)
      True
    }

      // 👇 Bổ sung dòng này để tránh lỗi non-exhaustive
      _ -> False
    }

  }
}