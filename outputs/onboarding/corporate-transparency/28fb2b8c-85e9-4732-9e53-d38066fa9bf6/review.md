# Mapping review: Corporate Tax Transparency
Config version **1**, hash `ba4c16c1b8df7f29297ac281e87ad07d0093ff9e4afdbb031cb034041f210523`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75`.
Grain: One row per corporate tax entity reported in the Income tax details worksheet. Subject: **legal_entity**.
Reader: `{"format": "xlsx", "encoding": "utf-8-sig", "delimiter": ",", "sheet": "Income tax details", "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| ABN | entity.abn | abn | 0.98 | Dataset notes state the reports contain the name and ABN for selected corporate tax entities; exact worksheet header 'ABN'; discovery sample Income tax details row 2 has ABN '94600082111'. The declarative abn operation validates the identifier and does not derive an ACN from an ABN suffix. |

## Before / after

```json
{
  "raw": [
    {
      "record_id": "3474695ec12ebea61407b45505ee53e8ea9caef1b13d3d7d333f9e889b396072",
      "locator": {
        "snapshot_sha": "6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75",
        "sheet": "Income tax details",
        "row": 2
      },
      "values": {
        "Name": "1 MENDS STREET PTY LTD",
        "ABN": "94600082111",
        "Total income $": "159074147",
        "Taxable income $": "",
        "Tax payable $": "",
        "Income year": "2023-24",
        "__unnamed_7": "",
        "__unnamed_8": "",
        "__unnamed_9": ""
      }
    },
    {
      "record_id": "6b6e73b96c15a7c981c5b9700f131317a985ef7181491d18b7f37a0a235fe755",
      "locator": {
        "snapshot_sha": "6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75",
        "sheet": "Income tax details",
        "row": 3
      },
      "values": {
        "Name": "1884 PTY LIMITED",
        "ABN": "83114980880",
        "Total income $": "337911962",
        "Taxable income $": "6347804",
        "Tax payable $": "1904341",
        "Income year": "2023-24",
        "__unnamed_7": "",
        "__unnamed_8": "",
        "__unnamed_9": ""
      }
    }
  ],
  "observations": [
    {
      "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
      "source_record_id": "3474695ec12ebea61407b45505ee53e8ea9caef1b13d3d7d333f9e889b396072",
      "observed_at": "2025-10-01T21:08:09.091363+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:09.161572+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:ba4c16c1b8df7f29297ac281e87ad07d0093ff9e4afdbb031cb034041f210523",
      "field": "entity.abn",
      "value": "94600082111",
      "source_fields": [
        "ABN"
      ],
      "raw_value": [
        "94600082111"
      ],
      "raw_locator": {
        "snapshot_sha": "6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75",
        "sheet": "Income tax details",
        "row": 2
      },
      "snapshot_id": "7f0f0031650e96d0b1e08eb2fb489dec1a181aa464eae44845ec2de99ac06bf2",
      "config_hash": "ba4c16c1b8df7f29297ac281e87ad07d0093ff9e4afdbb031cb034041f210523",
      "subject_role": "legal_entity",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "728975045eba831f6e3c77e87db05c1d90dbab5c64f682e98ee638fd568f9b5a"
    },
    {
      "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
      "source_record_id": "6b6e73b96c15a7c981c5b9700f131317a985ef7181491d18b7f37a0a235fe755",
      "observed_at": "2025-10-01T21:08:09.091363+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:09.161572+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:ba4c16c1b8df7f29297ac281e87ad07d0093ff9e4afdbb031cb034041f210523",
      "field": "entity.abn",
      "value": "83114980880",
      "source_fields": [
        "ABN"
      ],
      "raw_value": [
        "83114980880"
      ],
      "raw_locator": {
        "snapshot_sha": "6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75",
        "sheet": "Income tax details",
        "row": 3
      },
      "snapshot_id": "7f0f0031650e96d0b1e08eb2fb489dec1a181aa464eae44845ec2de99ac06bf2",
      "config_hash": "ba4c16c1b8df7f29297ac281e87ad07d0093ff9e4afdbb031cb034041f210523",
      "subject_role": "legal_entity",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "12e0fd0171e80b7d0c4bbd2bfc81c729a1a779ce57048d2268e56570f55d1b3e"
    },
    {
      "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
      "source_record_id": "478023b4f78b677966d69ad48f14c6b4fba74da1454bc291e2433345aef5956c",
      "observed_at": "2025-10-01T21:08:09.091363+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:09.161572+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:ba4c16c1b8df7f29297ac281e87ad07d0093ff9e4afdbb031cb034041f210523",
      "field": "entity.abn",
      "value": "71604999706",
      "source_fields": [
        "ABN"
      ],
      "raw_value": [
        "71604999706"
      ],
      "raw_locator": {
        "snapshot_sha": "6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75",
        "sheet": "Income tax details",
        "row": 4
      },
      "snapshot_id": "7f0f0031650e96d0b1e08eb2fb489dec1a181aa464eae44845ec2de99ac06bf2",
      "config_hash": "ba4c16c1b8df7f29297ac281e87ad07d0093ff9e4afdbb031cb034041f210523",
      "subject_role": "legal_entity",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "d31bbbcb472c0686f0ba7b183f0acd3a125b2bad8088faec52e2b8e67c803280"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 2; measured/reserved input/output: 12215/1475; calculated cost: 0.00482375.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **Name**: Exact worksheet header 'Name' and discovery sample row 2 value '1 MENDS STREET PTY LTD' provide an identity label, but the supplied source has no current-name indicator and does not document whether it is a current registered legal name, trading name, or historical name. Retained through subject_label_field only; not emitted as a canonical name.
- **Total income $**: Exact worksheet header 'Total income $' and discovery sample row 2 value '159074147' identify a financial measure with no corresponding field in the supplied ontology.
- **Taxable income $**: Exact worksheet header 'Taxable income $' and discovery sample row 2 is blank; this financial measure has no corresponding ontology field. Documented blank or unreportable values are not converted to zero.
- **Tax payable $**: Exact worksheet header 'Tax payable $' and discovery sample row 2 is blank; this financial measure has no corresponding ontology field. Documented blank or unreportable values are not converted to zero.
- **Income year**: Exact worksheet header 'Income year' and discovery sample row 2 value '2023-24' identify a reporting period, not entity.date_registered or observation time; no corresponding ontology field exists.
- **__unnamed_7**: Exact supplied worksheet header '__unnamed_7' is an empty unnamed column with no documented meaning or ontology target.
- **__unnamed_8**: Exact supplied worksheet header '__unnamed_8' is an empty unnamed column with no documented meaning or ontology target.
- **__unnamed_9**: Exact supplied worksheet header '__unnamed_9' is an empty unnamed column with no documented meaning or ontology target.

## Uncertainties

- The source envelope supplies publication_proxy '2025-10-01T21:08:09.091363' and licence 'Creative Commons Attribution 3.0 Australia'; no row-level statement timestamp is supplied, so publication_proxy is used for observed_at.
- No publisher current-name indicator is present. Name is retained only as subject_label_field; no canonical current legal or trading name is emitted, and historical names are not asserted as current.
- The tax-transparency inclusion criteria and ABN do not establish active status, deregistration, liquidation, external administration, registration date, address, or an ontology legal entity type. No such claims are made.
- No ACN is mapped or inferred from an ABN suffix. Only the documented ABN column is mapped with the abn validation operation.
- The source describes entity-level tax data and does not establish economic or accounting groupings; no reporting group, ownership, or beneficial-owner relationship is inferred.
- Financial measures and Income year are not represented in the supplied ontology and remain unmapped; blank financial cells remain unknown rather than zero.
- The supplied documentation array is empty; evidence is limited to dataset_notes, exact worksheet headers, discovery samples, and supplied ontology and engine semantics.
- Authority, field-confidence, and linking judgements are provisional and require human review.
- The mapping is deliberately partial: it maps only validated ABN and retains Name as a subject label, without asserting legal_name or trading_name. This is appropriate because the supplied source notes and samples do not establish name semantics or current/historic status.
- The row grain and legal-entity subject role are plausible for the Income tax details sheet, and the mapping does not infer reporting groups, ownership, branches, addresses, status, registration dates, ACNs, or entity type.
- The publication timestamp is used as an explicitly disclosed observed_at proxy; it is not treated as a row-change timestamp. Licence and envelope provenance are supplied by engine semantics.
- Financial measures, income year, and unnamed columns remain unmapped because the ontology has no corresponding fields or documented meanings. Blank financial cells are not converted to zero.
- The source documentation array is empty and the discovery preview is limited, so authority and broader workbook structure remain human-review limitations. The discovery evidence includes valid-looking ABNs and validation passed, but this is not semantic proof or link precision.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b8f1-1b0a-7281-9935-7ce5003877c5/run/01a0b8f2-316e-7a91-9c90-cdd7810f87c7?start_time=2026-09-19T09%3A14%3A35.246433%2B00%3A00)