# Mapping review: ASIC - Company Dataset
Config version **3**, hash `394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `deda104897463ae7551130b28f643abedf7c98dfc246c32cc2da1800a27ad234`.
Grain: One ASIC Company Dataset row representing a registered or historical company-name record. Subject: **legal_entity**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": "\t", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| Company Name | entity.legal_name | trim | 0.97 | ASIC Company Dataset Help File, p.8, data dictionary: “Company Name — Company name as it appears on the register”; p.4 example headers/records; discovery row 3: Current Name Indicator “Y”, Company Name “MONAKA PTY LTD”. The current-name filter prevents historical Company Name rows from being emitted as current legal names. |
| ACN | entity.acn | trim, digits, acn | 0.96 | ASIC Company Dataset Help File, p.8, data dictionary: “ACN — Australian Company Number”, 9-digit format including leading zeros; same page documents the exception that when Type='RACN' the field contains an ARBN. Discovery rows 2–9 show Type APTY and ACN values such as “000000019”. The declarative Type exclusion prevents ARBN emission as entity.acn. |
| ABN | entity.abn | trim, digits, abn | 0.97 | ASIC Company Dataset Help File, pp.10–11, data dictionary: “ABN — Australian Business Number”; it states the field shows the company ABN and shows 0 when there is no ABN. Discovery row 2 header/value: ABN “89000000019”. The abn operation validates the identifier and suppresses zero/invalid values. |
| Type | entity.entity_type | trim, enum | 0.84 | ASIC Company Dataset Help File, p.8, data dictionary: “Type — Specifies the type of company”; documented values APTY, APUB, FNOS and RACN. Discovery rows 2–9 show APTY. Mapping uses documented codes only and does not infer company type from a name suffix. |
| Status | entity.status | trim, enum | 0.9 | ASIC Company Dataset Help File, pp.9–10, data dictionary: “Status — Status of company”; REGD is “Registered”, DRGD “De-registered”, and EXAD “External administration (in receivership/liquidation)”. EXAD is deliberately mapped to unknown because the documentation does not establish that external administration is exactly the ontology’s in_liquidation status. Discovery row 2 has Status “REGD”. |
| Date of Registration | entity.date_registered | trim, date | 0.98 | ASIC Company Dataset Help File, p.11, data dictionary: “Date of Registration — Date on which a company was registered”, format DD/MM/YYYY; discovery row 2 sample “08/01/1990”. This field is not populated from charity, trading-name, licence, or deregistration dates. |

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
      "extractor_version": "extractor-1:394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
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
      "config_hash": "394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "ab57891d7a1b16d00731f5e5256ded436264c1eed0a91ceda1c7d2ddd819dbff"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "a82f09d7daa51c5dcf0562e99049396e950100e4c3e1f68d460589a774d0afa1",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
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
      "config_hash": "394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "17e6c83c7ac53d1101d1fbbf4ce2a3d0714eaf86e76ca1fab55c28c44560daaf"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "a82f09d7daa51c5dcf0562e99049396e950100e4c3e1f68d460589a774d0afa1",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
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
      "config_hash": "394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "832656f63bc37bd2bcf472cd54e588f0794f5321248ac99ee3c532d42d5b8f71"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "a82f09d7daa51c5dcf0562e99049396e950100e4c3e1f68d460589a774d0afa1",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
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
      "config_hash": "394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.84
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "a5da77a0f2e38badc2e6d42c84a77b1bf7646f77d6d725497ffc6a2d9b7a8deb"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "a82f09d7daa51c5dcf0562e99049396e950100e4c3e1f68d460589a774d0afa1",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
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
      "config_hash": "394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "fdb3fce329a84feebc76d65f30fff9fd8813631aae6c915aea0e193b672d315e"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "a82f09d7daa51c5dcf0562e99049396e950100e4c3e1f68d460589a774d0afa1",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
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
      "config_hash": "394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "7ce2426a2811c75eb4b46cedf0f309fdc1b1c9029c9f019f410e51b5f638d25f"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "272d67a9e6c65967c614aef82a2ce0c15e99b45062d0dc691598a1954ca86e4c",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
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
      "config_hash": "394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "fdda02561249e9be6d705574760f8345a8ed1f161beb320f35f1a540b481f82f"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "272d67a9e6c65967c614aef82a2ce0c15e99b45062d0dc691598a1954ca86e4c",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
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
      "config_hash": "394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "16d066af587a3ef6d9a4257fe7d0841c0a217b851da98794a47d5663d45f89df"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "272d67a9e6c65967c614aef82a2ce0c15e99b45062d0dc691598a1954ca86e4c",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
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
      "config_hash": "394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "1da254b39455d74d0ec7c24c846180521e9a5a16671326e612ddf087aeb6b39d"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "272d67a9e6c65967c614aef82a2ce0c15e99b45062d0dc691598a1954ca86e4c",
      "observed_at": "2026-09-14T14:53:34.014830+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:56:54.341936+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
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
        "row": 4
      },
      "snapshot_id": "a035439b77148df7078b70d97679bbc2d7a3792e06edac89cbd47c75e9d3288c",
      "config_hash": "394b9c061280955cc4ed49286c529cc4136344f04e884a4c13fa030601f86c75",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.84
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "83802c45c2078bb0d8e9a52901a0736fb95bdb34468c5b863f46dce631f322c3"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 6; measured/reserved input/output: 66368/18747; calculated cost: 0.039088399999999995.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **Class**: ASIC liability/class code is not represented by the supplied ontology; do not infer entity_type from it.
- **Sub Class**: ASIC company subclass code is not represented by the supplied ontology.
- **Date of Deregistration**: The ontology has no deregistration-date field; it must not be mapped to entity.date_registered.
- **Previous State of Registration**: This is historical state-registration metadata, not an address state.
- **State Registration number**: State registration identifier is not an ACN/ABN and has no corresponding ontology field.
- **Modified since last report**: Dataset-change flag has no corresponding ontology field.
- **Current Name Indicator**: Used only as a declarative current-name filter/condition; it has no ontology target field.
- **Current Name**: ASIC documents this as a conditional current-name field for historical records (Help File p.11–12), but the ontology has no separate legal-name-history field. It is not mapped to trading_name, and historical names are not emitted as current legal names.
- **Current Name Start Date**: Historical/current-name start date has no corresponding ontology field and is not the company registration date.

## Uncertainties

- The source is a weekly snapshot and ASIC warns it may not be accurate at query time; publication_proxy uses the supplied publication timestamp 2026-09-14T14:53:34.014830 and is not a row-change timestamp.
- The current-name filter emits only records with Current Name Indicator='Y'; historical name rows are retained as raw source evidence but do not produce current legal-name observations. Rows with other or missing indicators are excluded from mapped observations, so current-name coverage may be incomplete if publisher conventions vary.
- The row grain is a company-register name record; repeated ACNs represent name history and are not reconciled or collapsed during ingestion.
- The ACN field is documented to contain an ARBN when Type=RACN; the declarative Type exclusion prevents those values from being emitted as entity.acn. No ACN is inferred from an ABN suffix.
- ABN and ACN are independently validated with their dedicated operations; valid values of the other identifier type produce no observation, and zero/missing/invalid values produce no identifier observation.
- REGD is approximated as active and DRGD as deregistered. EXAD and all other unmapped-to-ontology status meanings are conservatively emitted as unknown; external administration is not equated with liquidation.
- No address, website, industry code, branch, trading-name ownership, licence, or reporting-group relationship is evidenced by this source.
- Authority, field, and linking scores are provisional judgements and require human review.
- The mapping is deliberately partial: Class, Sub Class, deregistration date, historical-name fields, and other non-ontology source fields remain unmapped, appropriately avoiding unsupported legal, address, trading-name, licence, or reporting-group claims.
- Current Name Indicator='Y' filtering is semantically supported by the documented paired-row pattern and prevents historical Company Name rows from being emitted as current legal names; however, this excludes historical-name observations rather than representing name history.
- The source documents the ABN column as emitting 0 when absent; the trusted engine semantics correctly suppress zero/invalid identifiers. ACN validation and RACN/ARBN exclusion are appropriately conservative.
- REGD→active and DRGD→deregistered are reasonable ontology approximations for this review, while other status codes are conservatively mapped to unknown. The mapping does not assert that EXAD means in_liquidation.
- The publication timestamp proxy is disclosed and engine-authorized; it is not a row-change timestamp. Confidence values are explicit provisional judgements, not measured probabilities.
- The source is a weekly register snapshot and validation is syntactic/structural, not semantic ground truth.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b8ee-60b1-7081-bb57-a21055a2afdd/run/01a0b8ef-05e0-7a52-b3fd-3516dbc1d912?start_time=2026-09-19T09%3A11%3A07.488643%2B00%3A00)