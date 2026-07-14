
/**
 * A single statement about a property relevant to an entity: in dataset X,
 * entity A had property P set to value V, observed between two timestamps.
 *
 * This mirrors the wire format of the Python `Statement.to_dict()`
 * (`StatementDict`), which emits all keys with `null` for unset values.
 * `prop_type` is not part of that serialization but is added by the
 * OpenSanctions statement API and CSV exports, so it is accepted here
 * as an optional extra.
 */
export interface IStatementDatum {
  id?: string | null
  entity_id: string
  canonical_id: string
  prop: string
  prop_type?: string
  schema: string
  value: string
  dataset: string
  lang?: string | null
  original_value?: string | null
  external: boolean
  first_seen?: string | null
  last_seen?: string | null
  origin?: string | null
}
