// Simple Reference Token Store Validator
use aiken/collection/list
use cardano/transaction.{OutputReference, Transaction}

/// Store parameters (supplied at script creation)
pub type StoreParams {
  /// Public key hash of the issuer (who can update)
  issuer_pkh: ByteArray,
}

/// Store redeemer (what action to take)
pub type StoreAction {
  Update  // Update the metadata
  Burn    // Burn the reference token
}

/// Main store validator
validator store_validator(params: StoreParams) {
  spend(
    _datum: Option<Data>,
    redeemer: StoreAction,
    _own_ref: OutputReference,
    ctx: Transaction,
  ) {
    when redeemer is {
      Update -> validate_update(ctx, params)
      Burn -> validate_burn(ctx, params)
    }
  }
}

/// Validate update operation
fn validate_update(tx: Transaction, params: StoreParams) -> Bool {
  // For update, just check issuer signed
  // (Reference token continues to exist at the store address)
  list.has(tx.extra_signatories, params.issuer_pkh)
}

/// Validate burn operation
fn validate_burn(tx: Transaction, params: StoreParams) -> Bool {
  // For burning, check issuer signed
  // (The actual burning is handled by the minting policy)
  list.has(tx.extra_signatories, params.issuer_pkh)
}
