# Mapping review: ASIC - Company Dataset
Config version **2**, hash `66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b`.
Ontology: `4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `85dc8773e5691a3be87991e3249651097fbb9c8be025487b84f57827c63e1b24`.
Grain: One row per ASIC company-register name record, including current or historical names associated with a company identifier; not one row per unique company.. Subject: **legal_entity**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": "\t", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| Company Name | entity.legal_name | trim | 0.94 | ASIC Company Dataset Help File, p. 7 (PDF p. 8): “Company Name” is the name as it appears on the register. The field list and sample on p. 3 (PDF p. 4) distinguish current-name records using Current Name Indicator=Y; sample rows show Company Name on the current-name row. |
| ACN | entity.acn | acn | 0.99 | ASIC Company Dataset Help File, p. 7 (PDF p. 8): ACN is a 9-digit numerical text field, including leading zeros; explicitly warns that Type=RACN rows contain an ARBN instead, so those rows are excluded. Sample header and values on p. 3 (PDF p. 4). |
| ABN | entity.abn | abn | 0.99 | ASIC Company Dataset Help File, p. 10 (PDF p. 11): ABN is the company's ABN; when the company has no ABN the field shows 0. Sample header and 11-digit values on p. 3 (PDF p. 4). The validator operation handles formatting/checksum and zero sentinel. |
| Type | entity.asic_company_type | trim, enum | 0.99 | ASIC Company Dataset Help File, p. 7 (PDF p. 8): Type specifies the type of company and documents APTY, APUB, FNOS and RACN. Sample header/value on p. 3 (PDF p. 4). |
| Class | entity.asic_company_class | trim, enum | 0.99 | ASIC Company Dataset Help File, pp. 7–8 (PDF pp. 8–9): Class specifies company liability class and documents LMSH, LMGT, LMSG, NLIA, UNLM and NONE. Sample header/value on p. 3 (PDF p. 4). |
| Sub Class | entity.asic_company_sub_class | trim, enum | 0.99 | ASIC Company Dataset Help File, pp. 8–9 (PDF pp. 9–10): Sub Class specifies the subclass and lists the mapped codes. Sample header/value on p. 3 (PDF p. 4). |
| Status | entity.asic_register_status | trim, enum | 0.99 | ASIC Company Dataset Help File, pp. 9–10 (PDF pp. 10–11): Status is the company-register status code; documents DRGD, EXAD, NOAC, NRGD, PROV, REGD, SOFF, DISS, DIV3, PEND and CNCL. Sample header/value on p. 3 (PDF p. 4). Raw code retained, not translated to broader status. |
| Date of Registration | entity.date_registered | date | 0.99 | ASIC Company Dataset Help File, p. 10 (PDF p. 11): “Date of Registration” is the date on which a company was registered, format DD/MM/YYYY. Example value 08/01/1990 on p. 3 (PDF p. 4). |
| Date of Deregistration | registration.company_deregistration_date | date | 0.99 | ASIC Company Dataset Help File, p. 10 (PDF p. 11): “Date of Deregistration” is the date the company was deregistered, format DD/MM/YYYY; change note on p. 12 (PDF p. 13) says added to dictionary March 2025. Dataset notes say available from 11 March 2025. |
| Previous State of Registration | registration.original_state | trim | 0.99 | ASIC Company Dataset Help File, p. 10 (PDF p. 11): field is the state in which the company was originally registered, abbreviated (example VIC). Sample value NSW on p. 3 (PDF p. 4). |
| State Registration number | registration.state_registration_number | trim | 0.99 | ASIC Company Dataset Help File, p. 10 (PDF p. 11): number assigned when originally registered by the State; format varies by state. Sample header and value 46869041 on p. 3 (PDF p. 4); preserve as string. |
| Current Name Start Date | registration.current_name_start_date | date | 0.96 | ASIC Company Dataset Help File, p. 10 (PDF p. 11): Current Name Start Date is the start date for the current registered company name, format DD/MM/YYYY. p. 11 (PDF p. 12) specifies it is shown when Current Name Indicator is null; sample historical-name record on p. 3 (PDF p. 4) has a date while the Y row is blank. |

## Before / after

```json
{
  "raw": [
    {
      "record_id": "71588e9f06ac843ac1013426ec1d5cec007a7170ca7f417bc68abe94e1b3c9f3",
      "locator": {
        "snapshot_sha": "85dc8773e5691a3be87991e3249651097fbb9c8be025487b84f57827c63e1b24",
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
      "record_id": "15264aea10c562e36f15f005625bfd632d3ee23212260caba9e579a216e493bb",
      "locator": {
        "snapshot_sha": "85dc8773e5691a3be87991e3249651097fbb9c8be025487b84f57827c63e1b24",
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
      "source_record_id": "71588e9f06ac843ac1013426ec1d5cec007a7170ca7f417bc68abe94e1b3c9f3",
      "observed_at": "2026-09-21T14:56:01.988918+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:38.379457+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "field": "entity.acn",
      "value": "000000019",
      "source_fields": [
        "ACN"
      ],
      "raw_value": [
        "000000019"
      ],
      "raw_locator": {
        "snapshot_sha": "85dc8773e5691a3be87991e3249651097fbb9c8be025487b84f57827c63e1b24",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "f056f393e486e56451330e23140bdf23bc91a823d571c5be8f50e2203f28b827",
      "config_hash": "66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "id": "dde6d7d44d9e020850cc6bb34661f51819995783c0f136a5606b5e8d83b04bc0"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "71588e9f06ac843ac1013426ec1d5cec007a7170ca7f417bc68abe94e1b3c9f3",
      "observed_at": "2026-09-21T14:56:01.988918+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:38.379457+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "field": "entity.abn",
      "value": "89000000019",
      "source_fields": [
        "ABN"
      ],
      "raw_value": [
        "89000000019"
      ],
      "raw_locator": {
        "snapshot_sha": "85dc8773e5691a3be87991e3249651097fbb9c8be025487b84f57827c63e1b24",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "f056f393e486e56451330e23140bdf23bc91a823d571c5be8f50e2203f28b827",
      "config_hash": "66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "id": "0f2531c1e69a9efd2d7ac3844d7ab909f8808eb3bd07f02c2c79c514b64c4dfd"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "71588e9f06ac843ac1013426ec1d5cec007a7170ca7f417bc68abe94e1b3c9f3",
      "observed_at": "2026-09-21T14:56:01.988918+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:38.379457+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "field": "entity.asic_company_type",
      "value": "APTY",
      "source_fields": [
        "Type"
      ],
      "raw_value": [
        "APTY"
      ],
      "raw_locator": {
        "snapshot_sha": "85dc8773e5691a3be87991e3249651097fbb9c8be025487b84f57827c63e1b24",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "f056f393e486e56451330e23140bdf23bc91a823d571c5be8f50e2203f28b827",
      "config_hash": "66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "enum",
      "cardinality": "one",
      "id": "70c8f4de64b85df19bff9399096bf574831ffb76a7cd7228674ad08c7e5db814"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "71588e9f06ac843ac1013426ec1d5cec007a7170ca7f417bc68abe94e1b3c9f3",
      "observed_at": "2026-09-21T14:56:01.988918+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:38.379457+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "field": "entity.asic_company_class",
      "value": "LMSH",
      "source_fields": [
        "Class"
      ],
      "raw_value": [
        "LMSH"
      ],
      "raw_locator": {
        "snapshot_sha": "85dc8773e5691a3be87991e3249651097fbb9c8be025487b84f57827c63e1b24",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "f056f393e486e56451330e23140bdf23bc91a823d571c5be8f50e2203f28b827",
      "config_hash": "66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "enum",
      "cardinality": "one",
      "id": "4d9996550934064637fea040f58103fe7122112a573cfceda8f3d9ca9b78503e"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "71588e9f06ac843ac1013426ec1d5cec007a7170ca7f417bc68abe94e1b3c9f3",
      "observed_at": "2026-09-21T14:56:01.988918+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:38.379457+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "field": "entity.asic_company_sub_class",
      "value": "PROP",
      "source_fields": [
        "Sub Class"
      ],
      "raw_value": [
        "PROP"
      ],
      "raw_locator": {
        "snapshot_sha": "85dc8773e5691a3be87991e3249651097fbb9c8be025487b84f57827c63e1b24",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "f056f393e486e56451330e23140bdf23bc91a823d571c5be8f50e2203f28b827",
      "config_hash": "66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "enum",
      "cardinality": "one",
      "id": "ffc2b239c4d868136e1b81a35798467de716dab13d6b2debc4f11bcf212cccf3"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "71588e9f06ac843ac1013426ec1d5cec007a7170ca7f417bc68abe94e1b3c9f3",
      "observed_at": "2026-09-21T14:56:01.988918+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:38.379457+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "field": "entity.asic_register_status",
      "value": "REGD",
      "source_fields": [
        "Status"
      ],
      "raw_value": [
        "REGD"
      ],
      "raw_locator": {
        "snapshot_sha": "85dc8773e5691a3be87991e3249651097fbb9c8be025487b84f57827c63e1b24",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "f056f393e486e56451330e23140bdf23bc91a823d571c5be8f50e2203f28b827",
      "config_hash": "66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "enum",
      "cardinality": "one",
      "id": "e9fd341d5d25292c3daea12c81edaee0da90e5cd8c52871284381f91ea372bcc"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "71588e9f06ac843ac1013426ec1d5cec007a7170ca7f417bc68abe94e1b3c9f3",
      "observed_at": "2026-09-21T14:56:01.988918+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:38.379457+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "field": "entity.date_registered",
      "value": "1990-01-08",
      "source_fields": [
        "Date of Registration"
      ],
      "raw_value": [
        "08/01/1990"
      ],
      "raw_locator": {
        "snapshot_sha": "85dc8773e5691a3be87991e3249651097fbb9c8be025487b84f57827c63e1b24",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "f056f393e486e56451330e23140bdf23bc91a823d571c5be8f50e2203f28b827",
      "config_hash": "66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "date",
      "cardinality": "one",
      "id": "6e4f3d1665c93bf33324aa931198db843c0e11aa57e1edd21ee403e5c952e919"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "71588e9f06ac843ac1013426ec1d5cec007a7170ca7f417bc68abe94e1b3c9f3",
      "observed_at": "2026-09-21T14:56:01.988918+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:38.379457+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "field": "registration.original_state",
      "value": "NSW",
      "source_fields": [
        "Previous State of Registration"
      ],
      "raw_value": [
        "NSW"
      ],
      "raw_locator": {
        "snapshot_sha": "85dc8773e5691a3be87991e3249651097fbb9c8be025487b84f57827c63e1b24",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "f056f393e486e56451330e23140bdf23bc91a823d571c5be8f50e2203f28b827",
      "config_hash": "66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "4188fea810ec7c3934c4261be5c5074b14e12e539b8d3976a993dbceb55c2d7b",
      "group_name": "company_register_registration",
      "id": "5872ec09ff92d254c941316c5625662171875864d8178c8a1d77dbae1b098ee6"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "71588e9f06ac843ac1013426ec1d5cec007a7170ca7f417bc68abe94e1b3c9f3",
      "observed_at": "2026-09-21T14:56:01.988918+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:38.379457+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "field": "registration.state_registration_number",
      "value": "46869041",
      "source_fields": [
        "State Registration number"
      ],
      "raw_value": [
        "46869041"
      ],
      "raw_locator": {
        "snapshot_sha": "85dc8773e5691a3be87991e3249651097fbb9c8be025487b84f57827c63e1b24",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "f056f393e486e56451330e23140bdf23bc91a823d571c5be8f50e2203f28b827",
      "config_hash": "66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "4188fea810ec7c3934c4261be5c5074b14e12e539b8d3976a993dbceb55c2d7b",
      "group_name": "company_register_registration",
      "id": "daccd5415bfd19e3dd98eee5c19a95e102079bce1e6eee6b476c1490b4fa7ea4"
    },
    {
      "source_id": "7b8656f9-606d-4337-af29-66b89b2eeefb",
      "source_record_id": "71588e9f06ac843ac1013426ec1d5cec007a7170ca7f417bc68abe94e1b3c9f3",
      "observed_at": "2026-09-21T14:56:01.988918+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:38.379457+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "field": "registration.current_name_start_date",
      "value": "2016-01-28",
      "source_fields": [
        "Current Name Start Date"
      ],
      "raw_value": [
        "28/01/2016"
      ],
      "raw_locator": {
        "snapshot_sha": "85dc8773e5691a3be87991e3249651097fbb9c8be025487b84f57827c63e1b24",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "f056f393e486e56451330e23140bdf23bc91a823d571c5be8f50e2203f28b827",
      "config_hash": "66cc567369cfe465e62d7c276144eb9c1e445463b99959a7606a1fa8e0b2c92b",
      "subject_role": "legal_entity",
      "source_kind": "company_register",
      "address_role": "unknown",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "date",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "4188fea810ec7c3934c4261be5c5074b14e12e539b8d3976a993dbceb55c2d7b",
      "group_name": "company_register_registration",
      "id": "178f5bee4a3e8cf0b4e82be7494f4069533de25ed652aab18537043be75d34a0"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 3; measured/reserved input/output: 45525/8201; calculated cost: 0.017532.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **Modified since last report**: Dataset-record modification flag, not an entity attribute; no matching ontology concept.
- **Current Name Indicator**: Control flag identifying current-name versus historical-name rows; no matching ontology concept. Used only to condition name/date mappings.
- **Current Name**: Documentation describes a conditional current-name companion value on historical name records; not a trading name. Mapping it to legal_name would duplicate that canonical target, and no separate historical-name concept is available.

## Uncertainties

- The source envelope supplies the publication proxy timestamp and licence; this is a weekly snapshot proxy, not row-level change time. The dataset notes warn it may be stale versus ASIC Connect.
- Rows include historical company-name records and deregistered companies from the past year; preserve source-row provenance and do not treat each name record as a distinct entity.
- ACN is excluded for Type=RACN because the documented field value is an ARBN in those cases; identifiers are validated, not inferred from ABN suffixes.
- Current Name is left unmapped rather than treated as a trading name or as a second legal_name mapping. Current-name legal_name claims are limited to rows with Current Name Indicator=Y.
- Company registration/deregistration claims remain distinct from the current-name start date and from any broader entity-status interpretation.
- Authority and field confidence scores are provisional and require human review.
- The discovery-code inspection script failed because `records` was undefined. The supplied raw discovery rows still directly demonstrate multiple historical/current name rows for identical ACNs, but exploration-based confidence should be treated cautiously.
- Several field confidence values are 0.99 despite limited raw discovery examples and no successful broader exploration. The field definitions and code lists are explicit in ASIC documentation, so this is a calibration warning rather than a semantic blocker.
- Current Name is deliberately unmapped. This avoids treating it as a trading name or creating a duplicate legal-name claim; the current-name row itself supplies the mapped legal name.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0d40f-c41f-7a00-97f4-2e5ce20bfe7e/run/01a0d410-65ef-7752-a1d0-153820ca1d9a?start_time=2026-09-24T15%3A37%3A19.599300%2B00%3A00)