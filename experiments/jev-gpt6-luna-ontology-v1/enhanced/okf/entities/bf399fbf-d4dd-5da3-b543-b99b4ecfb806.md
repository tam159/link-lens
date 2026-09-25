---
type: Business Profile
title: bf399fbf-d4dd-5da3-b543-b99b4ecfb806
description: Versioned profile assembled from proposed identity links.
tags:
- entity
- proposed-identity
generated:
  by: process:link-lens-exporter-1
  at: '2026-09-25T00:38:03.750948+00:00'
status: draft
profile_version: 0908b66344f121dff307b0dfc36b8a336846b3b254fe38b1144f9ed5ba7186b0
sources:
- resource: ../sources/ab7eddce-84df-4098-bc8f-500d0d9776d1.md
- resource: ../sources/c2524c87-cea4-4636-acac-599a82048a26.md
---

# Profile

Identity scores are uncalibrated. Review of a mapping does not verify every identity link.

```json
{
  "canonical_entity_key": "bf399fbf-d4dd-5da3-b543-b99b4ecfb806",
  "status": "profile_from_proposed_links",
  "policy_version": "field-authority-1+hybrid-evidence-2",
  "fields": {
    "entity.abn": {
      "status": "selected",
      "value": "59626521202",
      "confidence": {
        "source_reliability": 0.9,
        "field_confidence": 0.91
      },
      "provenance": [
        {
          "id": "df702b1335a33be5e96d26e52f762bd44680e934473fa8978cf136ba12da2f7a",
          "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
          "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
          "value": "59626521202",
          "observed_at": "2026-09-23T21:50:41.592631+00:00",
          "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
          "confidence": {
            "source_reliability": 0.9,
            "field_confidence": 0.91
          },
          "raw_locator": {
            "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
            "sheet": "csv",
            "row": 4401
          }
        },
        {
          "id": "878db2c3ba84162860c9d82d766a6a68f3837ea727362f6c6b1a75bab43c2ecb",
          "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
          "source_record_id": "09b8e9df670f3b6a984493259314c1a1dea92f130710e4799167d732f946db46",
          "value": "59626521202",
          "observed_at": "2025-10-01T21:08:09.091363+00:00",
          "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
          "confidence": {
            "source_reliability": 0.88,
            "field_confidence": 0.95
          },
          "raw_locator": {
            "snapshot_sha": "6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75",
            "sheet": "Income tax details",
            "row": 1675
          }
        }
      ],
      "alternatives": [],
      "decision": "Field-specific publisher role, then statement-vs-publication evidence, then most recent timestamp.",
      "temporal_caveat": "Publication time does not prove when this field changed."
    }
  },
  "source_records": [
    [
      "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a"
    ],
    [
      "c2524c87-cea4-4636-acac-599a82048a26",
      "09b8e9df670f3b6a984493259314c1a1dea92f130710e4799167d732f946db46"
    ]
  ],
  "uncertainties": [
    "Identity links are rule proposals; manual precision is measured separately.",
    "Confidence components are uncalibrated."
  ],
  "groups": [
    {
      "id": "0d5fc8acc9bbc602f64f83a16392ac79cdf954cc460ec33f76707da1a7168c09",
      "scope": "financial_period",
      "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
      "source_record_id": "09b8e9df670f3b6a984493259314c1a1dea92f130710e4799167d732f946db46",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "fields": {
        "financial_period.reporting_period": {
          "status": "selected",
          "value": "2023-24",
          "confidence": {
            "source_reliability": 0.88,
            "field_confidence": 0.99
          },
          "provenance": [
            {
              "id": "f86724e9d6af7ba014d470569fa3b92cdb482ab5fed4f4d596ca90f8a8524c41",
              "source_id": "c2524c87-cea4-4636-acac-599a82048a26",
              "source_record_id": "09b8e9df670f3b6a984493259314c1a1dea92f130710e4799167d732f946db46",
              "value": "2023-24",
              "observed_at": "2025-10-01T21:08:09.091363+00:00",
              "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
              "confidence": {
                "source_reliability": 0.88,
                "field_confidence": 0.99
              },
              "raw_locator": {
                "snapshot_sha": "6b47837efab92e1eb2b0cacc46945376a5b185c1b16814146c3282a1921b0c75",
                "sheet": "Income tax details",
                "row": 1675
              }
            }
          ],
          "alternatives": [],
          "decision": "Field-specific publisher role, then statement-vs-publication evidence, then most recent timestamp.",
          "temporal_caveat": "Publication time does not prove when this field changed."
        }
      },
      "decision": "Keep scoped source claims together; no cross-record winner or ownership inference."
    },
    {
      "id": "d68dffc884479b02105c454a75fc05610d520a5b22ed0a21b70bbaefd87295d9",
      "scope": "licence",
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
      "ontology_hash": "4a02fa33f46c0052df2775983fdb55cdc5df6f5ba2087b6a4b528342ba9e1227",
      "fields": {
        "licence.authorisation_condition": {
          "status": "multiple_values",
          "values": [
            {
              "value": "\"to retail and wholesale clients.\"",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "provenance": [
                {
                  "id": "e2cfb37693f400098dd9b2372b51a11348f58873c57acd3962bd4515cd79d1e5",
                  "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
                  "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
                  "value": "\"to retail and wholesale clients.\"",
                  "observed_at": "2026-09-23T21:50:41.592631+00:00",
                  "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
                  "confidence": {
                    "source_reliability": 0.9,
                    "field_confidence": 0.9
                  },
                  "raw_locator": {
                    "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                    "sheet": "csv",
                    "row": 4401
                  }
                }
              ],
              "authority_rank": [
                50,
                1,
                "2026-09-23T21:50:41.592631+00:00"
              ]
            },
            {
              "value": "\"This licence authorises the licensee to carry on a financial services business to:\"",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "provenance": [
                {
                  "id": "c8d49583cd79566df97dc0c764c6ae4b2383171e4333d750797ee7e3861b214d",
                  "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
                  "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
                  "value": "\"This licence authorises the licensee to carry on a financial services business to:\"",
                  "observed_at": "2026-09-23T21:50:41.592631+00:00",
                  "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
                  "confidence": {
                    "source_reliability": 0.9,
                    "field_confidence": 0.9
                  },
                  "raw_locator": {
                    "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                    "sheet": "csv",
                    "row": 4401
                  }
                }
              ],
              "authority_rank": [
                50,
                1,
                "2026-09-23T21:50:41.592631+00:00"
              ]
            },
            {
              "value": "\"(ii) securities; and\"",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "provenance": [
                {
                  "id": "17c4dc4175bd43c74b27a68e1b57dce9aa676a85c5813b31d38a27eea4a45253",
                  "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
                  "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
                  "value": "\"(ii) securities; and\"",
                  "observed_at": "2026-09-23T21:50:41.592631+00:00",
                  "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
                  "confidence": {
                    "source_reliability": 0.9,
                    "field_confidence": 0.9
                  },
                  "raw_locator": {
                    "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                    "sheet": "csv",
                    "row": 4401
                  }
                }
              ],
              "authority_rank": [
                50,
                1,
                "2026-09-23T21:50:41.592631+00:00"
              ]
            },
            {
              "value": "\"(i) deposit and payment products limited to:\"",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "provenance": [
                {
                  "id": "f82c446d75ba1c48ecf6b24a3e424264c15787b63c815ab2adfbefd3161b5995",
                  "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
                  "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
                  "value": "\"(i) deposit and payment products limited to:\"",
                  "observed_at": "2026-09-23T21:50:41.592631+00:00",
                  "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
                  "confidence": {
                    "source_reliability": 0.9,
                    "field_confidence": 0.9
                  },
                  "raw_locator": {
                    "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                    "sheet": "csv",
                    "row": 4401
                  }
                }
              ],
              "authority_rank": [
                50,
                1,
                "2026-09-23T21:50:41.592631+00:00"
              ]
            },
            {
              "value": "\"(i) applying for, acquiring, varying or disposing of a financial product on behalf of another person in respect of the following classes of products:\"",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "provenance": [
                {
                  "id": "720d9013f1a79d8b3eb4ff4220ca54b25cacf109c611f7f47afa4e8262de23d9",
                  "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
                  "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
                  "value": "\"(i) applying for, acquiring, varying or disposing of a financial product on behalf of another person in respect of the following classes of products:\"",
                  "observed_at": "2026-09-23T21:50:41.592631+00:00",
                  "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
                  "confidence": {
                    "source_reliability": 0.9,
                    "field_confidence": 0.9
                  },
                  "raw_locator": {
                    "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                    "sheet": "csv",
                    "row": 4401
                  }
                }
              ],
              "authority_rank": [
                50,
                1,
                "2026-09-23T21:50:41.592631+00:00"
              ]
            },
            {
              "value": "\"(b) deal in a financial product by:\"",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "provenance": [
                {
                  "id": "932d7d6299a5be446069e4ccbc106c4e67d29a3580753f1e6d53483adb483caf",
                  "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
                  "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
                  "value": "\"(b) deal in a financial product by:\"",
                  "observed_at": "2026-09-23T21:50:41.592631+00:00",
                  "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
                  "confidence": {
                    "source_reliability": 0.9,
                    "field_confidence": 0.9
                  },
                  "raw_locator": {
                    "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                    "sheet": "csv",
                    "row": 4401
                  }
                }
              ],
              "authority_rank": [
                50,
                1,
                "2026-09-23T21:50:41.592631+00:00"
              ]
            },
            {
              "value": "\"(a) provide general financial product advice for the following classes of financial products:\"",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "provenance": [
                {
                  "id": "637beae3c0a1cf6fec01492ea0b1a17fa01c02fffafceac71d2877399a7dfe62",
                  "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
                  "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
                  "value": "\"(a) provide general financial product advice for the following classes of financial products:\"",
                  "observed_at": "2026-09-23T21:50:41.592631+00:00",
                  "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
                  "confidence": {
                    "source_reliability": 0.9,
                    "field_confidence": 0.9
                  },
                  "raw_locator": {
                    "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                    "sheet": "csv",
                    "row": 4401
                  }
                }
              ],
              "authority_rank": [
                50,
                1,
                "2026-09-23T21:50:41.592631+00:00"
              ]
            },
            {
              "value": "\"(B) securities;\"",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "provenance": [
                {
                  "id": "b4e59eb13f262dd81eab00c194ed0ba96f2337a59aa8bb3efbfa572316638b04",
                  "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
                  "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
                  "value": "\"(B) securities;\"",
                  "observed_at": "2026-09-23T21:50:41.592631+00:00",
                  "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
                  "confidence": {
                    "source_reliability": 0.9,
                    "field_confidence": 0.9
                  },
                  "raw_locator": {
                    "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                    "sheet": "csv",
                    "row": 4401
                  }
                }
              ],
              "authority_rank": [
                50,
                1,
                "2026-09-23T21:50:41.592631+00:00"
              ]
            },
            {
              "value": "\"(B) deposit products other than basic deposit products; and\"",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "provenance": [
                {
                  "id": "ac970c8d9503e102dea9896e4d8fca36a58326893a748c4e2cfe3075b36228cb",
                  "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
                  "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
                  "value": "\"(B) deposit products other than basic deposit products; and\"",
                  "observed_at": "2026-09-23T21:50:41.592631+00:00",
                  "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
                  "confidence": {
                    "source_reliability": 0.9,
                    "field_confidence": 0.9
                  },
                  "raw_locator": {
                    "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                    "sheet": "csv",
                    "row": 4401
                  }
                }
              ],
              "authority_rank": [
                50,
                1,
                "2026-09-23T21:50:41.592631+00:00"
              ]
            },
            {
              "value": "\"(A) deposit and payment products limited to:\"",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "provenance": [
                {
                  "id": "fa9dbe8e540bdf8950a21b95ca1df4a54707e0bca6ba54111da3a1d95d162c10",
                  "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
                  "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
                  "value": "\"(A) deposit and payment products limited to:\"",
                  "observed_at": "2026-09-23T21:50:41.592631+00:00",
                  "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
                  "confidence": {
                    "source_reliability": 0.9,
                    "field_confidence": 0.9
                  },
                  "raw_locator": {
                    "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                    "sheet": "csv",
                    "row": 4401
                  }
                }
              ],
              "authority_rank": [
                50,
                1,
                "2026-09-23T21:50:41.592631+00:00"
              ]
            },
            {
              "value": "\"(A) basic deposit products;\"",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "provenance": [
                {
                  "id": "735885461f837a51ce2946000697c1f96eeacb867025015eaa3ae3440a45c065",
                  "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
                  "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
                  "value": "\"(A) basic deposit products;\"",
                  "observed_at": "2026-09-23T21:50:41.592631+00:00",
                  "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
                  "confidence": {
                    "source_reliability": 0.9,
                    "field_confidence": 0.9
                  },
                  "raw_locator": {
                    "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                    "sheet": "csv",
                    "row": 4401
                  }
                }
              ],
              "authority_rank": [
                50,
                1,
                "2026-09-23T21:50:41.592631+00:00"
              ]
            },
            {
              "value": "\"(2) deposit products other than basic deposit products; and\"",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "provenance": [
                {
                  "id": "c97ee1386aa0563489b3517483c44adab97bc2f1a6f65a6c6599e85e0e0ebf5c",
                  "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
                  "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
                  "value": "\"(2) deposit products other than basic deposit products; and\"",
                  "observed_at": "2026-09-23T21:50:41.592631+00:00",
                  "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
                  "confidence": {
                    "source_reliability": 0.9,
                    "field_confidence": 0.9
                  },
                  "raw_locator": {
                    "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                    "sheet": "csv",
                    "row": 4401
                  }
                }
              ],
              "authority_rank": [
                50,
                1,
                "2026-09-23T21:50:41.592631+00:00"
              ]
            },
            {
              "value": "\"(1) basic deposit products;\"",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "provenance": [
                {
                  "id": "35ca01778cf8e09063eb477000ecfb6976dce0a3b0eda5b5a5fb37907b68ebee",
                  "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
                  "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
                  "value": "\"(1) basic deposit products;\"",
                  "observed_at": "2026-09-23T21:50:41.592631+00:00",
                  "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
                  "confidence": {
                    "source_reliability": 0.9,
                    "field_confidence": 0.9
                  },
                  "raw_locator": {
                    "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                    "sheet": "csv",
                    "row": 4401
                  }
                }
              ],
              "authority_rank": [
                50,
                1,
                "2026-09-23T21:50:41.592631+00:00"
              ]
            }
          ],
          "decision": "Trading names are multi-valued; no winner is forced."
        },
        "licence.number": {
          "status": "selected",
          "value": "514654",
          "confidence": {
            "source_reliability": 0.9,
            "field_confidence": 0.99
          },
          "provenance": [
            {
              "id": "f6278fc69148e5344104b6935c489f8158e99dd4bfb00ea7238e3717156cc254",
              "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
              "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
              "value": "514654",
              "observed_at": "2026-09-23T21:50:41.592631+00:00",
              "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.99
              },
              "raw_locator": {
                "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                "sheet": "csv",
                "row": 4401
              }
            }
          ],
          "alternatives": [],
          "decision": "Field-specific publisher role, then statement-vs-publication evidence, then most recent timestamp.",
          "temporal_caveat": "Publication time does not prove when this field changed."
        },
        "licence.register_entry_name": {
          "status": "selected",
          "value": "HABIT FINANCIAL SERVICES PTY LTD",
          "confidence": {
            "source_reliability": 0.9,
            "field_confidence": 0.98
          },
          "provenance": [
            {
              "id": "e2057fa91483cc3cb42e36996223b31d3edf46628310bc3b3aed74a6ef88f9f4",
              "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
              "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
              "value": "HABIT FINANCIAL SERVICES PTY LTD",
              "observed_at": "2026-09-23T21:50:41.592631+00:00",
              "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.98
              },
              "raw_locator": {
                "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                "sheet": "csv",
                "row": 4401
              }
            }
          ],
          "alternatives": [],
          "decision": "Field-specific publisher role, then statement-vs-publication evidence, then most recent timestamp.",
          "temporal_caveat": "Publication time does not prove when this field changed."
        },
        "licence.start_date": {
          "status": "selected",
          "value": "2021-08-11",
          "confidence": {
            "source_reliability": 0.9,
            "field_confidence": 0.98
          },
          "provenance": [
            {
              "id": "88f1830a809a7197541e56ce63290b34a683c5ce110d69d05e003fc60b6a2f12",
              "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
              "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
              "value": "2021-08-11",
              "observed_at": "2026-09-23T21:50:41.592631+00:00",
              "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.98
              },
              "raw_locator": {
                "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                "sheet": "csv",
                "row": 4401
              }
            }
          ],
          "alternatives": [],
          "decision": "Field-specific publisher role, then statement-vs-publication evidence, then most recent timestamp.",
          "temporal_caveat": "Publication time does not prove when this field changed."
        }
      },
      "decision": "Keep scoped source claims together; no cross-record winner or ownership inference."
    }
  ],
  "addresses": [
    {
      "role": "business",
      "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
      "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
      "fields": {
        "address.locality": {
          "status": "selected",
          "value": "SYDNEY",
          "confidence": {
            "source_reliability": 0.9,
            "field_confidence": 0.98
          },
          "provenance": [
            {
              "id": "f79027e1eb4de186fc9b215c5ce4fd6ea6455498e29eec6005b715b1c8b0774a",
              "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
              "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
              "value": "SYDNEY",
              "observed_at": "2026-09-23T21:50:41.592631+00:00",
              "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.98
              },
              "raw_locator": {
                "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                "sheet": "csv",
                "row": 4401
              }
            }
          ],
          "alternatives": [],
          "decision": "Field-specific publisher role, then statement-vs-publication evidence, then most recent timestamp.",
          "temporal_caveat": "Publication time does not prove when this field changed."
        },
        "address.state": {
          "status": "selected",
          "value": "NSW",
          "confidence": {
            "source_reliability": 0.9,
            "field_confidence": 0.97
          },
          "provenance": [
            {
              "id": "39cc07418da960611b342b5d4fa8bd4be0aead4c00d97c13840d60f0d8baf585",
              "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
              "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
              "value": "NSW",
              "observed_at": "2026-09-23T21:50:41.592631+00:00",
              "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.97
              },
              "raw_locator": {
                "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                "sheet": "csv",
                "row": 4401
              }
            }
          ],
          "alternatives": [],
          "decision": "Field-specific publisher role, then statement-vs-publication evidence, then most recent timestamp.",
          "temporal_caveat": "Publication time does not prove when this field changed."
        },
        "address.postcode": {
          "status": "selected",
          "value": "2000",
          "confidence": {
            "source_reliability": 0.9,
            "field_confidence": 0.96
          },
          "provenance": [
            {
              "id": "1b9b76d66f10046dff093cd6fd90bf7c65841adfd89f6ca333cd28b8d29d44f2",
              "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
              "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
              "value": "2000",
              "observed_at": "2026-09-23T21:50:41.592631+00:00",
              "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.96
              },
              "raw_locator": {
                "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                "sheet": "csv",
                "row": 4401
              }
            }
          ],
          "alternatives": [],
          "decision": "Field-specific publisher role, then statement-vs-publication evidence, then most recent timestamp.",
          "temporal_caveat": "Publication time does not prove when this field changed."
        },
        "address.country": {
          "status": "selected",
          "value": "Australia",
          "confidence": {
            "source_reliability": 0.9,
            "field_confidence": 0.9
          },
          "provenance": [
            {
              "id": "eb2dce643e60082ddfc41ca46712348fcbbb55cdd764dc890363080f42429f87",
              "source_id": "ab7eddce-84df-4098-bc8f-500d0d9776d1",
              "source_record_id": "096e042039958f1e4dd8ba7e43f39016bec7f015367ee9aad0c3060ba52a171a",
              "value": "Australia",
              "observed_at": "2026-09-23T21:50:41.592631+00:00",
              "observed_at_basis": "CKAN resource last_modified; publication proxy, not a field change timestamp",
              "confidence": {
                "source_reliability": 0.9,
                "field_confidence": 0.9
              },
              "raw_locator": {
                "snapshot_sha": "a3aa6cfbec5d077566104837795893620a53c9354a6862053c63d00ee41aa2b0",
                "sheet": "csv",
                "row": 4401
              }
            }
          ],
          "alternatives": [],
          "decision": "Field-specific publisher role, then statement-vs-publication evidence, then most recent timestamp.",
          "temporal_caveat": "Publication time does not prove when this field changed."
        }
      },
      "decision": "Keep source address fields together; no inferred headquarters address."
    }
  ],
  "profile_version": "0908b66344f121dff307b0dfc36b8a336846b3b254fe38b1144f9ed5ba7186b0",
  "identity_basis": "exact_identifier",
  "reconciliation": {
    "version": "hybrid-evidence-2",
    "decisions": [],
    "equivalence_groups": [],
    "conflicts": []
  }
}
```

# Evidence

* [licence.authorisation_condition](../evidence/17c4dc4175bd43c74b27a68e1b57dce9aa676a85c5813b31d38a27eea4a45253.md) - source value and exact raw locator.
* [address.postcode](../evidence/1b9b76d66f10046dff093cd6fd90bf7c65841adfd89f6ca333cd28b8d29d44f2.md) - source value and exact raw locator.
* [licence.authorisation_condition](../evidence/35ca01778cf8e09063eb477000ecfb6976dce0a3b0eda5b5a5fb37907b68ebee.md) - source value and exact raw locator.
* [address.state](../evidence/39cc07418da960611b342b5d4fa8bd4be0aead4c00d97c13840d60f0d8baf585.md) - source value and exact raw locator.
* [licence.authorisation_condition](../evidence/637beae3c0a1cf6fec01492ea0b1a17fa01c02fffafceac71d2877399a7dfe62.md) - source value and exact raw locator.
* [licence.authorisation_condition](../evidence/720d9013f1a79d8b3eb4ff4220ca54b25cacf109c611f7f47afa4e8262de23d9.md) - source value and exact raw locator.
* [licence.authorisation_condition](../evidence/735885461f837a51ce2946000697c1f96eeacb867025015eaa3ae3440a45c065.md) - source value and exact raw locator.
* [entity.abn](../evidence/878db2c3ba84162860c9d82d766a6a68f3837ea727362f6c6b1a75bab43c2ecb.md) - source value and exact raw locator.
* [licence.start_date](../evidence/88f1830a809a7197541e56ce63290b34a683c5ce110d69d05e003fc60b6a2f12.md) - source value and exact raw locator.
* [licence.authorisation_condition](../evidence/932d7d6299a5be446069e4ccbc106c4e67d29a3580753f1e6d53483adb483caf.md) - source value and exact raw locator.
* [licence.authorisation_condition](../evidence/ac970c8d9503e102dea9896e4d8fca36a58326893a748c4e2cfe3075b36228cb.md) - source value and exact raw locator.
* [licence.authorisation_condition](../evidence/b4e59eb13f262dd81eab00c194ed0ba96f2337a59aa8bb3efbfa572316638b04.md) - source value and exact raw locator.
* [licence.authorisation_condition](../evidence/c8d49583cd79566df97dc0c764c6ae4b2383171e4333d750797ee7e3861b214d.md) - source value and exact raw locator.
* [licence.authorisation_condition](../evidence/c97ee1386aa0563489b3517483c44adab97bc2f1a6f65a6c6599e85e0e0ebf5c.md) - source value and exact raw locator.
* [entity.abn](../evidence/df702b1335a33be5e96d26e52f762bd44680e934473fa8978cf136ba12da2f7a.md) - source value and exact raw locator.
* [licence.register_entry_name](../evidence/e2057fa91483cc3cb42e36996223b31d3edf46628310bc3b3aed74a6ef88f9f4.md) - source value and exact raw locator.
* [licence.authorisation_condition](../evidence/e2cfb37693f400098dd9b2372b51a11348f58873c57acd3962bd4515cd79d1e5.md) - source value and exact raw locator.
* [address.country](../evidence/eb2dce643e60082ddfc41ca46712348fcbbb55cdd764dc890363080f42429f87.md) - source value and exact raw locator.
* [licence.number](../evidence/f6278fc69148e5344104b6935c489f8158e99dd4bfb00ea7238e3717156cc254.md) - source value and exact raw locator.
* [address.locality](../evidence/f79027e1eb4de186fc9b215c5ce4fd6ea6455498e29eec6005b715b1c8b0774a.md) - source value and exact raw locator.
* [licence.authorisation_condition](../evidence/f82c446d75ba1c48ecf6b24a3e424264c15787b63c815ab2adfbefd3161b5995.md) - source value and exact raw locator.
* [financial_period.reporting_period](../evidence/f86724e9d6af7ba014d470569fa3b92cdb482ab5fed4f4d596ca90f8a8524c41.md) - source value and exact raw locator.
* [licence.authorisation_condition](../evidence/fa9dbe8e540bdf8950a21b95ca1df4a54707e0bca6ba54111da3a1d95d162c10.md) - source value and exact raw locator.
