# Mapping review: Corporate Tax Transparency
Config version **2**, hash `ecb0b5daef0fe0cf8bb71fcdf4d11511df00a8aa462291ae89d9be26e457e9fb`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75`.
Grain: One row per corporate tax entity reported in the Income tax details worksheet. Subject: **legal_entity**.
Reader: `{"format": "xlsx", "encoding": "utf-8-sig", "delimiter": ",", "sheet": "Income tax details", "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| ABN | entity.abn | abn | 0.98 | Dataset notes state that the reports contain the name and ABN for selected corporate tax entities; exact worksheet header 'ABN' and discovery sample Income tax details row 2 value '94600082111'. |

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
      "extractor_version": "extractor-1:ecb0b5daef0fe0cf8bb71fcdf4d11511df00a8aa462291ae89d9be26e457e9fb",
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
      "config_hash": "ecb0b5daef0fe0cf8bb71fcdf4d11511df00a8aa462291ae89d9be26e457e9fb",
      "subject_role": "legal_entity",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "53c363a373e2ad66426c79c1b486c870cc01a87aa1238ba66d12c292b69300e0"
    },
    {
      "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
      "source_record_id": "6b6e73b96c15a7c981c5b9700f131317a985ef7181491d18b7f37a0a235fe755",
      "observed_at": "2025-10-01T21:08:09.091363+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:09.161572+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:ecb0b5daef0fe0cf8bb71fcdf4d11511df00a8aa462291ae89d9be26e457e9fb",
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
      "config_hash": "ecb0b5daef0fe0cf8bb71fcdf4d11511df00a8aa462291ae89d9be26e457e9fb",
      "subject_role": "legal_entity",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "82373bbf6f3e940af840ed0d0c9b6ba720dac7d036ddde0f27aaeb6b297d0a82"
    },
    {
      "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
      "source_record_id": "478023b4f78b677966d69ad48f14c6b4fba74da1454bc291e2433345aef5956c",
      "observed_at": "2025-10-01T21:08:09.091363+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:09.161572+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:ecb0b5daef0fe0cf8bb71fcdf4d11511df00a8aa462291ae89d9be26e457e9fb",
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
      "config_hash": "ecb0b5daef0fe0cf8bb71fcdf4d11511df00a8aa462291ae89d9be26e457e9fb",
      "subject_role": "legal_entity",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "9048be2b361cc2867ee538d652e76be7aa623d58b589e52fb05540f57c598b39"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 5; measured/reserved input/output: 27811/15771; calculated cost: 0.025877949999999997.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **Name**: The publisher labels this column only 'Name' and supplies no current-name indicator or documentation establishing that it is a current registered legal name or trading name; retain the raw identity label through subject_label_field without emitting a canonical name.
- **Total income $**: Financial measure is not represented in the supplied ontology.
- **Taxable income $**: Financial measure is not represented in the supplied ontology; documented blank/unreportable values must not be converted to zero.
- **Tax payable $**: Financial measure is not represented in the supplied ontology; documented blank/unreportable values must not be converted to zero.
- **Income year**: Reporting period is not represented by the supplied ontology and must not be treated as entity.date_registered or observation time.
- **__unnamed_7**: Empty unnamed column present in the supplied worksheet header; no ontology target.
- **__unnamed_8**: Empty unnamed column present in the supplied worksheet header; no ontology target.
- **__unnamed_9**: Empty unnamed column present in the supplied worksheet header; no ontology target.

## Uncertainties

- The source envelope supplies publication_proxy '2025-10-01T21:08:09.091363' and licence 'Creative Commons Attribution 3.0 Australia'; no row-level statement timestamp is provided, so publication_proxy is used for observed_at.
- The source documentation describes selected corporate tax entities and does not establish that Name is a current registered legal name; it is retained only as subject_label_field. No historical/current-name indicator is supplied, so no canonical name is emitted.
- This is not a complete company register. Inclusion in a tax-transparency report does not establish active status, deregistration, liquidation, external administration, entity type beyond the source's reporting description, or a registration date.
- The source notes that entity-level data does not reflect actual economic or accounting groupings; no reporting-group or beneficial-owner relationship is inferred.
- Financial measures and Income year remain unmapped because the supplied ontology has no corresponding fields; blank financial cells remain unknown.
- ABN is validated with the declarative abn operation only. No ACN is derived from an ABN suffix, and no status or legal-name claim is emitted.
- All authority, field-confidence, and linking judgements are provisional and require human review.
- The mapping is deliberately partial: it maps only ABN and preserves Name as a non-canonical subject label. This is semantically cautious because the source says only 'Name' and does not establish whether the value is a current registered legal name, trading name, or historical name.
- The legal_entity subject_role is somewhat stronger than the supplied name evidence alone, but the dataset documentation explicitly describes corporate tax entities and the mapped claim is only the ABN; no unsupported name or legal-status field is emitted. The source also warns that data does not reflect economic/accounting groupings, and no reporting group is inferred.
- No status, registration date, address, licence, or financial ontology fields are invented. Income year is correctly not used as observation time or registration date; publication_proxy is an allowed observed_at policy and is disclosed as such.
- ABN validation relies on the authoritative declarative operation, including checksum behavior. No ACN is suffix-derived. The validation result supports parsing/envelope behavior but is not semantic ground truth, as disclosed.
- The source documentation field is empty in the supplied source object, so conclusions rely on dataset_notes, raw headers/records, and supplied analysis rather than independently checking a linked documentation page.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b8ed-c2d2-7b32-a8bb-bba472483463/run/01a0b8ee-0f2e-7452-806a-ace1d8797184?start_time=2026-09-19T09%3A10%3A04.334150%2B00%3A00)