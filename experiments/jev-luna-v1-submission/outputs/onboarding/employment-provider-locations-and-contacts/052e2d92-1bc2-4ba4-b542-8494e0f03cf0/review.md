# Mapping review: Employment Services Provider Locations and Contacts
Config version **2**, hash `8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979`.
Grain: One employment-services service-location record per site, contract, and service-area row. Subject: **service_provider**.
Reader: `{"format": "csv", "encoding": "cp1252", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| SITE_ADDRESS_LN | address.full | trim | 0.96 | Exact source header SITE_ADDRESS_LN; sample row 2 value '2nd Floor 22 East Row' is a site street address. |
| SITE_LOCALITY_NAME | address.locality | trim | 0.98 | Exact source header SITE_LOCALITY_NAME; sample row 2 value 'CANBERRA' matches the site locality. |
| SITE_STATE_CD | address.state | trim, uppercase, enum | 0.97 | Exact source header SITE_STATE_CD; sample row 2 value 'ACT' is an ontology state code. |
| SITE_POSTCODE | address.postcode | trim, postcode | 0.94 | Exact source header SITE_POSTCODE; sample row 2 value '2601' is a four-digit site postcode and is retained as a string. |
| SITE_URL | entity.website | trim, website | 0.9 | Exact source header SITE_URL; sample row 2 value 'www.visionaustralia.org.au' is presented as the site URL. |

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
      "extractor_version": "extractor-1:8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "field": "address.full",
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
      "config_hash": "8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.78,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "5b62c364c6ca6cf4d722ea6da662128ce5471b001de6acb024b0f0ed31026bf3"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
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
      "config_hash": "8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.78,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "fab2e8c3a586d43028b3e52a92e5dde2a57a344cd57f092abe1b24cb0f230bb0"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "field": "address.state",
      "value": "ACT",
      "source_fields": [
        "SITE_STATE_CD"
      ],
      "raw_value": [
        "ACT"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.78,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "7f8a1b695c366dff4cbb6325fa3cd5782554d432c42c92c438d2fe0a4ab50e50"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "field": "address.postcode",
      "value": "2601",
      "source_fields": [
        "SITE_POSTCODE"
      ],
      "raw_value": [
        "2601"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.78,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "1ea7fecc4a0ab03be6b71c15a72d9d75beb2d8a608b1898986eaed1241bd4006"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "field": "entity.website",
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
      "config_hash": "8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.78,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "f3876c58c8ea2378f27f437a71511bce6c0dd12f1e789550938a80196af91145"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "field": "address.full",
      "value": "2B Campbell Street",
      "source_fields": [
        "SITE_ADDRESS_LN"
      ],
      "raw_value": [
        "2B Campbell Street"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.78,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "c03401929666a628b3b215a98f0ccd04dc89bdb8d4052f92a462fb0ac4ea0ada"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "field": "address.locality",
      "value": "YOUNG",
      "source_fields": [
        "SITE_LOCALITY_NAME"
      ],
      "raw_value": [
        "YOUNG"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.78,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "71989154689649dd5e6a79418e912e3d65782ae815f1a7dfe1195be1f9b2ee87"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "field": "address.state",
      "value": "NSW",
      "source_fields": [
        "SITE_STATE_CD"
      ],
      "raw_value": [
        "NSW"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.78,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "66f6ad53401c00b0e5f7774e76eabf7cbdaa943eebf0e83be6cb2c07354531a7"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "field": "address.postcode",
      "value": "2594",
      "source_fields": [
        "SITE_POSTCODE"
      ],
      "raw_value": [
        "2594"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.78,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "64e1ec75cfa7aae20fc550cf841c0a091d983c438a70e45583bdb2256412c657"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "field": "entity.website",
      "value": "www.jobcentreaustralia.com.au",
      "source_fields": [
        "SITE_URL"
      ],
      "raw_value": [
        "www.jobcentreaustralia.com.au"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "8240429754c36bea3c297f13824eb12ead13cc3acd3f31c95de461d1ae472cf6",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.78,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "15541806275dfab48db685be1371bd2960febd3a69a612d94d8d7e96c4fe1f01"
    }
  ]
}
```

## Checks

Validation: 250 records; 4 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 4; measured/reserved input/output: 20344/3786; calculated cost: 0.009629200000000001.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **DIS_SITE_CODE**: Site/distribution code has no canonical identifier field in the supplied ontology; its entity or site scope is undocumented.
- **CONTRACT_NAME**: May denote a program, contract, or reporting group; no ontology field supports this and it must not be treated as a legal entity.
- **LOCATION_NAME**: Location label is not sufficient evidence for a canonical legal or trading name.
- **SITE_NAME**: Retained as raw subject_label_field, but no confident canonical legal-name or trading-name mapping is justified by the source.
- **SITE_CONTACT_PHONE**: Phone fields are not represented in the supplied ontology.
- **SITE_EMAIL_ADDRESS**: Email fields are not represented in the supplied ontology.
- **ESA_CD_1**: Employment service-area code has no corresponding ontology field.
- **ESA_CD_2**: Employment service-area code has no corresponding ontology field; preview values are whitespace padding.
- **ESA_CD_3**: Employment service-area code has no corresponding ontology field; preview values are whitespace padding.
- **AGENT_FREECALL_NUM**: Phone fields are not represented in the supplied ontology; preview value is whitespace padding in row 2.
- **PHONE_NUMBER**: Phone fields are not represented in the supplied ontology.
- **LATITUDE**: Geographic coordinate fields are not represented in the supplied ontology.
- **LONGITUDE**: Geographic coordinate fields are not represented in the supplied ontology.
- **__unnamed_19**: Unnamed export-artifact column; preview values are empty and it has no ontology mapping.

## Uncertainties

- Documentation is empty, so identifier definitions, update semantics, and field-level authority are unconfirmed.
- The publication_proxy 2016-05-27T00:00:00 is used as the observation-time proxy from the source envelope; no row-level statement date is supplied.
- The source describes provider locations and contacts but does not establish legal entities, registered names, entity types, ABNs, ACNs, statuses, or registration dates.
- SITE_NAME is preserved only as a raw subject label; it is not asserted to be a legal name or trading name.
- DIS_SITE_CODE scope is uncertain and is not used as a canonical entity or address identifier.
- Repeated physical locations across contracts or service areas are retained as separate source observations; no reconciliation is performed.
- All field and source-reliability scores are provisional and require human review.
- The source envelope licence is Creative Commons Attribution 3.0 Australia; it is supplied as envelope metadata rather than a mapped source column.
- The mapping is deliberately partial and leaves legal/trading identity, identifiers, status, contract/reporting-group semantics, service-area codes, contacts, and coordinates unmapped, appropriately given the source documentation and ontology.
- SITE_NAME is retained only as a raw subject label and is not incorrectly asserted as a legal or trading name.
- The publication timestamp is used as an explicitly disclosed observation-time proxy; no row-level date is available.
- The postcode validator quarantined four three-digit values rather than inventing leading zeros, which is appropriate. Human review should note that the validation feedback reports 250 records versus the discovery count of 300, but the supplied facts do not establish this as a mapping defect.
- Website mapping is plausible as a provider/site website but its exact ownership is not established; this is a limitation rather than a blocker.
- The source documentation is empty, so DIS_SITE_CODE grain and CONTRACT_NAME reporting-group semantics remain unresolved and are correctly not mapped.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b898-85ef-74f3-8734-6e8a5bf54b6a/run/01a0b89e-039e-7ea2-a1ac-3406bf759aea?start_time=2026-09-19T07%3A42%3A38.494214%2B00%3A00)