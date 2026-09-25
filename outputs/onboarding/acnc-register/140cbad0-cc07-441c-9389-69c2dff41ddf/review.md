# Mapping review: ACNC Registered Charities
Config version **1**, hash `50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8`.
Ontology: `4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227`.
Licence: Creative Commons Attribution 3.0 Australia. Source snapshot: `4cc8292de175ba9c6af0bfe4562fd4d21881fd6d2e9f99dd09b6d9e3d31b633f`.
Grain: One ACNC Registered Charities CSV row representing a charity register record with charity attributes, a business address, and reported operating, subtype, and beneficiary indicators.. Subject: **legal_entity**.
Reader: `{"format": "csv", "encoding": "utf-8-sig", "delimiter": ",", "sheet": null, "header_row": 1, "json_records_path": []}`.

## Mappings

| Source fields | Canonical field | Operations | Confidence | Evidence |
|---|---|---|---|---|
| ABN | entity.abn | abn | 0.99 | ACNC Registered Charities user guide, PDF p. 2 §6: “This is a charity’s Australian Business Number (ABN).” Source header ABN; supplied sample row 2 value 97830467530. |
| Address_Type | address.type | trim, enum | 0.94 | Frozen header Address_Type; supplied sample row 2 is “Business”. ACNC user guide, PDF p. 2 §§12–14, identifies the charity address as its business address; ontology address.type retains the documented address category. |
| Address_Line_1 | address.line_1 | trim | 0.97 | ACNC user guide, PDF p. 2 §§13–14, lists Address line 1 among the charity business-address fields. Frozen header Address_Line_1; sample row 2 “L 15 216 St Georges Tce”. |
| Address_Line_2 | address.line_2 | trim | 0.97 | ACNC user guide, PDF p. 2 §§13–14, lists Address line 2 among the charity business-address fields. Frozen header Address_Line_2; supplied sample row 2 is blank. |
| Address_Line_3 | address.line_3 | trim | 0.97 | ACNC user guide, PDF p. 2 §§13–14, lists Address line 3 among the charity business-address fields and notes it is blank for many charities. Frozen header Address_Line_3; supplied sample row 2 is blank. |
| Town_City | address.locality | trim | 0.96 | ACNC user guide, PDF p. 2 §§13–14, lists Town/City among the charity business-address fields. Frozen header Town_City; sample row 2 “Perth”. |
| State | address.state | trim, enum | 0.95 | ACNC user guide, PDF p. 2 §§13–14, lists State among business-address fields. Frozen header State; sample row 2 “WA”; enum retains documented Australian state/territory abbreviations. |
| Postcode | address.postcode | trim | 0.96 | ACNC user guide, PDF p. 2 §§13–14, lists Postcode among the charity business-address fields. Frozen header Postcode; sample row 2 “6000”; retained as text. |
| Country | address.country | trim | 0.95 | ACNC user guide, PDF p. 2 §§13–14, lists Country among the charity business-address fields. Frozen header Country; sample row 2 “Australia”. |
| Charity_Website | entity.website | trim, website | 0.93 | ACNC user guide, PDF p. 2 §15: this field contains the charity’s website address where supplied. Frozen header Charity_Website; sample row 4 “www.nwrl.org.au”. Non-website representations such as sample value “Instagram” are not reinterpreted and may be quarantined. |
| Registration_Date | registration.acnc_date_registered | date | 0.98 | ACNC user guide, PDF p. 2 §§16–17: effective date the charity was registered with ACNC, with a documented 3 December 2012 convention for some pre-ACNC tax-concession charities. Frozen header Registration_Date; sample row 2 “13/11/2024”. Kept distinct from entity registration. |
| Date_Organisation_Established | entity.date_established | date | 0.98 | ACNC user guide, PDF p. 3 §18: date the charity was established, which may precede charity registration. Frozen header Date_Organisation_Established; sample row 5 “25/06/2024”. |
| Charity_Size | entity.charity_size | trim, enum | 0.95 | ACNC user guide, PDF p. 3 §§19–21: size categories Small, Medium, and Large are based on the latest Annual Information Statement. Frozen header Charity_Size; sample row 2 “Large”. |
| Number_of_Responsible_Persons | entity.responsible_person_count | integer | 0.95 | ACNC user guide, PDF p. 3 §22: number of board or committee members; a zero means the charity has not supplied the information. Frozen header Number_of_Responsible_Persons; sample row 2 “2”. Exact zero sentinel excluded. |
| Financial_Year_End | financial_period.year_end | trim | 0.95 | ACNC user guide, PDF p. 3 §§23–24: reported financial year end, which may differ from 30 June. Frozen header Financial_Year_End; sample row 2 “30-Jun”. |
| Operates_in_ACT, Operates_in_NSW, Operates_in_NT, Operates_in_QLD, Operates_in_SA, Operates_in_TAS, Operates_in_VIC, Operates_in_WA | entity.operating_region | indicator_categories | 0.96 | ACNC user guide, PDF p. 4 §§25–26: the eight state/territory columns record Y when the charity indicated it operates in that region; otherwise blank. Frozen headers Operates_in_ACT through Operates_in_WA; sample row 3 Operates_in_VIC “Y”. |
| PBI, HPC, Preventing_or_relieving_suffering_of_animals, Advancing_Culture, Advancing_Education, Advancing_Health, Promote_or_oppose_a_change_to_law__government_poll_or_prac, Advancing_natual_environment, Promoting_or_protecting_human_rights, Purposes_beneficial_to_ther_general_public_and_other_analogous, Promoting_reconciliation__mutual_respect_and_tolerance, Advancing_Religion, Advancing_social_or_public_welfare, Advancing_security_or_safety_of_Australia_or_Australian_public | entity.charity_subtype | indicator_categories | 0.94 | ACNC user guide, PDF p. 5 §§29–32, lists the 14 charity subtypes and states that Y is recorded for a registered subtype. Frozen headers correspond to these categories (including source spelling variants); supplied sample row 9 PBI “Y”. |
| Aboriginal_or_TSI, Adults, Aged_Persons, Children, Communities_Overseas, Early_Childhood, Ethnic_Groups, Families, Females, Financially_Disadvantaged, LGBTIQA+, General_Community_in_Australia, Males, Migrants_Refugees_or_Asylum_Seekers, Other_Beneficiaries, Other_Charities, People_at_risk_of_homelessness, People_with_Chronic_Illness, People_with_Disabilities, Pre_Post_Release_Offenders, Rural_Regional_Remote_Communities, Unemployed_Person, Veterans_or_their_families, Victims_of_crime, Victims_of_Disasters, Youth, animals, environment, other_gender_identities | entity.charity_beneficiary_category | indicator_categories | 0.94 | ACNC user guide, PDF p. 6 §§33–34, lists beneficiary categories and states that Y is recorded for a reported beneficiary group. Frozen headers correspond to the documented list, including lowercase animals, environment, and other_gender_identities; sample row 3 Families “Y”. |

## Before / after

```json
{
  "raw": [
    {
      "record_id": "ec953e4df60ff8a8f823e83f3bcef9576e07cdd55335b1b9f41c7e89f3fe3372",
      "locator": {
        "snapshot_sha": "4cc8292de175ba9c6af0bfe4562fd4d21881fd6d2e9f99dd09b6d9e3d31b633f",
        "sheet": "csv",
        "row": 2
      },
      "values": {
        "ABN": "97830467530",
        "Charity_Legal_Name": "The Dale Family Foundation",
        "Other_Organisation_Names": "",
        "Address_Type": "Business",
        "Address_Line_1": "L 15 216 St Georges Tce",
        "Address_Line_2": "",
        "Address_Line_3": "",
        "Town_City": "Perth",
        "State": "WA",
        "Postcode": "6000",
        "Country": "Australia",
        "Charity_Website": "",
        "Registration_Date": "13/11/2024",
        "Date_Organisation_Established": "13/11/2024",
        "Charity_Size": "Large",
        "Number_of_Responsible_Persons": "2",
        "Financial_Year_End": "30-Jun",
        "Operates_in_ACT": "",
        "Operates_in_NSW": "",
        "Operates_in_NT": "",
        "Operates_in_QLD": "",
        "Operates_in_SA": "",
        "Operates_in_TAS": "",
        "Operates_in_VIC": "",
        "Operates_in_WA": "",
        "Operating_Countries": "",
        "PBI": "",
        "HPC": "",
        "Preventing_or_relieving_suffering_of_animals": "",
        "Advancing_Culture": "",
        "Advancing_Education": "",
        "Advancing_Health": "",
        "Promote_or_oppose_a_change_to_law__government_poll_or_prac": "",
        "Advancing_natual_environment": "",
        "Promoting_or_protecting_human_rights": "",
        "Purposes_beneficial_to_ther_general_public_and_other_analogous": "Y",
        "Promoting_reconciliation__mutual_respect_and_tolerance": "",
        "Advancing_Religion": "",
        "Advancing_social_or_public_welfare": "",
        "Advancing_security_or_safety_of_Australia_or_Australian_public": "",
        "Aboriginal_or_TSI": "",
        "Adults": "",
        "Aged_Persons": "",
        "Children": "",
        "Communities_Overseas": "",
        "Early_Childhood": "",
        "Ethnic_Groups": "",
        "Families": "",
        "Females": "",
        "Financially_Disadvantaged": "",
        "LGBTIQA+": "",
        "General_Community_in_Australia": "",
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
      "record_id": "737e317506e76ef8de0c1012029c56b532f1287dbe9ff3211f347ee370c75a49",
      "locator": {
        "snapshot_sha": "4cc8292de175ba9c6af0bfe4562fd4d21881fd6d2e9f99dd09b6d9e3d31b633f",
        "sheet": "csv",
        "row": 3
      },
      "values": {
        "ABN": "90175059896",
        "Charity_Legal_Name": "The SJD Homes Foundation",
        "Other_Organisation_Names": "",
        "Address_Type": "Business",
        "Address_Line_1": "433 Princes Hwy",
        "Address_Line_2": "",
        "Address_Line_3": "",
        "Town_City": "Officer",
        "State": "VIC",
        "Postcode": "3809",
        "Country": "Australia",
        "Charity_Website": "",
        "Registration_Date": "27/10/2024",
        "Date_Organisation_Established": "27/10/2024",
        "Charity_Size": "Small",
        "Number_of_Responsible_Persons": "7",
        "Financial_Year_End": "30-Jun",
        "Operates_in_ACT": "",
        "Operates_in_NSW": "",
        "Operates_in_NT": "",
        "Operates_in_QLD": "",
        "Operates_in_SA": "",
        "Operates_in_TAS": "",
        "Operates_in_VIC": "Y",
        "Operates_in_WA": "",
        "Operating_Countries": "AUS",
        "PBI": "",
        "HPC": "",
        "Preventing_or_relieving_suffering_of_animals": "",
        "Advancing_Culture": "",
        "Advancing_Education": "",
        "Advancing_Health": "",
        "Promote_or_oppose_a_change_to_law__government_poll_or_prac": "",
        "Advancing_natual_environment": "",
        "Promoting_or_protecting_human_rights": "",
        "Purposes_beneficial_to_ther_general_public_and_other_analogous": "Y",
        "Promoting_reconciliation__mutual_respect_and_tolerance": "",
        "Advancing_Religion": "",
        "Advancing_social_or_public_welfare": "",
        "Advancing_security_or_safety_of_Australia_or_Australian_public": "",
        "Aboriginal_or_TSI": "",
        "Adults": "",
        "Aged_Persons": "",
        "Children": "",
        "Communities_Overseas": "",
        "Early_Childhood": "",
        "Ethnic_Groups": "",
        "Families": "Y",
        "Females": "",
        "Financially_Disadvantaged": "",
        "LGBTIQA+": "",
        "General_Community_in_Australia": "",
        "Males": "",
        "Migrants_Refugees_or_Asylum_Seekers": "",
        "Other_Beneficiaries": "",
        "Other_Charities": "",
        "People_at_risk_of_homelessness": "Y",
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
    }
  ],
  "observations": [
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "ec953e4df60ff8a8f823e83f3bcef9576e07cdd55335b1b9f41c7e89f3fe3372",
      "observed_at": "2026-09-20T19:00:20.049365+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:50.786869+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "field": "entity.abn",
      "value": "97830467530",
      "source_fields": [
        "ABN"
      ],
      "raw_value": [
        "97830467530"
      ],
      "raw_locator": {
        "snapshot_sha": "4cc8292de175ba9c6af0bfe4562fd4d21881fd6d2e9f99dd09b6d9e3d31b633f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "9d7eae78a75d6811729080941fe365a9b6caba863f07e2bb90c96202de90d999",
      "config_hash": "50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.99
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "id": "faa840fd1d55024f382079ee193577c0118e8b5119639524044dfd22e18a8263"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "ec953e4df60ff8a8f823e83f3bcef9576e07cdd55335b1b9f41c7e89f3fe3372",
      "observed_at": "2026-09-20T19:00:20.049365+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:50.786869+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "field": "address.type",
      "value": "Business",
      "source_fields": [
        "Address_Type"
      ],
      "raw_value": [
        "Business"
      ],
      "raw_locator": {
        "snapshot_sha": "4cc8292de175ba9c6af0bfe4562fd4d21881fd6d2e9f99dd09b6d9e3d31b633f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "9d7eae78a75d6811729080941fe365a9b6caba863f07e2bb90c96202de90d999",
      "config_hash": "50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.94
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "enum",
      "cardinality": "one",
      "id": "55b22f22d228f1859483546042ccc4fd74de910739a70b5c6e3f9fde591376a0"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "ec953e4df60ff8a8f823e83f3bcef9576e07cdd55335b1b9f41c7e89f3fe3372",
      "observed_at": "2026-09-20T19:00:20.049365+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:50.786869+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "field": "address.line_1",
      "value": "L 15 216 St Georges Tce",
      "source_fields": [
        "Address_Line_1"
      ],
      "raw_value": [
        "L 15 216 St Georges Tce"
      ],
      "raw_locator": {
        "snapshot_sha": "4cc8292de175ba9c6af0bfe4562fd4d21881fd6d2e9f99dd09b6d9e3d31b633f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "9d7eae78a75d6811729080941fe365a9b6caba863f07e2bb90c96202de90d999",
      "config_hash": "50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.97
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "id": "e98426147a0c50d4d61461e8b44fd90484eddeec7cb47d91892369929c3c3d7b"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "ec953e4df60ff8a8f823e83f3bcef9576e07cdd55335b1b9f41c7e89f3fe3372",
      "observed_at": "2026-09-20T19:00:20.049365+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:50.786869+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "field": "address.locality",
      "value": "Perth",
      "source_fields": [
        "Town_City"
      ],
      "raw_value": [
        "Perth"
      ],
      "raw_locator": {
        "snapshot_sha": "4cc8292de175ba9c6af0bfe4562fd4d21881fd6d2e9f99dd09b6d9e3d31b633f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "9d7eae78a75d6811729080941fe365a9b6caba863f07e2bb90c96202de90d999",
      "config_hash": "50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "id": "315ed7f7d9d2a344795729452100676a5f5793e7130efe2e687d8c32995dd2ed"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "ec953e4df60ff8a8f823e83f3bcef9576e07cdd55335b1b9f41c7e89f3fe3372",
      "observed_at": "2026-09-20T19:00:20.049365+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:50.786869+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "field": "address.state",
      "value": "WA",
      "source_fields": [
        "State"
      ],
      "raw_value": [
        "WA"
      ],
      "raw_locator": {
        "snapshot_sha": "4cc8292de175ba9c6af0bfe4562fd4d21881fd6d2e9f99dd09b6d9e3d31b633f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "9d7eae78a75d6811729080941fe365a9b6caba863f07e2bb90c96202de90d999",
      "config_hash": "50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.95
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "enum",
      "cardinality": "one",
      "id": "c841b589f64fae3772834a2dd9bf355273eee6d93ed35b46ee43ee270bd7c43c"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "ec953e4df60ff8a8f823e83f3bcef9576e07cdd55335b1b9f41c7e89f3fe3372",
      "observed_at": "2026-09-20T19:00:20.049365+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:50.786869+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "field": "address.postcode",
      "value": "6000",
      "source_fields": [
        "Postcode"
      ],
      "raw_value": [
        "6000"
      ],
      "raw_locator": {
        "snapshot_sha": "4cc8292de175ba9c6af0bfe4562fd4d21881fd6d2e9f99dd09b6d9e3d31b633f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "9d7eae78a75d6811729080941fe365a9b6caba863f07e2bb90c96202de90d999",
      "config_hash": "50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.96
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "id": "16cb998782a4998a554ebcaf2806ef9efeaf63c939db8d40bc34f14ff754cf50"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "ec953e4df60ff8a8f823e83f3bcef9576e07cdd55335b1b9f41c7e89f3fe3372",
      "observed_at": "2026-09-20T19:00:20.049365+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:50.786869+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "field": "address.country",
      "value": "Australia",
      "source_fields": [
        "Country"
      ],
      "raw_value": [
        "Australia"
      ],
      "raw_locator": {
        "snapshot_sha": "4cc8292de175ba9c6af0bfe4562fd4d21881fd6d2e9f99dd09b6d9e3d31b633f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "9d7eae78a75d6811729080941fe365a9b6caba863f07e2bb90c96202de90d999",
      "config_hash": "50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.95
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "string",
      "cardinality": "one",
      "id": "137492c3049d7b84cea0869f70dfa3e39e6e56a5102ae9bb36d706b5df3b54e3"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "ec953e4df60ff8a8f823e83f3bcef9576e07cdd55335b1b9f41c7e89f3fe3372",
      "observed_at": "2026-09-20T19:00:20.049365+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:50.786869+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "field": "registration.acnc_date_registered",
      "value": "2024-11-13",
      "source_fields": [
        "Registration_Date"
      ],
      "raw_value": [
        "13/11/2024"
      ],
      "raw_locator": {
        "snapshot_sha": "4cc8292de175ba9c6af0bfe4562fd4d21881fd6d2e9f99dd09b6d9e3d31b633f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "9d7eae78a75d6811729080941fe365a9b6caba863f07e2bb90c96202de90d999",
      "config_hash": "50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "date",
      "cardinality": "one",
      "scope": "registration",
      "group_id": "25dccb6b43a52121ac04079f3a1de9d8e30f4fa7d6a942e6d43beb4fd48e65f4",
      "group_name": "acnc_registration",
      "id": "043931c6a8b72eaea4bf46fb524bab60d785c8126d00c15032abe26360517a73"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "ec953e4df60ff8a8f823e83f3bcef9576e07cdd55335b1b9f41c7e89f3fe3372",
      "observed_at": "2026-09-20T19:00:20.049365+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:50.786869+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "field": "entity.date_established",
      "value": "2024-11-13",
      "source_fields": [
        "Date_Organisation_Established"
      ],
      "raw_value": [
        "13/11/2024"
      ],
      "raw_locator": {
        "snapshot_sha": "4cc8292de175ba9c6af0bfe4562fd4d21881fd6d2e9f99dd09b6d9e3d31b633f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "9d7eae78a75d6811729080941fe365a9b6caba863f07e2bb90c96202de90d999",
      "config_hash": "50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.98
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "date",
      "cardinality": "one",
      "id": "b292d56aaf82bfd9bbae1ab989ece9a8c5f557998d6cb3f45adc8338c9dc6bb3"
    },
    {
      "source_id": "b050b242-4487-4306-abf5-07ca073e5594",
      "source_record_id": "ec953e4df60ff8a8f823e83f3bcef9576e07cdd55335b1b9f41c7e89f3fe3372",
      "observed_at": "2026-09-20T19:00:20.049365+00:00",
      "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
      "timezone_assumption": "UTC assumed for timezone-naive source timestamp",
      "ingested_at": "2026-09-23T14:44:50.786869+00:00",
      "licence": "Creative Commons Attribution 3.0 Australia",
      "extractor_version": "extractor-1:50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "field": "entity.charity_size",
      "value": "Large",
      "source_fields": [
        "Charity_Size"
      ],
      "raw_value": [
        "Large"
      ],
      "raw_locator": {
        "snapshot_sha": "4cc8292de175ba9c6af0bfe4562fd4d21881fd6d2e9f99dd09b6d9e3d31b633f",
        "sheet": "csv",
        "row": 2
      },
      "snapshot_id": "9d7eae78a75d6811729080941fe365a9b6caba863f07e2bb90c96202de90d999",
      "config_hash": "50458da734fb0fba17ee484a3f474b694505cb4218282290cc020d54eb36d3b8",
      "subject_role": "legal_entity",
      "source_kind": "charity_register",
      "address_role": "business",
      "confidence": {
        "source_reliability": 0.96,
        "field_confidence": 0.95
      },
      "confidence_kind": "uncalibrated mapping/source judgements",
      "derivation_level": "L1",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "value_type": "enum",
      "cardinality": "one",
      "id": "9c6a4507a58b89cd56832882725e9f946ff46cba3ce9809320492bc167361df0"
    }
  ]
}
```

## Checks

Validation: 250 records; 1 field issues.
Final test: 100 previously withheld records; passed=True.
Model calls: 2; measured/reserved input/output: 42563/5703; calculated cost: 0.014918.
Pricing: unknown; no provider rates configured. Scores are uncalibrated, not measured accuracy.

## Unmapped

- **Charity_Legal_Name**: ACNC user guide, PDF p. 2 §§8–9, says this field is ordinarily the formal/legal name but explicitly permits ACNC to substitute an alternate identifier when the charity’s legal name is withheld. No usable discriminator is provided for those rows. Retain the raw subject label through subject_label_field, but do not make an unconditional entity.legal_name claim.
- **Other_Organisation_Names**: ACNC user guide, PDF p. 2 §§10–11, says values may be trading names or other names, potentially unlike the legal name. The source does not distinguish these alternatives per value, so do not assert trading-name status.
- **Operating_Countries**: ACNC user guide, PDF p. 4 §§27–28, describes ISO alpha-3 codes for overseas operation, but supplied sample rows include AUS. With no supported discriminator or alternative meaning, leave unmapped; do not assert overseas meaning for AUS.

## Uncertainties

- Charity_Legal_Name is retained as the raw subject label and intentionally not mapped to entity.legal_name because the source permits alternate identifiers when the legal name is withheld and supplies no safe discriminator.
- Other_Organisation_Names is unmapped because its values mix trading names and other names without a source distinction.
- Operating_Countries is unmapped because supplied values include AUS although the guide describes overseas operating-country codes; no overseas interpretation is asserted.
- ACNC registration date is mapped only to registration.acnc_date_registered; organisation establishment is a distinct date and neither is asserted as company registration.
- Number_of_Responsible_Persons value 0 is excluded as a documented non-response sentinel. Blank indicator cells are not interpreted as negative claims.
- No entity type, entity status, company registration, or ownership is inferred. No entity type is inferred from name suffixes.
- The source is updated weekly. The envelope publication timestamp is a proxy, not a row-change timestamp; withholding and update timing may affect completeness or freshness.
- The user guide describes a legacy column sequence; mapping uses only frozen reader headers and supplied sample evidence. Website values that are not recognized by the website transform, including Instagram in validation, are not reinterpreted.
- Supplied exploration code failed before duplicate-ABN and full-sample grain checks; therefore duplicate-key and row-grain assumptions have not been independently verified. All authority and field scores are provisional judgments requiring human review.
- The exploration script failed, so duplicate-ABN and full-discovery grain checks were not completed. The source guide and supplied rows support charity-record grain with a business address, and the mapping discloses this remaining uncertainty; verify in human review if full-source key uniqueness matters.
- Charity_Legal_Name and Other_Organisation_Names are intentionally unmapped: documentation permits an alternate identifier in the legal-name field when withheld and does not distinguish trading names from other names. The raw subject label is retained, so reviewers should ensure it is not treated as a canonical legal-name claim.
- Operating_Countries is appropriately left unmapped because discovery includes AUS while documentation describes overseas ISO alpha-3 codes. No unsupported country interpretation is made.
- The source contains only ACNC-registered charities, but the mapping does not infer entity.status=active; this is appropriately conservative. The publication proxy is disclosed as freshness metadata, not a row-change timestamp.
- Timestamp basis: CKAN resource last_modified; publication proxy, not a field change timestamp; naive source timestamps are explicitly labelled UTC assumptions.

Accept approves this exact stored config. Respond provides revision feedback. Ignore defers/rejects; it does not approve.

[LangSmith trace](https://smith.langchain.com/o/aed48a45-cf8f-5ef4-a1b3-11b8c0bc2137/projects/p/efcced63-046f-4a18-8505-e38fcd4a38b5/trace/01a0d40e-772a-7b30-a494-e7edba7f6479/run/01a0d40e-cf0e-7132-91f1-21475b36a86c?start_time=2026-09-24T15%3A35%3A35.438558%2B00%3A00)