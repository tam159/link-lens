# Mapping review: ACNC Registered Charities
Config version **2**, hash `6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa`.
Grain: One row per ACNC-registered charity record, normally identified by the supplied ABN, with weekly current-register attributes.. Subject: **legal_entity**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| ABN | entity.abn | trim, abn | 0.97 | ACNC user notes Dec 2024 p.2 ¶6–7: ABN is the charity Australian Business Number and numeric; supplied header ABN, sample 51214424410. |
| Address_Line_1 | address.full | trim | 0.82 | ACNC user notes Dec 2024 p.2 ¶12–14 define Address line 1 as part of the reported charity business address; supplied sample Address_Line_1=540 Regency Rd. |
| Town_City | address.locality | trim | 0.94 | ACNC user notes Dec 2024 p.2 ¶13–14 list Town/City as a business-address field; supplied sample Town_City=Enfield. |
| State | address.state | trim, uppercase | 0.97 | ACNC user notes Dec 2024 p.2 ¶13–14 list State as a business-address field; supplied samples use SA, VIC, NSW, NT, QLD and WA. |
| Postcode | address.postcode | trim, postcode | 0.96 | ACNC user notes Dec 2024 p.2 ¶13–14 list Postcode as a business-address field; supplied sample Postcode=0820 supports preservation as text. |
| Country | address.country | trim | 0.94 | ACNC user notes Dec 2024 p.2 ¶13–14 list Country as a business-address field; supplied sample Country=Australia. |
| Charity_Website | entity.website | trim, website | 0.94 | ACNC user notes Dec 2024 p.2 ¶15: field contains charity website address where supplied; samples include https://www.u3ainnernorth.org.au/ and www.spectrum3.org.au. |

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
      "extractor_version": "extractor-1:6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
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
      "config_hash": "6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "70f2168e83a4bdd2535fec83529cff32510bcc0cd2b41db604f28531436658ae"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
      "field": "address.full",
      "value": "540 Regency Rd",
      "source_fields": [
        "Address_Line_1"
      ],
      "raw_value": [
        "540 Regency Rd"
      ],
      "raw_locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "3c2dc18c3feda589be940ee51fc24f26a2ba5361e975e26a63e72de1c96904bc",
      "config_hash": "6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.82
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "43c230b6f5b00624bdd62c9eef632b1456f953d6920eec1b56673c250fa94c03"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
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
      "config_hash": "6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "1d81e488234c43491a0d1a6e1109a0a3f1c94e1273d670b60739f21aa4fb169c"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
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
      "config_hash": "6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "aa1cebc7f4a247dc4c2e6b22e1a7a42801180939e2b8357432ca5661d485dd2f"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
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
      "config_hash": "6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "2d2c41895d093fa74a1f024bf4ceea4facf5c2dc5d8b7d2128ebb9b751fc1d9b"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
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
      "config_hash": "6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "e563f391727fcd3399f3317d8197e1f9249c91e741bcfe34bb650e277c88e0d5"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "f397ffb9e7bc1c4b64598443efab06caa9765667deedad731906c79655ce3e2d",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
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
      "config_hash": "6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "07ad8a6c6da6124a89a3e490713bdedeadf891f5607e34a80f1556d9175ffeb9"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "84cf15074e9b37d330d406cc475201b3badcac70b815ab72f409ba715a19cfde",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
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
      "config_hash": "6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "b4d9f0ececa6ada6ec362d4f80d8f3174add0e904eb9dc97c9ef85de8117b909"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "84cf15074e9b37d330d406cc475201b3badcac70b815ab72f409ba715a19cfde",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
      "field": "address.full",
      "value": "U 7  43 Danaher Drive",
      "source_fields": [
        "Address_Line_1"
      ],
      "raw_value": [
        "U 7  43 Danaher Drive"
      ],
      "raw_locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "3c2dc18c3feda589be940ee51fc24f26a2ba5361e975e26a63e72de1c96904bc",
      "config_hash": "6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.82
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "9568a3a55d68579a9c793a3573708f259f13010ffe48abcbf8cd48f85bdd9417"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "84cf15074e9b37d330d406cc475201b3badcac70b815ab72f409ba715a19cfde",
      "observed_at": "2026-09-13T19:00:54.497199+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-18T00:57:06.135607+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
      "field": "address.locality",
      "value": "South Morang",
      "source_fields": [
        "Town_City"
      ],
      "raw_value": [
        "South Morang"
      ],
      "raw_locator": {
        "snapshot_sha": "d1c52aee8a24ed76a2897c2c43c2b4b7beda7465449a5401249a0a5defa4a8aa",
        "sheet": "csv",
        "row": 3
      },
      "snapshot_id": "3c2dc18c3feda589be940ee51fc24f26a2ba5361e975e26a63e72de1c96904bc",
      "config_hash": "6a404a7904ebf06f5060e97e0c6c86b5fee42840970ff5fe4686801942de59ef",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "id": "b88857d5618d0ed4fb7b86e1e23d25f6d032d30de7a37dd5d4b34f9e91f9a66a"
    }
  ]
}
```

## Checks

Validation: 250 records; 0 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 5; measured/reserved input/output: 75211/9633; calculated cost: None.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **Charity_Legal_Name**: Although p.2 ¶8 calls this the formal legal/official name, it may contain an alternate identifier when the legal name is withheld. No source field distinguishes that exception; retained only as subject_label_field.
- **Other_Organisation_Names**: Notes p.2 ¶10–11 permit one or more trading or other names but give no delimiter/one-name rule; cannot safely emit a single trading-name observation.
- **Address_Type**: Documentation p.2 ¶12–14 defines the address fields as business address but does not define this additional header or its value vocabulary; source-level address_role is business.
- **Address_Line_2**: Additional business-address component (notes p.2 ¶13–14), but no blank-safe declarative composition is available; mapping it independently to address.full would emit competing partial full addresses.
- **Address_Line_3**: Additional business-address component (notes p.2 ¶13–14), but no blank-safe declarative composition is available; mapping it independently to address.full would emit competing partial full addresses.
- **Registration_Date**: Notes p.2 ¶16–17 define effective ACNC charity-registration date, not entity/company date_registered.
- **Date_Organisation_Established**: Notes p.3 ¶18 define date the charity was established; it is not entity/company date_registered and no matching canonical field exists.
- **Charity_Size**: Latest Annual Information Statement reporting-size category (notes p.3 ¶19–21); no matching canonical field.
- **Number_of_Responsible_Persons**: Board/committee-member count (notes p.3 ¶22); no matching canonical field.
- **Financial_Year_End**: Charity financial-year-end value (notes p.3 ¶23–24); no matching canonical field.
- **Operates_in_ACT**: Operating-location Y/blank flag (notes p.4 ¶25–26); no matching canonical field.
- **Operates_in_NSW**: Operating-location Y/blank flag (notes p.4 ¶25–26); no matching canonical field.
- **Operates_in_NT**: Operating-location Y/blank flag (notes p.4 ¶25–26); no matching canonical field.
- **Operates_in_QLD**: Operating-location Y/blank flag (notes p.4 ¶25–26); no matching canonical field.
- **Operates_in_SA**: Operating-location Y/blank flag (notes p.4 ¶25–26); no matching canonical field.
- **Operates_in_TAS**: Operating-location Y/blank flag (notes p.4 ¶25–26); no matching canonical field.
- **Operates_in_VIC**: Operating-location Y/blank flag (notes p.4 ¶25–26); no matching canonical field.
- **Operates_in_WA**: Operating-location Y/blank flag (notes p.4 ¶25–26); no matching canonical field.
- **Operating_Countries**: Comma-separated ISO 3166-1 alpha-3 operating-country codes (notes p.4 ¶27–28), not the business-address country; no matching canonical field.
- **PBI**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **HPC**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **Preventing_or_relieving_suffering_of_animals**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **Advancing_Culture**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **Advancing_Education**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **Advancing_Health**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **Promote_or_oppose_a_change_to_law__government_poll_or_prac**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **Advancing_natual_environment**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **Promoting_or_protecting_human_rights**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **Purposes_beneficial_to_ther_general_public_and_other_analogous**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **Promoting_reconciliation__mutual_respect_and_tolerance**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **Advancing_Religion**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **Advancing_social_or_public_welfare**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **Advancing_security_or_safety_of_Australia_or_Australian_public**: Charity subtype Y/blank flag (notes p.5 ¶29–32); no matching canonical field.
- **Aboriginal_or_TSI**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Adults**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Aged_Persons**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Children**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Communities_Overseas**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Early_Childhood**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Ethnic_Groups**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Families**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Females**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Financially_Disadvantaged**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **LGBTIQA+**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **General_Community_in_Australia**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Males**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Migrants_Refugees_or_Asylum_Seekers**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Other_Beneficiaries**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Other_Charities**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **People_at_risk_of_homelessness**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **People_with_Chronic_Illness**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **People_with_Disabilities**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Pre_Post_Release_Offenders**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Rural_Regional_Remote_Communities**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Unemployed_Person**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Veterans_or_their_families**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Victims_of_crime**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Victims_of_Disasters**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **Youth**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **animals**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **environment**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.
- **other_gender_identities**: Beneficiary-group Y/blank flag (notes p.6 ¶33–34); no matching canonical field.

## Uncertainties

- This is a weekly updated subset of the ACNC Charity Register, containing registered charities only; it is not a general company register (notes p.1 ¶2–5).
- Information may be withheld, including whole records; blanks can mean not supplied or withheld (notes p.1 ¶5; p.2 ¶8, ¶14–15).
- Charity_Legal_Name is retained exclusively as raw subject label because notes p.2 ¶8 permit an alternate identifier in place of a withheld legal name; no entity.legal_name assertion is made.
- The ABN filter excludes withheld/missing ABN records rather than constructing identifiers. No ACN is supplied or inferred, and no entity type, company status, or company registration date is asserted.
- Address Line 1 is emitted as the sole address.full component to avoid the prior literal None defect from joining blank lines. Address Line 2 and 3 remain unmapped pending a blank-omitting composition operation. The documented business-address fields can contain postal-style values such as supplied samples Po Box 240 and Locked Bag 7064; they are not confirmed physical/service locations.
- Publication timestamp is an envelope-supplied proxy, not a per-record or per-field statement timestamp.
- All authority, source-reliability, and field-confidence scores are provisional uncalibrated judgements requiring human review.
- The active mapping deliberately does not emit `Charity_Legal_Name` as `entity.legal_name`. This is appropriate because ACNC notes p.2 ¶8 allow an alternate identifier to replace a withheld legal name; the source does not provide a reliable discriminator. The retained subject label must not be promoted downstream to a legal-name claim without resolving that exception.
- `Other_Organisation_Names` is correctly left unmapped. It can contain one or more trading or other names, and the documentation supplies no safe delimiter or per-name rule. It must not be treated as a legal name.
- The mapped address is the source-reported business address, not an operating/service location, branch address, or confirmed physical location. Discovery includes postal-style `Po Box 240` and `Locked Bag 7064` values. Preserve the business-address role and do not infer a service location.
- `address.full` is only `Address_Line_1`; Address_Line_2 and Address_Line_3 are omitted. This is a disclosed lossy representation rather than a reconstructed complete address. Reviewers should decide whether a line-1-only value is acceptable for the consumer of `address.full`; no unsupported concatenation or null literals are currently introduced.
- The mapping properly does not map ACNC `Registration_Date` to `entity.date_registered`: documentation defines it as the effective ACNC charity-registration date, including a 3 December 2012 default for pre-existing concession registrants. No entity registration, current status, ACN, entity type, branch, or reporting-group claim is supported here.
- The ABN filter deliberately excludes rows with withheld/missing ABNs. This creates a coverage limitation, not a negative claim about omitted charities. The row grain is reasonably a current ACNC-registered-charity record, normally ABN-identified, rather than a general company-register, branch, operating-location, or reporting-group record.
- The publication timestamp is explicitly recorded as a dataset-level proxy rather than a record-change timestamp; the assumed UTC treatment of a naive source timestamp remains a disclosed technical assumption.
- Confidence values and source reliability are expressly uncalibrated judgement values. They should not be read as measured precision or accuracy.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0b208-8ca1-74c3-bcd7-758b6267e99d/run/01a0b20c-17d6-7070-a79d-13269e59ec3b?start_time=2026-09-18T01%3A05%3A32.118783%2B00%3A00)