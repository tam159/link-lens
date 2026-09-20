# Mapping review: Employment Services Provider Locations and Contacts
Config version **2**, hash `b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `0034e176b580405064272e688c7bf51230f051880263cdeeb5107ac00bd7a979`.
Grain: One employment-services service-location record per site, contract, and service-area row. Subject: **service_provider**.
Reader: `{"format": "csv", "encoding": "cp1252", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| SITE_ADDRESS_LN | address.full | trim | 0.96 | Exact header SITE_ADDRESS_LN; supplied sample row 2 contains '2nd Floor 22 East Row'. Dataset title 'Employment Services Provider Locations and Contacts' and dataset notes describe location information; no documentation supports treating this as a registered address. |
| SITE_LOCALITY_NAME | address.locality | trim | 0.98 | Exact header SITE_LOCALITY_NAME; supplied sample row 2 contains 'CANBERRA', alongside the site address and state/postcode fields. |
| SITE_STATE_CD | address.state | trim, uppercase, enum | 0.97 | Exact header SITE_STATE_CD; supplied sample row 2 contains 'ACT', an ontology state value; enum restricts emitted values to ontology values. |
| SITE_POSTCODE | address.postcode | trim, postcode | 0.94 | Exact header SITE_POSTCODE; supplied sample row 2 contains '2601'. The postcode operation validates source text and does not zero-pad damaged values. |

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
      "extractor_version": "extractor-1:b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
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
      "config_hash": "b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.72,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "ed9e52fb523e5e13d0fe9d26a4c3f1547f3c9c9967110093f9e488980e31b9ea"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
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
      "config_hash": "b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.72,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "08aaf3250be436440cccb558af03219f11b72e8b5442c6f909ec5c915031e2ab"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
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
      "config_hash": "b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.72,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "bb7c6f180a975c4662c6055777959b495a5c2f2b2e962f0cda43c4465bb0ba72"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "9fb844d1a1dbfc59650eab0e6133f5b8430e435ace6f458418f28cd9124ff9a2",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
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
      "config_hash": "b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.72,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "684168328855812fd688ee8957074740a914759d29f44f9be0a0d0608bb05595"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
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
      "config_hash": "b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.72,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "06fbe1fed105ad4d07821fb28a7903799c81ef0c747d9f88d260c7d7ad40c2af"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
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
      "config_hash": "b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.72,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "21018582f177fa46604f697b49c58d6ac25a710813bef6f585a8e5615c242940"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
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
      "config_hash": "b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.72,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "39692ee900af398e3c339ee8b5f86364ae20eeb43b452a219bc1024cffcd705e"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "048629cb8da742f04b3f94ba2c9bba343543966c3f337e4d6d83287adc24913a",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
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
      "config_hash": "b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.72,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "85683c49110c31df984a8b8684833e937df0fb42b2d3a4d99c01af10bf4a6e03"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "a04e4162f7c4f87fc40748e9ed56fb1f8dfd9a66644220e37316fa3acb21dc7d",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
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
      "config_hash": "b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.72,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "0a77ebf1459523055a4da7b98d95a3c16de6456221db6eb3abd20b0ac2060bf2"
    },
    {
      "source_id": "638f89d7-1c12-4db9-8342-abfcd7b49e95",
      "source_record_id": "a04e4162f7c4f87fc40748e9ed56fb1f8dfd9a66644220e37316fa3acb21dc7d",
      "observed_at": "2016-05-27T00:00:00+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:11.621160+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
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
      "config_hash": "b1f6967915d1d9e97a7f200f00411e033a7b55455161bc8197c29fdc1a8a88f8",
      "subject_role": "service_provider",
      "source_kind": "service_locations",
      "address_role": "service_location",
      "confidence": {
        "source_reliability": 0.72,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "22134997c05f9a29f43e94bac4f26c7c676ed515d7312f87ab22d7095b221017"
    }
  ]
}
```

## Checks

Validation: 250 records; 4 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 4; measured/reserved input/output: 37946/15695; calculated cost: 0.0283205.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **DIS_SITE_CODE**: Site/distribution code has no canonical identifier field; its scope is undocumented and it is not treated as an entity or address identifier.
- **CONTRACT_NAME**: Values such as 'DESB' and 'DESA' are not documented as legal entities, trading names, or entity types; no contract/reporting-group target exists in the ontology.
- **LOCATION_NAME**: A location label such as 'CANBERRA' is not sufficient evidence of a legal or trading name and has no separate ontology field.
- **SITE_NAME**: Retained as the raw subject label via subject_label_field; supplied values such as 'Vision Australia' and 'Job Centre Australia' are not supported by this source as current legal or trading names.
- **SITE_CONTACT_PHONE**: Contact phone has no corresponding ontology field.
- **SITE_URL**: The source presents this URL with site/provider contact and location data, but does not establish legal-entity ownership; entity.website would overstate the supported subject.
- **SITE_EMAIL_ADDRESS**: Contact email has no corresponding ontology field.
- **ESA_CD_1**: Employment service-area code has no corresponding ontology field.
- **ESA_CD_2**: Employment service-area code has no corresponding ontology field; supplied samples contain whitespace padding.
- **ESA_CD_3**: Employment service-area code has no corresponding ontology field; supplied samples contain whitespace padding.
- **AGENT_FREECALL_NUM**: Freecall phone number has no corresponding ontology field; supplied sample row 2 contains whitespace padding.
- **PHONE_NUMBER**: Phone number has no corresponding ontology field.
- **LATITUDE**: Geographic latitude has no corresponding ontology field.
- **LONGITUDE**: Geographic longitude has no corresponding ontology field.
- **__unnamed_19**: Unnamed export-artifact column; supplied sample rows are empty and no ontology field supports it.

## Uncertainties

- Documentation is empty; identifier definitions, current-name indicators, update semantics, and field-level authority are unconfirmed.
- No source field supports a current legal-name or trading-name claim; SITE_NAME is retained only as a raw subject label.
- The source does not establish legal entities, registered names, entity types, ABNs, ACNs, statuses, or registration dates; none are inferred.
- SITE_URL is deliberately unmapped because entity.website would assert legal-entity ownership not established by this service-location source.
- Mapped address fields describe a service location, not a registered legal-entity address.
- Repeated physical locations across contracts or service areas remain separate source observations; no reconciliation is performed.
- The publication_proxy 2016-05-27T00:00:00 supplied in the source envelope is used under publication_proxy; it is not a row-change timestamp.
- The source-envelope licence is Creative Commons Attribution 3.0 Australia and is emitted as envelope metadata, not mapped from a source column.
- All authority and field scores are provisional and require human review.
- The mapping is deliberately partial: it maps only service-location address components and leaves identifiers, names, website, contacts, ESA codes, coordinates, and contract fields unmapped, which is appropriate given the empty documentation and ontology limits.
- SITE_NAME is retained as a raw subject label rather than asserted as a legal or trading name; this preserves the legal/trading distinction, though human review should confirm the intended subject label semantics.
- The row grain and service_provider role are reasonable for the title, notes, and repeated site/contract/ESA examples, but DIS_SITE_CODE scope and CONTRACT_NAME semantics remain unconfirmed.
- Address fields are explicitly treated as service locations rather than registered legal-entity addresses.
- The publication proxy is disclosed as an observation-time policy rather than a row-change timestamp; source documentation has no explicit timestamp.
- Four invalid three-digit postcodes were quarantined rather than padded, which is semantically conservative.
- Confidence values are provisional judgements and are not independently calibrated; source reliability 0.72 is disclosed and should not be read as measured accuracy.
- The exploration script failed because it treated header/value dictionaries as sequences, but supplied discovery records and validation evidence still support the reviewed columns and the validator passed.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b936-22e8-73a1-b7f7-c60ff5cdca70/run/01a0b936-4eda-7911-9c4e-e2b368fd5c89?start_time=2026-09-19T10%3A28%3A59.226232%2B00%3A00)