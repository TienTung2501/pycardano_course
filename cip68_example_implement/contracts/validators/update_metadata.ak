use aiken/builtin.{append_bytearray}
use aiken/collection/list
use cardano/assets.{AssetName, PolicyId, quantity_of}
use cardano/transaction.{InlineDatum, Input, OutputReference, Transaction}

/// CIP-68 Metadata Structure - Full CIP-25 compatible
/// Supports name, image, description, attributes, và custom fields
pub type CIP68Metadata {
  name: ByteArray,
  image: ByteArray,
  description: ByteArray,
  // Attributes as list of key-value pairs
  attributes: List<(ByteArray, ByteArray)>,
  // Additional optional fields
  media_type: ByteArray,
  files: List<ByteArray>,
}

/// Redeemer cho việc update metadata
pub type UpdateRedeemer {
  new_metadata: CIP68Metadata,
  token_name: ByteArray,
}

pub type ActionRedeemer {
  Update(UpdateRedeemer)
  Burn(ByteArray)
}

/// Validator kiểm soát việc update reference token
/// Parameter: reference_token_policy - Policy ID của CIP-68 tokens
validator update_metadata(reference_token_policy: PolicyId) {
  spend(
    _old_datum: Option<CIP68Metadata>,
    redeemer: ActionRedeemer,
    oref: OutputReference,
    tx: Transaction,
  ) {
    let Transaction { inputs, outputs, mint, .. } = tx

    when redeemer is {
      Update(UpdateRedeemer { new_metadata, token_name }) -> {
        let ref_token_name: AssetName = append_bytearray("100", token_name)
        let user_token_name: AssetName = append_bytearray("222", token_name)

        when list.filter(inputs, fn(input) { input.output_reference == oref }) is {
          [reference_token_input] ->
            when
              (
                list.filter(
                  outputs,
                  fn(output) {
                    output.address == reference_token_input.output.address &&
                      quantity_of(
                        output.value,
                        reference_token_policy,
                        ref_token_name,
                      ) == 1
                  },
                ),
                list.filter(
                  inputs,
                  fn(input) {
                    quantity_of(
                      input.output.value,
                      reference_token_policy,
                      user_token_name,
                    ) == 1
                  },
                ),
                list.filter(
                  outputs,
                  fn(output) {
                    quantity_of(
                      output.value,
                      reference_token_policy,
                      user_token_name,
                    ) == 1
                  },
                ),
              )
            is {
              ([reference_token_output], [owner_token_input], [owner_token_output]) ->
                when reference_token_output.datum is {
                  InlineDatum(ref_output_datum) -> {
                    expect new_datum: CIP68Metadata = ref_output_datum

                    and {
                      new_datum.name == new_metadata.name,
                      new_datum.image == new_metadata.image,
                      new_datum.description == new_metadata.description,
                      quantity_of(
                        reference_token_input.output.value,
                        reference_token_policy,
                        ref_token_name,
                      ) == 1,
                      quantity_of(
                        reference_token_output.value,
                        reference_token_policy,
                        ref_token_name,
                      ) == 1,
                      owner_token_input.output.address == owner_token_output.address,
                    }
                  }
                  _ -> False
                }
              _ -> False
            }
          _ -> False
        }
      }

      Burn(token_name) -> {
        let ref_token_name: AssetName = append_bytearray("100", token_name)
        let user_token_name: AssetName = append_bytearray("222", token_name)

        when list.filter(inputs, fn(input) { input.output_reference == oref }) is {
          [reference_token_input] ->
            when list.filter(
              inputs,
              fn(input) {
                quantity_of(
                  input.output.value,
                  reference_token_policy,
                  user_token_name,
                ) == 1
              },
            )
            is {
              [owner_token_input] -> {
                let ref_token_outputs = list.filter(
                  outputs,
                  fn(output) {
                    quantity_of(
                      output.value,
                      reference_token_policy,
                      ref_token_name,
                    ) > 0
                  },
                )

                let user_token_outputs = list.filter(
                  outputs,
                  fn(output) {
                    quantity_of(
                      output.value,
                      reference_token_policy,
                      user_token_name,
                    ) > 0
                  },
                )

                and {
                  quantity_of(
                    reference_token_input.output.value,
                    reference_token_policy,
                    ref_token_name,
                  ) == 1,
                  quantity_of(
                    owner_token_input.output.value,
                    reference_token_policy,
                    user_token_name,
                  ) == 1,
                  list.is_empty(ref_token_outputs),
                  list.is_empty(user_token_outputs),
                  quantity_of(
                    mint,
                    reference_token_policy,
                    ref_token_name,
                  ) == -1,
                  quantity_of(
                    mint,
                    reference_token_policy,
                    user_token_name,
                  ) == -1,
                }
              }
              _ -> False
            }
          _ -> False
        }
      }
    }
  }

  else(_) {
    fail
  }
}
