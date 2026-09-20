# Mapping review: ASIC - Australian Financial Services Licensee Dataset
Config version **1**, hash `412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f`.
Grain: One row per current Australian Financial Services licence/register entry, stating the licence-holder register label, optional ABN or ACN, licence issue date, principal business address components, and licence conditions. Subject: **licence_holder**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| AFS_LIC_ABN_ACN | entity.abn | digits, abn | 0.98 | ASIC Australian Financial Services Licensee Help File p.8, exact header AFS_LIC_ABN_ACN: the field contains the licensee's ABN or ACN and shows an ABN when one has been provided. Discovery sample row 2: 85007186003. The abn operation supplies checksum and exact-length validation. |
| AFS_LIC_ABN_ACN | entity.acn | digits, acn | 0.98 | ASIC Australian Financial Services Licensee Help File p.8, exact header AFS_LIC_ABN_ACN: if no ABN is provided, the field may show an ACN. Discovery establishes this as one mixed identifier column. The acn operation independently applies exact-length and checksum validation; it does not derive an ACN from an ABN suffix, and valid ABNs yield no ACN observation. |
| AFS_LIC_ADD_LOCAL | address.locality | trim | 0.99 | ASIC Australian Financial Services Licensee Help File p.9, exact header AFS_LIC_ADD_LOCAL: locality of the current principal business address. Discovery sample row 2: SOUTHBANK. |
| AFS_LIC_ADD_STATE | address.state | trim, uppercase, enum | 0.99 | ASIC Australian Financial Services Licensee Help File p.10, exact header AFS_LIC_ADD_STATE: state from the current principal business address. Discovery samples rows 2-10 include VIC, NSW and WA. |
| AFS_LIC_ADD_PCODE | address.postcode | trim, postcode | 0.97 | ASIC Australian Financial Services Licensee Help File p.10, exact header AFS_LIC_ADD_PCODE: postcode from the current principal business address. Help File p.12 change log states that outside-Australia addresses display null rather than zero. Discovery sample row 2: 3006. |
| AFS_LIC_ADD_COUNTRY | address.country | trim | 0.98 | ASIC Australian Financial Services Licensee Help File p.10, exact header AFS_LIC_ADD_COUNTRY: country from the principal business address; countries outside Australia are represented by the literal placeholder International. Discovery sample row 2: Australia. The filter excludes blank and placeholder values rather than treating International as a country. |

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
      "extractor_version": "extractor-1:412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
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
      "config_hash": "412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "97bd992c7014ff9892128ff8c85c6e1b91ab84b54284b440fd557360861fce26"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
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
      "config_hash": "412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "c100f49c8768ccce2e8dc6cfc94dafc915e5b87fc8293c30cb0865dae0e32972"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
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
      "config_hash": "412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "f23f61cb7b52c3dce5a4f9e5eafbed09e9c5b1f522f7fbd2df3ccc5c573bccdf"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
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
      "config_hash": "412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "4fbf4584642c8d9fe98744133e25180afdd0e4e70fe8f5a2ec88de2cd618839a"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
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
      "config_hash": "412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "56b53da97e650d92f99988b1855eb70109d02e13ce06fbe835bb91b4fa52506e"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
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
      "config_hash": "412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "650976978ae633ab6ade271d9b09bfed8157183753ab83e862bde6978a931541"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
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
      "config_hash": "412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "b6dc3e1e8e3b079407450baeec84e6372387a828b2ebb596f0cacd28c2d61d9e"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
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
      "config_hash": "412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "a95537668c417d2b51ccf5a907c29dd7b387ca2d4edb8046b2708438375f6759"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
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
      "config_hash": "412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "9b95924a8e6c3dba6d4a44364bff8b87c1ff69a7605eb717b7eea12dc02f06b2"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
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
      "config_hash": "412bf5d1ce4b7fa0ed190013c502877f16b2d6d3a55ac83ff846039551493da6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.95,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "853b779bc81a9be9c931da13b0ee0e651cd10ed9ce4568cb888ee83eab2da26e"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 2; measured/reserved input/output: 28312/2436; calculated cost: 0.0100012.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **REGISTER_NAME**: Register classification has no ontology target and is not evidence of legal entity type or entity status; Help File p.8 describes it only as the register name.
- **AFS_LIC_NUM**: ASIC licence number is a licence identifier, but this ontology subset has no licence-number field. It must not be used as an ABN or ACN; Help File p.8 describes it as a unique number allocated to the AFS licensee.
- **AFS_LIC_NAME**: Help File p.8 calls this the register entry name and states it may be a person's given names and surname or an organisation name. It is retained as the raw subject label through subject_label_field, but the source provides no current legal-name indicator and does not support entity.legal_name or entity.trading_name.
- **AFS_LIC_START_DT**: Help File p.8 defines this as the date the AFS licence was issued/start date, not company registration. It therefore cannot map to entity.date_registered.
- **AFS_LIC_PRE_FSR**: Help File p.9 defines this as superseded pre-FSR register identifiers and licence numbers, with nested tilde-delimited values. The ontology has no licence or predecessor-licence target, so it is not flattened into an entity identifier or date.
- **AFS_LIC_CONDITION**: Help File p.11 defines this as current financial services/products authorised under the licence, with nested tilde-delimited output formats. The ontology has no licence-authorisation or condition target.

## Uncertainties

- The dataset documentation says it is a point-in-time snapshot containing current Australian Financial Services licensees (Help File p.3), but there is no row-level current-name indicator. Accordingly AFS_LIC_NAME is retained only as a raw subject label, not emitted as a current legal or trading name.
- The combined AFS_LIC_ABN_ACN field is tested independently as ABN and ACN. Checksum-invalid values and valid identifiers of the other type produce no observation; no ACN is inferred from an ABN suffix, and no ARBN case is mapped as ACN because the documented field does not provide a type qualifier distinguishing ARBN from ACN.
- A current AFS licence record does not establish company registration, deregistration, liquidation, external administration, or any ontology entity status. No status mapping is made.
- AFS_LIC_START_DT is deliberately not mapped to entity.date_registered because it is a licence issue/start date.
- Only principal business address components are supplied. No street-level full address, branch status, service-location assertion, or legal ownership is inferred.
- The source supplies no row-level statement timestamp. The envelope must use the supplied publication timestamp 2026-09-16T21:52:45.982310 as a publication proxy, not as a row-change timestamp.
- AFS_LIC_PRE_FSR and AFS_LIC_CONDITION remain raw source evidence because their nested licence semantics have no ontology target.
- Confidence and source-reliability values are provisional judgements requiring human review.
- The mapping is deliberately partial: it leaves the licence number, register name, licence start date, licence name, predecessor-FSR data, and licence conditions unmapped because the ontology has no compatible targets.
- AFS_LIC_NAME is correctly retained as a subject label rather than asserted as legal_name or trading_name; the source does not establish that distinction, historical status, or ownership beyond the licence-holder role.
- The source provides a principal business address, not necessarily a branch or service-location address and not a full street address; the mapping only emits supported components.
- The mixed ABN/ACN field is safely tested with mutually exclusive, checksummed operations. Invalid or unsupported identifiers are omitted, and no suffix-derived ACN is created.
- The source is a current-licensee snapshot but does not support legal-entity status or company registration date, so those omissions are appropriate.
- Publication timestamp is used as a disclosed proxy for observed_at; this is not a row-change timestamp. Confidence values are provisional judgements, not measured probabilities.
- Country mapping excludes the documented International placeholder, but the mapping does not normalize Australia to the ontology default AU; retaining the explicit source value is semantically safer than an unsupported constant.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b8f1-1b48-7dc3-8429-b9e09ee37a06/run/01a0b8f2-d0c4-7363-a274-ad6282a2b595?start_time=2026-09-19T09%3A15%3A16.036186%2B00%3A00)