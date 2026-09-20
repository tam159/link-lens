# Mapping review: Employment Services Provider Locations and Contacts
Config version **3**, hash `50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979`.
Grain: One provider service-site offering under a contract and Employment Service Area code.. Subject: **service_provider**.
Reader: `{"format": "csv", "encoding": "cp1252", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| SITE_ADDRESS_LN | address.full | trim | 0.75 | Exact header SITE_ADDRESS_LN. Discovery rows 2–9 contain street-address text: "2nd Floor 22 East Row", "2B Campbell Street", "55 Peter Street", and "Shop 6 & 7 The HUB Wynyard Street". The dataset title is "Employment Services Provider Locations and Contacts" and its notes state it provides location, service and contact information. Locality, state and postcode are separately headed fields. |
| SITE_LOCALITY_NAME | address.locality | trim | 0.9 | Exact header SITE_LOCALITY_NAME; discovery row 2 is "CANBERRA", row 3 is "YOUNG", and rows 4–9 include "WAGGA WAGGA", "TUMUT", and "COOTAMUNDRA". These occur beside the separately supplied site-address, state, and postcode components. |
| SITE_STATE_CD | address.state | trim, uppercase, enum | 0.9 | Exact header SITE_STATE_CD. Discovery rows show "ACT" and "NSW"; validation output additionally confirms direct "QLD" output. These are ontology state literals; enum mapping does not infer a state from another field. |
| SITE_POSTCODE | address.postcode | trim, postcode | 0.88 | Exact header SITE_POSTCODE. Discovery row 2 is "2601", row 3 is "2594", and rows 4–9 include "2650", "2720", and "2590". Validation confirms preserved "4300" output and quarantines short raw values such as "871" rather than zero-padding. |

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
      "extractor_version": "extractor-1:50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
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
      "config_hash": "50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.7,
        "field_confidence": 0.75
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "0cbb2353818808a38d5687c595427ba4bcc52da5a2b3c2f30cee0ab42bde98f3"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
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
      "config_hash": "50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.7,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "fefd080747ca6f3e1336eafef50ce4efb1c8e65643d976841868e753dcfad805"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
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
      "config_hash": "50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.7,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "10bf365d45878367b8c84547a07d0d12ddd491a076e46578f01b6e9c87200f1e"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
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
      "config_hash": "50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.7,
        "field_confidence": 0.88
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "73d8973df5d0d72845185238657edc01dcf57efe8a1ded56bc594652bfe80e31"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
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
      "config_hash": "50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.7,
        "field_confidence": 0.75
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "977e6e183267f546a8e50d7290f44c33848eedfc981a25576f3b57e1b26cf005"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
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
      "config_hash": "50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.7,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "f4ca3562b572288e7f56efd19d47249b5f7ffc3d4336fd7b481c096df649008d"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
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
      "config_hash": "50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.7,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "b88ac7899d3a6c98dc69d08d4fa55422b073c2893cd0e5fd21ce52d71307a610"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
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
      "config_hash": "50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.7,
        "field_confidence": 0.88
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "e6fab05659edeac71d0b4a7fc15fda15c59bd7862c9a20d8cfc8ba8e00823601"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "a04e4162f7c4f87fc40748e9ed56fb1f8dfd9a66644220e37316fa3acb21dc7d",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
      "field": "address.full",
      "value": "55 Peter Street",
      "source_fields": [
        "SITE_ADDRESS_LN"
      ],
      "raw_value": [
        "55 Peter Street"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 4
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.7,
        "field_confidence": 0.75
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "09ab1d0111c8e0dc709f5e28c2c471214c28bca74e6765146c86aa4b8b70e10b"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "a04e4162f7c4f87fc40748e9ed56fb1f8dfd9a66644220e37316fa3acb21dc7d",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
      "field": "address.locality",
      "value": "WAGGA WAGGA",
      "source_fields": [
        "SITE_LOCALITY_NAME"
      ],
      "raw_value": [
        "WAGGA WAGGA"
      ],
      "raw_locator": {
        "snapshot_sha": "0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979",
        "sheet": "csv",
        "row": 4
      },
      "snapshot_id": "6db5393d177fbca86b33c90f4e593bd2ecb860a740dbdf21f56bf8d9dc2fa359",
      "config_hash": "50f578a4e6d3000c7d17622b63804059ef65a65790f7c330145dc84221ecb3b4",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.7,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "f1fe8ae918d6c58584a303d9358cb09a4f59c0fc1bbec783e5c07cf4b21a7596"
    }
  ]
}
```

## Checks

Validation: 250 records; 4 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 7; measured/reserved input/output: 52443/19487; calculated cost: None.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **DIS_SITE_CODE**: Site-like code (for example A230); the ontology has no site identifier, and it is not a legal-entity identifier.
- **CONTRACT_NAME**: Contract/program code (for example DESB or DESA); no corresponding canonical field.
- **LOCATION_NAME**: Location label (for example CANBERRA); locality is directly supplied in SITE_LOCALITY_NAME, while this field has no separate canonical role.
- **SITE_NAME**: Retained as subject_label_field because it is a provider/site-facing label (for example Vision Australia or Job Centre Australia), not evidence of a legal or registered trading name.
- **SITE_CONTACT_PHONE**: Site contact telephone number; no telephone canonical field.
- **SITE_URL**: The header and dataset purpose support a site/provider contact URL, but there is no location-website field and legal-entity ownership is not established; do not map to entity.website.
- **SITE_EMAIL_ADDRESS**: Site email address; no email canonical field.
- **ESA_CD_1**: Employment Service Area code; no corresponding canonical field and no authoritative code meaning is supplied.
- **ESA_CD_2**: Additional Employment Service Area code; discovery values are whitespace and no corresponding canonical field exists.
- **ESA_CD_3**: Additional Employment Service Area code; discovery values are whitespace and no corresponding canonical field exists.
- **AGENT_FREECALL_NUM**: Freecall telephone number; no telephone canonical field.
- **PHONE_NUMBER**: Telephone number; no telephone canonical field.
- **LATITUDE**: Geographic coordinate; no latitude canonical field.
- **LONGITUDE**: Geographic coordinate; no longitude canonical field.
- **__unnamed_19**: Unnamed trailing column; discovery samples are empty and it has no canonical meaning.

## Uncertainties

- This is a service-location dataset, not a company, business-name, or licence register. It does not establish legal-entity identity, legal name, trading-name status, entity type, entity status, or registration date.
- SITE_NAME is retained only as a raw subject label. No supplied documentation or identifier establishes it as a legal name or trading name.
- Discovery rows 4–5 share DIS_SITE_CODE A300, SITE_NAME, and address but differ in CONTRACT_NAME (DESA/DESB) and ESA_CD_1 (4SOE/5MRV). Rows are service-site offerings, not unique entities and not necessarily unique physical locations.
- SITE_ADDRESS_LN is mapped only as the source-supplied street-address text. It is not an assembled address: SITE_LOCALITY_NAME, SITE_STATE_CD, and SITE_POSTCODE remain separate observations.
- The 0.75 confidence for SITE_ADDRESS_LN is an uncalibrated mapping judgement, not a measured quality score. It is acceptable under the supplied semantic review, but deliberately lower than locality/state/postcode because the header's abbreviated "LN" is supported by repeated street-text samples rather than supplied field documentation, and the value is only one component of the address. It does not indicate low usability or establish entity linkage.
- SITE_URL is intentionally unmapped because the evidence supports only a site/provider contact URL, not a website owned by an identified legal entity.
- No per-record observation, effective, or current-status date is supplied. observed_at uses only the supplied publication proxy, 2016-05-27T00:00:00, not a per-site effective date.
- No explicit country field is supplied; address.country is intentionally unmapped rather than inferred from Australian provenance or state/postcode values.
- The postcode operation emits only preserved valid postcodes. Validation quarantined raw short values "871", "850", "836", and "822"; no leading zeroes are invented.
- No dataset documentation pages were supplied. Mapped-field evidence is therefore limited to exact headers, discovery samples, dataset title/notes, and validation output. Authority and confidence scores are provisional and require human review.
- The supplied exploratory profiling failed before full-file profiling. Claims about full-file duplication, trailing-column population, and code cardinality are limited to the supplied samples and validation feedback.
- The mapping is intentionally partial and appropriately does not assert a legal entity, legal/trading name, registration identifier, entity status, licence, reporting group, or website ownership. `SITE_NAME` is only a subject label; human reviewers should preserve that non-entity interpretation.
- The physical/source grain is correctly disclosed as a service-site offering under contract/ESA, supported by repeated `DIS_SITE_CODE` values across DESA/DESB and ESA codes. There are no filters collapsing these records, so the mapping does not wrongly claim unique sites or entities.
- All mapped address components are service-location attributes, not entity registered/principal addresses. `address_role: service_location` makes this explicit. The ontology address fields themselves lack a role qualifier, so downstream use must retain the record role/context.
- `address.full` receives only `SITE_ADDRESS_LN`, a street-address component rather than a complete postal address. This is explicitly disclosed and the separate locality/state/postcode mappings prevent an unsupported assembled value. The canonical field name `full` could be misread downstream; this is a disclosed semantic limitation, not a blocker because the raw component is faithfully preserved and provenance is supplied.
- There is no source documentation beyond title/notes and headers. The publication proxy supports neither current-status semantics nor per-record effective/observation dates. The stated proxy policy and limitation are appropriate, but historical currency remains uncertain.
- `address.country` is deliberately unmapped. This is conservative despite Australian source context and requires no remediation absent an explicit source field.
- The state enum does not include an `OTHER` fallback mapping. Evidence only supports ACT/NSW directly and says validation produced QLD; full-file state-domain coverage was not successfully profiled. Unknown or unexpected raw state codes should be quarantined/unmapped rather than coerced. This is an operational coverage limitation, not evidence that the current mappings are semantically wrong.
- Confidence values and source reliability are uncalibrated judgements. The mapping says so and does not offer unsupported link confidence. The 0.75 address confidence is conservative and adequately tied to header/sample evidence.
- The supplied discovery preview itself shows eight records, while the narrative calls it a six-row preview. This inconsistency is immaterial to the address mappings and is not relied upon for a substantive claim. The failed profiling is candidly disclosed.
- The successful validator output establishes parse behavior only, not semantic truth; the mapping correctly repeats that distinction.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b2fc-fdd6-7073-a73f-c93b77645389/run/01a0b2fd-5dd1-75a1-b011-7f4a11391f4e?start_time=2026-09-18T05%3A29%3A04.209102%2B00%3A00)