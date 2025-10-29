use aiken/collection/dict.{Dict}

// ---------------------------
// ACTION TYPES
// ---------------------------

pub type MintAction {
  Mint
  Burn
}

pub type StoreAction {
  Update
  Remove
}

// ---------------------------
// META-DATUM (for CIP-68 reference UTxO)
// ---------------------------

pub type MetaDatum {
  metadata: Dict<ByteArray, Data>,
  version: Int,
  extra: ByteArray,
}

// ---------------------------
// SERIALIZATION HELPERS
// ---------------------------

// // Encode MetaDatum -> Data (to put on-chain)
// pub fn to_data(meta: MetaDatum) -> Data {
//   list_data([
//     list_data(
//       Dict.to_list(meta.metadata)
//         |> list.map(fn ((k, v)) { list_data([b_data(k), v]) })
//     ),
//     i_data(meta.version),
//     b_data(meta.extra),
//   ])
// }

// // Decode Data -> MetaDatum (to use inside validator)
// pub fn from_data(d: Data) -> MetaDatum {
//   // Step 1: expect top-level list
//   expect list_data(top) = d

//   // Step 2: Extract metadata_list, version, extra
//   expect Some(metadata_list_d) = list.head(top)
//   expect Some(rest1) = list.tail(top)
//   expect Some(version_d) = list.head(rest1)
//   expect Some(rest2) = list.tail(rest1)
//   expect Some(extra_d) = list.head(rest2)

//   // Step 3: decode version & extra
//   expect un_i_data(version) = version_d
//   expect un_b_data(extra) = extra_d

//   // Step 4: decode metadata_list_d -> List<(ByteArray, Data)>
//   expect list_data(kvs_d) = metadata_list_d

//   let kv_pairs =
//     list.map(kvs_d, fn (kv_d) {
//       expect list_data([k_d, v]) = kv_d
//       expect un_b_data(k) = k_d
//       (k, v)
//     })

//   MetaDatum {
//     metadata: Dict.from_list(kv_pairs),
//     version,
//     extra,
//   }
// }
