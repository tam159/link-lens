# Mapping review: ASIC - Australian Financial Services Licensee Dataset
Config version **2**, hash `8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f`.
Grain: One row per current Australian Financial Services licence/register entry, stating the licence holder label, optional ABN or ACN, licence issue date, principal business address components, and licence conditions. Subject: **licence_holder**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| AFS_LIC_ABN_ACN | entity.abn | digits, abn | 0.98 | Help File p.8 data dictionary: AFS_LIC_ABN_ACN is the licensee's ABN or ACN; the field displays an ABN if the licensee has provided one. |
| AFS_LIC_ABN_ACN | entity.acn | digits, acn | 0.98 | Help File p.8 data dictionary: AFS_LIC_ABN_ACN is the licensee's ABN or ACN; the field displays an ACN if no ABN is provided. The independent acn validation does not derive an ACN from an ABN suffix. |
| AFS_LIC_ADD_LOCAL | address.locality | trim | 0.99 | Help File p.9 exact field header AFS_LIC_ADD_LOCAL: locality from the current principal business address; blank fields represent records where the address could not be validated. |
| AFS_LIC_ADD_STATE | address.state | trim, uppercase, enum | 0.99 | Help File p.10 exact field header AFS_LIC_ADD_STATE: state from the current principal business address. |
| AFS_LIC_ADD_PCODE | address.postcode | trim, postcode | 0.97 | Help File p.10 exact field header AFS_LIC_ADD_PCODE: postcode from the current principal business address; Help File p.12 change log: outside-Australia addresses display null rather than zero. |
| AFS_LIC_ADD_COUNTRY | address.country | trim | 0.98 | Help File p.10 exact field header AFS_LIC_ADD_COUNTRY: country of the principal business address; countries outside Australia are set to the literal value International. |

## Before / after

```json
{
  "raw": [
    {
      "record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "locator": {
        "snapshot_sha": "6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f",
        "sheet": "csv",
        "row": 2
      },
      "values": {
        "REGISTER_NAME": "AFS Licence",
        "AFS_LIC_NUM": "218600",
        "AFS_LIC_NAME": "IPIB PTY LTD",
        "AFS_LIC_ABN_ACN": "85007186003",
        "AFS_LIC_START_DT": "02/05/2002",
        "AFS_LIC_PRE_FSR": "\"General insurance broker\",\"000030366\"",
        "AFS_LIC_ADD_LOCAL": "SOUTHBANK",
        "AFS_LIC_ADD_STATE": "VIC",
        "AFS_LIC_ADD_PCODE": "3006",
        "AFS_LIC_ADD_COUNTRY": "Australia",
        "AFS_LIC_CONDITION": "\"This licence authorises the licensee to carry on a financial services business to:\"~\"(a) provide financial product advice for the following classes of financial products:\"~\"(i) general insurance products; and\"~\"(b) deal in a financial product by:\"~\"(i) applying for, acquiring, varying or disposing of a financial product on behalf of another person in respect of the following classes of products:\"~\"(A) general insurance products;\"~\"to retail and wholesale clients.\""
      }
    },
    {
      "record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "locator": {
        "snapshot_sha": "6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f",
        "sheet": "csv",
        "row": 3
      },
      "values": {
        "REGISTER_NAME": "AFS Licence",
        "AFS_LIC_NUM": "218678",
        "AFS_LIC_NAME": "IMC PACIFIC PTY LTD",
        "AFS_LIC_ABN_ACN": "89099273846",
        "AFS_LIC_START_DT": "26/04/2002",
        "AFS_LIC_PRE_FSR": "",
        "AFS_LIC_ADD_LOCAL": "SYDNEY",
        "AFS_LIC_ADD_STATE": "NSW",
        "AFS_LIC_ADD_PCODE": "2000",
        "AFS_LIC_ADD_COUNTRY": "Australia",
        "AFS_LIC_CONDITION": "\"This licence authorises the licensee to carry on a financial services business to:\"~\"(a) deal in a financial product by:\"~\"(i) issuing, applying for, acquiring, varying or disposing of a financial product in respect of the following classes of financial products:\"~\"(A) derivatives; and\"~\"(B) foreign exchange contracts; and\"~\"(b) make a market for the following financial products:\"~\"(i) foreign exchange contracts;\"~\"(ii) derivatives; and\"~\"(iii) limited to financial products other than:\"~\"(A) derivatives;\"~\"(B) foreign exchange contracts; and\"~\"(C) debentures, stocks or bonds issued or proposed to be issued by a government and/or debentures issued by any other body;\"~\"to wholesale clients.\""
      }
    }
  ],
  "observations": [
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "field": "entity.abn",
      "value": "85007186003",
      "source_fields": [
        "AFS_LIC_ABN_ACN"
      ],
      "raw_value": [
        "85007186003"
      ],
      "raw_locator": {
        "snapshot_sha": "6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "b98b4d1e7d35fba9103f52959e33f369dfae77731f17f96870d3a67573f67f9d",
      "config_hash": "8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "42bf5c74121077b2b038d0e35942af68efcc0595dc19d78d7ee6faedcad0b8d5"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "field": "address.locality",
      "value": "SOUTHBANK",
      "source_fields": [
        "AFS_LIC_ADD_LOCAL"
      ],
      "raw_value": [
        "SOUTHBANK"
      ],
      "raw_locator": {
        "snapshot_sha": "6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "b98b4d1e7d35fba9103f52959e33f369dfae77731f17f96870d3a67573f67f9d",
      "config_hash": "8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "13b5ff26c9719341135f8f5a5861085f6f603361b7c6754894349c8d67d2e605"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "field": "address.state",
      "value": "VIC",
      "source_fields": [
        "AFS_LIC_ADD_STATE"
      ],
      "raw_value": [
        "VIC"
      ],
      "raw_locator": {
        "snapshot_sha": "6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "b98b4d1e7d35fba9103f52959e33f369dfae77731f17f96870d3a67573f67f9d",
      "config_hash": "8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "1de16f01163c8c17c897d5c605509e1159da42ee69322a1d7e62f3c76b8d08ae"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "field": "address.postcode",
      "value": "3006",
      "source_fields": [
        "AFS_LIC_ADD_PCODE"
      ],
      "raw_value": [
        "3006"
      ],
      "raw_locator": {
        "snapshot_sha": "6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "b98b4d1e7d35fba9103f52959e33f369dfae77731f17f96870d3a67573f67f9d",
      "config_hash": "8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "ef1d1e7faea872c6e639a06aebcac877dc984d405b9d014d2367fb638249e307"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "field": "address.country",
      "value": "Australia",
      "source_fields": [
        "AFS_LIC_ADD_COUNTRY"
      ],
      "raw_value": [
        "Australia"
      ],
      "raw_locator": {
        "snapshot_sha": "6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "b98b4d1e7d35fba9103f52959e33f369dfae77731f17f96870d3a67573f67f9d",
      "config_hash": "8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "78bf9aff31af665a12ba1c0fba5d82b7326926c4aed84cef48b407fda12e1ed6"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "field": "entity.abn",
      "value": "89099273846",
      "source_fields": [
        "AFS_LIC_ABN_ACN"
      ],
      "raw_value": [
        "89099273846"
      ],
      "raw_locator": {
        "snapshot_sha": "6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "b98b4d1e7d35fba9103f52959e33f369dfae77731f17f96870d3a67573f67f9d",
      "config_hash": "8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "e11e33e63e5255772cfd21e5f999b64c44b06dcfc07f946f761ed166d448c111"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "field": "address.locality",
      "value": "SYDNEY",
      "source_fields": [
        "AFS_LIC_ADD_LOCAL"
      ],
      "raw_value": [
        "SYDNEY"
      ],
      "raw_locator": {
        "snapshot_sha": "6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "b98b4d1e7d35fba9103f52959e33f369dfae77731f17f96870d3a67573f67f9d",
      "config_hash": "8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "cf1b1b1d5817cadba959097752c23ce19c93c0398e135bbeaf9d4aa079519bec"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "field": "address.state",
      "value": "NSW",
      "source_fields": [
        "AFS_LIC_ADD_STATE"
      ],
      "raw_value": [
        "NSW"
      ],
      "raw_locator": {
        "snapshot_sha": "6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "b98b4d1e7d35fba9103f52959e33f369dfae77731f17f96870d3a67573f67f9d",
      "config_hash": "8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "25fffa54b42ef12436980db865ea625c76bd390a8d62eb953e16bc86a4c8a2f3"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "field": "address.postcode",
      "value": "2000",
      "source_fields": [
        "AFS_LIC_ADD_PCODE"
      ],
      "raw_value": [
        "2000"
      ],
      "raw_locator": {
        "snapshot_sha": "6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "b98b4d1e7d35fba9103f52959e33f369dfae77731f17f96870d3a67573f67f9d",
      "config_hash": "8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "c08bbba89ab150ff2b48ed804205843226f1ba4f9c1caa9aa49335396b4c667d"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "field": "address.country",
      "value": "Australia",
      "source_fields": [
        "AFS_LIC_ADD_COUNTRY"
      ],
      "raw_value": [
        "Australia"
      ],
      "raw_locator": {
        "snapshot_sha": "6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "b98b4d1e7d35fba9103f52959e33f369dfae77731f17f96870d3a67573f67f9d",
      "config_hash": "8d75a2c95ce4d2dc4ab337b6705d93f1319a51300a2f86a9946e78c6b153e44a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "7d672a5546676a89da62fef5ba96ae79d645738a423e59510542f5aedece0910"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 4; measured/reserved input/output: 46708/4521; calculated cost: 0.017102199999999998.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **REGISTER_NAME**: Register classification has no matching ontology target; it is not evidence of legal entity type or status.
- **AFS_LIC_NUM**: AFS licence number is a licence identifier, but this ontology subset has no licence identifier field; it must not be used as an ABN or ACN.
- **AFS_LIC_NAME**: The documentation calls this the register entry name (Help File p.8), not necessarily a legal name for every record; it is retained as the raw subject label via subject_label_field but is not mapped to entity.legal_name or entity.trading_name.
- **AFS_LIC_START_DT**: This is the date the AFS licence was issued (Help File p.8), not company registration; it cannot map to entity.date_registered.
- **AFS_LIC_PRE_FSR**: Superseded pre-FSR register identifiers and licence numbers have no ontology target; the nested values cannot be flattened into the supplied fields.
- **AFS_LIC_CONDITION**: Current financial services and products authorised under the licence (Help File p.11) have no matching ontology target; nested condition text remains source evidence only.

## Uncertainties

- AFS_LIC_NAME is retained as a raw subject label, but is not asserted as entity.legal_name because the source describes it as a register entry name and the documentation also supports individual entries; no legal-name status is established for every row.
- The combined AFS_LIC_ABN_ACN column is tested independently by checksum-valid abn and acn operations. Valid identifiers of the other type produce no value; no ACN is inferred from an ABN suffix, and invalid values produce no identifier observation.
- The source describes current Australian Financial Services licensees in a point-in-time snapshot (Help File p.3), but supplies no entity deregistration/status field. A current licence record does not prove company registration, entity activity, or absence of deregistration.
- The source supplies no row-level statement timestamp. The envelope must use the supplied publication timestamp 2026-09-16T21:52:45.982310 under publication_proxy, not as a row-change timestamp.
- Only principal business address locality, state, postcode, and country are available. A full street address is not supplied; the documentation states blank address components can represent addresses that could not be validated (Help File pp.9-10).
- AFS_LIC_PRE_FSR and AFS_LIC_CONDITION contain nested tilde-delimited structures, but the ontology has no licence, authorisation, or condition fields, so they are deliberately unmapped.
- All authority and field confidence scores are provisional and require human review.
- AFS_LIC_NAME is correctly not asserted as legal or trading name; however, the mapping's use as a raw subject label should remain clearly non-canonical. The source explicitly describes it as a register entry name and can include individuals.
- The licence-holder subject role is appropriate for row-level licence claims, but exact entity linking should remain deferred unless a validated ABN/ACN is emitted. AFS_LIC_NUM must not be treated as an entity identifier.
- The separate ABN and ACN mappings are semantically consistent with the combined source field and authoritative engine exclusivity/checksum semantics. Some valid identifiers may be omitted if the source value fails validation, which is an acceptable disclosed limitation.
- The address mapping correctly represents current principal business-address components, not a branch, service location in general, or full street address. The source does not establish reporting groups or trading names.
- No status mapping is made, appropriately: current licensee/register coverage does not establish the ontology's entity status, and licence start is not date_registered.
- AFS_LIC_START_DT, AFS_LIC_PRE_FSR, AFS_LIC_CONDITION, REGISTER_NAME, and AFS_LIC_NUM are appropriately unmapped because the supplied ontology subset lacks corresponding targets.
- Confidence values are high but disclosed as provisional. They are judgements rather than measured probabilities; human review should assess whether 0.98/0.99 overstates parsing/link certainty, especially for combined identifiers and source-name subject semantics.
- Publication-proxy observed_at is permitted by engine semantics and is disclosed as distinct from row-change time. The supplied timestamp is later than the 31/07/2026 help-file date but is a dataset publication proxy, not evidence of row history.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b8e4-76b7-7a12-b005-649b2896185a/run/01a0b8e5-23b6-70c1-b75b-baa34e677900?start_time=2026-09-19T09%3A00%3A19.766065%2B00%3A00)