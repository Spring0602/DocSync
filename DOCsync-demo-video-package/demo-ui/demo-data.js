/* Embedded original CLI reports, kept unchanged for offline file:// use. */
window.DOCSYNC_DEMO_REPORTS = {
  "repoName": "examples/minimal_repo",
  "before": {
    "schema_version": "2.0",
    "manifest": {
      "schema_version": "2.0",
      "run_id": "0511dd76bbf34b1e90049bb141732395",
      "versions": {
        "docsync": "0.2.0",
        "schema": "2.0",
        "extractor": "python-static/2",
        "claims": "markdown/2",
        "verifier": "verifier/2",
        "method": "full",
        "pydantic": "2.13.4",
        "markdown-it-py": "4.2.0"
      },
      "config_hash": "bf16e86a77600af101c341957cf19ecfc3c9b3e3ec35e9e2db1f9a09b7176ba1",
      "mode": "rules",
      "status": "COMPLETED",
      "enabled_types": [
        "DEFAULT_VALUE",
        "SIGNATURE",
        "CONFIG"
      ],
      "semantic_coverage": "supported-static-claims-only",
      "budget": {
        "max_requests": 20,
        "max_total_tokens": 100000
      },
      "usage": {
        "requests": 0,
        "input_tokens": 0,
        "output_tokens": 0
      },
      "diagnostics": [],
      "stage_seconds": {
        "extraction": 0.022903700002643745,
        "alignment": 0.00003119999746559188,
        "judging": 0.00005769999552285299,
        "verification": 0.00009020000288728625,
        "analysis_total": 0.023799199996574316,
        "repository": 0.19467640000220854,
        "patch_validation": 0.00376249999681022,
        "total": 0.25675200000114273
      },
      "model": {
        "provider": "none",
        "model": null,
        "temperature": 0
      },
      "events": [
        "CREATED",
        "ANALYZING",
        "EXTRACTING",
        "ALIGNING",
        "JUDGING",
        "VERIFYING",
        "REPORTING",
        "COMPLETED"
      ],
      "model_calls": []
    },
    "snapshot": {
      "repo_id": "0626f9b1de6af24de63bf353",
      "head_sha": "9b0e14eabdead86cc67ab2505746987f4c640632",
      "base_sha": null,
      "mode": "commit",
      "files_hash": "67325ac19c2d5f720fcbe71f",
      "dirty": false,
      "files": [
        {
          "path": "README.md",
          "blob_hash": "4c1c960bca1c4ee38edff253562add9f90e088a5b88160104e8a9b916b810064",
          "size": 142,
          "encoding": "utf-8"
        },
        {
          "path": "src/client.py",
          "blob_hash": "605ccaaa0035fd5397a215840519181f728ee794e6ca23cfdb816a20ceee9803",
          "size": 117,
          "encoding": "utf-8"
        }
      ],
      "changed_paths": []
    },
    "entities": [
      {
        "entity_id": "e268e37b0d36452f2961ff42",
        "kind": "function",
        "qualified_name": "src.client.connect",
        "module": "src.client",
        "signature": [
          {
            "name": "timeout",
            "kind": "POSITIONAL_OR_KEYWORD",
            "required": false,
            "value_state": "KNOWN",
            "typed_value": {
              "type": "int",
              "canonical": "[\"int\",60]"
            },
            "expression": "60"
          }
        ],
        "decorators": [],
        "span": {
          "path": "src/client.py",
          "start_line": 4,
          "end_line": 5,
          "start_byte": 73,
          "end_byte": 116,
          "blob_hash": "605ccaaa0035fd5397a215840519181f728ee794e6ca23cfdb816a20ceee9803"
        }
      }
    ],
    "facts": [
      {
        "fact_id": "ce9973d08171ee07be0c4273",
        "entity_id": "e268e37b0d36452f2961ff42",
        "subject": "src.client.connect",
        "property": "timeout",
        "value_state": "KNOWN",
        "typed_value": {
          "type": "int",
          "canonical": "[\"int\",60]"
        },
        "expression": "60",
        "span": {
          "path": "src/client.py",
          "start_line": 4,
          "end_line": 4,
          "start_byte": 93,
          "end_byte": 95,
          "blob_hash": "605ccaaa0035fd5397a215840519181f728ee794e6ca23cfdb816a20ceee9803"
        },
        "fact_kind": "DEFAULT_VALUE",
        "parameters": [],
        "receiver": "none",
        "extractor_version": "python-static/2",
        "provenance": []
      },
      {
        "fact_id": "d99e4dcb3f2a39ff5d0a3afe",
        "entity_id": "e268e37b0d36452f2961ff42",
        "subject": "src.client.connect",
        "property": "__signature__",
        "value_state": "KNOWN",
        "typed_value": null,
        "expression": "def connect(timeout=60):\n    return timeout",
        "span": {
          "path": "src/client.py",
          "start_line": 4,
          "end_line": 5,
          "start_byte": 73,
          "end_byte": 116,
          "blob_hash": "605ccaaa0035fd5397a215840519181f728ee794e6ca23cfdb816a20ceee9803"
        },
        "fact_kind": "SIGNATURE",
        "parameters": [
          {
            "name": "timeout",
            "kind": "POSITIONAL_OR_KEYWORD",
            "required": false,
            "value_state": "KNOWN",
            "typed_value": {
              "type": "int",
              "canonical": "[\"int\",60]"
            },
            "expression": "60"
          }
        ],
        "receiver": "none",
        "extractor_version": "python-static/2",
        "provenance": []
      }
    ],
    "claims": [
      {
        "claim_id": "c327cc581107e3d6442bb36f",
        "subject": "connect",
        "predicate": "timeout",
        "kind": "DEFAULT_ASSERTION",
        "value": {
          "type": "int",
          "canonical": "[\"int\",30]"
        },
        "qualifiers": [],
        "version_scope": "current",
        "span": {
          "path": "README.md",
          "start_line": 5,
          "end_line": 5,
          "start_byte": 32,
          "end_byte": 62,
          "blob_hash": "4c1c960bca1c4ee38edff253562add9f90e088a5b88160104e8a9b916b810064"
        },
        "value_span": {
          "path": "README.md",
          "start_line": 5,
          "end_line": 5,
          "start_byte": 56,
          "end_byte": 58,
          "blob_hash": "4c1c960bca1c4ee38edff253562add9f90e088a5b88160104e8a9b916b810064"
        },
        "quote": "`timeout` 默认值为 `30`。",
        "extraction_method": "markdown-rules/2",
        "source_hint": null,
        "positional_count": null,
        "keyword_names": [],
        "unpacking": false,
        "bound_receiver": false
      },
      {
        "claim_id": "99b0d46e5c094a39ae642358",
        "subject": "connect",
        "predicate": "__signature__",
        "kind": "CALL_EXAMPLE",
        "value": null,
        "qualifiers": [],
        "version_scope": "current",
        "span": {
          "path": "README.md",
          "start_line": 9,
          "end_line": 11,
          "start_byte": 108,
          "end_byte": 142,
          "blob_hash": "4c1c960bca1c4ee38edff253562add9f90e088a5b88160104e8a9b916b810064"
        },
        "value_span": null,
        "quote": "```python\nconnect(timeout=30)\n```\n",
        "extraction_method": "markdown-call/2",
        "source_hint": null,
        "positional_count": 0,
        "keyword_names": [
          "timeout"
        ],
        "unpacking": false,
        "bound_receiver": false
      }
    ],
    "candidates": [
      {
        "claim_id": "c327cc581107e3d6442bb36f",
        "candidates": [
          {
            "fact_id": "ce9973d08171ee07be0c4273",
            "rank": 1,
            "score": 1,
            "features": [
              "exact_symbol",
              "parameter_owner"
            ]
          }
        ],
        "ambiguity": false,
        "reason": "MATCH"
      },
      {
        "claim_id": "99b0d46e5c094a39ae642358",
        "candidates": [
          {
            "fact_id": "d99e4dcb3f2a39ff5d0a3afe",
            "rank": 1,
            "score": 1,
            "features": [
              "exact_symbol",
              "parameter_owner"
            ]
          }
        ],
        "ambiguity": false,
        "reason": "MATCH"
      }
    ],
    "judgments": [
      {
        "claim_id": "c327cc581107e3d6442bb36f",
        "decision": "INCONSISTENT",
        "fact_ids": [
          "ce9973d08171ee07be0c4273"
        ],
        "reason_code": "LITERAL_MISMATCH",
        "reason_text": "Compare explicit typed default values for the same parameter",
        "claim_type_check": true,
        "version_compatible": true,
        "score": null,
        "uncertainty_reason": null,
        "model_run_id": null
      },
      {
        "claim_id": "99b0d46e5c094a39ae642358",
        "decision": "CONSISTENT",
        "fact_ids": [
          "d99e4dcb3f2a39ff5d0a3afe"
        ],
        "reason_code": "CALL_ACCEPTED",
        "reason_text": "Statically bind supplied arguments to the supported signature",
        "claim_type_check": true,
        "version_compatible": true,
        "score": null,
        "uncertainty_reason": null,
        "model_run_id": null
      }
    ],
    "findings": [
      {
        "finding_id": "1306034f148975851b847468",
        "drift_type": "DEFAULT_VALUE",
        "claim_id": "c327cc581107e3d6442bb36f",
        "fact_ids": [
          "ce9973d08171ee07be0c4273"
        ],
        "evidence": {
          "head_sha": "9b0e14eabdead86cc67ab2505746987f4c640632",
          "snapshot_hash": "67325ac19c2d5f720fcbe71f",
          "entity_id": "e268e37b0d36452f2961ff42",
          "document": {
            "path": "README.md",
            "start_line": 5,
            "end_line": 5,
            "start_byte": 32,
            "end_byte": 62,
            "blob_hash": "4c1c960bca1c4ee38edff253562add9f90e088a5b88160104e8a9b916b810064"
          },
          "code": {
            "path": "src/client.py",
            "start_line": 4,
            "end_line": 4,
            "start_byte": 93,
            "end_byte": 95,
            "blob_hash": "605ccaaa0035fd5397a215840519181f728ee794e6ca23cfdb816a20ceee9803"
          },
          "code_provenance": [],
          "rule_id": "DEFAULT_VALUE/1",
          "verifier_version": "verifier/2"
        },
        "severity": "warning",
        "status": "INCONSISTENT",
        "verification_status": "VERIFIED",
        "ignored": false,
        "ignore_reason": null,
        "ignore_expires": null
      }
    ],
    "rejected": [],
    "patches": [
      {
        "patch_id": "16b9b6fe7d6db878fa1573ab",
        "finding_ids": [
          "1306034f148975851b847468"
        ],
        "base_hashes": {
          "README.md": "4c1c960bca1c4ee38edff253562add9f90e088a5b88160104e8a9b916b810064"
        },
        "edits": [
          {
            "span": {
              "path": "README.md",
              "start_line": 5,
              "end_line": 5,
              "start_byte": 56,
              "end_byte": 58,
              "blob_hash": "4c1c960bca1c4ee38edff253562add9f90e088a5b88160104e8a9b916b810064"
            },
            "old_text": "30",
            "new_text": "60"
          }
        ],
        "diff": "--- a/README.md\n+++ b/README.md\n@@ -2,7 +2,7 @@\n \n ## `connect`\n \n-`timeout` 默认值为 `30`。\n+`timeout` 默认值为 `60`。\n \n 可以显式选择较短的等待时间：\n \n",
        "validation": "VALIDATED",
        "requires_review": true,
        "validation_details": [
          "All byte preimages match",
          "Code fences unchanged",
          "In-memory rescan: target conflicts removed; no new confirmed conflicts",
          "Human semantic review still required"
        ]
      }
    ]
  },
  "after": {
    "schema_version": "2.0",
    "manifest": {
      "schema_version": "2.0",
      "run_id": "1b2987c8d15e4037a96e6cf6ef5c1325",
      "versions": {
        "docsync": "0.2.0",
        "schema": "2.0",
        "extractor": "python-static/2",
        "claims": "markdown/2",
        "verifier": "verifier/2",
        "method": "full",
        "pydantic": "2.13.4",
        "markdown-it-py": "4.2.0"
      },
      "config_hash": "bf16e86a77600af101c341957cf19ecfc3c9b3e3ec35e9e2db1f9a09b7176ba1",
      "mode": "rules",
      "status": "COMPLETED",
      "enabled_types": [
        "DEFAULT_VALUE",
        "SIGNATURE",
        "CONFIG"
      ],
      "semantic_coverage": "supported-static-claims-only",
      "budget": {
        "max_requests": 20,
        "max_total_tokens": 100000
      },
      "usage": {
        "requests": 0,
        "input_tokens": 0,
        "output_tokens": 0
      },
      "diagnostics": [],
      "stage_seconds": {
        "extraction": 0.010455199997522868,
        "alignment": 0.0000318000020342879,
        "judging": 0.00006379999831551686,
        "verification": 0.000004199995601084083,
        "analysis_total": 0.01140579999628244,
        "repository": 0.15285050000238698,
        "patch_validation": 0.000019099999917671084,
        "total": 0.16742599999997765
      },
      "model": {
        "provider": "none",
        "model": null,
        "temperature": 0
      },
      "events": [
        "CREATED",
        "ANALYZING",
        "EXTRACTING",
        "ALIGNING",
        "JUDGING",
        "VERIFYING",
        "REPORTING",
        "COMPLETED"
      ],
      "model_calls": []
    },
    "snapshot": {
      "repo_id": "0626f9b1de6af24de63bf353",
      "head_sha": "9b0e14eabdead86cc67ab2505746987f4c640632",
      "base_sha": null,
      "mode": "working-tree",
      "files_hash": "d9358580dc06515abdd2d88b",
      "dirty": true,
      "files": [
        {
          "path": "README.md",
          "blob_hash": "017421c07c0749ae29d0d1c8caa452de56345872eaacc7f2973924c7aa1f6201",
          "size": 142,
          "encoding": "utf-8"
        },
        {
          "path": "src/client.py",
          "blob_hash": "605ccaaa0035fd5397a215840519181f728ee794e6ca23cfdb816a20ceee9803",
          "size": 117,
          "encoding": "utf-8"
        }
      ],
      "changed_paths": []
    },
    "entities": [
      {
        "entity_id": "e268e37b0d36452f2961ff42",
        "kind": "function",
        "qualified_name": "src.client.connect",
        "module": "src.client",
        "signature": [
          {
            "name": "timeout",
            "kind": "POSITIONAL_OR_KEYWORD",
            "required": false,
            "value_state": "KNOWN",
            "typed_value": {
              "type": "int",
              "canonical": "[\"int\",60]"
            },
            "expression": "60"
          }
        ],
        "decorators": [],
        "span": {
          "path": "src/client.py",
          "start_line": 4,
          "end_line": 5,
          "start_byte": 73,
          "end_byte": 116,
          "blob_hash": "605ccaaa0035fd5397a215840519181f728ee794e6ca23cfdb816a20ceee9803"
        }
      }
    ],
    "facts": [
      {
        "fact_id": "ce9973d08171ee07be0c4273",
        "entity_id": "e268e37b0d36452f2961ff42",
        "subject": "src.client.connect",
        "property": "timeout",
        "value_state": "KNOWN",
        "typed_value": {
          "type": "int",
          "canonical": "[\"int\",60]"
        },
        "expression": "60",
        "span": {
          "path": "src/client.py",
          "start_line": 4,
          "end_line": 4,
          "start_byte": 93,
          "end_byte": 95,
          "blob_hash": "605ccaaa0035fd5397a215840519181f728ee794e6ca23cfdb816a20ceee9803"
        },
        "fact_kind": "DEFAULT_VALUE",
        "parameters": [],
        "receiver": "none",
        "extractor_version": "python-static/2",
        "provenance": []
      },
      {
        "fact_id": "d99e4dcb3f2a39ff5d0a3afe",
        "entity_id": "e268e37b0d36452f2961ff42",
        "subject": "src.client.connect",
        "property": "__signature__",
        "value_state": "KNOWN",
        "typed_value": null,
        "expression": "def connect(timeout=60):\n    return timeout",
        "span": {
          "path": "src/client.py",
          "start_line": 4,
          "end_line": 5,
          "start_byte": 73,
          "end_byte": 116,
          "blob_hash": "605ccaaa0035fd5397a215840519181f728ee794e6ca23cfdb816a20ceee9803"
        },
        "fact_kind": "SIGNATURE",
        "parameters": [
          {
            "name": "timeout",
            "kind": "POSITIONAL_OR_KEYWORD",
            "required": false,
            "value_state": "KNOWN",
            "typed_value": {
              "type": "int",
              "canonical": "[\"int\",60]"
            },
            "expression": "60"
          }
        ],
        "receiver": "none",
        "extractor_version": "python-static/2",
        "provenance": []
      }
    ],
    "claims": [
      {
        "claim_id": "b49a90cf0785ff3ab8bf4243",
        "subject": "connect",
        "predicate": "timeout",
        "kind": "DEFAULT_ASSERTION",
        "value": {
          "type": "int",
          "canonical": "[\"int\",60]"
        },
        "qualifiers": [],
        "version_scope": "current",
        "span": {
          "path": "README.md",
          "start_line": 5,
          "end_line": 5,
          "start_byte": 32,
          "end_byte": 62,
          "blob_hash": "017421c07c0749ae29d0d1c8caa452de56345872eaacc7f2973924c7aa1f6201"
        },
        "value_span": {
          "path": "README.md",
          "start_line": 5,
          "end_line": 5,
          "start_byte": 56,
          "end_byte": 58,
          "blob_hash": "017421c07c0749ae29d0d1c8caa452de56345872eaacc7f2973924c7aa1f6201"
        },
        "quote": "`timeout` 默认值为 `60`。",
        "extraction_method": "markdown-rules/2",
        "source_hint": null,
        "positional_count": null,
        "keyword_names": [],
        "unpacking": false,
        "bound_receiver": false
      },
      {
        "claim_id": "619a063f54c1d10100442ed3",
        "subject": "connect",
        "predicate": "__signature__",
        "kind": "CALL_EXAMPLE",
        "value": null,
        "qualifiers": [],
        "version_scope": "current",
        "span": {
          "path": "README.md",
          "start_line": 9,
          "end_line": 11,
          "start_byte": 108,
          "end_byte": 142,
          "blob_hash": "017421c07c0749ae29d0d1c8caa452de56345872eaacc7f2973924c7aa1f6201"
        },
        "value_span": null,
        "quote": "```python\nconnect(timeout=30)\n```\n",
        "extraction_method": "markdown-call/2",
        "source_hint": null,
        "positional_count": 0,
        "keyword_names": [
          "timeout"
        ],
        "unpacking": false,
        "bound_receiver": false
      }
    ],
    "candidates": [
      {
        "claim_id": "b49a90cf0785ff3ab8bf4243",
        "candidates": [
          {
            "fact_id": "ce9973d08171ee07be0c4273",
            "rank": 1,
            "score": 1,
            "features": [
              "exact_symbol",
              "parameter_owner"
            ]
          }
        ],
        "ambiguity": false,
        "reason": "MATCH"
      },
      {
        "claim_id": "619a063f54c1d10100442ed3",
        "candidates": [
          {
            "fact_id": "d99e4dcb3f2a39ff5d0a3afe",
            "rank": 1,
            "score": 1,
            "features": [
              "exact_symbol",
              "parameter_owner"
            ]
          }
        ],
        "ambiguity": false,
        "reason": "MATCH"
      }
    ],
    "judgments": [
      {
        "claim_id": "b49a90cf0785ff3ab8bf4243",
        "decision": "CONSISTENT",
        "fact_ids": [
          "ce9973d08171ee07be0c4273"
        ],
        "reason_code": "LITERAL_EQUAL",
        "reason_text": "Compare explicit typed default values for the same parameter",
        "claim_type_check": true,
        "version_compatible": true,
        "score": null,
        "uncertainty_reason": null,
        "model_run_id": null
      },
      {
        "claim_id": "619a063f54c1d10100442ed3",
        "decision": "CONSISTENT",
        "fact_ids": [
          "d99e4dcb3f2a39ff5d0a3afe"
        ],
        "reason_code": "CALL_ACCEPTED",
        "reason_text": "Statically bind supplied arguments to the supported signature",
        "claim_type_check": true,
        "version_compatible": true,
        "score": null,
        "uncertainty_reason": null,
        "model_run_id": null
      }
    ],
    "findings": [],
    "rejected": [],
    "patches": []
  }
};
