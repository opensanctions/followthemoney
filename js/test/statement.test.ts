import { IStatementDatum } from '../src/followthemoney'

// Shape emitted by Python Statement.to_dict(): all keys present,
// null for unset optionals, no prop_type.
const ftmStatement: IStatementDatum = {
  canonical_id: 'Q7747',
  entity_id: 'ofac-9914',
  prop: 'name',
  schema: 'Person',
  value: 'Vladimir Vladimirovich PUTIN',
  dataset: 'us_ofac_sdn',
  lang: null,
  original_value: null,
  first_seen: '2021-01-01T00:00:00',
  last_seen: '2023-06-01T00:00:00',
  external: false,
  origin: null,
  id: '81cf3b47f28f8ac8d80cad84d558a17dcbe0973b'
}

// Shape returned by the OpenSanctions statement API, which adds
// prop_type and omits null keys.
const apiStatement: IStatementDatum = {
  id: '81cf3b47f28f8ac8d80cad84d558a17dcbe0973b',
  entity_id: 'ofac-9914',
  canonical_id: 'Q7747',
  prop: 'name',
  prop_type: 'name',
  schema: 'Person',
  dataset: 'us_ofac_sdn',
  value: 'Vladimir Vladimirovich PUTIN',
  external: false,
  first_seen: '2021-01-01T00:00:00',
  last_seen: '2023-06-01T00:00:00'
}

describe('ftm/IStatementDatum', () => {
  it('covers the Python statement wire format', function() {
    expect(ftmStatement.canonical_id).toBe('Q7747')
    expect(ftmStatement.prop_type).toBeUndefined()
  })
  it('covers the statement API response format', function() {
    expect(apiStatement.prop_type).toBe('name')
  })
})
