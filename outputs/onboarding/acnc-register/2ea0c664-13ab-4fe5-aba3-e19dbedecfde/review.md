# Mapping review: ACNC Registered Charities
Config version **1**, hash `44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa`.
Grain: One row per ACNC-registered charity record, primarily identified by source ABN; the row describes the charity record and its business address, not separate legal entities for other names.. Subject: **legal_entity**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| ABN | entity.abn | digits, abn | 0.98 | ACNC Registered Charities User Guide, Dec 2024, p.2 §§6-7: ABN is the charity's Australian Business Number and the field is numeric; exact header ABN and sample 51214424410. The abn operation validates checksum and does not infer ACN or entity type. |
| Charity_Legal_Name | entity.legal_name | trim | 0.97 | ACNC Registered Charities User Guide, Dec 2024, p.2 §§8-9: Charity name is the charity's formal name as it appears on legal or official documents; exact header Charity_Legal_Name and samples U3A Inner North Incorporated and SPECTRUM 3 INC. |
| Other_Organisation_Names | entity.trading_name | trim | 0.86 | ACNC Registered Charities User Guide, Dec 2024, p.2 §§10-11: other organisation names can include trading names or other names by which the charity is known; exact header Other_Organisation_Names and sample Georges Riverkeeper. No separator is inferred. |
| Address_Line_1, Address_Line_2, Address_Line_3 | address.full | join | 0.91 | ACNC Registered Charities User Guide, Dec 2024, p.2 §§12-14: Charity address is the business address and includes address lines 1-3; exact headers Address_Line_1, Address_Line_2, Address_Line_3 and sample 540 Regency Rd. Discovery rows also show PO Box values, so this remains a source address claim. |
| Town_City | address.locality | trim | 0.98 | ACNC Registered Charities User Guide, Dec 2024, p.2 §13 lists Town/City among address fields; exact header Town_City and sample Enfield. |
| State | address.state | trim, uppercase | 0.98 | ACNC Registered Charities User Guide, Dec 2024, p.2 §13 lists State among address fields; exact header State and samples SA and VIC. |
| Postcode | address.postcode | trim, postcode | 0.97 | ACNC Registered Charities User Guide, Dec 2024, p.2 §13 lists Postcode among address fields; exact header Postcode and sample 5085. The postcode operation preserves numeric IDs as strings and does not zero-pad damaged values. |
| Country | address.country | trim | 0.97 | ACNC Registered Charities User Guide, Dec 2024, p.2 §13 lists Country among address fields; exact header Country and sample Australia. |
| Charity_Website | entity.website | trim, website | 0.96 | ACNC Registered Charities User Guide, Dec 2024, p.2 §15: Charity website contains the supplied website address; exact header Charity_Website and samples https://www.u3ainnernorth.org.au/ and www.spectrum3.org.au. |

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
      "extractor_version": "extractor-1:44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
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
      "config_hash": "44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "1a4ec28abdd3fca3dda5384d139c2c52f7f96c82ddeefc91226142856326e939"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
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
      "config_hash": "44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "4013a71c19a21a73389dbe9f5ffe9511593cc8d5019f400308c1d76a2a9f4226"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
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
      "config_hash": "44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.91
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "ddefea850d3ab1b90e81dcbeca58edb36862d6f7360e415f49ec927a3fbdd49a"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
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
      "config_hash": "44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "b4e1873462fb612abe2be9166cad70155a92083c5d3107e85e8d73be34939712"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
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
      "config_hash": "44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "9ddcc17b358aed8489d7b8e8759075b2f57c310953ebb43f26871f1cb91857b6"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
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
      "config_hash": "44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "406e279c1453d1a9649af2d3d84f7816fc681703cc6d09bcc5994e939d657524"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
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
      "config_hash": "44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "f7e80a97826ba808e45e6041aae8964100c1ae153177e51ee30f49b983ae4aa2"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
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
      "config_hash": "44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "791a8bfed2e6e338212b8061a7843a4f97788c0e5de68cade2a75c9bc7fbd34f"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "84cf15074e9b37d330d406cc475201b3badcac70b815ab72f409ba715a19cfde",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
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
      "config_hash": "44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "9f02e4e6b7bb7a7360d2d55bc17dbb8471e151846cdde908c9993aadc98727c3"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "84cf15074e9b37d330d406cc475201b3badcac70b815ab72f409ba715a19cfde",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
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
      "config_hash": "44fda6069d8697cfbbce223d43eaf65dcc0543cd212600de0719df45dbaf673b",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "6eb7c569e5319c953c698fa4f7b1500e426ce5263c0dcbbc2400a0e83f12d115"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 2; measured/reserved input/output: 33625/4390; calculated cost: 0.013674249999999999.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **Address_Type**: Business-address type label has no corresponding ontology field; address_role=business is supported by ACNC User Guide Dec 2024 p.2 §§12-14, so the raw column is not separately emitted.
- **Registration_Date**: ACNC charity registration effective date, not legal-entity registration date; deliberately not mapped to entity.date_registered. ACNC User Guide Dec 2024 p.2 §§16-17.
- **Date_Organisation_Established**: Organisation establishment date, not legal-entity registration date, and no matching ontology field exists. ACNC User Guide Dec 2024 p.3 §18.
- **Charity_Size**: Charity reporting-size classification based on the latest Annual Information Statement; no ontology field. ACNC User Guide Dec 2024 p.3 §§19-21.
- **Number_of_Responsible_Persons**: Count of board or committee members; no ontology field. ACNC User Guide Dec 2024 p.3 §22.
- **Financial_Year_End**: Charity financial-year end; no ontology field. ACNC User Guide Dec 2024 p.3 §§23-24.
- **Operates_in_ACT**: Operating-location indicator; ontology has no operating-region field. ACNC User Guide Dec 2024 p.4 §§25-26.
- **Operates_in_NSW**: Operating-location indicator; ontology has no operating-region field. ACNC User Guide Dec 2024 p.4 §§25-26.
- **Operates_in_NT**: Operating-location indicator; ontology has no operating-region field. ACNC User Guide Dec 2024 p.4 §§25-26.
- **Operates_in_QLD**: Operating-location indicator; ontology has no operating-region field. ACNC User Guide Dec 2024 p.4 §§25-26.
- **Operates_in_SA**: Operating-location indicator; ontology has no operating-region field. ACNC User Guide Dec 2024 p.4 §§25-26.
- **Operates_in_TAS**: Operating-location indicator; ontology has no operating-region field. ACNC User Guide Dec 2024 p.4 §§25-26.
- **Operates_in_VIC**: Operating-location indicator; ontology has no operating-region field. ACNC User Guide Dec 2024 p.4 §§25-26.
- **Operates_in_WA**: Operating-location indicator; ontology has no operating-region field. ACNC User Guide Dec 2024 p.4 §§25-26.
- **Operating_Countries**: ISO 3166-1 alpha-3 operating-country list, not address country; no operating-country ontology field. ACNC User Guide Dec 2024 p.4 §§27-28.
- **PBI**: Charity subtype indicator; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **HPC**: Charity subtype indicator; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **Preventing_or_relieving_suffering_of_animals**: Charity subtype indicator; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **Advancing_Culture**: Charity subtype indicator; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **Advancing_Education**: Charity subtype indicator; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **Advancing_Health**: Charity subtype indicator; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **Promote_or_oppose_a_change_to_law__government_poll_or_prac**: Charity subtype indicator; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **Advancing_natual_environment**: Charity subtype indicator; source spelling retained; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **Promoting_or_protecting_human_rights**: Charity subtype indicator; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **Purposes_beneficial_to_ther_general_public_and_other_analogous**: Charity subtype indicator; source spelling retained; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **Promoting_reconciliation__mutual_respect_and_tolerance**: Charity subtype indicator; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **Advancing_Religion**: Charity subtype indicator; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **Advancing_social_or_public_welfare**: Charity subtype indicator; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **Advancing_security_or_safety_of_Australia_or_Australian_public**: Charity subtype indicator; no ontology field. ACNC User Guide Dec 2024 p.5 §§29-32.
- **Aboriginal_or_TSI**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Adults**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Aged_Persons**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Children**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Communities_Overseas**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Early_Childhood**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Ethnic_Groups**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Families**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Females**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Financially_Disadvantaged**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **LGBTIQA+**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **General_Community_in_Australia**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Males**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Migrants_Refugees_or_Asylum_Seekers**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Other_Beneficiaries**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Other_Charities**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **People_at_risk_of_homelessness**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **People_with_Chronic_Illness**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **People_with_Disabilities**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Pre_Post_Release_Offenders**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Rural_Regional_Remote_Communities**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Unemployed_Person**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Veterans_or_their_families**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Victims_of_crime**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Victims_of_Disasters**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **Youth**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **animals**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **environment**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.
- **other_gender_identities**: Charity beneficiary indicator; no ontology field. ACNC User Guide Dec 2024 p.6 §§33-34.

## Uncertainties

- The source envelope publication_proxy 2026-09-13T19:00:54.497199 is used as a dataset-level observed_at proxy; it is not a row-change timestamp.
- The dataset is updated weekly and only includes ACNC-registered charities; records or fields may be withheld, so absence is not evidence of nonexistence. ACNC User Guide Dec 2024 p.1 §§2-5.
- Other_Organisation_Names may contain one or more names; this mapping emits the raw trimmed field as one trading_name observation because no documented separator is supplied and does not assert separate legal entities or ownership for each name.
- The business address is source-described as a business address and may include PO Boxes; it is not asserted to be a registered office or physical service location.
- Registration_Date is ACNC charity registration, not legal-entity registration; no entity.date_registered, entity.status, entity.entity_type, ACN, ARBN, liquidation, or deregistration claim is inferred.
- ABN values may be withheld or substituted by an alternate identifier in the charity-name field; ABN checksum validation emits only valid ABNs and does not infer incorporation type.
- No reporting-group or ownership/holder relationship is supplied.
- All authority and field-confidence scores are provisional judgements requiring human review.
- The frozen reader and partitions are retained unchanged.
- The mapping is deliberately partial and leaves ACNC registration date, establishment date, status, entity type, operating locations/countries, subtypes, beneficiaries, responsible-person count, size, and financial year end unmapped because the ontology lacks compatible fields or the semantics do not support the target. This is appropriate rather than a defect.
- The source documentation says Charity_Legal_Name is formal/legal or official name, but may contain an ACNC alternate identifier when the legal name is withheld; the mapping does not condition or flag such substituted values, so legal_name confidence should be understood as conditional on the source value actually being a legal name.
- Other_Organisation_Names may contain multiple trading or other names. Emitting the unsplit trimmed field as one trading_name observation is supported by the absence of a documented separator, but it can represent multiple names in one value and does not establish ownership; this limitation is disclosed.
- The business address is explicitly an operating/business address, not necessarily a registered office. Discovery includes PO Box values, so address.full is a source address claim and should not be interpreted as a physical service location without further qualification.
- Country is copied as the address-country value (observed as Australia), while Operating_Countries is correctly left unmapped; the source's alpha-3 operating-country codes are not address country.
- No source field supplies current/historic entity status or reporting-group membership, and the mapping correctly does not invent them.
- Confidence values are provisional judgements, not measured probabilities. The discovery/exploration script failed due to a counting bug and cannot establish full-file distributions; validation passed on its separate sample but is not semantic proof.
- The source publication proxy is an allowed dataset-level observed_at policy, not a row-change timestamp; this is disclosed. The supplied envelope semantics cover required provenance fields.
- Address_Type is unmapped despite being Business; the mapping's declared business address role and source documentation adequately explain the semantic use, and no ontology field requires the raw type label.
- The source dataset is weekly and may omit withheld records or fields; blank values therefore do not mean nonexistence. No unsupported constants or legal meanings are introduced. The mapped ABN operation is appropriate under the authoritative checksum semantics; no ACN suffix derivation is made.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b939-c15c-7e73-bddb-06062cf2e8ce/run/01a0b93a-1d99-76a3-b508-9cf812c63ed3?start_time=2026-09-19T10%3A33%3A08.761830%2B00%3A00)