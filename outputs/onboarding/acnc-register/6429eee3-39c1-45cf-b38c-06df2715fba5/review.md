# Mapping review: ACNC Registered Charities
Config version **2**, hash `6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa`.
Grain: One row per ACNC-registered charity record, primarily identified by the source ABN; the row describes the charity/legal-entity record and its business address, not separate legal entities for other names.. Subject: **legal_entity**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| ABN | entity.abn | digits, abn | 0.98 | ACNC Registered Charities User Guide, Dec 2024, p.2 §§6-7: ABN is the charity's Australian Business Number and the field is numeric; exact header ABN and sample 51214424410. Validated with the ABN operation; this does not infer entity type. |
| Charity_Legal_Name | entity.legal_name | trim | 0.97 | ACNC Registered Charities User Guide, Dec 2024, p.2 §§8-9: Charity name is the charity's formal name as it appears on legal or official documents; exact header Charity_Legal_Name and samples U3A Inner North Incorporated and SPECTRUM 3 INC. |
| Other_Organisation_Names | entity.trading_name | trim | 0.86 | ACNC Registered Charities User Guide, Dec 2024, p.2 §§10-11: other organisation names can include trading names or other names by which the charity is known; exact header Other_Organisation_Names and sample Georges Riverkeeper. No separator is inferred. |
| Address_Line_1, Address_Line_2, Address_Line_3 | address.full | join | 0.91 | ACNC Registered Charities User Guide, Dec 2024, p.2 §§12-14: Charity address is the business address and includes address lines 1-3; exact headers Address_Line_1, Address_Line_2, Address_Line_3 and sample 540 Regency Rd. It may be a PO Box, as shown by validation output Po Box 3122. |
| Town_City | address.locality | trim | 0.98 | ACNC Registered Charities User Guide, Dec 2024, p.2 §13 lists Town/City among the address fields; exact header Town_City and sample Enfield. |
| State | address.state | trim, uppercase | 0.98 | ACNC Registered Charities User Guide, Dec 2024, p.2 §13 lists State among the address fields; exact header State and samples SA and VIC. |
| Postcode | address.postcode | trim, postcode | 0.97 | ACNC Registered Charities User Guide, Dec 2024, p.2 §13 lists Postcode among the address fields; exact header Postcode and sample 5085. The postcode operation does not zero-pad damaged values. |
| Country | address.country | trim | 0.97 | ACNC Registered Charities User Guide, Dec 2024, p.2 §13 lists Country among the address fields; exact header Country and sample Australia. |
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
      "extractor_version": "extractor-1:6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
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
      "config_hash": "6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "9794980cf1065d2960ef60ff4a4237191e714e24ec1f3312df837c387b91a1dd"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
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
      "config_hash": "6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "6b7a6b6b08cf64fb6c1be33a5a78a65e6804afddaddd37d7d282381d04a90838"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
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
      "config_hash": "6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.91
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "777d14c053eb963d2efed519f1bda267f69b1002d3dc42041429c4321e5756ff"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
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
      "config_hash": "6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "65220f0b0c3b415150869227637bac08b8ac2258ea8ba8b5adacf8200a24e759"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
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
      "config_hash": "6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "4bc055607fb71146ad3bef6f8dc5dea90379f5f369313d82fe12f5a44cfc6950"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
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
      "config_hash": "6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "b4f10c50134c7cf1f980fa86d95b17b4b17cc6ea72a637b68f9bd207885dccc2"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
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
      "config_hash": "6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "6f92fa832230818aaed2b57ddb012be680591d4016949c9e2a64a3aee93876b6"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
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
      "config_hash": "6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "8ee63e6fa762122f76b023b41e8790602212cc510f8cdc386ff2faf0af3eb749"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "84cf15074e9b37d330d406cc475201b3badcac70b815ab72f409ba715a19cfde",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
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
      "config_hash": "6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "9d200e47fb686d1644c851fc2c722f95f3f2ad628674af17251c024ba5bfaaa1"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "84cf15074e9b37d330d406cc475201b3badcac70b815ab72f409ba715a19cfde",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
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
      "config_hash": "6a92ce3e28985bd800d30112d85c9b53cf9ee7016aa2189fa0fdf123c9fbcebb",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.93,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "8c19b7ad77124c8f094e23258e1569d21f06a1459e67c0dcb9c39d5ffcd45b29"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 4; measured/reserved input/output: 66811/8483; calculated cost: 0.02688235.
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
- **Operating_Countries**: ISO 3166-1 alpha-3 operating-country list, not the address country; no operating-country ontology field. ACNC User Guide Dec 2024 p.4 §§27-28.
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
- The mapping is deliberately partial: it leaves ACNC registration date, organisation-establishment date, status, entity type, reporting groups, operating locations, subtypes, beneficiaries, and responsible-person/financial fields unmapped rather than assigning unsupported ontology meanings.
- The source business address is correctly treated as an address claim for the charity record, but the source permits PO Boxes; it should not be interpreted as a registered office or necessarily a physical service location.
- Other_Organisation_Names may contain multiple trading or other names, but no separator is documented. Emitting the trimmed field as one trading_name observation is conservative and does not assert separate entities or ownership; review whether the engine's one-value behavior is acceptable for multi-name cells.
- The ACNC registration date is explicitly not the legal entity registration date, so omitting entity.date_registered is correct. No source status semantics support an active/deregistered claim.
- The publication timestamp is a disclosed dataset-level observed_at proxy, not row-change time; this is an acceptable limitation under the supplied engine semantics.
- The source may withhold records/fields, so blank values cannot be read as negative facts. ABN checksum validation and the documented non-conversion of ACN/ABN forms are appropriate.
- No unsupported constants appear in the mapped fields: country is sourced from Country, and no entity type/status/legal meaning is invented. Confidence values are disclosed provisional judgements, not measured probabilities.
- The preview and failed exploratory script do not establish full-file duplicate/blank/value distributions, but the mapping does not rely on those unverified distributions. Validation passed with no quarantined fields or parse errors.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b8f1-1af0-7540-8bf1-1f40e24416f0/run/01a0b8f1-ef41-77c1-bcf3-f53a62e61a88?start_time=2026-09-19T09%3A14%3A18.305737%2B00%3A00)