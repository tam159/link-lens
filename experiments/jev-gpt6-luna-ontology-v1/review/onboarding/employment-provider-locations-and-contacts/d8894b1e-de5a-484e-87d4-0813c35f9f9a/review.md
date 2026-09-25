# Mapping review: Employment Services Provider Locations and Contacts
Config version **1**, hash `05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a`.
Ontology: `4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979`.
Grain: One employment-services service-location record per recorded contract association, potentially repeating a physical site across contracts.. Subject: **service_provider**.
Reader: `{"format": "csv", "encoding": "cp1252", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| DIS_SITE_CODE | service_location.code | trim | 0.97 | Exact header DIS_SITE_CODE; discovery sample A230 and A290 are site codes, consistent with ontology source identifier for a service location. |
| CONTRACT_NAME | service_location.contract_name | trim | 0.95 | Exact header CONTRACT_NAME; samples DESB and DESA match a contract label, not an asserted legal relationship. |
| LOCATION_NAME | service_location.name | trim | 0.9 | Exact header LOCATION_NAME; samples CANBERRA, YOUNG and WAGGA WAGGA are location labels. |
| SITE_ADDRESS_LN | service_location.address_line | trim | 0.96 | Exact header SITE_ADDRESS_LN; samples '2nd Floor 22 East Row' and '2B Campbell Street' are premises/street address lines. |
| SITE_URL | service_location.website | trim | 0.93 | Exact header SITE_URL; sample www.visionaustralia.org.au is a URL explicitly recorded for the site. |
| LATITUDE | service_location.latitude | decimal | 0.96 | Exact header LATITUDE; sample -35.2791945 is a plain decimal coordinate within the ontology latitude range. |
| LONGITUDE | service_location.longitude | decimal | 0.96 | Exact header LONGITUDE; sample 149.1306937 is a plain decimal coordinate within the ontology longitude range. |
| AGENT_FREECALL_NUM | service_location.agent_freecall_phone | trim | 0.95 | Exact header AGENT_FREECALL_NUM; sample 1800466046 is explicitly identified as an agent free-call number. |
| SITE_CONTACT_PHONE | contact.phone | trim | 0.96 | Exact header SITE_CONTACT_PHONE; sample 61325800 is explicitly identified as a site contact phone. |
| SITE_EMAIL_ADDRESS | contact.email | trim | 0.95 | Exact header SITE_EMAIL_ADDRESS; sample kal.perera@visionaustralia.org is an email recorded for a site contact. |
| SITE_LOCALITY_NAME | address.locality | trim | 0.93 | Exact header SITE_LOCALITY_NAME; sample CANBERRA identifies the service-location locality. |
| SITE_STATE_CD | address.state | trim, enum | 0.94 | Exact header SITE_STATE_CD; samples ACT and NSW are ontology state abbreviations and refer to service-location addresses. |
| SITE_POSTCODE | address.postcode | trim | 0.94 | Exact header SITE_POSTCODE; samples 2601 and 2594 are postcodes associated with service locations. |

## Before / after

```json
{
  "raw": [
    {
      "record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 2
      },
      "values": {
        "DIS_SITE_CODE": "A230",
        "CONTRACT_NAME": "DESB",
        "LOCATION_NAME": "CANBERRA",
        "SITE_NAME": "Vision Australia",
        "SITE_CONTACT_PHONE": "61325800",
        "SITE_ADDRESS_LN": "2nd Floor 22 East Row",
        "SITE_LOCALITY_NAME": "CANBERRA",
        "SITE_STATE_CD": "ACT",
        "SITE_POSTCODE": "2601",
        "SITE_URL": "www.visionaustralia.org.au",
        "SITE_EMAIL_ADDRESS": "kal.perera@visionaustralia.org",
        "ESA_CD_1": "5ACT",
        "ESA_CD_2": "    ",
        "ESA_CD_3": "    ",
        "AGENT_FREECALL_NUM": "          ",
        "PHONE_NUMBER": "61325800",
        "LATITUDE": "-35.2791945",
        "LONGITUDE": "149.1306937",
        "__unnamed_19": ""
      }
    },
    {
      "record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 3
      },
      "values": {
        "DIS_SITE_CODE": "A290",
        "CONTRACT_NAME": "DESB",
        "LOCATION_NAME": "YOUNG",
        "SITE_NAME": "Job Centre Australia",
        "SITE_CONTACT_PHONE": "1800466046",
        "SITE_ADDRESS_LN": "2B Campbell Street",
        "SITE_LOCALITY_NAME": "YOUNG",
        "SITE_STATE_CD": "NSW",
        "SITE_POSTCODE": "2594",
        "SITE_URL": "www.jobcentreaustralia.com.au",
        "SITE_EMAIL_ADDRESS": "jcayoung@jobcentreaustralia.com.au",
        "ESA_CD_1": "5ACT",
        "ESA_CD_2": "    ",
        "ESA_CD_3": "    ",
        "AGENT_FREECALL_NUM": "1800466046",
        "PHONE_NUMBER": "63823222",
        "LATITUDE": "-34.31470378",
        "LONGITUDE": "148.2943602",
        "__unnamed_19": ""
      }
    }
  ],
  "observations": [
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "field": "service_location.code",
      "value": "A230",
      "source_fields": [
        "DIS_SITE_CODE"
      ],
      "raw_value": [
        "A230"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.77,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "service_location",
      "group_id": "389901b7e59d66d12a8098f2e99b4dd951b73e97f3c5a8c70879267cb22b4660",
      "group_name": "service_location_record",
      "id": "043814ac7aa7d75cced0105adb20f7927daa7f8be5e9fdcd56fe36a819590985"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "field": "service_location.contract_name",
      "value": "DESB",
      "source_fields": [
        "CONTRACT_NAME"
      ],
      "raw_value": [
        "DESB"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.77,
        "field_confidence": 0.95
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "service_location",
      "group_id": "389901b7e59d66d12a8098f2e99b4dd951b73e97f3c5a8c70879267cb22b4660",
      "group_name": "service_location_record",
      "id": "03e2d9dafe8a146d9d212afad396b61439d743bd421accedf4126617bb1f3598"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "field": "service_location.name",
      "value": "CANBERRA",
      "source_fields": [
        "LOCATION_NAME"
      ],
      "raw_value": [
        "CANBERRA"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.77,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "service_location",
      "group_id": "389901b7e59d66d12a8098f2e99b4dd951b73e97f3c5a8c70879267cb22b4660",
      "group_name": "service_location_record",
      "id": "362c27662af99f7a87906201204d0ee0cff43bcda4f48e069397b94de724f67f"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "field": "service_location.address_line",
      "value": "2nd Floor 22 East Row",
      "source_fields": [
        "SITE_ADDRESS_LN"
      ],
      "raw_value": [
        "2nd Floor 22 East Row"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.77,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "service_location",
      "group_id": "389901b7e59d66d12a8098f2e99b4dd951b73e97f3c5a8c70879267cb22b4660",
      "group_name": "service_location_record",
      "id": "af3a688d0d28f9a7dfbe775cbd37dfcb46ddae8752196cb276ccd3acbc51bbee"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "field": "service_location.website",
      "value": "www.visionaustralia.org.au",
      "source_fields": [
        "SITE_URL"
      ],
      "raw_value": [
        "www.visionaustralia.org.au"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.77,
        "field_confidence": 0.93
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "service_location",
      "group_id": "389901b7e59d66d12a8098f2e99b4dd951b73e97f3c5a8c70879267cb22b4660",
      "group_name": "service_location_record",
      "id": "a753d5f7d6f264628337ddc0add290a104f62d6ce7f7a484013ad82bdc663f61"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "field": "service_location.latitude",
      "value": "-35.2791945",
      "source_fields": [
        "LATITUDE"
      ],
      "raw_value": [
        "-35.2791945"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.77,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "decimal",
      "cardinality": "one",
      "scope": "service_location",
      "group_id": "389901b7e59d66d12a8098f2e99b4dd951b73e97f3c5a8c70879267cb22b4660",
      "group_name": "service_location_record",
      "id": "7a7f3caf17fc54ca913abf3dbebb80561e38bfbdbb3b3485c84a0fc0d2dec673"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "field": "service_location.longitude",
      "value": "149.1306937",
      "source_fields": [
        "LONGITUDE"
      ],
      "raw_value": [
        "149.1306937"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.77,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "decimal",
      "cardinality": "one",
      "scope": "service_location",
      "group_id": "389901b7e59d66d12a8098f2e99b4dd951b73e97f3c5a8c70879267cb22b4660",
      "group_name": "service_location_record",
      "id": "d9409724f02da8f5a1a692d426ffd6802122222a18f87d8fff7dc1dd764ab3cd"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "field": "contact.phone",
      "value": "61325800",
      "source_fields": [
        "SITE_CONTACT_PHONE"
      ],
      "raw_value": [
        "61325800"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.77,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "contact",
      "group_id": "cebcb055b7fdfdcfd217b4f09e46a9e3bd0518eac07db180cb9a9f63c27ee71e",
      "group_name": "site_contact",
      "id": "d73dbd396826e8144aacbb8dc835aa6225dc79dc93df6e4e8225b820523b946d"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "field": "contact.email",
      "value": "kal.perera@visionaustralia.org",
      "source_fields": [
        "SITE_EMAIL_ADDRESS"
      ],
      "raw_value": [
        "kal.perera@visionaustralia.org"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.77,
        "field_confidence": 0.95
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "contact",
      "group_id": "cebcb055b7fdfdcfd217b4f09e46a9e3bd0518eac07db180cb9a9f63c27ee71e",
      "group_name": "site_contact",
      "id": "ea66b42297949f617ca399fc0790f1bb0e1f9464f3f72bd942af77cc6469c53f"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "field": "address.locality",
      "value": "CANBERRA",
      "source_fields": [
        "SITE_LOCALITY_NAME"
      ],
      "raw_value": [
        "CANBERRA"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "05b0269c8deeec4a9f736999097befb7dc77ca16d2f4e6b2f5eeeaa329097b2a",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.77,
        "field_confidence": 0.93
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "id": "057554c130f11a8eb1af91e9121c04ada050476fc1896b7219a5a3f75c1bf96f"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 3; measured/reserved input/output: 22911/3546; calculated cost: 0.00838725.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **SITE_NAME**: Retained as the raw subject label via subject_label_field; the dataset does not establish that it is a legal name or trading name.
- **ESA_CD_1**: Opaque ESA code; no supplied code definitions or matching ontology field.
- **ESA_CD_2**: Opaque ESA code; no supplied code definitions or matching ontology field.
- **ESA_CD_3**: Opaque ESA code; no supplied code definitions or matching ontology field.
- **PHONE_NUMBER**: Generic phone number header does not establish whether this is a contact phone, site line, or another telephone role.
- **__unnamed_19**: Unnamed trailing column; sample cells are empty, and no meaning can be established.

## Uncertainties

- No documentation was supplied; field interpretations rely on exact headers and the shown sample values only.
- SITE_NAME is preserved only as the raw subject label and is not asserted to be a legal entity name or trading name.
- The source describes provider locations but supplies no ABN/ACN or authoritative legal-holder evidence; service_provider role does not assert incorporation or ownership.
- Rows may repeat a physical location across contracts; grouping and identity resolution beyond the supplied site code are not inferred.
- SITE_LOCALITY_NAME, SITE_STATE_CD and SITE_POSTCODE are mapped as service-location address attributes, not registered addresses.
- PHONE_NUMBER, ESA_CD_1, ESA_CD_2 and ESA_CD_3 remain unmapped because their specific meaning is not established.
- The trailing unnamed column is preserved in the unmapped inventory; shown sample values are blank.
- Publication proxy 2016-05-27 is supplied by the source envelope and is not a claim that individual rows changed on that date.
- The supplied source metadata provides no detailed documentation, so semantic conclusions rest on descriptive title/notes, exact headers, sample rows, ontology definitions, and validation examples.
- SITE_NAME is preserved only as a subject label, not mapped as a legal or trading name; provider legal identity and ownership remain unresolved.
- LOCATION_NAME and SITE_ADDRESS_LN are appropriately treated as location-scoped. State/locality/postcode use address-scoped concepts, but are disclosed as service-location attributes rather than registered addresses.
- The dataset includes a trailing unnamed column and generic PHONE_NUMBER field; both are explicitly left unmapped. ESA codes are likewise left unmapped because no definitions or compatible ontology field are supplied.
- The record-grain wording is cautious and compatible with evidence showing repeated DIS_SITE_CODE values across DESA/DESB rows; no unsupported collapse or entity linking is asserted.
- SITE_NAME as subject_label_field and service_provider subject role do not create legal-name, trading-name, or ownership claims under the supplied engine semantics.
- The publication proxy is disclosed as policy metadata, not row-change time; engine envelope behavior and successful validation support this implementation.
- Confidence scores are qualitative and somewhat high given documentation is absent, but the mapping's explicit limitations and field-level evidence make this a caution rather than a semantic blocker.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0d406-6e49-74a1-8378-5cc40e693d37/run/01a0d40b-b31f-7510-8f73-152a45363440?start_time=2026-09-24T15%3A32%3A11.679596%2B00%3A00)