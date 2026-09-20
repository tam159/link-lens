# Mapping review: ASIC - Australian Financial Services Licensee Dataset
Config version **1**, hash `74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f`.
Grain: One current AFS licence register entry/licensee per row.. Subject: **licence_holder**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| AFS_LIC_ABN_ACN | entity.abn | abn | 0.9 | Help file p.8 defines AFS_LIC_ABN_ACN as the licensee ABN or ACN; sample row 2 has 85007186003. |
| AFS_LIC_ABN_ACN | entity.acn | acn | 0.9 | Help file p.8 states this mixed field is ABN or ACN; ACN validator emits only valid 9-digit ACNs. |
| AFS_LIC_ADD_LOCAL | address.locality | trim | 0.94 | Help file p.9 defines this as locality of the current principal business address; sample row 2 is SOUTHBANK. |
| AFS_LIC_ADD_STATE | address.state | trim, uppercase, enum | 0.94 | Help file p.10 defines this as state of current principal business address; sample rows include VIC and NSW. |
| AFS_LIC_ADD_PCODE | address.postcode | trim, postcode | 0.93 | Help file p.10 defines this as postcode of current principal business address; sample row 2 is 3006. |
| AFS_LIC_ADD_COUNTRY | address.country | trim | 0.92 | Help file p.10 defines this as country of principal business address; sample row 2 is Australia. |

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
      "extractor_version": "extractor-1:74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
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
      "config_hash": "74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "a4631c2cc1d801bbac8e7264513a83799183a7219d1aa29ea2496e2534ceeba2"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
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
      "config_hash": "74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "ba9368dc65aaf642c444df801f263ee28540a64975c166fc48f006fec2c17d4a"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
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
      "config_hash": "74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "d21851467b4f5d260f993ec6cfdd44c7d7805ad9fa6d1909d043bb62c5adf482"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
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
      "config_hash": "74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.93
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "7ca5270c142d5a9316257e882eca37e77e4a103193409efca0b168982000af10"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
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
      "config_hash": "74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.92
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "6bf06e4d4040e854295d3f779ba3d7cda902c8e0821242e6ab77a0f9eaa803be"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
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
      "config_hash": "74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "ab456a007c17bbac157320a3cc46ea98dbb291ae6fae878617311c1ff6a8219d"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
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
      "config_hash": "74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "8c78180b98b5f748e88b0e3d0b5ec2330028df2cf37938cd4375a9fa71cea89c"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
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
      "config_hash": "74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "354ac952526a8d4266246a638dbf2a3f81066d376cfbd0f843ce0bfcbbe13da0"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
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
      "config_hash": "74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.93
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "c1f04138a2adf0f833f2a54bda83d74a74232921f32253868d821534b224a6a3"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
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
      "config_hash": "74e089c6cfd868eb2bea14a2cd71aab0832231cb6630a3103b355b8bcc9d671a",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.92
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "40bff81e0fcea78f7931642aa78cbc5a35ac496593182948411cb5d2acedf8e5"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 3; measured/reserved input/output: 32086/2953; calculated cost: None.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **REGISTER_NAME**: Identifies the register to which the record belongs (help file p.8), not an available entity or address field; retained only as a documented partition filter.
- **AFS_LIC_NUM**: Unique AFS licence number (help file p.8); the assignment ontology has no licence-number field, and it must not be treated as an entity identifier.
- **AFS_LIC_NAME**: Register entry name of the AFS licensee; help file p.8 specifies it may be a person's given and last names or an organisation name. It is retained as subject_label_field, but is not confidently a registered legal name or trading name.
- **AFS_LIC_START_DT**: Start date of the Australian Financial Services licensee/licence (help file p.8), not entity company registration date.
- **AFS_LIC_PRE_FSR**: Previous superseded-register identifier and licence number(s) (help file p.9); no corresponding licence-history field exists in the assignment ontology.
- **AFS_LIC_CONDITION**: Current financial services/products authorised under the licence (help file p.11); no licence-condition or authorisation field exists in the assignment ontology.

## Uncertainties

- This is a point-in-time snapshot of current Australian Financial Services licensees (help file p.3); it supports neither entity deregistration nor a general entity-status claim.
- The row represents a licence register entry/licensee and can represent an individual or organisation; no legal-entity name is emitted from AFS_LIC_NAME.
- AFS_LIC_ABN_ACN is source-labelled only as ABN or ACN (help file p.8). Both identifier mappings are intentionally present; checksum/length validation decides which, and no ACN is derived from an ABN suffix.
- Principal business address components are not a registered address and the help file notes blank values can indicate an unvalidated provided address (pp.9-10).
- The source envelope, rather than a row field, supplies the publication timestamp and licence. Authority and confidence assessments are provisional and require human review.
- The mapping is deliberately partial: it emits only validated ABN/ACN and principal-business address components. It does not represent the AFS licence number, licence start date, pre-FSR licences, conditions, or the register-entry name because this ontology subset has no safe corresponding fields.
- `AFS_LIC_NAME` must remain unmapped as legal_name and trading_name. Documentation explicitly permits either an individual name or organisation name and calls it the register-entry name; it does not establish a registered legal name or a trading name.
- The row is a current AFS-licence register entry/licensee, not necessarily a legal-entity master row. The declared licence-holder role and no-name-emission policy appropriately preserve that limitation. Identifier emissions provide the only entity linkage and are correctly validator-gated.
- Do not infer `entity.status=active` from inclusion without an explicit mapping semantics review: the source is a current-licensee snapshot, which supports licence/register inclusion but not the ontology's general legal-entity status. The mapping does not make this inference.
- The address is correctly constrained to current principal business address components. It is not a registered office, service location, or necessarily a full/validated address; blanks may mean the provided address could not be validated. No unsupported full-address or country constant is emitted.
- `AFS_LIC_ABN_ACN` is a mixed source field. Dual ABN/ACN mappings are semantically acceptable under the supplied engine: accepted lengths/checksums are disjoint, invalid/missing values emit nothing, and no suffix-derived ACN is produced. The source documentation says the value is ABN if provided, otherwise ACN, but does not label the type per row.
- The filter on `REGISTER_NAME = AFS Licence` is evidenced by the documentation and discovery data. It is semantically harmless, although the available preview/exploration shows this is the sole value and filter effectiveness across a complete release remains a source-version property.
- Confidence values are uncalibrated judgements as disclosed. 0.90 for each identifier field is somewhat strong given a mixed unlabeled column, but checksum/length gating and direct source documentation make it not a human-review blocker; field confidence is not link precision.
- Envelope details such as exact source_id, source_record_id construction, publication-proxy observed_at, ingested_at, extractor version, and licence literal are not shown in the mapping field list. They remain required implementation/envelope obligations; no evidence here indicates they are incorrectly populated. The stated publication-proxy policy is appropriate for a snapshot where no row observation timestamp is supplied.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b210-c47b-7a32-9298-2cea56461d04/run/01a0b211-6805-7660-a203-9d1e6a2691a5?start_time=2026-09-18T01%3A11%3A20.325481%2B00%3A00)