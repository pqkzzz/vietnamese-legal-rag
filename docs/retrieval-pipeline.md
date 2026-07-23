# Retrieval Pipeline

## Purpose

Retrieval chunks are JSONL records built from normalized legal data. They preserve the legal hierarchy while preparing deterministic `embedding_text` strings and metadata payloads for a later embedding/indexing stage.

This stage reads `data/normalized/*.json` and writes `data/retrieval/*_chunks.jsonl` plus per-law reports in `data/retrieval/reports/`. It does not create embedding vectors, call LLMs, connect to Qdrant, ingest data, build hybrid retrieval, or rerank results.

## Normalized To Retrieval

Normalized files remain the source of truth and are not modified. Each normalized `legal_unit` becomes one or more retrieval chunks:

- `article`: one article chunk when the article has no clauses.
- `article_lead`: skipped as an independent retrieval chunk.
- `clause` without points: one clause chunk.
- `clause` with legal points: one parent clause chunk plus one child chunk per point.
- `repealed` unit: still emitted for historical lookup, but not retrievable by default.

## Point Splitting

The splitter recognizes Vietnamese legal point markers only at the beginning of a line after optional indentation:

```text
a) b) c) d) đ) e) g) h) i) k) l) m) n) o) p) q) r) s) t) u) v) x) y)
```

It requires at least two markers in one clause, a sequence starting at `a)`, valid legal order, and non-empty content for every point. It does not split `a)` in the middle of a sentence, examples like `(a)`, numeric lists such as `1)`, or suspicious repeated/out-of-order marker sequences. Suspicious clauses stay as clause chunks and receive `INVALID_POINT_SEQUENCE` warnings.

## Point IDs

Point chunk IDs are deterministic and derived from the parent clause ID:

```text
LKDBDS_2023_D1_K2_DA
LKDBDS_2023_D1_K2_DB
LKDBDS_2023_D1_K2_DC
LKDBDS_2023_D1_K2_DD
LKDBDS_2023_D1_K2_DDD
```

The suffix mapping keeps `d` and `đ` distinct: `d -> DD`, `đ -> DDD`. Point IDs contain no Vietnamese diacritics and can be recreated from parent ID plus point number.

## Parent-Child Retrieval

When a clause has points, the parent clause chunk is emitted first and carries the full clause content. Its payload has:

```json
{
  "has_children": true,
  "child_ids": ["LKDBDS_2023_D1_K2_DA"],
  "is_retrievable": false
}
```

Point children inherit law metadata, article/clause position, tags, cross-references, source, and provision status from the parent. Their `parent_id` is the parent clause chunk ID. Effective point children are retrievable; repealed point children are not.

## JSONL Schema

Each JSONL line is one object:

```json
{
  "chunk_id": "LKDBDS_2023_D1_K2_DA",
  "source_unit_id": "LKDBDS_2023_D1_K2",
  "unit_type": "point",
  "embedding_text": "Văn bản: ...",
  "payload": {
    "law_id": "LKDBDS_2023",
    "law_name": "Luật Kinh doanh bất động sản 2023",
    "full_name": "Luật Kinh doanh bất động sản 2023 (Văn bản hợp nhất 06/VBHN-VPQH 2025)",
    "document_number": "06/VBHN-VPQH",
    "document_type": "Văn bản hợp nhất",
    "document_status": "effective",
    "issue_date": "2025-02-21",
    "effective_from": "2024-08-01",
    "effective_to": null,
    "chapter_number": "1",
    "chapter_title": null,
    "section_number": null,
    "section_title": null,
    "article_number": "1",
    "article_title": "Phạm vi điều chỉnh",
    "clause_number": "2",
    "point_number": "a",
    "article_id": "LKDBDS_2023_D1",
    "parent_id": "LKDBDS_2023_D1_K2",
    "content_raw": "a) ...",
    "content_clean": "a) ...",
    "clause_lead_raw": "2. ...",
    "clause_lead_clean": "2. ...",
    "has_children": false,
    "child_ids": [],
    "cross_references": [],
    "tags": [],
    "provision_status": "effective",
    "is_retrievable": true,
    "source": {"source_file": "...", "source_url": null}
  }
}
```

## Embedding Text

`embedding_text` is plain text for a later embedding model. It is not a vector.

Article format:

```text
Văn bản: {law_name}
Số văn bản: {document_number}
Điều {article_number}: {article_title}
{content_clean}
```

Clause format:

```text
Văn bản: {law_name}
Số văn bản: {document_number}
Điều {article_number}: {article_title}
Khoản {clause_number}
{content_clean}
```

Point format:

```text
Văn bản: {law_name}
Số văn bản: {document_number}
Điều {article_number}: {article_title}
Khoản {clause_number}: {clause_lead_without_leading_number}
Điểm {point_number}: {point_content_without_marker}
```

The builder does not add executive summaries, tags, sibling point content, or whole parent clause text to point embedding text. Payload content remains unchanged.

## Retrievability

- Article chunks follow normalized `is_retrievable`.
- Clause chunks without children follow normalized `is_retrievable`.
- Parent clauses with point children are emitted but default to `is_retrievable=false`.
- Effective point children are retrievable.
- Repealed chunks and their point children are never retrievable by default.
- Article leads are not emitted as retrieval chunks.

## Reports

Each normalized file creates `data/retrieval/reports/{law_id}_chunk_report.json` with input/output counts, chunk type counts, split counts, skipped article leads, retrievable/non-retrievable counts, warnings, and errors. Validation checks duplicate chunk IDs, point parents, parent `child_ids`, article lead leakage, empty content, JSONL parseability, and report count consistency.

## Run

From repository root:

```powershell
python apps/api/scripts/build_chunks.py --overwrite
```

Optional examples:

```powershell
python apps/api/scripts/build_chunks.py --input-dir data/normalized --output-dir data/retrieval --overwrite
python apps/api/scripts/build_chunks.py --file LDD_2024_normalized.json --overwrite
python apps/api/scripts/build_chunks.py --dry-run
python apps/api/scripts/build_chunks.py --strict --overwrite
```

## Example Parent And Child

Parent chunk:

```json
{
  "chunk_id": "LKDBDS_2023_D1_K2",
  "source_unit_id": "LKDBDS_2023_D1_K2",
  "unit_type": "clause",
  "payload": {
    "parent_id": "LKDBDS_2023_D1",
    "has_children": true,
    "child_ids": ["LKDBDS_2023_D1_K2_DA", "LKDBDS_2023_D1_K2_DB"],
    "is_retrievable": false
  }
}
```

Point child:

```json
{
  "chunk_id": "LKDBDS_2023_D1_K2_DA",
  "source_unit_id": "LKDBDS_2023_D1_K2",
  "unit_type": "point",
  "payload": {
    "parent_id": "LKDBDS_2023_D1_K2",
    "article_id": "LKDBDS_2023_D1",
    "point_number": "a",
    "has_children": false,
    "child_ids": [],
    "is_retrievable": true
  }
}
```

## Not Implemented

Embedding vector generation, Qdrant collections, Qdrant ingestion, hybrid retrieval, sparse indexes, LLM parsing, and reranking are intentionally left for later stages.
