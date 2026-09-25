# Mapping review: ASIC - Business Names Dataset
Config version **1**, hash `a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34`.
Ontology: `4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `5e0b998acfbe89481d1421ae87d0238e8584d7b7b61b68942debda3fe44ca78b`.
Grain: One ASIC Business Names Register entry per row in a point-in-time snapshot.. Subject: **unknown**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": "\t", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| BN_NAME | registration.registered_business_name | trim | 0.99 | ASIC Help File p. 8 data dictionary defines BN_NAME as the Business Name as it appears on ASIC's Business Names register; preview row 2 has BN_NAME “  ATTENTION TO D'TILE”. |
| BN_STATUS | registration.business_name_status | trim, enum | 0.96 | ASIC Help File p. 8 defines BN_STATUS as registration status and documents Registered and Cancelled; preview row 4 supplies exact value “Deregistered”. Retain source labels, including the observed undocumented label. |
| BN_REG_DT | registration.business_name_registration_date | date | 0.99 | ASIC Help File p. 9 dictionary: BN_REG_DT is the date the Business Name started; date format DD/MM/YYYY. Preview row 2: 18/11/2020. |
| BN_CANCEL_DT | registration.business_name_cancellation_date | date | 0.99 | ASIC Help File p. 9 dictionary: BN_CANCEL_DT is the date the Business Name ceased and is populated if cancelled; date format DD/MM/YYYY. Preview row 4: 27/01/2026. |
| BN_STATE_NUM | registration.former_state_number | trim | 0.99 | ASIC Help File p. 9 defines BN_STATE_NUM as the Former State Number allocated by a previous state/territory regulator before 28 May 2012; preview row 5: “B2167404E”. |
| BN_STATE_OF_REG | registration.previous_state_of_registration | trim, enum | 0.99 | ASIC Help File p. 9 defines BN_STATE_OF_REG as previous state of registration and lists ACT, NSW, NT, QLD, SA, TAS, VIC, WA; preview row 5: “VIC”. |
| BN_ABN | registration.business_name_abn | trim | 0.98 | ASIC Help File p. 10 dictionary identifies BN_ABN as the ABN shown for a Business Name register entry and notes it can be NULL when suppressed or otherwise unavailable; preview row 2: “36817347826”. |

## Before / after

```json
{
  "raw": [
    {
      "record_id": "13d0bd6382af57bbf3ee51015a461aba8d219efcd585b193fe4edb2600e13e74",
      "locator": {
        "snapshot_sha": "5e0b998acfbe89481d1421ae87d0238e8584d7b7b61b68942debda3fe44ca78b",
        "sheet": "csv",
        "row": 2
      },
      "values": {
        "REGISTER_NAME": "BUSINESS NAMES",
        "BN_NAME": "  ATTENTION TO D'TILE",
        "BN_STATUS": "Registered",
        "BN_REG_DT": "18/11/2020",
        "BN_CANCEL_DT": "",
        "BN_STATE_NUM": "",
        "BN_STATE_OF_REG": "",
        "BN_ABN": "36817347826"
      }
    },
    {
      "record_id": "ed47e52fd110bba2c53fdc1e0882b94cd6be6d598545a67fea0dc4b4ca17d63c",
      "locator": {
        "snapshot_sha": "5e0b998acfbe89481d1421ae87d0238e8584d7b7b61b68942debda3fe44ca78b",
        "sheet": "csv",
        "row": 3
      },
      "values": {
        "REGISTER_NAME": "BUSINESS NAMES",
        "BN_NAME": "  Educational Fidget Therapy",
        "BN_STATUS": "Registered",
        "BN_REG_DT": "15/11/2024",
        "BN_CANCEL_DT": "",
        "BN_STATE_NUM": "",
        "BN_STATE_OF_REG": "",
        "BN_ABN": "65163692266"
      }
    }
  ],
  "observations": [
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "13d0bd6382af57bbf3ee51015a461aba8d219efcd585b193fe4edb2600e13e74",
      "observed_at": "2026-09-22T20:35:53.157792+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:44.525251+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "field": "registration.registered_business_name",
      "value": "ATTENTION TO D'TILE",
      "source_fields": [
        "BN_NAME"
      ],
      "raw_value": [
        "  ATTENTION TO D'TILE"
      ],
      "raw_locator": {
        "snapshot_sha": "5e0b998acfbe89481d1421ae87d0238e8584d7b7b61b68942debda3fe44ca78b",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "a5f5022e673f371727b058968c4c64d2e839b9a5bc94d32a4e899edd9e6c9a1b",
      "config_hash": "a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "subject_role": "unknown",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.82,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "5f7312e05e9d23fdff25b01c189d8972f484f08a11ce87728a5039dd239e3731",
      "group_name": "business_name_registration",
      "id": "941b71bbeb7bfb778e3dc77fe21969f07f84e464345f079bb52b6cd72fceb4b3"
    },
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "13d0bd6382af57bbf3ee51015a461aba8d219efcd585b193fe4edb2600e13e74",
      "observed_at": "2026-09-22T20:35:53.157792+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:44.525251+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "field": "registration.business_name_status",
      "value": "Registered",
      "source_fields": [
        "BN_STATUS"
      ],
      "raw_value": [
        "Registered"
      ],
      "raw_locator": {
        "snapshot_sha": "5e0b998acfbe89481d1421ae87d0238e8584d7b7b61b68942debda3fe44ca78b",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "a5f5022e673f371727b058968c4c64d2e839b9a5bc94d32a4e899edd9e6c9a1b",
      "config_hash": "a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "subject_role": "unknown",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.82,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "enum",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "5f7312e05e9d23fdff25b01c189d8972f484f08a11ce87728a5039dd239e3731",
      "group_name": "business_name_registration",
      "id": "ac1a22da1740cd9124d8c3ebdb49303159750594c7bd84a1c01d5842f4071049"
    },
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "13d0bd6382af57bbf3ee51015a461aba8d219efcd585b193fe4edb2600e13e74",
      "observed_at": "2026-09-22T20:35:53.157792+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:44.525251+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "field": "registration.business_name_registration_date",
      "value": "2020-11-18",
      "source_fields": [
        "BN_REG_DT"
      ],
      "raw_value": [
        "18/11/2020"
      ],
      "raw_locator": {
        "snapshot_sha": "5e0b998acfbe89481d1421ae87d0238e8584d7b7b61b68942debda3fe44ca78b",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "a5f5022e673f371727b058968c4c64d2e839b9a5bc94d32a4e899edd9e6c9a1b",
      "config_hash": "a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "subject_role": "unknown",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.82,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "date",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "5f7312e05e9d23fdff25b01c189d8972f484f08a11ce87728a5039dd239e3731",
      "group_name": "business_name_registration",
      "id": "ee8d86118b596827c09a585057e96737c4c328418154e6b66a4753565be5ef41"
    },
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "13d0bd6382af57bbf3ee51015a461aba8d219efcd585b193fe4edb2600e13e74",
      "observed_at": "2026-09-22T20:35:53.157792+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:44.525251+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "field": "registration.business_name_abn",
      "value": "36817347826",
      "source_fields": [
        "BN_ABN"
      ],
      "raw_value": [
        "36817347826"
      ],
      "raw_locator": {
        "snapshot_sha": "5e0b998acfbe89481d1421ae87d0238e8584d7b7b61b68942debda3fe44ca78b",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "a5f5022e673f371727b058968c4c64d2e839b9a5bc94d32a4e899edd9e6c9a1b",
      "config_hash": "a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "subject_role": "unknown",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.82,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "5f7312e05e9d23fdff25b01c189d8972f484f08a11ce87728a5039dd239e3731",
      "group_name": "business_name_registration",
      "id": "a564826d3d13b5a3938305e9fcab67f405923942c6059fe05ee0885aa3de87f8"
    },
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "ed47e52fd110bba2c53fdc1e0882b94cd6be6d598545a67fea0dc4b4ca17d63c",
      "observed_at": "2026-09-22T20:35:53.157792+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:44.525251+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "field": "registration.registered_business_name",
      "value": "Educational Fidget Therapy",
      "source_fields": [
        "BN_NAME"
      ],
      "raw_value": [
        "  Educational Fidget Therapy"
      ],
      "raw_locator": {
        "snapshot_sha": "5e0b998acfbe89481d1421ae87d0238e8584d7b7b61b68942debda3fe44ca78b",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "a5f5022e673f371727b058968c4c64d2e839b9a5bc94d32a4e899edd9e6c9a1b",
      "config_hash": "a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "subject_role": "unknown",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.82,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "68d9e92ededf0d92e35dcfe31d227992dd13f5474705ad6c08f4e1a3e7b9b10f",
      "group_name": "business_name_registration",
      "id": "5463bdf8bb6e6653d1bb6580eee63905a1c4cff3e3cafa706e1f164001c5c4bd"
    },
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "ed47e52fd110bba2c53fdc1e0882b94cd6be6d598545a67fea0dc4b4ca17d63c",
      "observed_at": "2026-09-22T20:35:53.157792+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:44.525251+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "field": "registration.business_name_status",
      "value": "Registered",
      "source_fields": [
        "BN_STATUS"
      ],
      "raw_value": [
        "Registered"
      ],
      "raw_locator": {
        "snapshot_sha": "5e0b998acfbe89481d1421ae87d0238e8584d7b7b61b68942debda3fe44ca78b",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "a5f5022e673f371727b058968c4c64d2e839b9a5bc94d32a4e899edd9e6c9a1b",
      "config_hash": "a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "subject_role": "unknown",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.82,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "enum",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "68d9e92ededf0d92e35dcfe31d227992dd13f5474705ad6c08f4e1a3e7b9b10f",
      "group_name": "business_name_registration",
      "id": "06fda50e8c5e2224704658425838f08e428e04d0ae12af9fd2057956524897a6"
    },
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "ed47e52fd110bba2c53fdc1e0882b94cd6be6d598545a67fea0dc4b4ca17d63c",
      "observed_at": "2026-09-22T20:35:53.157792+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:44.525251+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "field": "registration.business_name_registration_date",
      "value": "2024-11-15",
      "source_fields": [
        "BN_REG_DT"
      ],
      "raw_value": [
        "15/11/2024"
      ],
      "raw_locator": {
        "snapshot_sha": "5e0b998acfbe89481d1421ae87d0238e8584d7b7b61b68942debda3fe44ca78b",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "a5f5022e673f371727b058968c4c64d2e839b9a5bc94d32a4e899edd9e6c9a1b",
      "config_hash": "a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "subject_role": "unknown",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.82,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "date",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "68d9e92ededf0d92e35dcfe31d227992dd13f5474705ad6c08f4e1a3e7b9b10f",
      "group_name": "business_name_registration",
      "id": "28e0351f08b823e58a0f0c16796eba4dcabd61e7012df45a1fef01bf7ccbaa46"
    },
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "ed47e52fd110bba2c53fdc1e0882b94cd6be6d598545a67fea0dc4b4ca17d63c",
      "observed_at": "2026-09-22T20:35:53.157792+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:44.525251+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "field": "registration.business_name_abn",
      "value": "65163692266",
      "source_fields": [
        "BN_ABN"
      ],
      "raw_value": [
        "65163692266"
      ],
      "raw_locator": {
        "snapshot_sha": "5e0b998acfbe89481d1421ae87d0238e8584d7b7b61b68942debda3fe44ca78b",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "a5f5022e673f371727b058968c4c64d2e839b9a5bc94d32a4e899edd9e6c9a1b",
      "config_hash": "a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "subject_role": "unknown",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.82,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "68d9e92ededf0d92e35dcfe31d227992dd13f5474705ad6c08f4e1a3e7b9b10f",
      "group_name": "business_name_registration",
      "id": "61fb5826e3b88c8acd495887c57f49084ee565b07dfffdb47529f781252eefe5"
    },
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "71c40fab58d8e8dd2ab79185772abcad72660bc708078e6fca2f2c6250757753",
      "observed_at": "2026-09-22T20:35:53.157792+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:44.525251+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "field": "registration.registered_business_name",
      "value": "Felden Aware",
      "source_fields": [
        "BN_NAME"
      ],
      "raw_value": [
        "  Felden Aware"
      ],
      "raw_locator": {
        "snapshot_sha": "5e0b998acfbe89481d1421ae87d0238e8584d7b7b61b68942debda3fe44ca78b",
        "sheet": "csv",
        "row": 4
      },
      "snapshot_id": "a5f5022e673f371727b058968c4c64d2e839b9a5bc94d32a4e899edd9e6c9a1b",
      "config_hash": "a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "subject_role": "unknown",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.82,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "754160b6356b95ce1e2c3c5e356b5deeb1c75d9e68fd2fda248f860c841694cc",
      "group_name": "business_name_registration",
      "id": "67c80c3ecd4da49fb41125900a4d88f190c235f7bbcec45a74c76b856996f369"
    },
    {
      "source_id": "bc515135-4bb6-4d50-957a-3713709a76d3",
      "source_record_id": "71c40fab58d8e8dd2ab79185772abcad72660bc708078e6fca2f2c6250757753",
      "observed_at": "2026-09-22T20:35:53.157792+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:44.525251+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "field": "registration.business_name_status",
      "value": "Deregistered",
      "source_fields": [
        "BN_STATUS"
      ],
      "raw_value": [
        "Deregistered"
      ],
      "raw_locator": {
        "snapshot_sha": "5e0b998acfbe89481d1421ae87d0238e8584d7b7b61b68942debda3fe44ca78b",
        "sheet": "csv",
        "row": 4
      },
      "snapshot_id": "a5f5022e673f371727b058968c4c64d2e839b9a5bc94d32a4e899edd9e6c9a1b",
      "config_hash": "a95b3a4fa656edc61265adde19eaabd64a95d6c35f4d8579f0689fca14c1dd34",
      "subject_role": "unknown",
      "source_kind": "business_name_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.82,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "enum",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "754160b6356b95ce1e2c3c5e356b5deeb1c75d9e68fd2fda248f860c841694cc",
      "group_name": "business_name_registration",
      "id": "5eac8d3435d4d6682dbc803b33630a17f0b1e8a0133291f491da61d4d7d720aa"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 2; measured/reserved input/output: 25662/2288; calculated cost: 0.0081315.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **REGISTER_NAME**: The column identifies the register name (“BUSINESS NAMES” in preview) but the supplied ontology has no registered concept for a register title; do not treat it as entity identity or infer another canonical field.

## Uncertainties

- Business-name register records are not necessarily legal entities and the source does not establish ownership of the business name or the displayed BN_ABN; subject role is unknown and the ABN is retained only as an entry-level registration claim.
- BN_STATUS preview includes “Deregistered”, while the data dictionary describes Registered and Cancelled; the source label is preserved without translating it into legal-entity status.
- BN_STATE_NUM and BN_STATE_OF_REG describe historical registration by a previous state/territory regulator, not current branch or service locations.
- Publication timestamp is a source-envelope proxy for observation time, not a row-level change time; dataset notes and help file differ on update cadence.
- BN_RENEW_DT was removed in April 2025 and is not present in the supplied columns.
- BN_STATUS documentation lists Registered and Cancelled, while discovery rows include Deregistered. The mapping explicitly preserves that observed source label and discloses the discrepancy; do not interpret it as legal-entity status.
- The attempted exploration script failed because its variable `records` was undefined. Assessment therefore relies on the supplied raw discovery rows, source documentation, and the separate validation report rather than that script's summaries.
- BN_ABN is correctly retained as an entry-level string claim without asserting that it identifies or belongs to a legal entity; its blank/suppression and checksum semantics remain a limitation of this partial mapping.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0d40f-3b01-7ea3-a642-5acdaea529c6/run/01a0d40f-6e62-7812-8a0e-cd52a98fd138?start_time=2026-09-24T15%3A36%3A16.226072%2B00%3A00)