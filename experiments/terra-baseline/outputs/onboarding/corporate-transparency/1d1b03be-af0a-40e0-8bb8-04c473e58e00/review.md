# Mapping review: Corporate Tax Transparency
Config version **2**, hash `f81993ff7872eb550477a77b15d2b60086438db750aa98e563acc033d26a4f36`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75`.
Grain: One income-tax disclosure row for a named corporate tax entity and stated income year.. Subject: **unknown**.
Reader: `{"format": "xlsx", "encoding": "utf-8-sig", "delimiter": ",", "sheet": "Income tax details", "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| ABN | entity.abn | digits, abn | 0.94 | ATO dataset notes state reports contain the ABN for corporate tax entities; exact sheet header is “ABN”; row 2 sample is 94600082111. |

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
      "extractor_version": "extractor-1:f81993ff7872eb550477a77b15d2b60086438db750aa98e563acc033d26a4f36",
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
      "config_hash": "f81993ff7872eb550477a77b15d2b60086438db750aa98e563acc033d26a4f36",
      "subject_role": "unknown",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.82,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "4db49f0369c9690cfb0a7573ed2a7afa59cd68ab0b26104ed562015c2f0ebe99"
    },
    {
      "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
      "source_record_id": "6b6e73b96c15a7c981c5b9700f131317a985ef7181491d18b7f37a0a235fe755",
      "observed_at": "2025-10-01T21:08:09.091363+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:09.161572+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:f81993ff7872eb550477a77b15d2b60086438db750aa98e563acc033d26a4f36",
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
      "config_hash": "f81993ff7872eb550477a77b15d2b60086438db750aa98e563acc033d26a4f36",
      "subject_role": "unknown",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.82,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "728855ec606612ff40d84543b5e1cdcf133f61f7c634991b43dd2a798e858775"
    },
    {
      "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
      "source_record_id": "478023b4f78b677966d69ad48f14c6b4fba74da1454bc291e2433345aef5956c",
      "observed_at": "2025-10-01T21:08:09.091363+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:09.161572+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:f81993ff7872eb550477a77b15d2b60086438db750aa98e563acc033d26a4f36",
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
      "config_hash": "f81993ff7872eb550477a77b15d2b60086438db750aa98e563acc033d26a4f36",
      "subject_role": "unknown",
      "source_kind": "tax_disclosure",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.82,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "efeb35cb38cb2b6d5a5d1265cdfccf7ca3a009516cba00d194af3a4b022cc19a"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 5; measured/reserved input/output: 39343/4029; calculated cost: None.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **Name**: Retained only as subject_label_field. ATO dataset notes say the report contains a name, but do not establish it as a registered legal name, trading name, or other canonical name.
- **Total income $**: Tax-disclosure measure with no corresponding canonical field in the supplied ontology; header is “Total income $”.
- **Taxable income $**: Tax-disclosure measure with no corresponding canonical field in the supplied ontology; header is “Taxable income $”.
- **Tax payable $**: Tax-disclosure measure with no corresponding canonical field in the supplied ontology; header is “Tax payable $”.
- **Income year**: Disclosure reporting-period field with no corresponding canonical field; it is not an entity registration date. Header is “Income year”; sample rows show 2023-24.
- **__unnamed_7**: Unnamed trailing column; supplied rows 2–9 are empty and there is no semantic header or canonical field.
- **__unnamed_8**: Unnamed trailing column; supplied rows 2–9 are empty and there is no semantic header or canonical field.
- **__unnamed_9**: Unnamed trailing column; supplied rows 2–9 are empty and there is no semantic header or canonical field.

## Uncertainties

- Subject role is unknown: ATO documentation describes rows as corporate tax entities and does not establish that each tax subject is a legal entity in this ontology. No legal-entity, reporting-group, parent, branch, or licence-holder relationship is asserted.
- The Name field is retained as the raw subject label only; it is not mapped to legal name or trading name.
- ABN is checksum-validated after conservative digits normalization. No ACN is inferred from any ABN suffix.
- No row filter is encoded: supplied notes establish disclosure content and thresholds but do not provide a row-validity/completeness rule supporting exclusion. Empty or invalid ABN values emit no ABN observation under the field condition.
- Publication proxy is used because the selected sheet has no row-level statement datetime. The source-envelope publication timestamp is not the income-year date or an entity fact date.
- Tax measures and income year have no fields in this ontology subset. Blank tax cells are not converted to zero.
- Only the frozen Income tax details sheet is covered. The analysis notes a separate PRRT details sheet at a different grain that requires separate onboarding.
- Authority and confidence scores are provisional, uncalibrated judgements requiring human review.
- The provided previous mapping itself declares `subject_role: unknown`; that is semantically appropriate for this source. A conflicting embedded `semantic_feedback` refers to a `subject_role: legal_entity`, but that classification is not present in the actual mapping or output examples under review. No change is required on that point.
- The source supports ABN as the identifier of the disclosed corporate tax entity, but does not establish that the tax subject is a legal entity in the ontology sense. Retaining an unknown subject role and emitting only the direct ABN observation avoids overclaiming.
- `Name` is correctly retained only as a raw subject label. Documentation and sampled rows do not establish it as a registered legal name, trading name, current name, or historical name; it should remain unmapped to canonical name fields.
- The record grain is correctly limited to one income-tax disclosure row for the stated ABN and income year. It must not imply a parent, consolidated/reporting group, branch, licence holder, service location, address, registration date, or entity status.
- The selected sheet contains no ontology destination for total income, taxable income, tax payable, or income year. Leaving these fields unmapped is appropriate. In particular, blanks must not be converted into zero values; the stated interpretation should remain source context, not a generated numeric claim.
- `observed_at` is a disclosed CKAN modification/publication proxy, not the income-year date, entity-change date, or row-level assertion time. This is an acceptable limitation given the available source data, provided the basis remains attached as shown.
- ABN digit normalization plus checksum validation is a reasonable L1 parse/validation step, but it should preserve the raw value/provenance and not cause ACN inference. The output examples show raw values and exact row locators.
- Source reliability 0.82 and field confidence 0.94 are unsupported by the publisher but are explicitly disclosed as uncalibrated internal judgements. They are acceptable as such, not as measured evidence. No link confidence is necessary for a direct source identifier observation.
- Coverage is correctly restricted to `Income tax details`; the separately noted PRRT sheet should not be combined with this extraction without a separate mapping and explicit grain policy.
- The raw discovery preview supports the stated headers and 11-digit ABN values. The unnamed trailing columns are empty in the shown samples and are appropriately unmapped.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b208-8cb0-7d10-84db-80a95f0abcab/run/01a0b20c-fce0-7b51-be95-0ab60e80fbd1?start_time=2026-09-18T01%3A06%3A30.752074%2B00%3A00)