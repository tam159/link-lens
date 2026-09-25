# Mapping review: ASIC - Australian Financial Services Licensee Dataset
Config version **2**, hash `3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f`.
Grain: One row per current Australian Financial Services licence/register entry, stating a licence-holder register label, optional mixed ABN or ACN, licence start date, principal business address components, and licence conditions. Subject: **licence_holder**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| AFS_LIC_ADD_LOCAL | address.locality | trim, uppercase | 0.98 | ASIC Australian Financial Services Licensee Dataset Help File p.9, exact header AFS_LIC_ADD_LOCAL: locality from the current principal business address of the Australian Financial Services licensee. Discovery CSV row 2 sample: SOUTHBANK. |
| AFS_LIC_ADD_STATE | address.state | trim, uppercase, enum | 0.98 | ASIC Australian Financial Services Licensee Dataset Help File p.10, exact header AFS_LIC_ADD_STATE: state from the current principal business address. Discovery CSV rows 2-10 sample values include VIC, NSW and WA. |
| AFS_LIC_ADD_PCODE | address.postcode | trim, postcode | 0.96 | ASIC Australian Financial Services Licensee Dataset Help File p.10, exact header AFS_LIC_ADD_PCODE: postcode from the current principal business address. Discovery CSV row 2 sample: 3006. The p.12 change log states non-Australian addresses display null rather than zero; no zero-padding or repair is applied. |
| AFS_LIC_ADD_COUNTRY | address.country | trim | 0.97 | ASIC Australian Financial Services Licensee Dataset Help File p.10, exact header AFS_LIC_ADD_COUNTRY: country from the principal business address; countries outside Australia are represented by the literal sentinel International, and blanks represent unvalidated addresses. Discovery CSV row 2 sample: Australia. |

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
      "extractor_version": "extractor-1:3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
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
      "config_hash": "3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "7b3dc72754b4544b0f499cb9c2c185440896ac5e83076b27208455a78df22e84"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
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
      "config_hash": "3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "063ebed433ca835f2479350e456b5ce43b07cef7d6d67b17f207ad326e87e4de"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
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
      "config_hash": "3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "3900183b8bb0b467b5b00ceaca7a36ef44ceafb19fe5d98993e1532bba3b3588"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "3b846f9e6a7b22d76b127f56686fc36e61beef0066c11b6f2ce7621c0afab19a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
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
      "config_hash": "3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "19c78f0422a6b8b6c365d56a95b07fc583f22a8cd1c7663adc124393de5f59cb"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
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
      "config_hash": "3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "d4ebd98d0d5d3aea810206ae6f82765bd57a7babf61689772794e68dbf5f71b6"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
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
      "config_hash": "3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "10f1c496f2365d28137342c8bc9be6e679f3b82376b733112c0b8e1409fede08"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
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
      "config_hash": "3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "8267ffd2e33afe1861cf379b16f473566d659e4d8e1ac623d8ae8edc99a12826"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "4dfe1031f73cefb5bf98f5efe85e263844a5cc023d2d5d3009a2fa72cff2471e",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
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
      "config_hash": "3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "cf4f7863cb3b148d03eafb550cf2c438b9261331b2c9889f9d5cc1be5db9f48f"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "dfc7af12a3f41059cff4fa434f0b51b34747df177120d049af1e69f6aea11a4a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
      "field": "address.locality",
      "value": "TOORADIN",
      "source_fields": [
        "AFS_LIC_ADD_LOCAL"
      ],
      "raw_value": [
        "TOORADIN"
      ],
      "raw_locator": {
        "snapshot_sha": "6190811ea4f4df19daab6ad63677f4a0930a0d5669b62ba6312624385681d86f",
        "sheet": "csv",
        "row": 4
      },
      "snapshot_id": "b98b4d1e7d35fba9103f52959e33f369dfae77731f17f96870d3a67573f67f9d",
      "config_hash": "3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "fae7becdaf4a231a7826c4d4d30d59d5e01fb32804efcb3c2bf902ed0805f203"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "dfc7af12a3f41059cff4fa434f0b51b34747df177120d049af1e69f6aea11a4a",
      "observed_at": "2026-09-16T21:52:45.982310+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:02.276683+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
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
        "row": 4
      },
      "snapshot_id": "b98b4d1e7d35fba9103f52959e33f369dfae77731f17f96870d3a67573f67f9d",
      "config_hash": "3d423c445dfcac297519623ccdf126e9e108bf77e24693e0d2033a60bc81a0bd",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "c7e8d8f8a75793ebbbee25bc6f58d921ac2adee01da49d75421aa762ec651fbd"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 4; measured/reserved input/output: 59296/5769; calculated cost: 0.021746799999999997.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **REGISTER_NAME**: ASIC Help File p.8 exact header REGISTER_NAME describes the register classification only. The ontology has no register target; it is not evidence of legal name, entity type, status, or reporting group.
- **AFS_LIC_NUM**: ASIC Help File p.8 exact header AFS_LIC_NUM describes a unique number allocated to the Australian Financial Services licensee. No licence-number target exists, and it must not be treated as an ABN or ACN.
- **AFS_LIC_NAME**: ASIC Help File p.8 exact header AFS_LIC_NAME defines the register entry name, not necessarily a registered legal name or trading name. It is retained as subject_label_field, but no ontology name target is supported without asserting an unsupported legal/trading interpretation.
- **AFS_LIC_ABN_ACN**: ASIC Help File p.8 exact header AFS_LIC_ABN_ACN contains either an ABN or ACN but exposes no row-level type distinction. Checksum/length validation alone cannot establish whether the source stated ABN or ACN, so the mixed identifier is left unmapped rather than misclassified; no ACN is inferred from an ABN suffix.
- **AFS_LIC_START_DT**: ASIC Help File p.8 exact header AFS_LIC_START_DT defines the AFS licence start/issue date. It is not company registration, so it is not mapped to entity.date_registered.
- **AFS_LIC_PRE_FSR**: ASIC Help File p.9 exact header AFS_LIC_PRE_FSR describes superseded pre-FSR register identifiers and licence numbers, including nested tilde-delimited values. No compatible predecessor-licence target exists.
- **AFS_LIC_CONDITION**: ASIC Help File p.11 exact header AFS_LIC_CONDITION describes financial services and products authorised under the licence, with nested tilde-delimited output formats. No compatible licence-condition target exists.

## Uncertainties

- The Help File p.3 describes a point-in-time snapshot of current Australian Financial Services licensees, but no row-level snapshot timestamp is supplied. Use the supplied publication proxy 2026-09-16T21:52:45.982310 for observed_at under publication_proxy; this is provenance for publication, not a claim of row-change time or exact register snapshot time.
- AFS_LIC_NAME is retained only as the raw subject label for the licence-holder role. It is not mapped to entity.legal_name or entity.trading_name because the documentation calls it a register entry name and does not establish legal/trading-name semantics.
- AFS_LIC_ABN_ACN is a mixed ABN/ACN column without a source type flag. It remains unmapped; identifier checksum validators cannot determine the source-declared type, and no suffix-derived ACN is produced.
- The source describes licence holders and does not establish incorporation, legal entity type, deregistration, branches, trading names, reporting groups, or ownership. No entity.entity_type, entity.status, or entity.date_registered mapping is made. A current licence snapshot does not prove active legal-entity status or deregistration.
- Locality, state, postcode, and country are components of the current principal business address of the licence holder, not a complete street address, branch, service location, or independently resolved entity address. Their subject attachment remains the licence-holder observation.
- The documented International country sentinel and blanks are omitted from canonical country claims. Invalid or unsupported state/postcode values are not repaired or coerced.
- AFS_LIC_START_DT, AFS_LIC_NUM, AFS_LIC_PRE_FSR, and AFS_LIC_CONDITION remain raw source evidence because this ontology subset has no compatible licence fields.
- All authority, source-reliability, and field-confidence values are provisional uncalibrated judgements requiring human review.
- The mapping is deliberately partial: it does not map AFS_LIC_NAME, the mixed ABN/ACN field, licence number, licence start date, prior FSR data, or licence conditions because the ontology subset lacks compatible targets or source semantics are insufficient. This is appropriate, but the raw subject label remains available only as a role label rather than a canonical name claim.
- The row grain and subject_role are semantically aligned with the documentation: one current licence/register entry concerning a licence holder. AFS_LIC_NUM is not incorrectly used as an entity identifier, and no unsupported legal-entity, trading-name, branch, reporting-group, ownership, incorporation, or status claims are made.
- The address mappings correctly represent current principal business address components, not full addresses, branches, or service locations. The country filter omits the documented International sentinel and blanks. State filtering and postcode handling avoid unsupported coercion.
- AFS_LIC_START_DT is correctly not mapped to entity.date_registered; it is a licence start/issue date. Current-licensee snapshot semantics are not converted into entity.status=active.
- The publication timestamp proxy is disclosed as publication provenance rather than row-change time, consistent with engine semantics. Confidence values are provisional judgements, not measured probabilities, and should remain subject to human review.
- The supplied exploration Python failed because records was undefined, but the provided raw discovery records, documentation, and successful validation evidence are sufficient for this semantic review; this is not a mapping blocker.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b939-c187-7823-85e8-983541907ffc/run/01a0b93a-ddc4-7141-b025-96bdd16047fc?start_time=2026-09-19T10%3A33%3A57.956517%2B00%3A00)