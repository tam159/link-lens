# Mapping review: ASIC - Australian Financial Services Licensee Dataset
Config version **2**, hash `b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13`.
Ontology: `4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0`.
Grain: One row per current Australian Financial Services licensee register entry, with one licence and its reported licensee identifiers, licence start date, principal business address components, prior FSR references, and authorisation conditions.. Subject: **licence_holder**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| AFS_LIC_NUM | licence.number | trim | 0.99 | Help File p.8: AFS_LIC_NUM is a unique identifying number allocated to the licensee; sample header AFS_LIC_NUM, value 218600. Retain as string. |
| AFS_LIC_NAME | licence.register_entry_name | trim | 0.98 | Help File p.8: AFS_LIC_NAME is the licensee register-entry name, shown as given names/last name for a person or organisation name otherwise; sample header AFS_LIC_NAME, value IPIB PTY LTD. Not mapped as legal name. |
| AFS_LIC_ABN_ACN | entity.abn | abn | 0.91 | Help File p.8: AFS_LIC_ABN_ACN contains the licensee ABN or ACN, displaying ABN if provided; sample header AFS_LIC_ABN_ACN, value 85007186003. Checksum validation only. |
| AFS_LIC_ABN_ACN | entity.acn | acn | 0.91 | Help File p.8: AFS_LIC_ABN_ACN contains the licensee ABN or ACN; sample header AFS_LIC_ABN_ACN, value 85007186003. Checksum validation only; no ABN-suffix inference. |
| AFS_LIC_START_DT | licence.start_date | date | 0.98 | Help File p.8: AFS_LIC_START_DT is the licence start date, format DD/MM/YYYY; sample header AFS_LIC_START_DT, value 02/05/2002. Not entity registration. |
| AFS_LIC_PRE_FSR | licence.pre_fsr_reference | split | 0.9 | Help File p.9: prior register licence references are separated by tilde '~'; sample header AFS_LIC_PRE_FSR, value "General insurance broker","000030366". Split only at documented tilde; retain each reference payload without interpreting its internal quoted fields. |
| AFS_LIC_CONDITION | licence.authorisation_condition | split | 0.9 | Help File p.11: conditions are represented as tilde-separated condition lines or rows; sample header AFS_LIC_CONDITION, value begins "This licence authorises the licensee to carry on a financial services business to:"~"(a) provide financial product advice...". Split on documented tilde and retain each part without interpreting it. |
| AFS_LIC_ADD_LOCAL | address.locality | trim | 0.98 | Help File p.9: AFS_LIC_ADD_LOCAL is the locality of the current principal business address; sample header AFS_LIC_ADD_LOCAL, value SOUTHBANK. |
| AFS_LIC_ADD_STATE | address.state | trim, enum | 0.97 | Help File p.10: AFS_LIC_ADD_STATE is the state of the current principal business address; sample header AFS_LIC_ADD_STATE, value VIC. Source abbreviations align to ontology state categories. |
| AFS_LIC_ADD_PCODE | address.postcode | trim | 0.96 | Help File p.10: AFS_LIC_ADD_PCODE is the postcode of the current principal business address; sample header AFS_LIC_ADD_PCODE, value 3006. Preserve as string. |
| AFS_LIC_ADD_COUNTRY | address.country | trim | 0.9 | Help File p.10: AFS_LIC_ADD_COUNTRY is country of principal business address; countries outside Australia are labelled International; sample header AFS_LIC_ADD_COUNTRY, value Australia. Omit documented International placeholder. |

## Before / after

```json
{
  "raw": [
    {
      "record_id": "d63e04430d99d39ba149f3af8ffec43e6217466ecc48cd182e3de742b16de93a",
      "locator": {
        "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
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
      "record_id": "e194990f9f08739ba2df9aa7449c88b15f1d5ebda58c8435308c3033c2456354",
      "locator": {
        "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
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
      "source_record_id": "d63e04430d99d39ba149f3af8ffec43e6217466ecc48cd182e3de742b16de93a",
      "observed_at": "2026-09-23T21:50:41.592631+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-24T03:34:20.324275+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "field": "licence.number",
      "value": "218600",
      "source_fields": [
        "AFS_LIC_NUM"
      ],
      "raw_value": [
        "218600"
      ],
      "raw_locator": {
        "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "778654b1d9a9f0f45c18b4ca841399f05b2578ee03c350a72816edbd8578a5de",
      "config_hash": "b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "licence",
      "group_id": "254a682b76c65f0e4c3a89767705838592f4a87a9c09e71ba626f96de16cbfc6",
      "group_name": "afs_licence",
      "id": "ba82aad4bc07f3a517a22c5259253362fef2a6ebdb21a64e9a66ebf3661fbf5a"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "d63e04430d99d39ba149f3af8ffec43e6217466ecc48cd182e3de742b16de93a",
      "observed_at": "2026-09-23T21:50:41.592631+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-24T03:34:20.324275+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "field": "licence.register_entry_name",
      "value": "IPIB PTY LTD",
      "source_fields": [
        "AFS_LIC_NAME"
      ],
      "raw_value": [
        "IPIB PTY LTD"
      ],
      "raw_locator": {
        "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "778654b1d9a9f0f45c18b4ca841399f05b2578ee03c350a72816edbd8578a5de",
      "config_hash": "b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "licence",
      "group_id": "254a682b76c65f0e4c3a89767705838592f4a87a9c09e71ba626f96de16cbfc6",
      "group_name": "afs_licence",
      "id": "8cfc56966bd5331225a4bc7c377c4cce9aa803b3e431ab687b57e8360ab5bdc8"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "d63e04430d99d39ba149f3af8ffec43e6217466ecc48cd182e3de742b16de93a",
      "observed_at": "2026-09-23T21:50:41.592631+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-24T03:34:20.324275+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "field": "entity.abn",
      "value": "85007186003",
      "source_fields": [
        "AFS_LIC_ABN_ACN"
      ],
      "raw_value": [
        "85007186003"
      ],
      "raw_locator": {
        "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "778654b1d9a9f0f45c18b4ca841399f05b2578ee03c350a72816edbd8578a5de",
      "config_hash": "b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.91
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "id": "b182c7ab4793cba002a45595cdfe0f22ac9ac594600e5edd1158cb6b16ad8095"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "d63e04430d99d39ba149f3af8ffec43e6217466ecc48cd182e3de742b16de93a",
      "observed_at": "2026-09-23T21:50:41.592631+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-24T03:34:20.324275+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "field": "licence.start_date",
      "value": "2002-05-02",
      "source_fields": [
        "AFS_LIC_START_DT"
      ],
      "raw_value": [
        "02/05/2002"
      ],
      "raw_locator": {
        "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "778654b1d9a9f0f45c18b4ca841399f05b2578ee03c350a72816edbd8578a5de",
      "config_hash": "b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "date",
      "cardinality": "one",
      "scope": "licence",
      "group_id": "254a682b76c65f0e4c3a89767705838592f4a87a9c09e71ba626f96de16cbfc6",
      "group_name": "afs_licence",
      "id": "9bb194fe47445b18782c07c5cc01b625f5d107056407ec9746ab3e96886ecb9f"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "d63e04430d99d39ba149f3af8ffec43e6217466ecc48cd182e3de742b16de93a",
      "observed_at": "2026-09-23T21:50:41.592631+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-24T03:34:20.324275+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "field": "licence.pre_fsr_reference",
      "value": "\"General insurance broker\",\"000030366\"",
      "source_fields": [
        "AFS_LIC_PRE_FSR"
      ],
      "raw_value": [
        "\"General insurance broker\",\"000030366\""
      ],
      "raw_locator": {
        "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "778654b1d9a9f0f45c18b4ca841399f05b2578ee03c350a72816edbd8578a5de",
      "config_hash": "b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "many",
      "scope": "licence",
      "group_id": "254a682b76c65f0e4c3a89767705838592f4a87a9c09e71ba626f96de16cbfc6",
      "group_name": "afs_licence",
      "id": "dd147abfcc8e0bce1276b4dcd34546e046e6e94b4d072e5c09c622092c484305"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "d63e04430d99d39ba149f3af8ffec43e6217466ecc48cd182e3de742b16de93a",
      "observed_at": "2026-09-23T21:50:41.592631+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-24T03:34:20.324275+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "field": "licence.authorisation_condition",
      "value": "\"This licence authorises the licensee to carry on a financial services business to:\"",
      "source_fields": [
        "AFS_LIC_CONDITION"
      ],
      "raw_value": [
        "\"This licence authorises the licensee to carry on a financial services business to:\"~\"(a) provide financial product advice for the following classes of financial products:\"~\"(i) general insurance products; and\"~\"(b) deal in a financial product by:\"~\"(i) applying for, acquiring, varying or disposing of a financial product on behalf of another person in respect of the following classes of products:\"~\"(A) general insurance products;\"~\"to retail and wholesale clients.\""
      ],
      "raw_locator": {
        "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "778654b1d9a9f0f45c18b4ca841399f05b2578ee03c350a72816edbd8578a5de",
      "config_hash": "b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "many",
      "scope": "licence",
      "group_id": "254a682b76c65f0e4c3a89767705838592f4a87a9c09e71ba626f96de16cbfc6",
      "group_name": "afs_licence",
      "id": "042b1c1fdaeb9ee424f771f0bbf9836be4e333717404829a5d0360181d61c456"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "d63e04430d99d39ba149f3af8ffec43e6217466ecc48cd182e3de742b16de93a",
      "observed_at": "2026-09-23T21:50:41.592631+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-24T03:34:20.324275+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "field": "licence.authorisation_condition",
      "value": "\"(a) provide financial product advice for the following classes of financial products:\"",
      "source_fields": [
        "AFS_LIC_CONDITION"
      ],
      "raw_value": [
        "\"This licence authorises the licensee to carry on a financial services business to:\"~\"(a) provide financial product advice for the following classes of financial products:\"~\"(i) general insurance products; and\"~\"(b) deal in a financial product by:\"~\"(i) applying for, acquiring, varying or disposing of a financial product on behalf of another person in respect of the following classes of products:\"~\"(A) general insurance products;\"~\"to retail and wholesale clients.\""
      ],
      "raw_locator": {
        "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "778654b1d9a9f0f45c18b4ca841399f05b2578ee03c350a72816edbd8578a5de",
      "config_hash": "b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "many",
      "scope": "licence",
      "group_id": "254a682b76c65f0e4c3a89767705838592f4a87a9c09e71ba626f96de16cbfc6",
      "group_name": "afs_licence",
      "id": "bb817cbfe0519131053219ccf3ea8db3da42700120fea668ce7e11aa2e31a2df"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "d63e04430d99d39ba149f3af8ffec43e6217466ecc48cd182e3de742b16de93a",
      "observed_at": "2026-09-23T21:50:41.592631+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-24T03:34:20.324275+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "field": "licence.authorisation_condition",
      "value": "\"(i) general insurance products; and\"",
      "source_fields": [
        "AFS_LIC_CONDITION"
      ],
      "raw_value": [
        "\"This licence authorises the licensee to carry on a financial services business to:\"~\"(a) provide financial product advice for the following classes of financial products:\"~\"(i) general insurance products; and\"~\"(b) deal in a financial product by:\"~\"(i) applying for, acquiring, varying or disposing of a financial product on behalf of another person in respect of the following classes of products:\"~\"(A) general insurance products;\"~\"to retail and wholesale clients.\""
      ],
      "raw_locator": {
        "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "778654b1d9a9f0f45c18b4ca841399f05b2578ee03c350a72816edbd8578a5de",
      "config_hash": "b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "many",
      "scope": "licence",
      "group_id": "254a682b76c65f0e4c3a89767705838592f4a87a9c09e71ba626f96de16cbfc6",
      "group_name": "afs_licence",
      "id": "1cd3996c1abcefe45027fd0b76ce3cddf6ab01e8e4c1027ac33f1e29d77f991d"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "d63e04430d99d39ba149f3af8ffec43e6217466ecc48cd182e3de742b16de93a",
      "observed_at": "2026-09-23T21:50:41.592631+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-24T03:34:20.324275+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "field": "licence.authorisation_condition",
      "value": "\"(b) deal in a financial product by:\"",
      "source_fields": [
        "AFS_LIC_CONDITION"
      ],
      "raw_value": [
        "\"This licence authorises the licensee to carry on a financial services business to:\"~\"(a) provide financial product advice for the following classes of financial products:\"~\"(i) general insurance products; and\"~\"(b) deal in a financial product by:\"~\"(i) applying for, acquiring, varying or disposing of a financial product on behalf of another person in respect of the following classes of products:\"~\"(A) general insurance products;\"~\"to retail and wholesale clients.\""
      ],
      "raw_locator": {
        "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "778654b1d9a9f0f45c18b4ca841399f05b2578ee03c350a72816edbd8578a5de",
      "config_hash": "b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "many",
      "scope": "licence",
      "group_id": "254a682b76c65f0e4c3a89767705838592f4a87a9c09e71ba626f96de16cbfc6",
      "group_name": "afs_licence",
      "id": "9fc693706879182473fd2f4ab7775364bd3303511f44ac13cd101d39eab138fc"
    },
    {
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "d63e04430d99d39ba149f3af8ffec43e6217466ecc48cd182e3de742b16de93a",
      "observed_at": "2026-09-23T21:50:41.592631+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-24T03:34:20.324275+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "field": "licence.authorisation_condition",
      "value": "\"(i) applying for, acquiring, varying or disposing of a financial product on behalf of another person in respect of the following classes of products:\"",
      "source_fields": [
        "AFS_LIC_CONDITION"
      ],
      "raw_value": [
        "\"This licence authorises the licensee to carry on a financial services business to:\"~\"(a) provide financial product advice for the following classes of financial products:\"~\"(i) general insurance products; and\"~\"(b) deal in a financial product by:\"~\"(i) applying for, acquiring, varying or disposing of a financial product on behalf of another person in respect of the following classes of products:\"~\"(A) general insurance products;\"~\"to retail and wholesale clients.\""
      ],
      "raw_locator": {
        "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "778654b1d9a9f0f45c18b4ca841399f05b2578ee03c350a72816edbd8578a5de",
      "config_hash": "b127ceac8f80341f51ab51f246baf91954a50938d2da8cd5a5fc4cf05929aa13",
      "subject_role": "licence_holder",
      "source_kind": "licence_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.9
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "many",
      "scope": "licence",
      "group_id": "254a682b76c65f0e4c3a89767705838592f4a87a9c09e71ba626f96de16cbfc6",
      "group_name": "afs_licence",
      "id": "43538b83d446613b660273cd9733203ed10a1ee449568b24464332a6f06cc0a1"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 5; measured/reserved input/output: 78221/7430; calculated cost: 0.02512775.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **REGISTER_NAME**: Help File p.8 defines this as the name of the register for the record (sample value AFS Licence); no registered ontology concept represents register metadata.

## Uncertainties

- Dataset documentation describes a point-in-time snapshot of current licensees (Help File p.3), but there is no row-level status field or filter; this does not establish entity deregistration or a historical status claim.
- AFS_LIC_NAME may be a person's displayed name or an organisation's register-entry name (Help File p.8); retained as licence.register_entry_name and subject label, not asserted to be a legal name or company type.
- AFS_LIC_ABN_ACN is a mixed ABN/ACN column (Help File p.8); checksum validators independently emit only a valid identifier of the corresponding type. No ACN is inferred from an ABN suffix and no legal form is inferred.
- AFS_LIC_START_DT is a licence start date, not company registration date.
- AFS_LIC_PRE_FSR and AFS_LIC_CONDITION are split only on documented tilde separators; embedded quotation/comma structures are retained as raw text and not semantically parsed.
- Principal business address fields are components, not a complete street address. Help File pp.9-10 notes blank fields can mean the provided address could not be validated; International is omitted as a placeholder country claim.
- The source envelope supplies the publication timestamp and licence. publication_proxy labels the snapshot time, not a row-change time.
- The source documentation describes current licensees in a point-in-time snapshot but does not supply an explicit row-level licence or legal-entity status; the mapping correctly avoids inventing one and discloses this limitation.
- AFS_LIC_ABN_ACN is an either/or ABN/ACN source column. Separate mappings are semantically acceptable under the supplied checksum and identifier-exclusivity engine semantics; the sample evidence shown includes an ABN, not a demonstrated ACN case.
- The principal-business-address fields provide components rather than a street address, and source blanks may indicate failed address validation. The mapping does not fabricate a full address and discloses this limitation.
- Tilde splitting retains the source's embedded quoted structures rather than normalizing their legal meaning, consistent with the supplied definitions and sample payloads.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0d406-6e0e-7282-ad37-aa6380413fca/run/01a0d40a-c6c2-7df0-960e-e5b1dd7fe3ba?start_time=2026-09-24T15%3A31%3A11.171004%2B00%3A00)