// CIP-68 Utilities - Simplified version
use aiken/primitive/bytearray

/// CIP-68 token name labels (4 bytes big-endian)
pub const label_100: ByteArray = #"00000064"  // Reference token (100)
pub const label_222: ByteArray = #"000000de"  // User token (222)

/// Check if a token name has the correct CIP-68 label
pub fn has_label(token_name: ByteArray, label: ByteArray) -> Bool {
  // Token name must be 32 bytes: 4-byte label + 28-byte asset name
  if bytearray.length(token_name) != 32 {
    False
  } else {
    // Check first 4 bytes match the label
    bytearray.take(token_name, 4) == label
  }
}

/// Get the asset name suffix (last 28 bytes) from a token name
pub fn get_asset_name(token_name: ByteArray) -> ByteArray {
  bytearray.drop(token_name, 4)
}

/// Build reference token name from asset name
pub fn make_ref_token(asset_name: ByteArray) -> ByteArray {
  bytearray.concat(label_100, asset_name)
}

/// Build user token name from asset name
pub fn make_user_token(asset_name: ByteArray) -> ByteArray {
  bytearray.concat(label_222, asset_name)
}
