use aiken/collection/list
use aiken/crypto.{Blake2b_224, Hash, Script, VerificationKey}
use aiken/primitive/bytearray as bytes
use aiken/primitive/int as int

use cardano/address.{Address, Credential}
use cardano/assets as assets
use cardano/transaction.{InlineDatum, Output, Transaction}


// Kiểm tra token name có prefix 4 byte (CIP-67) == label (big-endian)
pub fn has_label(tn: ByteArray, label: Int) -> Bool {
  int.from_bytearray_big_endian(bytes.take(tn, 4)) == label
}

pub fn drop_label(tn: ByteArray) -> ByteArray {
  bytes.drop(tn, 4)
}

pub fn same_suffix(tn1: ByteArray, tn2: ByteArray) -> Bool {
  drop_label(tn1) == drop_label(tn2)
}

pub fn is_locked_by_script(
  addr: Address,
  script_hash: Hash<Blake2b_224, Script>,
) -> Bool {
  let Address { payment_credential, .. } = addr

  when payment_credential is {
    Credential.Script(h) -> h == script_hash
    _ -> False
  }
}



// Output ref phải có inline datum kiểu MetaDatum và chỉ 1 non-ADA asset
pub fn check_output_utxo(output: Output) -> Bool {
  expect InlineDatum(_data) = output.datum

  let flat =
    output.value
      |> assets.without_lovelace()
      |> assets.flatten()

  list.length(flat) == 1
}
// Kiểm tra Value có chứa (policy, name) với qty > 0
pub fn has_asset(v: assets.Value, policy: assets.PolicyId, name: ByteArray) -> Bool {
  let flat =
    v
      |> assets.without_lovelace()
      |> assets.flatten()

    list.any(flat, fn (item) {
    let (pid, tn, amt) = item
    pid == policy && tn == name && amt > 0
  })
}


// Tìm output ở đúng script address và phải chứa asset (policy, name)
pub fn find_output_by_script_and_asset(
  outputs: List<Output>,
  script_hash: Hash<Blake2b_224, Script>,
  policy: assets.PolicyId,
  name: ByteArray,
) -> Option<Output> {
  list.find(outputs, fn (o: Output) {
    is_locked_by_script(o.address, script_hash)
       && has_asset(o.value, policy, name)
  })
}

// Tìm output bất kỳ có chứa asset
pub fn find_output_by_asset(
  outputs: List<Output>,
  policy: assets.PolicyId,
  name: ByteArray,
) -> Option<Output> {
  list.find(outputs, fn (o: Output) { has_asset(o.value, policy, name) })
}

// Wrapper contains (tiện dùng trong validators)
pub fn contains_asset(v: assets.Value, policy: assets.PolicyId, name: ByteArray) -> Bool {
  has_asset(v, policy, name)
}
// Kiểm tra tx có chữ ký của issuer (extra_signatories)
pub fn is_signed_by(tx: Transaction, who: Hash<Blake2b_224, VerificationKey>) -> Bool {
  list.any(tx.extra_signatories, fn (sig) { sig == who })
}
