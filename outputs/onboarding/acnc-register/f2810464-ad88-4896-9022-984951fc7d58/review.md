# Mapping review: ACNC Registered Charities
Config version **2**, hash `52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa`.
Grain: One row per ACNC-registered charity record, primarily identified by the source ABN; the row describes the charity/legal-name record, its business address and charity attributes, not separate entities for other names.. Subject: **legal_entity**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| ABN | entity.abn | digits, abn | 0.99 | ACNC User guide, Dec 2024, p. 2 §§6-7: ABN is the charity's Australian Business Number and the field is numeric; exact header ABN and sample 51214424410. |
| Charity_Legal_Name | entity.legal_name | trim | 0.98 | ACNC User guide, p. 2 §§8-9: Charity name is the formal name appearing on legal or official documents; exact header Charity_Legal_Name and sample U3A Inner North Incorporated. |
| Address_Line_1, Address_Line_2, Address_Line_3 | address.full | join | 0.91 | ACNC User guide, p. 2 §§12-14: Charity address is the business address and Address lines 1-3 are supplied address fields; exact headers Address_Line_1, Address_Line_2, Address_Line_3 and sample 540 Regency Rd. Some samples are PO Boxes, so the source's business-address claim is preserved without reinterpretation. |
| Town_City | address.locality | trim | 0.98 | ACNC User guide, p. 2 §13 lists Town/City as an address field; exact header Town_City and sample Enfield. |
| State | address.state | trim, uppercase | 0.99 | ACNC User guide, p. 2 §13 lists State as an address field; exact header State and samples SA and VIC. |
| Postcode | address.postcode | trim, postcode | 0.98 | ACNC User guide, p. 2 §13 lists Postcode as an address field; exact header Postcode and sample 5085. Preserve numeric postcode text; do not zero-pad damaged values. |
| Country | address.country | trim | 0.98 | ACNC User guide, p. 2 §13 lists Country as an address field; exact header Country and sample Australia. |
| Charity_Website | entity.website | trim, website | 0.96 | ACNC User guide, p. 2 §15: Charity website contains the supplied website address; exact header Charity_Website and samples https://www.u3ainnernorth.org.au/ and www.spectrum3.org.au. |

## Before / after

```json
{
  "raw": [
    {
      "record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 2
      },
      "values": {
        "ABN": "51214424410",
        "Charity_Legal_Name": "U3A Inner North Incorporated",
        "Other_Organisation_Names": "",
        "Address_Type": "Business",
        "Address_Line_1": "540 Regency Rd",
        "Address_Line_2": "",
        "Address_Line_3": "",
        "Town_City": "Enfield",
        "State": "SA",
        "Postcode": "5085",
        "Country": "Australia",
        "Charity_Website": "https://www.u3ainnernorth.org.au/",
        "Registration_Date": "20/02/2018",
        "Date_Organisation_Established": "20/02/2018",
        "Charity_Size": "",
        "Number_of_Responsible_Persons": "9",
        "Financial_Year_End": "30-Jun",
        "Operates_in_ACT": "",
        "Operates_in_NSW": "",
        "Operates_in_NT": "",
        "Operates_in_QLD": "",
        "Operates_in_SA": "Y",
        "Operates_in_TAS": "",
        "Operates_in_VIC": "",
        "Operates_in_WA": "",
        "Operating_Countries": "",
        "PBI": "",
        "HPC": "",
        "Preventing_or_relieving_suffering_of_animals": "",
        "Advancing_Culture": "",
        "Advancing_Education": "Y",
        "Advancing_Health": "",
        "Promote_or_oppose_a_change_to_law__government_poll_or_prac": "",
        "Advancing_natual_environment": "",
        "Promoting_or_protecting_human_rights": "",
        "Purposes_beneficial_to_ther_general_public_and_other_analogous": "",
        "Promoting_reconciliation__mutual_respect_and_tolerance": "",
        "Advancing_Religion": "",
        "Advancing_social_or_public_welfare": "",
        "Advancing_security_or_safety_of_Australia_or_Australian_public": "",
        "Aboriginal_or_TSI": "",
        "Adults": "",
        "Aged_Persons": "Y",
        "Children": "",
        "Communities_Overseas": "",
        "Early_Childhood": "",
        "Ethnic_Groups": "",
        "Families": "",
        "Females": "",
        "Financially_Disadvantaged": "",
        "LGBTIQA+": "",
        "General_Community_in_Australia": "Y",
        "Males": "",
        "Migrants_Refugees_or_Asylum_Seekers": "",
        "Other_Beneficiaries": "",
        "Other_Charities": "",
        "People_at_risk_of_homelessness": "",
        "People_with_Chronic_Illness": "",
        "People_with_Disabilities": "",
        "Pre_Post_Release_Offenders": "",
        "Rural_Regional_Remote_Communities": "",
        "Unemployed_Person": "",
        "Veterans_or_their_families": "",
        "Victims_of_crime": "",
        "Victims_of_Disasters": "",
        "Youth": "",
        "animals": "",
        "environment": "",
        "other_gender_identities": ""
      }
    },
    {
      "record_id": "84cf15074e9b37d330d406cc475201b3badcac70b815ab72f409ba715a19cfde",
      "locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 3
      },
      "values": {
        "ABN": "88721033578",
        "Charity_Legal_Name": "SPECTRUM 3 INC.",
        "Other_Organisation_Names": "",
        "Address_Type": "Business",
        "Address_Line_1": "U 7  43 Danaher Drive",
        "Address_Line_2": "",
        "Address_Line_3": "",
        "Town_City": "South Morang",
        "State": "VIC",
        "Postcode": "3752",
        "Country": "Australia",
        "Charity_Website": "www.spectrum3.org.au",
        "Registration_Date": "09/09/2024",
        "Date_Organisation_Established": "09/09/2024",
        "Charity_Size": "",
        "Number_of_Responsible_Persons": "3",
        "Financial_Year_End": "30-Jun",
        "Operates_in_ACT": "",
        "Operates_in_NSW": "",
        "Operates_in_NT": "",
        "Operates_in_QLD": "",
        "Operates_in_SA": "",
        "Operates_in_TAS": "",
        "Operates_in_VIC": "Y",
        "Operates_in_WA": "",
        "Operating_Countries": "",
        "PBI": "Y",
        "HPC": "",
        "Preventing_or_relieving_suffering_of_animals": "",
        "Advancing_Culture": "",
        "Advancing_Education": "",
        "Advancing_Health": "",
        "Promote_or_oppose_a_change_to_law__government_poll_or_prac": "",
        "Advancing_natual_environment": "",
        "Promoting_or_protecting_human_rights": "",
        "Purposes_beneficial_to_ther_general_public_and_other_analogous": "",
        "Promoting_reconciliation__mutual_respect_and_tolerance": "",
        "Advancing_Religion": "",
        "Advancing_social_or_public_welfare": "Y",
        "Advancing_security_or_safety_of_Australia_or_Australian_public": "",
        "Aboriginal_or_TSI": "",
        "Adults": "Y",
        "Aged_Persons": "Y",
        "Children": "Y",
        "Communities_Overseas": "",
        "Early_Childhood": "",
        "Ethnic_Groups": "",
        "Families": "",
        "Females": "Y",
        "Financially_Disadvantaged": "",
        "LGBTIQA+": "",
        "General_Community_in_Australia": "Y",
        "Males": "Y",
        "Migrants_Refugees_or_Asylum_Seekers": "",
        "Other_Beneficiaries": "",
        "Other_Charities": "",
        "People_at_risk_of_homelessness": "",
        "People_with_Chronic_Illness": "",
        "People_with_Disabilities": "Y",
        "Pre_Post_Release_Offenders": "",
        "Rural_Regional_Remote_Communities": "",
        "Unemployed_Person": "",
        "Veterans_or_their_families": "",
        "Victims_of_crime": "",
        "Victims_of_Disasters": "",
        "Youth": "Y",
        "animals": "",
        "environment": "",
        "other_gender_identities": ""
      }
    }
  ],
  "observations": [
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "field": "entity.abn",
      "value": "51214424410",
      "source_fields": [
        "ABN"
      ],
      "raw_value": [
        "51214424410"
      ],
      "raw_locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "3c2dc18c3feda589be940ee51fc24f26a2ba5361e975e26a63e72de1c96904bc",
      "config_hash": "52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "2476327f3d3f839ca9e67cedcc702c346d95a4be8e01999f3268895329ee9b44"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "field": "entity.legal_name",
      "value": "U3A Inner North Incorporated",
      "source_fields": [
        "Charity_Legal_Name"
      ],
      "raw_value": [
        "U3A Inner North Incorporated"
      ],
      "raw_locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "3c2dc18c3feda589be940ee51fc24f26a2ba5361e975e26a63e72de1c96904bc",
      "config_hash": "52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "02356fe9b85f0105f99e530ab98dc1de4348a0d09e89938bc22eca273d6134c9"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "field": "address.full",
      "value": "540 Regency Rd",
      "source_fields": [
        "Address_Line_1",
        "Address_Line_2",
        "Address_Line_3"
      ],
      "raw_value": [
        "540 Regency Rd",
        "",
        ""
      ],
      "raw_locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "3c2dc18c3feda589be940ee51fc24f26a2ba5361e975e26a63e72de1c96904bc",
      "config_hash": "52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.91
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "3276aabeecb0eebc2f32264d584a2c2895dc4d60d58c2db83df2c1a9afbdb048"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "field": "address.locality",
      "value": "Enfield",
      "source_fields": [
        "Town_City"
      ],
      "raw_value": [
        "Enfield"
      ],
      "raw_locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "3c2dc18c3feda589be940ee51fc24f26a2ba5361e975e26a63e72de1c96904bc",
      "config_hash": "52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "9d56a6038706b1c282cbaeeb3b274b83c7db9f3419069267771eaeedf8581731"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "field": "address.state",
      "value": "SA",
      "source_fields": [
        "State"
      ],
      "raw_value": [
        "SA"
      ],
      "raw_locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "3c2dc18c3feda589be940ee51fc24f26a2ba5361e975e26a63e72de1c96904bc",
      "config_hash": "52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "c0578b51d54945f54d532ed57009e6e1b00e8a48940b472bfaafc73d3889e6d5"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "field": "address.postcode",
      "value": "5085",
      "source_fields": [
        "Postcode"
      ],
      "raw_value": [
        "5085"
      ],
      "raw_locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "3c2dc18c3feda589be940ee51fc24f26a2ba5361e975e26a63e72de1c96904bc",
      "config_hash": "52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "a5d27f58594d3c9bca2f87d6e3a7e6c2a65e8e292362ab95b56f974345ebd42d"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "field": "address.country",
      "value": "Australia",
      "source_fields": [
        "Country"
      ],
      "raw_value": [
        "Australia"
      ],
      "raw_locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "3c2dc18c3feda589be940ee51fc24f26a2ba5361e975e26a63e72de1c96904bc",
      "config_hash": "52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "e604cae253c995640816f2910945d126f95f9e3b830a0c3a19039bf0dcd12866"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "field": "entity.website",
      "value": "https://www.u3ainnernorth.org.au/",
      "source_fields": [
        "Charity_Website"
      ],
      "raw_value": [
        "https://www.u3ainnernorth.org.au/"
      ],
      "raw_locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "3c2dc18c3feda589be940ee51fc24f26a2ba5361e975e26a63e72de1c96904bc",
      "config_hash": "52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "99af6395e61c7e4c1eff746b09c217ce2bf8bdf91ea585e1a5011da32229a8b0"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "84cf15074e9b37d330d406cc475201b3badcac70b815ab72f409ba715a19cfde",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "field": "entity.abn",
      "value": "88721033578",
      "source_fields": [
        "ABN"
      ],
      "raw_value": [
        "88721033578"
      ],
      "raw_locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "3c2dc18c3feda589be940ee51fc24f26a2ba5361e975e26a63e72de1c96904bc",
      "config_hash": "52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "8cf0ed7410f7ff784c76f69b3787c369fd9139796360e71010bde9cfe190f536"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "84cf15074e9b37d330d406cc475201b3badcac70b815ab72f409ba715a19cfde",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "field": "entity.legal_name",
      "value": "SPECTRUM 3 INC.",
      "source_fields": [
        "Charity_Legal_Name"
      ],
      "raw_value": [
        "SPECTRUM 3 INC."
      ],
      "raw_locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "3c2dc18c3feda589be940ee51fc24f26a2ba5361e975e26a63e72de1c96904bc",
      "config_hash": "52c6dffb35e6983b8c505fda12ee6e5c9e3b507aca7f84e624a3eb422348a2ec",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "d295cbf8084b0475626ec98ba5a3021e8f5d7f916e8bd4ee02fc61a681e00f29"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 5; measured/reserved input/output: 63454/9851; calculated cost: 0.0276847.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **Other_Organisation_Names**: Documentation, p. 2 §§10-11, says this may contain one or more trading names or other names. The ontology has no source-faithful generic other-name field, no supported separator is documented, and mapping every value as entity.trading_name would assert an unsupported role; left unmapped.
- **Address_Type**: Describes the source address type; no canonical address-type field. The documentation calls the charity address a business address, retained only by address_role=business.
- **Registration_Date**: Effective ACNC charity registration date, not established as legal-entity registration; explicitly not mapped to entity.date_registered. ACNC User guide p. 2 §§16-17.
- **Date_Organisation_Established**: Organisation establishment date, not legal-entity registration date; no matching ontology field. ACNC User guide p. 3 §18.
- **Charity_Size**: Charity reporting-size classification based on the latest Annual Information Statement; no ontology field. ACNC User guide p. 3 §§19-21.
- **Number_of_Responsible_Persons**: Count of board or committee members; no ontology field. ACNC User guide p. 3 §22.
- **Financial_Year_End**: Charity financial year-end; no ontology field. ACNC User guide p. 3 §§23-24.
- **Operates_in_ACT**: Operating-location indicator; no ontology field for operating regions. ACNC User guide p. 4 §§25-26.
- **Operates_in_NSW**: Operating-location indicator; no ontology field for operating regions. ACNC User guide p. 4 §§25-26.
- **Operates_in_NT**: Operating-location indicator; no ontology field for operating regions. ACNC User guide p. 4 §§25-26.
- **Operates_in_QLD**: Operating-location indicator; no ontology field for operating regions. ACNC User guide p. 4 §§25-26.
- **Operates_in_SA**: Operating-location indicator; no ontology field for operating regions. ACNC User guide p. 4 §§25-26.
- **Operates_in_TAS**: Operating-location indicator; no ontology field for operating regions. ACNC User guide p. 4 §§25-26.
- **Operates_in_VIC**: Operating-location indicator; no ontology field for operating regions. ACNC User guide p. 4 §§25-26.
- **Operates_in_WA**: Operating-location indicator; no ontology field for operating regions. ACNC User guide p. 4 §§25-26.
- **Operating_Countries**: ISO 3166-1 alpha-3 operating-country list, not the entity's address country; no operating-country field. ACNC User guide p. 4 §§27-28.
- **PBI**: Charity subtype indicator; no ontology field. ACNC User guide p. 5 §§29-32.
- **HPC**: Charity subtype indicator; no ontology field. ACNC User guide p. 5 §§29-32.
- **Preventing_or_relieving_suffering_of_animals**: Charity subtype indicator; no ontology field. ACNC User guide p. 5 §§29-32.
- **Advancing_Culture**: Charity subtype indicator; no ontology field. ACNC User guide p. 5 §§29-32.
- **Advancing_Education**: Charity subtype indicator; no ontology field. ACNC User guide p. 5 §§29-32.
- **Advancing_Health**: Charity subtype indicator; no ontology field. ACNC User guide p. 5 §§29-32.
- **Promote_or_oppose_a_change_to_law__government_poll_or_prac**: Charity subtype indicator; no ontology field. ACNC User guide p. 5 §§29-32.
- **Advancing_natual_environment**: Charity subtype indicator; exact source spelling retained; no ontology field. ACNC User guide p. 5 §§29-32.
- **Promoting_or_protecting_human_rights**: Charity subtype indicator; no ontology field. ACNC User guide p. 5 §§29-32.
- **Purposes_beneficial_to_ther_general_public_and_other_analogous**: Charity subtype indicator; exact source spelling retained; no ontology field. ACNC User guide p. 5 §§29-32.
- **Promoting_reconciliation__mutual_respect_and_tolerance**: Charity subtype indicator; no ontology field. ACNC User guide p. 5 §§29-32.
- **Advancing_Religion**: Charity subtype indicator; no ontology field. ACNC User guide p. 5 §§29-32.
- **Advancing_social_or_public_welfare**: Charity subtype indicator; no ontology field. ACNC User guide p. 5 §§29-32.
- **Advancing_security_or_safety_of_Australia_or_Australian_public**: Charity subtype indicator; no ontology field. ACNC User guide p. 5 §§29-32.
- **Aboriginal_or_TSI**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Adults**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Aged_Persons**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Children**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Communities_Overseas**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Early_Childhood**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Ethnic_Groups**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Families**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Females**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Financially_Disadvantaged**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **LGBTIQA+**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **General_Community_in_Australia**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Males**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Migrants_Refugees_or_Asylum_Seekers**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Other_Beneficiaries**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Other_Charities**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **People_at_risk_of_homelessness**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **People_with_Chronic_Illness**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **People_with_Disabilities**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Pre_Post_Release_Offenders**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Rural_Regional_Remote_Communities**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Unemployed_Person**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Veterans_or_their_families**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Victims_of_crime**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Victims_of_Disasters**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **Youth**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **animals**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **environment**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.
- **other_gender_identities**: Charity beneficiary indicator; no ontology field. ACNC User guide p. 6 §§33-34.

## Uncertainties

- The source envelope publication_proxy 2026-09-13T19:00:54.497199 is used as a dataset-level observation-time proxy; no record-level statement timestamp is supplied.
- The ACNC Registered Charities dataset is a subset of the Charity Register, updated weekly, and may exclude records or fields withheld by charities; absence is not evidence of nonexistence. ACNC User guide, p. 1 §§2-5.
- Other_Organisation_Names is intentionally unmapped because it may contain trading names or other names and may contain one or more names; the ontology lacks a generic name-role field and the source supplies no documented separator.
- The supplied discovery analysis reports 300 records while prior validation reports 250 records with zero filters; this coverage discrepancy is unresolved and requires reconciliation before relying on production coverage. The frozen reader/header configuration is retained unchanged.
- The source does not explicitly establish entity_type, status, ACN, industry_code, or legal-entity registration date; none are inferred. Charity registration is not treated as company registration, and no active status is inferred.
- The source reports a business address, but observed samples include PO Boxes; address_role=business follows the documentation and does not reinterpret the value as a registered address.
- All source-reliability and field-confidence scores are provisional judgements requiring human review.
- The mapping is deliberately partial: Other_Organisation_Names is left unmapped even though documentation says it may contain trading names or other names. This is defensible because the field may contain multiple values without a documented separator and does not establish that every value is a trading name; human review may nevertheless consider a source-faithful one-value treatment if the full-file format supports it.
- Registration_Date is correctly not mapped to entity.date_registered: it is the effective ACNC charity-registration date, not established here as legal-entity registration. No status is asserted, which avoids incorrectly treating inclusion in this weekly registered-charities extract as an ontology active status.
- The business address mapping follows the source documentation, but discovery includes PO Boxes (for example 'Po Box 3122'); this is a source business-address field, not necessarily a physical service location or registered office. The mapping discloses this limitation and does not invent an address subtype.
- The source has no reporting-group field or evidence of group membership; none is demanded or inferred. It also does not support entity_type, ACN, industry_code, or a legal-entity registration date, and leaving these unmapped is appropriate.
- The supplied discovery/validation coverage is inconsistent (discovery analysis reports 300 records while validation reports 250); this is a material coverage/reconciliation limitation, but not a semantic defect in the field mappings themselves.
- The dataset can omit withheld records or values, so blanks must not be interpreted as negative facts. The mapping limitations disclose this.
- Confidence values are appropriately separated by claim type where used and appear to be provisional judgements; no link confidence is required because the mapping emits no cross-source entity links.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b898-85d1-7c43-af06-1cca2f8a5f06/run/01a0b89c-f64e-7561-a3ba-053c72c1c19e?start_time=2026-09-19T07%3A41%3A29.550842%2B00%3A00)