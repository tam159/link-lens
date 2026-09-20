# Mapping review: ASIC - Company Dataset
Config version **2**, hash `9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234`.
Grain: One current-name row for a legal entity in an ASIC Company Register snapshot; historical-name rows are excluded.. Subject: **legal_entity**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": "\t", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| Company Name | entity.legal_name | trim | 0.96 | ASIC Company Dataset Help File p.7 defines Company Name as the company name as it appears on the ASIC register; p.10 says Current Name Indicator flags whether the displayed company name is current. Filter retains Y rows. |
| ACN | entity.acn | trim, acn | 0.95 | Help File p.7 defines ACN as a 9-digit Australian Company Number including leading zeroes and expressly says that, where Type=RACN, this field instead contains an ARBN. RACN rows are excluded from this field mapping. |
| ABN | entity.abn | trim, abn | 0.95 | Help File p.10 defines ABN as the Australian Business Number for the company and states that 0 is shown when absent. The ABN operation suppresses missing/0 and validates the 11-digit identifier. |
| Status | entity.status | trim, enum | 0.86 | Help File pp.9-10 defines REGD as Registered and DRGD as De-registered. It defines EXAD as external administration (receivership/liquidation), which cannot safely assert the narrower target in_liquidation; all non-exact target meanings map to unknown. |
| Date of Registration | entity.date_registered | trim, date | 0.95 | Help File p.10 defines Date of Registration as the date on which a company was registered and gives DD/MM/YYYY as the source format. |
| Type | entity.entity_type | trim, enum | 0.85 | Help File p.7 defines APTY as Australian proprietary company, APUB as Australian public company, and FNOS as a foreign company registered in Australia. It defines RACN as a registered Australian corporation/organisation, so RACN is retained only as unknown rather than inferred as company. |

## Before / after

```json
{
  "raw": [
    {
      "record_id": "fcf5d0df8b8e5b6463e5d6f74dcfb2626916200cc9c5fcccc98c1081ebeb724b",
      "locator": {
        "snapshot_sha": "deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234",
        "sheet": "csv",
        "row": 2
      },
      "values": {
        "Company Name": "LOVINI HOLDINGS PTY LTD",
        "ACN": "000000019",
        "Type": "APTY",
        "Class": "LMSH",
        "Sub Class": "PROP",
        "Status": "REGD",
        "Date of Registration": "08/01/1990",
        "Date of Deregistration": "",
        "Previous State of Registration": "NSW",
        "State Registration number": "46869041",
        "Modified since last report": "",
        "Current Name Indicator": "",
        "ABN": "89000000019",
        "Current Name": "MONAKA PTY LTD",
        "Current Name Start Date": "28/01/2016"
      }
    },
    {
      "record_id": "a82f09d7daa51c5dcf0562e99049396e950100e4c3e1f68d460589a774d0afa1",
      "locator": {
        "snapshot_sha": "deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234",
        "sheet": "csv",
        "row": 3
      },
      "values": {
        "Company Name": "MONAKA PTY LTD",
        "ACN": "000000019",
        "Type": "APTY",
        "Class": "LMSH",
        "Sub Class": "PROP",
        "Status": "REGD",
        "Date of Registration": "08/01/1990",
        "Date of Deregistration": "",
        "Previous State of Registration": "NSW",
        "State Registration number": "46869041",
        "Modified since last report": "",
        "Current Name Indicator": "Y",
        "ABN": "89000000019",
        "Current Name": "",
        "Current Name Start Date": ""
      }
    }
  ],
  "observations": [
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "a82f09d7daa51c5dcf0562e99049396e950100e4c3e1f68d460589a774d0afa1",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "field": "entity.legal_name",
      "value": "MONAKA PTY LTD",
      "source_fields": [
        "Company Name"
      ],
      "raw_value": [
        "MONAKA PTY LTD"
      ],
      "raw_locator": {
        "snapshot_sha": "deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "a035439b77148df7078b70d97679bbc2d7a3792e06edac89cbd47c75e9d3288c",
      "config_hash": "9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "2410a4eb2f6a00540db2e607407826e19fb204eeb1e87f08e436a0a57b6b5c88"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "a82f09d7daa51c5dcf0562e99049396e950100e4c3e1f68d460589a774d0afa1",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "field": "entity.acn",
      "value": "000000019",
      "source_fields": [
        "ACN"
      ],
      "raw_value": [
        "000000019"
      ],
      "raw_locator": {
        "snapshot_sha": "deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "a035439b77148df7078b70d97679bbc2d7a3792e06edac89cbd47c75e9d3288c",
      "config_hash": "9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.95
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "ad7c018295809d3651edbfa8bf31a0ef7b04830c98c7819e087d7eaaf7d663cc"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "a82f09d7daa51c5dcf0562e99049396e950100e4c3e1f68d460589a774d0afa1",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "field": "entity.abn",
      "value": "89000000019",
      "source_fields": [
        "ABN"
      ],
      "raw_value": [
        "89000000019"
      ],
      "raw_locator": {
        "snapshot_sha": "deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "a035439b77148df7078b70d97679bbc2d7a3792e06edac89cbd47c75e9d3288c",
      "config_hash": "9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.95
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "4d94370b69fadf7ec315957019f0f285ea9ad8b075020d435444faac986b7de4"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "a82f09d7daa51c5dcf0562e99049396e950100e4c3e1f68d460589a774d0afa1",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "field": "entity.status",
      "value": "active",
      "source_fields": [
        "Status"
      ],
      "raw_value": [
        "REGD"
      ],
      "raw_locator": {
        "snapshot_sha": "deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "a035439b77148df7078b70d97679bbc2d7a3792e06edac89cbd47c75e9d3288c",
      "config_hash": "9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.86
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "b99acea66b13489f0264a59c5d95cad6f50ce1f1092778bcad9944257acbcf05"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "a82f09d7daa51c5dcf0562e99049396e950100e4c3e1f68d460589a774d0afa1",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "field": "entity.date_registered",
      "value": "1990-01-08",
      "source_fields": [
        "Date of Registration"
      ],
      "raw_value": [
        "08/01/1990"
      ],
      "raw_locator": {
        "snapshot_sha": "deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "a035439b77148df7078b70d97679bbc2d7a3792e06edac89cbd47c75e9d3288c",
      "config_hash": "9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.95
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "a0978a80f67d0b0ac6185d11f3a56e71c9ea77482e77a835819e6ee7b2e1cea1"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "a82f09d7daa51c5dcf0562e99049396e950100e4c3e1f68d460589a774d0afa1",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "field": "entity.entity_type",
      "value": "company",
      "source_fields": [
        "Type"
      ],
      "raw_value": [
        "APTY"
      ],
      "raw_locator": {
        "snapshot_sha": "deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "a035439b77148df7078b70d97679bbc2d7a3792e06edac89cbd47c75e9d3288c",
      "config_hash": "9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.85
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "808c699e2a91a79a17e40cac108ac556581272a4bc299ab030d69eb0882f129b"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "272d67a9e6c65967c614aef82a2ce0c15e99b45062d0dc691598a1954ca86e4c",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "field": "entity.legal_name",
      "value": "CHRISTENSEN & ASSOCIATES PTY LTD",
      "source_fields": [
        "Company Name"
      ],
      "raw_value": [
        "CHRISTENSEN & ASSOCIATES PTY LTD"
      ],
      "raw_locator": {
        "snapshot_sha": "deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234",
        "sheet": "csv",
        "row": 4
      },
      "snapshot_id": "a035439b77148df7078b70d97679bbc2d7a3792e06edac89cbd47c75e9d3288c",
      "config_hash": "9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "164b0894bdb7bb8d627eca04bd81c1b0adeac7c6215aa20a6cb33d2b223758e5"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "272d67a9e6c65967c614aef82a2ce0c15e99b45062d0dc691598a1954ca86e4c",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "field": "entity.acn",
      "value": "000000028",
      "source_fields": [
        "ACN"
      ],
      "raw_value": [
        "000000028"
      ],
      "raw_locator": {
        "snapshot_sha": "deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234",
        "sheet": "csv",
        "row": 4
      },
      "snapshot_id": "a035439b77148df7078b70d97679bbc2d7a3792e06edac89cbd47c75e9d3288c",
      "config_hash": "9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.95
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "757953b1310927dafb82c00e59955d58fa72f14085c7e3ca1bb9925e7cd02f5b"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "272d67a9e6c65967c614aef82a2ce0c15e99b45062d0dc691598a1954ca86e4c",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "field": "entity.abn",
      "value": "91000000028",
      "source_fields": [
        "ABN"
      ],
      "raw_value": [
        "91000000028"
      ],
      "raw_locator": {
        "snapshot_sha": "deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234",
        "sheet": "csv",
        "row": 4
      },
      "snapshot_id": "a035439b77148df7078b70d97679bbc2d7a3792e06edac89cbd47c75e9d3288c",
      "config_hash": "9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.95
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "158d754a140030c9dc217c8312ac4a02e7873b088c7ee784babc7f2182fc7629"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "272d67a9e6c65967c614aef82a2ce0c15e99b45062d0dc691598a1954ca86e4c",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "field": "entity.status",
      "value": "active",
      "source_fields": [
        "Status"
      ],
      "raw_value": [
        "REGD"
      ],
      "raw_locator": {
        "snapshot_sha": "deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234",
        "sheet": "csv",
        "row": 4
      },
      "snapshot_id": "a035439b77148df7078b70d97679bbc2d7a3792e06edac89cbd47c75e9d3288c",
      "config_hash": "9363fc043a0381f39e87bcdd7213ea6cbe5ce1b17ce15a21807476f65318714f",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.86
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "12666e8779a094f5318a0f57e8353260d8f931fbdd8e2ad1d027a433332730b0"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 5; measured/reserved input/output: 51966/5957; calculated cost: None.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **Class**: Liability-class codes (for example LMSH) have no corresponding canonical field; they are not used to infer entity type.
- **Sub Class**: Company subclass codes have no corresponding canonical field and do not safely map to the limited entity_type enum.
- **Date of Deregistration**: No canonical deregistration-date field exists. Status is separately supplied and no status is derived from this date.
- **Previous State of Registration**: Historical original-registration jurisdiction has no corresponding canonical field and is not an address.
- **State Registration number**: Historical state registration identifier has no matching canonical identifier field; it is preserved unmapped rather than retyped.
- **Modified since last report**: Dataset-change flag has no canonical field and does not provide an observation timestamp.
- **Current Name Indicator**: Used solely as the documented filter selecting current displayed company names; no canonical field represents this flag.
- **Current Name**: Help File p.11 describes this as a current-company-name helper for historical records. Historical rows are filtered out; it is not documented as a trading name.
- **Current Name Start Date**: Help File p.11 describes a name-history effective-date helper. There is no corresponding canonical name-validity field, and it is not a company registration date.

## Uncertainties

- ASIC Help File p.2 describes this as a weekly point-in-time snapshot and warns it may not be current; the supplied publication timestamp is used only as an observation-time proxy, not as the time underlying company facts became true.
- The extract includes historical company-name data (Help File p.2). Help File p.10 and discovery rows 2-9 show Current Name Indicator=Y selects the displayed current Company Name; historical names are excluded and are not treated as trading names.
- Discovery exploration found repeated ACNs for 81 of 165 ACNs in the 300-row sample, so unfiltered rows do not have legal-entity grain.
- For Type=RACN, the value in ACN is documented as an ARBN (Help File p.7), for which this ontology provides no field; it cannot emit entity.acn.
- REGD mapped to active is a constrained target-enum approximation of registered status, not evidence of operational activity. EXAD remains unknown because ASIC expressly includes receivership as well as liquidation.
- No addresses, service locations, branches, reporting groups, licences, websites, industry codes, or trading names are documented in this extract.
- All field-confidence and source-reliability scores are provisional human-review judgements, not calibrated measurements.
- The mapping intentionally discards historical-name rows. This is semantically defensible because the documented Current Name Indicator is used as an explicit Y filter, but it means no historical legal-name observations or name-effective dates are retained. That is a disclosed coverage limitation, not an error.
- The extract is a weekly snapshot and has no row-level snapshot/as-of timestamp. Using the supplied publication proxy for observed_at must remain clearly distinguished from a factual effective time; the mapping already discloses this.
- The source documentation identifies Type=RACN ACN-column values as ARBNs. Suppressing entity.acn for RACN is correct; the ontology has no ARBN field. The available discovery sample contains no RACN row, so this safeguard is documentation-based rather than preview-demonstrated.
- REGD to active is an ontology-level approximation of register status, not proof of operational activity. The explicit limitation adequately preserves that distinction. Other ambiguous statuses, including EXAD, remain unknown.
- No source evidence supports addresses/service locations, branches, reporting groups, licences, trading names, websites, or industry codes. Their omission is appropriate.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b210-c498-7320-b92e-3ca0a3d07c60/run/01a0b213-7364-7d63-9fae-2013867aa3ab?start_time=2026-09-18T01%3A13%3A34.308103%2B00%3A00)