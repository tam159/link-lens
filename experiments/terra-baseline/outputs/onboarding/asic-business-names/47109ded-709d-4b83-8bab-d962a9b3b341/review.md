# Mapping review: ASIC - Business Names Dataset
Config version **2**, hash `473d003d207ab074f567f1f2b2551d9d1fbe2d0c23d73a37cea8433392c77787`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `24cfce11f830019ba0760d6d21c83562ea37d944f2a2183b15cbcabcf68aa6d9`.
Grain: One published ASIC Business Names Register row describing one business name and its business-name registration attributes in a snapshot; it does not identify a legal entity or establish an ABN-holder relationship.. Subject: **unknown**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": "\t", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| BN_NAME | entity.trading_name | trim | 0.93 | Help file p.7 defines BN_NAME as a name used, or to be used, in relation to one or more businesses and as it appears on ASIC's Business Names register. Sample rows show whitespace-padded business-name labels, e.g. '   Plumbing Gas and Solar'. |

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
      "extractor_version": "extractor-1:473d003d207ab074f567f1f2b2551d9d1fbe2d0c23d73a37cea8433392c77787",
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
      "config_hash": "473d003d207ab074f567f1f2b2551d9d1fbe2d0c23d73a37cea8433392c77787",
      "subject_role": "unknown",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.93
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "78679edf09aeb289ca3d288285426c993c2941c937d47c49996c3fedd6bc30de"
    },
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "62dfe8fc3fdfc76a20f79f1d8b42e0d3c034d7f4177111a5101fae503d625f2a",
      "observed_at": "2026-09-15T20:36:19.202924+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:58.295938+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:473d003d207ab074f567f1f2b2551d9d1fbe2d0c23d73a37cea8433392c77787",
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
      "config_hash": "473d003d207ab074f567f1f2b2551d9d1fbe2d0c23d73a37cea8433392c77787",
      "subject_role": "unknown",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.93
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "8a898943780a2973230d6e506bd72cbe39e36fc2ffca71b28bfe6289295ee25a"
    },
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "9751c2e6805f12318cc89cc542f918dbc63e73f56eb393b8653b770c8dcde409",
      "observed_at": "2026-09-15T20:36:19.202924+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:58.295938+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:473d003d207ab074f567f1f2b2551d9d1fbe2d0c23d73a37cea8433392c77787",
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
      "config_hash": "473d003d207ab074f567f1f2b2551d9d1fbe2d0c23d73a37cea8433392c77787",
      "subject_role": "unknown",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.93
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "1a4947cedfacdde6be3b9ef93178f63a32c154b9685dfdb67260b5c088a62329"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 5; measured/reserved input/output: 51928/4708; calculated cost: None.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **REGISTER_NAME**: Help file p.7 defines it as the name of the register, not an entity attribute. It is BUSINESS NAMES in all 300 discovery rows.
- **BN_STATUS**: Help file p.7 defines status of the business-name registration, not legal-entity status. Discovery observes Registered and Deregistered; no entity.status conversion is justified.
- **BN_REG_DT**: Help file p.8 defines the date by which the business name started. This is not company/legal-entity date_registered.
- **BN_CANCEL_DT**: Help file p.8 defines the date by which the business name ceased. No canonical business-name cancellation-date field exists, and it does not establish entity deregistration.
- **BN_STATE_NUM**: Help file p.8 defines a former state business-name registration number. No canonical field represents this historic business-name identifier; retain raw text externally without numeric coercion or zero-padding.
- **BN_STATE_OF_REG**: Help file p.8 defines the previous state in which the business name was registered. It is neither an entity address nor an entity jurisdiction field.
- **BN_ABN**: Help file p.9 identifies this value as an ABN but does not explicitly state that it identifies the holder/legal entity for the BN_NAME row. It is nullable for documented former-regulator, multiple-ABN, and suppressed-ABN cases. Mapping it alongside BN_NAME would assert an unsupported business-name-to-holder relationship.

## Uncertainties

- ASIC describes this as a selective, point-in-time snapshot of its Business Names Register, containing currently registered business names and deregistered business names for 12 months (help file p.2). It is not a company or business-name-holder register extract.
- The source has no stable business-name registration identifier and supplies no explicit holder/legal-entity name or holder relationship. BN_ABN therefore remains unmapped rather than being treated as the identity of the unknown subject.
- BN_NAME is mapped only as a trading name; it is not mapped as entity.legal_name. The untransformed raw label is retained through subject_label_field.
- No filter is applied: documentation describes the published snapshot scope, but does not provide a condition that safely selects legal entities or current names for this ontology.
- The source envelope publication timestamp is a publication proxy, not a row-level registration, cancellation, or change timestamp.
- All authority, source-reliability, and field-confidence scores are provisional uncalibrated judgements requiring human review.
- The mapping is intentionally partial: it emits only `BN_NAME` as `entity.trading_name` while declaring the subject role unknown. This avoids asserting that a business-name record is itself a legal entity or that the name is a legal name.
- `BN_ABN` is conservatively unmapped. The help file identifies it as an ABN but, in the supplied documentation, does not explicitly define it as the holder/legal-entity identifier for the business-name row. It is also nullable for documented multiple-ABN, former-regulator, and suppression cases. No relationship or entity-identity assertion is made.
- Business-name status and dates are correctly left unmapped. They concern the business-name registration, not entity status or entity registration. The discovery sample contains `Deregistered`, whereas the data dictionary describes `Cancelled`, further supporting the decision not to translate these values into the entity-status enum.
- The map must not be read as evidence that all emitted names are current. The documented snapshot includes currently registered names and deregistered names for 12 months, and no filter distinguishes them. It also supplies no historic-name relationship; registration and cancellation dates remain raw/unmapped.
- No legal name, entity type, address/service location, branch, licence, reporting group, or legal-holder mapping is available from the mapped data. These are appropriately disclosed rather than fabricated.
- The deterministic source-record identifier is necessarily extractor-constructed because the source has no supplied row key. It is traceable to the snapshot locator, but must not be represented as an ASIC business-name registration identifier.
- The CKAN timestamp is correctly described as a publication proxy rather than a row-level observed/change timestamp. The timezone assumption should remain explicitly documented.
- `REGISTER_NAME` being constant in the 300-row discovery sample does not establish a dataset-wide invariant, but it is unmapped and therefore creates no unsupported constant claim. Confidence scores are explicitly uncalibrated judgments.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b208-8c81-7ea2-a2b3-5a150d01eddf/run/01a0b209-7235-7942-94e0-a23c20b10290?start_time=2026-09-18T01%3A02%3A38.645096%2B00%3A00)