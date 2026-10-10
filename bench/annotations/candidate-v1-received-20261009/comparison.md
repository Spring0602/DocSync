# B/C 标注对照（非最终裁决）

字段差异按原字符串比较，不自动认定语义冲突；目标限定名和行区间的不同仍需 A 核对。两份原始标签、理由和证据保留在各自 CSV 中。

| 样本 | B 标签 | C 标签 | 不同字段 |
| --- | --- | --- | --- |
| candidate-01 | INCONSISTENT | INCONSISTENT | target_entity |
| candidate-02 | CONSISTENT | CONSISTENT | target_entity |
| candidate-03 | INCONSISTENT | INCONSISTENT | target_entity |
| candidate-04 | CONSISTENT | CONSISTENT | target_entity |
| candidate-05 | INCONSISTENT | INCONSISTENT | target_entity |
| candidate-06 | CONSISTENT | CONSISTENT | target_entity |
| candidate-07 | INSUFFICIENT | INSUFFICIENT | target_entity, code_lines |
| candidate-08 | CONSISTENT | CONSISTENT | target_entity, code_lines |
| candidate-09 | CONSISTENT | CONSISTENT | document_lines |
| candidate-10 | INCONSISTENT | INCONSISTENT | document_lines |
| candidate-11 | CONSISTENT | CONSISTENT | document_lines |
| candidate-12 | INSUFFICIENT | INSUFFICIENT | code_lines, document_lines |
| candidate-13 | CONSISTENT | CONSISTENT | code_lines, document_lines |
| candidate-14 | INCONSISTENT | INCONSISTENT | code_lines, document_lines |
| candidate-15 | INCONSISTENT | INCONSISTENT | code_lines, document_lines |
| candidate-16 | INSUFFICIENT | INSUFFICIENT | code_lines, document_lines |
| candidate-17 | INCONSISTENT | INCONSISTENT | target_entity |
| candidate-18 | CONSISTENT | CONSISTENT | target_entity |
| candidate-19 | INSUFFICIENT | INSUFFICIENT | target_entity |
| candidate-20 | CONSISTENT | CONSISTENT | target_entity |
| candidate-21 | INCONSISTENT | INCONSISTENT | target_entity |
| candidate-22 | CONSISTENT | CONSISTENT | target_entity |
| candidate-23 | INSUFFICIENT | INSUFFICIENT | target_entity |
| candidate-24 | CONSISTENT | CONSISTENT | target_entity |

## candidate-01

| 字段 | B | C |
| --- | --- | --- |
| label | INCONSISTENT | INCONSISTENT |
| drift_type | DEFAULT_VALUE | DEFAULT_VALUE |
| target_entity | PageReader.__init__ | PageReader.__init__.encoding |
| code_lines | 2 | 2 |
| document_lines | 5 | 5 |

## candidate-02

| 字段 | B | C |
| --- | --- | --- |
| label | CONSISTENT | CONSISTENT |
| drift_type | DEFAULT_VALUE | DEFAULT_VALUE |
| target_entity | download_resource | download_resource.retries |
| code_lines | 1 | 1 |
| document_lines | 5 | 5 |

## candidate-03

| 字段 | B | C |
| --- | --- | --- |
| label | INCONSISTENT | INCONSISTENT |
| drift_type | DEFAULT_VALUE | DEFAULT_VALUE |
| target_entity | emit_record | emit_record.tags |
| code_lines | 1 | 1 |
| document_lines | 5 | 5 |

## candidate-04

| 字段 | B | C |
| --- | --- | --- |
| label | CONSISTENT | CONSISTENT |
| drift_type | DEFAULT_VALUE | DEFAULT_VALUE |
| target_entity | MemoryBuffer.__init__ | MemoryBuffer.__init__.capacity |
| code_lines | 2 | 2 |
| document_lines | 5 | 5 |

## candidate-05

| 字段 | B | C |
| --- | --- | --- |
| label | INCONSISTENT | INCONSISTENT |
| drift_type | DEFAULT_VALUE | DEFAULT_VALUE |
| target_entity | read_batch | read_batch.limit |
| code_lines | 1-6 | 1-6 |
| document_lines | 5 | 5 |

## candidate-06

| 字段 | B | C |
| --- | --- | --- |
| label | CONSISTENT | CONSISTENT |
| drift_type | DEFAULT_VALUE | DEFAULT_VALUE |
| target_entity | encode_packet | encode_packet.codec |
| code_lines | 1-4 | 1-4 |
| document_lines | 5 | 5 |

## candidate-07

| 字段 | B | C |
| --- | --- | --- |
| label | INSUFFICIENT | INSUFFICIENT |
| drift_type | DEFAULT_VALUE | DEFAULT_VALUE |
| target_entity | flush_records | flush_records.interval |
| code_lines | 3-6 | 1-7 |
| document_lines | 5 | 5 |

## candidate-08

| 字段 | B | C |
| --- | --- | --- |
| label | CONSISTENT | CONSISTENT |
| drift_type | DEFAULT_VALUE | DEFAULT_VALUE |
| target_entity | export_records | export_records.format_name |
| code_lines | 1-4 | 1-5 |
| document_lines | 5 | 5 |

## candidate-09

| 字段 | B | C |
| --- | --- | --- |
| label | CONSISTENT | CONSISTENT |
| drift_type | SIGNATURE | SIGNATURE |
| target_entity | attach_volume | attach_volume |
| code_lines | 1 | 1 |
| document_lines | 6-8 | 5-8 |

## candidate-10

| 字段 | B | C |
| --- | --- | --- |
| label | INCONSISTENT | INCONSISTENT |
| drift_type | SIGNATURE | SIGNATURE |
| target_entity | send_notice | send_notice |
| code_lines | 1 | 1 |
| document_lines | 6-8 | 5-8 |

## candidate-11

| 字段 | B | C |
| --- | --- | --- |
| label | CONSISTENT | CONSISTENT |
| drift_type | SIGNATURE | SIGNATURE |
| target_entity | place_marker | place_marker |
| code_lines | 1 | 1 |
| document_lines | 6-9 | 5-9 |

## candidate-12

| 字段 | B | C |
| --- | --- | --- |
| label | INSUFFICIENT | INSUFFICIENT |
| drift_type | SIGNATURE | SIGNATURE |
| target_entity | queue_notice | queue_notice |
| code_lines | 4-7 | 1-8 |
| document_lines | 6-7 | 5-7 |

## candidate-13

| 字段 | B | C |
| --- | --- | --- |
| label | CONSISTENT | CONSISTENT |
| drift_type | SIGNATURE | SIGNATURE |
| target_entity | ArtifactStore.open | ArtifactStore.open |
| code_lines | 2-3 | 1-4 |
| document_lines | 6-7 | 5-7 |

## candidate-14

| 字段 | B | C |
| --- | --- | --- |
| label | INCONSISTENT | INCONSISTENT |
| drift_type | SIGNATURE | SIGNATURE |
| target_entity | Formatter.render | Formatter.render |
| code_lines | 2-3 | 1-4 |
| document_lines | 6-7 | 5-7 |

## candidate-15

| 字段 | B | C |
| --- | --- | --- |
| label | INCONSISTENT | INCONSISTENT |
| drift_type | SIGNATURE | SIGNATURE |
| target_entity | Registry.register | Registry.register |
| code_lines | 1-2 | 1-3 |
| document_lines | 6-8 | 5-8 |

## candidate-16

| 字段 | B | C |
| --- | --- | --- |
| label | INSUFFICIENT | INSUFFICIENT |
| drift_type | SIGNATURE | SIGNATURE |
| target_entity | dispatcher().deliver | dispatcher().deliver |
| code_lines | 3-14 | 1-14 |
| document_lines | 6-7 | 5-7 |

## candidate-17

| 字段 | B | C |
| --- | --- | --- |
| label | INCONSISTENT | INCONSISTENT |
| drift_type | CONFIG | CONFIG |
| target_entity | case17.RETRY_WINDOW | RETRY_WINDOW |
| code_lines | 1-2 | 1-2 |
| document_lines | 5 | 5 |

## candidate-18

| 字段 | B | C |
| --- | --- | --- |
| label | CONSISTENT | CONSISTENT |
| drift_type | CONFIG | CONFIG |
| target_entity | case18.PORT | PORT |
| code_lines | 1-2 | 1-2 |
| document_lines | 5 | 5 |

## candidate-19

| 字段 | B | C |
| --- | --- | --- |
| label | INSUFFICIENT | INSUFFICIENT |
| drift_type | CONFIG | CONFIG |
| target_entity | case19.ARCHIVE_LEVEL | ARCHIVE_LEVEL |
| code_lines | 1-6 | 1-6 |
| document_lines | 5 | 5 |

## candidate-20

| 字段 | B | C |
| --- | --- | --- |
| label | CONSISTENT | CONSISTENT |
| drift_type | CONFIG | CONFIG |
| target_entity | case20.SERVICE_OPTIONS | SERVICE_OPTIONS.workers |
| code_lines | 1-2 | 1-2 |
| document_lines | 5 | 5 |

## candidate-21

| 字段 | B | C |
| --- | --- | --- |
| label | INCONSISTENT | INCONSISTENT |
| drift_type | CONFIG | CONFIG |
| target_entity | case21.PIPELINE.export | PIPELINE.export.compression |
| code_lines | 1 | 1 |
| document_lines | 5 | 5 |

## candidate-22

| 字段 | B | C |
| --- | --- | --- |
| label | CONSISTENT | CONSISTENT |
| drift_type | CONFIG | CONFIG |
| target_entity | case22.RETRY_DELAYS | RETRY_DELAYS |
| code_lines | 1 | 1 |
| document_lines | 5 | 5 |

## candidate-23

| 字段 | B | C |
| --- | --- | --- |
| label | INSUFFICIENT | INSUFFICIENT |
| drift_type | CONFIG | CONFIG |
| target_entity | case23.STORAGE.local | STORAGE.local.root |
| code_lines | 1-3 | 1-3 |
| document_lines | 5 | 5 |

## candidate-24

| 字段 | B | C |
| --- | --- | --- |
| label | CONSISTENT | CONSISTENT |
| drift_type | CONFIG | CONFIG |
| target_entity | case24.CACHE | CACHE.enabled |
| code_lines | 1 | 1 |
| document_lines | 5 | 5 |
