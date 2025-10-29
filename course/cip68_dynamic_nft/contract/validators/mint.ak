use aiken/collection/list
use aiken/crypto.{Blake2b_224, Hash, Script, VerificationKey}
use cardano/script_context as sc
use cardano/script_context.{ScriptContext}
use cardano/transaction.{Transaction}
use cardano/assets as assets

use cip68_nft/types.{MintAction}
use cip68_nft/utils

// Đặt tên validator: mint
validator mint_policy(
  issuer: Hash<Blake2b_224, VerificationKey>,
  store: Hash<Blake2b_224, Script>,
) {
  mint(rdmr: Option<MintAction>, _policy_id: assets.PolicyId, ctx: ScriptContext) -> Bool {

    // const PROJECT_VERSION = #"cip68_nfts_example_v1"    
    let ScriptContext { transaction, info, .. } = ctx
    when info is {
      sc.Minting(policy_id) -> {
        let Transaction { outputs, .. } = transaction

        // Tất cả entries mint/burn (flatten)
        let minted_flat =
          transaction.mint
            |> assets.flatten()

        when rdmr is {
          // Mint: +1 ref(100) +1 user(222), cùng suffix, ref gửi vào store với datum hợp lệ
          Some(MintAction.Mint) -> {
            let minted_pos =
              list.filter(minted_flat, fn ((pid, _tn, amt)) { pid == policy_id && amt == 1 })

            expect 2 = list.length(minted_pos)

            let refs =
              list.filter(minted_pos, fn ((_pid, tn, _amt)) { utils.has_label(tn, 100) })
            let users =
              list.filter(minted_pos, fn ((_pid, tn, _amt)) { utils.has_label(tn, 222) })

            expect 1 = list.length(refs)
            expect 1 = list.length(users)

            expect Some((_, tn_ref, _)) = list.head(refs)
            expect Some((_, tn_user, _)) = list.head(users)

            expect True = utils.same_suffix(tn_ref, tn_user)
            expect True = utils.is_signed_by(transaction, issuer)

            expect Some(out_ref) =
              utils.find_output_by_script_and_asset(outputs, store, policy_id, tn_ref)
            expect True = utils.check_output_utxo(out_ref)

            True
          }

          // Burn: -1 ref(100) và -1 user(222), cùng suffix, issuer ký
          Some(MintAction.Burn) -> {
            let refs_burn =
              list.filter(minted_flat, fn ((pid, tn, amt)) {
                pid == policy_id && amt == -1 && utils.has_label(tn, 100)
              })

            let users_burn =
              list.filter(minted_flat, fn ((pid, tn, amt)) {
                pid == policy_id && amt == -1 && utils.has_label(tn, 222)
              })

            expect 1 = list.length(refs_burn)
            expect 1 = list.length(users_burn)

            expect Some((_, tn_ref_b, _)) = list.head(refs_burn)
            expect Some((_, tn_user_b, _)) = list.head(users_burn)

            expect True = utils.same_suffix(tn_ref_b, tn_user_b)
            expect True = utils.is_signed_by(transaction, issuer)

            True
          }
            // 👇 Bổ sung dòng này để tránh lỗi non-exhaustive
        _ -> False
        }
      }
      _ -> False
    }
  }
}
