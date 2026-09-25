# Mapping review: Corporate Tax Transparency
Config version **1**, hash `e791390fb47c87e1403c8fa2ff52d1db5bb7df1d3a1c77e28b2a388dbfebf636`.
Ontology: `4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75`.
Grain: One corporate tax entity's income tax disclosure for one income year in the Income tax details sheet.. Subject: **legal_entity**.
Reader: `{"format": "xlsx", "encoding": "utf-8-sig", "delimiter": ",", "sheet": "Income tax details", "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| ABN | entity.abn | trim, abn | 0.95 | Source dataset_notes describes the reported field as ABN. Exact header: “ABN”; sample values include “94600082111” (row 2) and “83114980880” (row 3). Apply checksum validation; do not derive an ACN. |
| Income year | financial_period.reporting_period | trim | 0.99 | Exact header: “Income year”; sample value “2023-24” (row 2). The dataset is organized by income year; ontology definition retains labels such as 2023-24. |

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
      "extractor_version": "extractor-1:e791390fb47c87e1403c8fa2ff52d1db5bb7df1d3a1c77e28b2a388dbfebf636",
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
      "config_hash": "e791390fb47c87e1403c8fa2ff52d1db5bb7df1d3a1c77e28b2a388dbfebf636",
      "subject_role": "legal_entity",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.88,
        "field_confidence": 0.95
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "id": "480507cf7bb5b5374c07e323179c36191e20444a97fb7ee8e075791d02acd49d"
    },
    {
      "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
      "source_record_id": "3474695ec12ebea61407b45505ee53e8ea9caef1b13d3d7d333f9e889b396072",
      "observed_at": "2025-10-01T21:08:09.091363+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:09.161572+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:e791390fb47c87e1403c8fa2ff52d1db5bb7df1d3a1c77e28b2a388dbfebf636",
      "field": "financial_period.reporting_period",
      "value": "2023-24",
      "source_fields": [
        "Income year"
      ],
      "raw_value": [
        "2023-24"
      ],
      "raw_locator": {
        "snapshot_sha": "6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75",
        "sheet": "Income tax details",
        "row": 2
      },
      "snapshot_id": "7f0f0031650e96d0b1e08eb2fb489dec1a181aa464eae44845ec2de99ac06bf2",
      "config_hash": "e791390fb47c87e1403c8fa2ff52d1db5bb7df1d3a1c77e28b2a388dbfebf636",
      "subject_role": "legal_entity",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.88,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "financial_period",
      "group_id": "f06d5e58584d3a46f770e1c4ff50f4d20e7473a51718d3d4d2ff9862afe62be6",
      "group_name": "tax_reporting_period",
      "id": "ef17d2d7fb68196051b0194675dc5e4e2b79bfb51bbc0dffb864be13fd6a3703"
    },
    {
      "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
      "source_record_id": "6b6e73b96c15a7c981c5b9700f131317a985ef7181491d18b7f37a0a235fe755",
      "observed_at": "2025-10-01T21:08:09.091363+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:09.161572+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:e791390fb47c87e1403c8fa2ff52d1db5bb7df1d3a1c77e28b2a388dbfebf636",
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
      "config_hash": "e791390fb47c87e1403c8fa2ff52d1db5bb7df1d3a1c77e28b2a388dbfebf636",
      "subject_role": "legal_entity",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.88,
        "field_confidence": 0.95
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "id": "aa06a8ace459a0fd6bcbcae71e25d68e411db332e75151700d0f438f75951904"
    },
    {
      "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
      "source_record_id": "6b6e73b96c15a7c981c5b9700f131317a985ef7181491d18b7f37a0a235fe755",
      "observed_at": "2025-10-01T21:08:09.091363+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:09.161572+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:e791390fb47c87e1403c8fa2ff52d1db5bb7df1d3a1c77e28b2a388dbfebf636",
      "field": "financial_period.reporting_period",
      "value": "2023-24",
      "source_fields": [
        "Income year"
      ],
      "raw_value": [
        "2023-24"
      ],
      "raw_locator": {
        "snapshot_sha": "6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75",
        "sheet": "Income tax details",
        "row": 3
      },
      "snapshot_id": "7f0f0031650e96d0b1e08eb2fb489dec1a181aa464eae44845ec2de99ac06bf2",
      "config_hash": "e791390fb47c87e1403c8fa2ff52d1db5bb7df1d3a1c77e28b2a388dbfebf636",
      "subject_role": "legal_entity",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.88,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "financial_period",
      "group_id": "fd734e4c4dc6b813130f207fae9b39e859a57a1554e61061a64bf5db9ee0e553",
      "group_name": "tax_reporting_period",
      "id": "3757bba252b5e3265189c11e5f112ca988cffd4b12355a41ea4b1430da3125c6"
    },
    {
      "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
      "source_record_id": "478023b4f78b677966d69ad48f14c6b4fba74da1454bc291e2433345aef5956c",
      "observed_at": "2025-10-01T21:08:09.091363+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:09.161572+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:e791390fb47c87e1403c8fa2ff52d1db5bb7df1d3a1c77e28b2a388dbfebf636",
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
      "config_hash": "e791390fb47c87e1403c8fa2ff52d1db5bb7df1d3a1c77e28b2a388dbfebf636",
      "subject_role": "legal_entity",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.88,
        "field_confidence": 0.95
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "id": "234067a29b913eb91af5911d6b1350531dc7e6c33836614e61b3eafb10be026c"
    },
    {
      "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
      "source_record_id": "478023b4f78b677966d69ad48f14c6b4fba74da1454bc291e2433345aef5956c",
      "observed_at": "2025-10-01T21:08:09.091363+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:09.161572+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:e791390fb47c87e1403c8fa2ff52d1db5bb7df1d3a1c77e28b2a388dbfebf636",
      "field": "financial_period.reporting_period",
      "value": "2023-24",
      "source_fields": [
        "Income year"
      ],
      "raw_value": [
        "2023-24"
      ],
      "raw_locator": {
        "snapshot_sha": "6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75",
        "sheet": "Income tax details",
        "row": 4
      },
      "snapshot_id": "7f0f0031650e96d0b1e08eb2fb489dec1a181aa464eae44845ec2de99ac06bf2",
      "config_hash": "e791390fb47c87e1403c8fa2ff52d1db5bb7df1d3a1c77e28b2a388dbfebf636",
      "subject_role": "legal_entity",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.88,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "financial_period",
      "group_id": "ed33c53be7ab99eec49f20baba9513d541af3ea3d8db88281daf0a96aa44bee5",
      "group_name": "tax_reporting_period",
      "id": "9f9b5767327d6796044548d71cc0283a7a9112ca203d43d207afbdeffa963aed"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 3; measured/reserved input/output: 20104/3786; calculated cost: 0.007865500000000001.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **Name**: Retained as the raw subject label via subject_label_field. The documentation and header do not establish this label as the registered legal name, so it is not mapped to entity.legal_name.
- **Total income $**: Financial amount has no matching registered ontology concept; do not infer currency or add a target.
- **Taxable income $**: Financial amount has no matching registered ontology concept; blank values must not be interpreted as zero.
- **Tax payable $**: Financial amount has no matching registered ontology concept; blank values must not be interpreted as zero.
- **__unnamed_7**: Unnamed source column; preview cells are blank and no meaning is documented.
- **__unnamed_8**: Unnamed source column; preview cells are blank and no meaning is documented.
- **__unnamed_9**: Unnamed source column; preview cells are blank and no meaning is documented.

## Uncertainties

- Publication timestamp is an envelope-supplied proxy, not evidence of when an individual row or claim changed.
- The supplied documentation says the report names corporate tax entities but does not establish that Name is their registered legal name; the raw label is retained without that assertion.
- Rows are entity-by-income-year disclosures, not evidence of economic or accounting group membership; do not infer corporate groups.
- Income and tax amounts are not mapped because this ontology has no suitable financial-amount concepts and no currency should be inferred. Blank taxable-income or tax-payable cells are not zero claims.
- No row filter is justified by the supplied notes or preview. Eligibility thresholds vary by income year and entity category, and are not encoded as filters.
- The supplied documentation is limited to dataset_notes; no page-numbered report documentation was provided.
- The `legal_entity` subject role is a defensible reading of rows described as corporate tax entities with ABNs, and the source explicitly says the disclosures are not economic/accounting groups. Still, the supplied notes do not describe the detailed legal forms represented, so do not treat that role as evidence that every subject is a company or that `Name` is its registered legal name; the mapping appropriately avoids both claims.
- Validation success and the publication-proxy timestamp policy support implementation, not semantic ground truth. The mapping discloses these limits.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0d406-6e3b-7eb0-9edc-786d3fc79b88/run/01a0d40b-3f61-7852-b196-0c6d7cca97a8?start_time=2026-09-24T15%3A31%3A42.049835%2B00%3A00)