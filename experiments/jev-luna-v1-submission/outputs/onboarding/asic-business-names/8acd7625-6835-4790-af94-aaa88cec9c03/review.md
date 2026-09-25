# Mapping review: ASIC - Business Names Dataset
Config version **2**, hash `3b4157f160992eec5242a4f2de783628e303e02f85b13f2be1f4f07833de9f98`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `24cfce11f830019ba0760d6d21c83562ea37d944f2a2183b15cbcabcf68aa6d9`.
Grain: One row per ASIC Business Names Register business-name registration record, representing a business-name record rather than necessarily a legal entity. Subject: **business_name_holder**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": "\t", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| BN_NAME | entity.trading_name | trim | 0.96 | ASIC Business Names Dataset Help File, p. 7, data dictionary: BN_NAME is “A name used, or to be used, in relation to one or more businesses” and is the Business Name as it appears on ASIC’s Business Names register. ASIC Help File, p. 2, states the dataset contains currently registered business names and deregistered business names for the preceding 12 months; exact header/sample evidence: BN_NAME values such as “  Plumbing Gas and Solar” and BN_STATUS “Registered”. The Registered filter restricts this emitted trading-name claim to records supported as current by ASIC’s status indicator. |

## Before / after

```json
{
  "raw": [
    {
      "record_id": "ed458a0fad054468fc459a474924619954ab0ef70522f13a5a8becb6a9342555",
      "locator": {
        "snapshot_sha": "24cfce11f830019ba0760d6d21c83562ea37d944f2a2183b15cbcabcf68aa6d9",
        "sheet": "csv",
        "row": 2
      },
      "values": {
        "REGISTER_NAME": "BUSINESS NAMES",
        "BN_NAME": "   Plumbing Gas and Solar",
        "BN_STATUS": "Registered",
        "BN_REG_DT": "09/05/2013",
        "BN_CANCEL_DT": "",
        "BN_STATE_NUM": "",
        "BN_STATE_OF_REG": "",
        "BN_ABN": "30947976159"
      }
    },
    {
      "record_id": "62dfe8fc3fdfc76a20f79f1d8b42e0d3c034d7f4177111a5101fae503d625f2a",
      "locator": {
        "snapshot_sha": "24cfce11f830019ba0760d6d21c83562ea37d944f2a2183b15cbcabcf68aa6d9",
        "sheet": "csv",
        "row": 3
      },
      "values": {
        "REGISTER_NAME": "BUSINESS NAMES",
        "BN_NAME": "  Bruce Ward Training",
        "BN_STATUS": "Registered",
        "BN_REG_DT": "12/04/2018",
        "BN_CANCEL_DT": "",
        "BN_STATE_NUM": "",
        "BN_STATE_OF_REG": "",
        "BN_ABN": "16897173642"
      }
    }
  ],
  "observations": [
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "ed458a0fad054468fc459a474924619954ab0ef70522f13a5a8becb6a9342555",
      "observed_at": "2026-09-15T20:36:19.202924+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:58.295938+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:3b4157f160992eec5242a4f2de783628e303e02f85b13f2be1f4f07833de9f98",
      "field": "entity.trading_name",
      "value": "Plumbing Gas and Solar",
      "source_fields": [
        "BN_NAME"
      ],
      "raw_value": [
        "   Plumbing Gas and Solar"
      ],
      "raw_locator": {
        "snapshot_sha": "24cfce11f830019ba0760d6d21c83562ea37d944f2a2183b15cbcabcf68aa6d9",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "da44f27f1ffc7a414929ea349dcd45e0549f52b332b1909db335c751aa445e6a",
      "config_hash": "3b4157f160992eec5242a4f2de783628e303e02f85b13f2be1f4f07833de9f98",
      "subject_role": "business_name_holder",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "d565a2035ef9d11184a437029cfcd41ef9af9dabad481df695e9dc409d855320"
    },
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "62dfe8fc3fdfc76a20f79f1d8b42e0d3c034d7f4177111a5101fae503d625f2a",
      "observed_at": "2026-09-15T20:36:19.202924+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:58.295938+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:3b4157f160992eec5242a4f2de783628e303e02f85b13f2be1f4f07833de9f98",
      "field": "entity.trading_name",
      "value": "Bruce Ward Training",
      "source_fields": [
        "BN_NAME"
      ],
      "raw_value": [
        "  Bruce Ward Training"
      ],
      "raw_locator": {
        "snapshot_sha": "24cfce11f830019ba0760d6d21c83562ea37d944f2a2183b15cbcabcf68aa6d9",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "da44f27f1ffc7a414929ea349dcd45e0549f52b332b1909db335c751aa445e6a",
      "config_hash": "3b4157f160992eec5242a4f2de783628e303e02f85b13f2be1f4f07833de9f98",
      "subject_role": "business_name_holder",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "b4f88709eaa24ef8ddb81999bb97574cab82198f223f332dbc77c74002142f6c"
    },
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "9751c2e6805f12318cc89cc542f918dbc63e73f56eb393b8653b770c8dcde409",
      "observed_at": "2026-09-15T20:36:19.202924+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:58.295938+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:3b4157f160992eec5242a4f2de783628e303e02f85b13f2be1f4f07833de9f98",
      "field": "entity.trading_name",
      "value": "Elite Power Services",
      "source_fields": [
        "BN_NAME"
      ],
      "raw_value": [
        "  Elite Power Services"
      ],
      "raw_locator": {
        "snapshot_sha": "24cfce11f830019ba0760d6d21c83562ea37d944f2a2183b15cbcabcf68aa6d9",
        "sheet": "csv",
        "row": 4
      },
      "snapshot_id": "da44f27f1ffc7a414929ea349dcd45e0549f52b332b1909db335c751aa445e6a",
      "config_hash": "3b4157f160992eec5242a4f2de783628e303e02f85b13f2be1f4f07833de9f98",
      "subject_role": "business_name_holder",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "5d4a4b5fac3a94d802a211c112c9bffcf4e77a7c7967ece1201468b3f3a515f8"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 5; measured/reserved input/output: 44763/16091; calculated cost: 0.030499949999999998.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **REGISTER_NAME**: Register label (“BUSINESS NAMES”), not a legal entity name, trading name, identifier, address, or ontology status; ASIC Help File p. 7 defines it as the name of the register.
- **BN_STATUS**: Describes registration status of the business name, not the status of a legal entity. It is used only as an exact filter to retain BN_NAME records marked Registered; no business-name cancellation or status is emitted as entity status. ASIC Help File p. 7 defines BN_STATUS as Registration Status for the Business Name and documents Registered/Cancelled.
- **BN_REG_DT**: Business-name start/registration date, not legal-entity registration date; therefore not mapped to entity.date_registered. ASIC Help File p. 8 defines BN_REG_DT as the date by which the Business Name started; exact header/sample evidence: BN_REG_DT “09/05/2013”.
- **BN_CANCEL_DT**: Date the business name ceased, not legal-entity deregistration date; the ontology has no business-name cancellation-date target. ASIC Help File p. 8 states it is shown when the Business Name has been cancelled and otherwise NULL.
- **BN_STATE_NUM**: Former State Number allocated by a previous business-names regulator before 28 May 2012; no ontology target and not a current legal-entity identifier. ASIC Help File p. 8.
- **BN_STATE_OF_REG**: Previous state of registration under a former business-names regulator, not a current entity or address state; no suitable ontology target. ASIC Help File p. 8 documents the historical field and allowable state abbreviations.
- **BN_ABN**: Although ASIC Help File p. 9 documents this as an ABN field, it may be NULL when suppressed, multiple, or unavailable, and this business-name-register row does not establish legal-entity ownership or identity. Under the supplied provenance semantics, the identifier remains unmapped when holder/ownership is unsupported. No ACN is inferred from an ABN suffix; no ARBN/type qualifier is present in this source. Exact header/sample evidence: BN_ABN values such as “30947976159”.

## Uncertainties

- This is an ASIC Business Names Register snapshot, not a company register; a row is not necessarily a legal entity record.
- BN_NAME is retained as a raw subject label and mapped only to a current-status-filtered trading-name observation; no legal-name or ownership claim is made.
- Cancelled or otherwise non-Registered rows remain represented by the source snapshot but produce no canonical trading-name observation under the exact Registered filter.
- No legal entity, company type, branch, address, licence, or reporting-group fields are supplied.
- BN_ABN is not emitted because the source does not support safe holder/legal-entity identity linkage; no ACN or ARBN claim is made.
- ASIC states the dataset includes currently registered business names and deregistered business names for the preceding 12 months (Help File p. 2); coverage outside that window is not represented.
- The supplied publication timestamp 2026-09-15T20:36:19.202924 is used by the source envelope as an allowed publication proxy, not as a row-change timestamp.
- All authority and field-confidence scores are provisional judgements and require human review.
- The mapping is deliberately partial: it emits only BN_NAME as entity.trading_name for rows with BN_STATUS exactly Registered. This is semantically supported as a current business-name claim, not a legal-name, holder, licence, branch, reporting-group, or legal-entity-status claim.
- The source documents that BN_NAME is a name used in relation to one or more businesses; calling the target entity.trading_name is acceptable only under the stated unknown/unsupported ownership semantics and should not be read as asserting that the label belongs to a resolved legal entity.
- Trimming leading whitespace is a supported normalization and does not erase meaningful documented name content in the supplied evidence, but the raw value remains available through provenance.
- BN_ABN is correctly left unmapped: although documented as an ABN, the row does not establish holder/legal-entity ownership, and the source documents suppression, multiple-ABN, and unavailable cases. No unsupported identifier linkage is asserted.
- BN_STATUS is correctly used as an exact membership filter rather than mapped to entity.status. BN_REG_DT and BN_CANCEL_DT are correctly excluded because they concern the business name, not necessarily the legal entity.
- The dataset is a point-in-time snapshot containing current registrations and deregistered names for the preceding 12 months; cancellation/history coverage is therefore limited. The publication proxy timestamp is an allowed observation-time policy, not row-change time.
- No source addresses, service locations, licence numbers, legal names, entity types, reporting groups, ACNs, or renewal date are supplied. The removed BN_RENEW_DT should not be expected or mapped.
- The supplied exploratory Python failed with NameError, but raw discovery records, documentation, mapping, and validator evidence were still available; this limits independent exploration only and is not itself a semantic defect.
- Confidence values are disclosed as provisional judgements, not measured probabilities.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b8ee-3029-7b21-8b39-0ea5321e27ed/run/01a0b8ee-aad5-7381-a8ce-4e11c662fc8f?start_time=2026-09-19T09%3A10%3A44.181717%2B00%3A00)