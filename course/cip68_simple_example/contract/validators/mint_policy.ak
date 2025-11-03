// Simple CIP-68 Minting Policy
use aiken/collection/list
use cardano/address.{Script}
use cardano/assets.{PolicyId, flatten, quantity_of}
use cardano/script_context.{ScriptContext}
use cardano/transaction.{InlineDatum, Mint, Output, OutputReference, Transaction}
use cip68.{get_asset_name, has_label, label_100, label_222}

/// CIP-68 Metadata stored in reference token datum
pub type Metadata {
  metadata: List<(ByteArray, ByteArray)>,  // Key-value pairs
  version: Int,                             // Metadata version
  extra: ByteArray,                        // Extra data
}

/// Minting action
pub type MintAction {
  Mint
  Burn
}

/// Minting policy parameters (supplied at script creation)
pub type MintParams {
  /// Hash of the reference token store validator
  store_validator_hash: ByteArray,
  /// Public key hash of the issuer (who can mint)
  issuer_pkh: ByteArray,
}

/// Main minting validator
validator mint_policy(params: MintParams) {
  mint(redeemer: MintAction, own_policy: PolicyId, ctx: ScriptContext) {
    let ScriptContext { transaction, .. } = ctx
    
    when redeemer is {
      Mint -> validate_mint(transaction, own_policy, params)
      Burn -> validate_burn(transaction, own_policy, params)
    }
  }
}

/// Validate minting operation
fn validate_mint(
  tx: Transaction,
  own_policy: PolicyId,
  params: MintParams,
) -> Bool {
  // Get all minted tokens for this policy - flatten returns List<(PolicyId, AssetName, Int)>
  let all_minted = flatten(tx.mint)
  
  // Filter for our policy
  let our_mints =
    list.filter(
      all_minted,
      fn(entry) {
        let (policy_id, _asset_name, _qty) = entry
        policy_id == own_policy
      },
    )
  
  // Must mint exactly 2 tokens
  expect [(_, name1, qty1), (_, name2, qty2)] = our_mints
  
  // Both quantities must be 1
  let valid_quantities = qty1 == 1 && qty2 == 1
  
  // One must be ref token (100), one must be user token (222)
  let (ref_token, user_token) =
    if has_label(name1, label_100) && has_label(name2, label_222) {
      (name1, name2)
    } else if has_label(name1, label_222) && has_label(name2, label_100) {
      (name2, name1)
    } else {
      fail @"Invalid token labels"
    }
  
  // Both must have same asset name suffix
  let matching_suffix = get_asset_name(ref_token) == get_asset_name(user_token)
  
  // Check reference token goes to store validator with inline datum
  let ref_to_store =
    check_ref_output(
      tx.outputs,
      params.store_validator_hash,
      own_policy,
      ref_token,
    )
  
  // Check issuer signed the transaction
  let issuer_signed = list.has(tx.extra_signatories, params.issuer_pkh)
  
  // All checks must pass
  valid_quantities && matching_suffix && ref_to_store && issuer_signed
}

/// Check that reference token is sent to store with inline datum
fn check_ref_output(
  outputs: List<Output>,
  store_hash: ByteArray,
  policy: PolicyId,
  ref_token: ByteArray,
) -> Bool {
  list.any(
    outputs,
    fn(output) {
      // Check address is the store validator
      let correct_address =
        when output.address.payment_credential is {
          Script(hash) -> hash == store_hash
          _ -> False
        }
      
      // Check it contains the reference token
      let has_ref_token = quantity_of(output.value, policy, ref_token) == 1
      
      // Check it has inline datum
      let has_inline_datum =
        when output.datum is {
          InlineDatum(_) -> True
          _ -> False
        }
      
      correct_address && has_ref_token && has_inline_datum
    },
  )
}

/// Validate burning operation
fn validate_burn(
  tx: Transaction,
  _own_policy: PolicyId,
  params: MintParams,
) -> Bool {
  // For burning, just check issuer signed
  list.has(tx.extra_signatories, params.issuer_pkh)
}
