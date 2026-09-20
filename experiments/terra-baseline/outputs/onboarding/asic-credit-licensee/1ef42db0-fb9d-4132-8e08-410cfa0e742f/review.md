# Mapping review: ASIC – Credit Licensee Dataset
Config version **1**, hash `7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `3afe1c545551249d82b9446b6db75c87c24ac0307792c2991deaffcf302d0325`.
Grain: One Credit Licence register entry/licensee record per row; CRED_LIC_NUM is a source licence-entry identifier but is not represented in the supplied canonical-field subset.. Subject: **licence_holder**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| CRED_LIC_ABN_ACN | entity.abn | trim, abn | 0.9 | Help file p.10 defines CRED_LIC_ABN_ACN as the licensee ABN or ACN; preview row 2 contains 80005443292. |
| CRED_LIC_ABN_ACN | entity.acn | trim, acn | 0.9 | Help file p.10 says this mixed field contains either ABN or ACN; ACN validation emits only valid 9-digit ACNs. |
| CRED_LIC_BN | entity.trading_name | split, trim | 0.82 | Help file p.12 calls CRED_LIC_BN current or previous operating/business names and specifies tilde delimiters; preview row 5 is PLANNING PARTNERS. |
| CRED_LIC_LOCALITY | address.locality | trim | 0.93 | Help file p.11 defines CRED_LIC_LOCALITY as town/city from the current principal business address; preview row 2 is LEONGATHA. |
| CRED_LIC_STATE | address.state | trim, uppercase, enum | 0.93 | Help file p.11 defines CRED_LIC_STATE as the state from the current principal business address; preview row 2 is VIC. |
| CRED_LIC_PCODE | address.postcode | trim, postcode | 0.9 | Help file p.12 defines CRED_LIC_PCODE as postcode from the current principal business address; preview row 2 is 3953. |

## Before / after

```json
{
  "raw": [
    {
      "record_id": "c44e2b22ef646d920cc6221c08c90af96127b20c2d4f50cd8f45f1894a7e6908",
      "locator": {
        "snapshot_sha": "3afe1c545551249d82b9446b6db75c87c24ac0307792c2991deaffcf302d0325",
        "sheet": "csv",
        "row": 2
      },
      "values": {
        "REGISTER_NAME": "Credit Licence",
        "CRED_LIC_NUM": "219612",
        "CRED_LIC_NAME": "RELI CAPITAL LTD",
        "CRED_LIC_START_DT": "04/10/2010",
        "CRED_LIC_END_DT": "",
        "CRED_LIC_STATUS": "APPR",
        "CRED_LIC_ABN_ACN": "80005443292",
        "CRED_LIC_AFSL_NUM": "219612",
        "CRED_LIC_STATUS_HISTORY": "",
        "CRED_LIC_LOCALITY": "LEONGATHA",
        "CRED_LIC_STATE": "VIC",
        "CRED_LIC_PCODE": "3953",
        "CRED_LIC_LAT": "-38.4761569",
        "CRED_LIC_LNG": "145.9458605",
        "CRED_LIC_EDRS": "AFCA",
        "CRED_LIC_BN": "",
        "CRED_LIC_AUTHORISATIONS": "This licence authorises the licensee to:~Engage in credit activities as a credit provider by:~carrying on a business of providing credit being credit the provision of which the National Credit Code applies to; and/or~being a credit provider under a credit contract; and/or~performing the obligations or exercising the rights of a credit provider in relation to a credit contract or proposed credit contract as the credit provider; and/or~providing credit assistance to a consumer which relates to a credit contract or proposed credit contract under which the licensee is or will be the credit provider; and/or~being a mortgagee under a mortgage that secures or will secure obligations under a credit contract under which the licensee is the credit provider; and/or~performing the obligations or exercising the rights of a mortgagee in relation to a mortgage or proposed mortgage which secures or will secure obligations under a credit contract under which the licensee is the credit provider; and/or~being a beneficiary under a guarantee that guarantees obligations under a credit contract under which the licensee is the credit provider; and/or~performing the obligations or exercising the rights of a beneficiary under a guarantee or proposed guarantee which guarantees obligations under a credit contract under which the licensee is the credit provider; and/or~carrying on a business of providing consumer leases; and/or~being a lessor under a consumer lease; and/or~providing credit assistance to a consumer in relation to a consumer lease or proposed consumer lease for which the licensee is the lessor; and/or~performing the obligations or exercising the rights of a lessor in relation to the consumer lease as the lessor"
      }
    },
    {
      "record_id": "c0f550efb4fde61478919f7b28ece3dbfa3406aff83c0c8d3d1deb143a2982ac",
      "locator": {
        "snapshot_sha": "3afe1c545551249d82b9446b6db75c87c24ac0307792c2991deaffcf302d0325",
        "sheet": "csv",
        "row": 3
      },
      "values": {
        "REGISTER_NAME": "Credit Licence",
        "CRED_LIC_NUM": "222213",
        "CRED_LIC_NAME": "LA TROBE FINANCIAL ASSET MANAGEMENT LIMITED",
        "CRED_LIC_START_DT": "16/03/2011",
        "CRED_LIC_END_DT": "",
        "CRED_LIC_STATUS": "APPR",
        "CRED_LIC_ABN_ACN": "27007332363",
        "CRED_LIC_AFSL_NUM": "222213",
        "CRED_LIC_STATUS_HISTORY": "",
        "CRED_LIC_LOCALITY": "MELBOURNE",
        "CRED_LIC_STATE": "VIC",
        "CRED_LIC_PCODE": "3000",
        "CRED_LIC_LAT": "-37.8142454",
        "CRED_LIC_LNG": "144.9631732",
        "CRED_LIC_EDRS": "AFCA",
        "CRED_LIC_BN": "",
        "CRED_LIC_AUTHORISATIONS": "This licence authorises the licensee to:~Engage in credit activities as a credit provider by:~carrying on a business of providing credit being credit the provision of which the National Credit Code applies to; and/or~being a credit provider under a credit contract; and/or~performing the obligations or exercising the rights of a credit provider in relation to a credit contract or proposed credit contract as the credit provider; and/or~providing credit assistance to a consumer which relates to a credit contract or proposed credit contract under which the licensee is or will be the credit provider; and/or~being a mortgagee under a mortgage that secures or will secure obligations under a credit contract under which the licensee is the credit provider; and/or~performing the obligations or exercising the rights of a mortgagee in relation to a mortgage or proposed mortgage which secures or will secure obligations under a credit contract under which the licensee is the credit provider; and/or~being a beneficiary under a guarantee that guarantees obligations under a credit contract under which the licensee is the credit provider; and/or~performing the obligations or exercising the rights of a beneficiary under a guarantee or proposed guarantee which guarantees obligations under a credit contract under which the licensee is the credit provider; and/or~carrying on a business of providing consumer leases; and/or~being a lessor under a consumer lease; and/or~providing credit assistance to a consumer in relation to a consumer lease or proposed consumer lease for which the licensee is the lessor; and/or~performing the obligations or exercising the rights of a lessor in relation to the consumer lease as the lessor"
      }
    }
  ],
  "observations": [
    {
      "source_id": "fa0b0d71-b8b8-4af8-bc59-0b000ce0d5e4",
      "source_record_id": "c44e2b22ef646d920cc6221c08c90af96127b20c2d4f50cd8f45f1894a7e6908",
      "observed_at": "2026-09-17T05:31:11.908502+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T01:08:19.853193+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "field": "entity.abn",
      "value": "80005443292",
      "source_fields": [
        "CRED_LIC_ABN_ACN"
      ],
      "raw_value": [
        "80005443292"
      ],
      "raw_locator": {
        "snapshot_sha": "3afe1c545551249d82b9446b6db75c87c24ac0307792c2991deaffcf302d0325",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "399fd247640b608e71c32996d4d3ac663d5c6708f5de30e50bf1dca618bb6545",
      "config_hash": "7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.86,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "19e0a6eb551d8bc7c3ba094a92b2f41da2148867b9530e0334af219980e449f3"
    },
    {
      "source_id": "fa0b0d71-b8b8-4af8-bc59-0b000ce0d5e4",
      "source_record_id": "c44e2b22ef646d920cc6221c08c90af96127b20c2d4f50cd8f45f1894a7e6908",
      "observed_at": "2026-09-17T05:31:11.908502+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T01:08:19.853193+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "field": "address.locality",
      "value": "LEONGATHA",
      "source_fields": [
        "CRED_LIC_LOCALITY"
      ],
      "raw_value": [
        "LEONGATHA"
      ],
      "raw_locator": {
        "snapshot_sha": "3afe1c545551249d82b9446b6db75c87c24ac0307792c2991deaffcf302d0325",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "399fd247640b608e71c32996d4d3ac663d5c6708f5de30e50bf1dca618bb6545",
      "config_hash": "7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.86,
        "field_confidence": 0.93
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "8d785d099eedb7cb36c697edb341e96fd4910cff58bf4caa1e80df2582013dc5"
    },
    {
      "source_id": "fa0b0d71-b8b8-4af8-bc59-0b000ce0d5e4",
      "source_record_id": "c44e2b22ef646d920cc6221c08c90af96127b20c2d4f50cd8f45f1894a7e6908",
      "observed_at": "2026-09-17T05:31:11.908502+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T01:08:19.853193+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "field": "address.state",
      "value": "VIC",
      "source_fields": [
        "CRED_LIC_STATE"
      ],
      "raw_value": [
        "VIC"
      ],
      "raw_locator": {
        "snapshot_sha": "3afe1c545551249d82b9446b6db75c87c24ac0307792c2991deaffcf302d0325",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "399fd247640b608e71c32996d4d3ac663d5c6708f5de30e50bf1dca618bb6545",
      "config_hash": "7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.86,
        "field_confidence": 0.93
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "3ecef2d3399572ca2bb44c45d2aedaea59596debf97b4f47b97f9d871cc80c46"
    },
    {
      "source_id": "fa0b0d71-b8b8-4af8-bc59-0b000ce0d5e4",
      "source_record_id": "c44e2b22ef646d920cc6221c08c90af96127b20c2d4f50cd8f45f1894a7e6908",
      "observed_at": "2026-09-17T05:31:11.908502+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T01:08:19.853193+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "field": "address.postcode",
      "value": "3953",
      "source_fields": [
        "CRED_LIC_PCODE"
      ],
      "raw_value": [
        "3953"
      ],
      "raw_locator": {
        "snapshot_sha": "3afe1c545551249d82b9446b6db75c87c24ac0307792c2991deaffcf302d0325",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "399fd247640b608e71c32996d4d3ac663d5c6708f5de30e50bf1dca618bb6545",
      "config_hash": "7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.86,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "623a9cfe22642726bdc45423497c5f25c7bfd16286b4d177973c4264963f1dd9"
    },
    {
      "source_id": "fa0b0d71-b8b8-4af8-bc59-0b000ce0d5e4",
      "source_record_id": "c0f550efb4fde61478919f7b28ece3dbfa3406aff83c0c8d3d1deb143a2982ac",
      "observed_at": "2026-09-17T05:31:11.908502+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T01:08:19.853193+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "field": "entity.abn",
      "value": "27007332363",
      "source_fields": [
        "CRED_LIC_ABN_ACN"
      ],
      "raw_value": [
        "27007332363"
      ],
      "raw_locator": {
        "snapshot_sha": "3afe1c545551249d82b9446b6db75c87c24ac0307792c2991deaffcf302d0325",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "399fd247640b608e71c32996d4d3ac663d5c6708f5de30e50bf1dca618bb6545",
      "config_hash": "7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.86,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "a254d9a2a5464ec46059a723d5e5e2fd33d91cfc332d7e4f5a284eab374ac409"
    },
    {
      "source_id": "fa0b0d71-b8b8-4af8-bc59-0b000ce0d5e4",
      "source_record_id": "c0f550efb4fde61478919f7b28ece3dbfa3406aff83c0c8d3d1deb143a2982ac",
      "observed_at": "2026-09-17T05:31:11.908502+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T01:08:19.853193+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "field": "address.locality",
      "value": "MELBOURNE",
      "source_fields": [
        "CRED_LIC_LOCALITY"
      ],
      "raw_value": [
        "MELBOURNE"
      ],
      "raw_locator": {
        "snapshot_sha": "3afe1c545551249d82b9446b6db75c87c24ac0307792c2991deaffcf302d0325",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "399fd247640b608e71c32996d4d3ac663d5c6708f5de30e50bf1dca618bb6545",
      "config_hash": "7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.86,
        "field_confidence": 0.93
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "3af45d80bff6e5739a29bb6d99019246ab0ee4cbffa4d77b23ec4428f0702b5d"
    },
    {
      "source_id": "fa0b0d71-b8b8-4af8-bc59-0b000ce0d5e4",
      "source_record_id": "c0f550efb4fde61478919f7b28ece3dbfa3406aff83c0c8d3d1deb143a2982ac",
      "observed_at": "2026-09-17T05:31:11.908502+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T01:08:19.853193+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "field": "address.state",
      "value": "VIC",
      "source_fields": [
        "CRED_LIC_STATE"
      ],
      "raw_value": [
        "VIC"
      ],
      "raw_locator": {
        "snapshot_sha": "3afe1c545551249d82b9446b6db75c87c24ac0307792c2991deaffcf302d0325",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "399fd247640b608e71c32996d4d3ac663d5c6708f5de30e50bf1dca618bb6545",
      "config_hash": "7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.86,
        "field_confidence": 0.93
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "5347f5f10d7fc2aa455e6c8dee5c59975d4b386813657d7dcd7109755375b951"
    },
    {
      "source_id": "fa0b0d71-b8b8-4af8-bc59-0b000ce0d5e4",
      "source_record_id": "c0f550efb4fde61478919f7b28ece3dbfa3406aff83c0c8d3d1deb143a2982ac",
      "observed_at": "2026-09-17T05:31:11.908502+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T01:08:19.853193+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "field": "address.postcode",
      "value": "3000",
      "source_fields": [
        "CRED_LIC_PCODE"
      ],
      "raw_value": [
        "3000"
      ],
      "raw_locator": {
        "snapshot_sha": "3afe1c545551249d82b9446b6db75c87c24ac0307792c2991deaffcf302d0325",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "399fd247640b608e71c32996d4d3ac663d5c6708f5de30e50bf1dca618bb6545",
      "config_hash": "7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.86,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "741bf6eb499db8dcb79215640a7e20aa088880bf063b2850da833a70e88ac45f"
    },
    {
      "source_id": "fa0b0d71-b8b8-4af8-bc59-0b000ce0d5e4",
      "source_record_id": "5af5be7433de9a2204d759d29bbcbc0e49c7a10b2714af9c9c8adcca689aab2a",
      "observed_at": "2026-09-17T05:31:11.908502+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T01:08:19.853193+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "field": "entity.abn",
      "value": "20090555436",
      "source_fields": [
        "CRED_LIC_ABN_ACN"
      ],
      "raw_value": [
        "20090555436"
      ],
      "raw_locator": {
        "snapshot_sha": "3afe1c545551249d82b9446b6db75c87c24ac0307792c2991deaffcf302d0325",
        "sheet": "csv",
        "row": 4
      },
      "snapshot_id": "399fd247640b608e71c32996d4d3ac663d5c6708f5de30e50bf1dca618bb6545",
      "config_hash": "7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.86,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "9a18a204f15d9f9012fc9b4bbb493c3956b22a4c0263453a512fe1d99db1f372"
    },
    {
      "source_id": "fa0b0d71-b8b8-4af8-bc59-0b000ce0d5e4",
      "source_record_id": "5af5be7433de9a2204d759d29bbcbc0e49c7a10b2714af9c9c8adcca689aab2a",
      "observed_at": "2026-09-17T05:31:11.908502+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T01:08:19.853193+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "field": "address.locality",
      "value": "MASCOT",
      "source_fields": [
        "CRED_LIC_LOCALITY"
      ],
      "raw_value": [
        "MASCOT"
      ],
      "raw_locator": {
        "snapshot_sha": "3afe1c545551249d82b9446b6db75c87c24ac0307792c2991deaffcf302d0325",
        "sheet": "csv",
        "row": 4
      },
      "snapshot_id": "399fd247640b608e71c32996d4d3ac663d5c6708f5de30e50bf1dca618bb6545",
      "config_hash": "7a576c9875d880e98e429210b874ad4744b17b60a03411aa420716cc48baf0e6",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.86,
        "field_confidence": 0.93
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "09b3d2aa0dcd80f631d2017522ecb14d29c22220ea3c82be752287abf231bb5d"
    }
  ]
}
```

## Checks

Validation: 250 records; 6 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 3; measured/reserved input/output: 35725/3565; calculated cost: None.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **REGISTER_NAME**: Identifies the source register (for example, Credit Licence), not a canonical entity or address field.
- **CRED_LIC_NUM**: Unique credit-licensee/licence-entry number (help file p.9); no licence identifier field exists in the supplied canonical subset. Retain raw and preserve as a string.
- **CRED_LIC_NAME**: Help file p.9 defines this as the register entry name and states it may be a person's Last name, First name or a full organisation name. It is retained as subject_label_field, but is not confidently a legal name.
- **CRED_LIC_START_DT**: Help file p.9 defines the start date of the credit licensee/licence, not company registration date; no licence-date field exists in the subset.
- **CRED_LIC_END_DT**: Help file p.9 defines the end date of the credit licensee/licence, not entity deregistration date; no applicable canonical field exists.
- **CRED_LIC_STATUS**: Help file p.9 defines licence registration status (APPR/SUSP). It does not establish canonical entity status, especially not deregistration.
- **CRED_LIC_AFSL_NUM**: AFSL licence number (help file p.10); no licence identifier field exists in the supplied canonical subset. Preserve raw as a string.
- **CRED_LIC_STATUS_HISTORY**: Historical credit-licence suspensions, reasons, and dates (help file p.10), not canonical entity status; no matching field exists.
- **CRED_LIC_LAT**: Latitude coordinate is present in the supplied header and preview (for example, -38.4761569), but the supplied canonical subset has no geospatial field.
- **CRED_LIC_LNG**: Longitude coordinate is present in the supplied header and preview (for example, 145.9458605), but the supplied canonical subset has no geospatial field.
- **CRED_LIC_EDRS**: External dispute-resolution scheme code(s) (help file p.12); no matching canonical field exists.
- **CRED_LIC_AUTHORISATIONS**: Free-text description of authorised credit services/products (help file p.12); no matching canonical field exists.

## Uncertainties

- The supplied reader is retained unchanged as required. This conflicts with help file p.3, which says the CSV is TAB-delimited; the supplied frozen preview instead has coherent comma-delimited records and the stated reader is authoritative for extraction.
- CRED_LIC_NAME is preserved only as the raw subject label because the documentation explicitly permits both persons and organisations; it is not asserted as entity.legal_name.
- CRED_LIC_ABN_ACN has no type discriminator. Both identifier mappings rely exclusively on their respective validators; no ACN is derived from an ABN suffix, and invalid, zero, or opposite-type values emit nothing.
- CRED_LIC_BN includes current or previous operating names (help file p.12). Splitting emits the source-stated name values but does not establish their currency or registration status.
- Address components are the licensee's current principal business address (help file pp.11–12), not a registered address. Documentation says null locality/state and zero postcode can indicate foreign addresses; no country field is available, so country is not asserted.
- The source is a point-in-time public register snapshot (help file p.3 and dataset notes). Publication proxy is used because no per-record observation timestamp is supplied.
- Source-reliability and field-confidence scores are provisional judgments requiring human review.
- CRED_LIC_BN is documented as a tilde-delimited list of current or previous operating/business names. Emitted entity.trading_name observations correctly retain source-stated names, but do not establish that each name is current, formally registered, or a legal name; this is disclosed.
- CRED_LIC_NAME is properly not mapped to entity.legal_name: the documentation says it is a register-entry name and may identify either a person or an organisation. The mapping consequently remains deliberately partial for legal names and entity type.
- CRED_LIC_STATUS and its history concern the credit-licence/register status, not the legal entity's corporate status. Leaving entity.status unmapped is semantically appropriate.
- The address components are only the licensee's current principal business address, not a registered address or necessarily a service location. Mapping them under the disclosed business-address role is supported; country is appropriately not asserted, especially given documented foreign-address null/zero conventions.
- CRED_LIC_ABN_ACN is a mixed ABN-or-ACN column without a type marker. Parallel mappings are acceptable because the supplied engine enforces disjoint valid ABN/ACN forms and never derives an ACN from an ABN; malformed and zero values are quarantined/non-emitting. This does not itself verify that a valid identifier resolves to a particular legal entity.
- The supplied documentation describes a tab-delimited CSV, whereas the supplied frozen discovery material and selected reader evidence coherent comma-delimited rows. Retaining the supplied reader is reasonable for this extraction, but full-resource parsing should remain monitored because this is a source/documentation discrepancy.
- CRED_LIC_NUM is supported as the row's unique credit-licensee identifier in the reviewed sample, but the canonical subset has no licence-identifier destination. Its retention as raw/source traceability rather than entity identifier is appropriate.
- Publication-proxy observed_at is a disclosed snapshot-level approximation, not a per-row statement time. Confidence values are uncalibrated judgments, as acknowledged.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b215-5bde-7521-b5e7-e9230d8577fe/run/01a0b215-f0eb-7293-bc46-fa719d82e6bb?start_time=2026-09-18T01%3A16%3A17.515381%2B00%3A00)