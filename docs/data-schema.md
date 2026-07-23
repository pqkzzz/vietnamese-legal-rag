# Data Schema

## Purpose

Normalized data is the stable intermediate format for Vietnamese legal documents. It is produced from `data/raw/*.json` and is intended for later retrieval preparation, embedding, and indexing steps. This stage does not split points, create retrieval chunks, call LLMs, create embeddings, or ingest Qdrant.

## Input Schema

Raw files are JSON objects with:

```json
{
  "law_info": {
    "law_id": "LDD_2024",
    "law_name": "Luật Đất đai 2024 (Văn bản hợp nhất 45/VBHN-VPQH 2025)",
    "publisher": "Văn phòng Quốc hội",
    "document_number": "45/VBHN-VPQH",
    "issue_date": "28/02/2025",
    "effective_date": "01/08/2024",
    "status": "Đang có hiệu lực",
    "executive_summary": "..."
  },
  "clauses": []
}
```

Each raw clause normally has `id`, `position`, `content`, `cross_references`, and `tags`. Current raw data uses `position.chapter`, `position.article`, `position.article_title`, and `position.clause`; article values may be strings or numbers.

## Output Schema

Each output file is written as `data/normalized/{law_id}_normalized.json`:

```json
{
  "schema_version": "1.0",
  "law_info": {},
  "legal_units": [],
  "normalization_report": {}
}
```

`law_info` fields:

- `law_id`: preserved from raw.
- `law_name`: short name, with a final explicit consolidated-document suffix removed when present.
- `full_name`: original raw `law_info.law_name`.
- `publisher`, `document_number`, `executive_summary`: preserved as strings when available.
- `document_type`: `Văn bản hợp nhất` only when the name or number indicates a consolidated document; otherwise `null`.
- `issue_date`, `effective_from`, `effective_to`: ISO `YYYY-MM-DD` dates or `null`. `effective_from` comes from raw `effective_date`.
- `document_status`: one of `effective`, `expired`, `not_yet_effective`, `repealed`, or `unknown`.

`legal_units` fields:

- `unit_id` and `source_unit_id`: original raw `id`.
- `unit_type`: `article`, `article_lead`, `clause`, or `point`.
- `position`: all number/title fields are strings or `null`.
- `article_id`: `{law_id}_D{article_number}`.
- `parent_id`: `null` for articles, `article_id` for article leads and clauses, and the parent clause ID for points when known.
- `content_raw`: original content converted to a string without trimming inside content.
- `content_clean`: safe cleaned content for downstream retrieval.
- `cross_references`: normalized references while preserving each original object or string in `raw_reference`.
- `tags`: trimmed strings, de-duplicated case-insensitively in first-seen order.
- `provision_status`: `effective` or `repealed`.
- `is_retrievable`: boolean based on unit type, repeal status, and substantive content.
- `source`: source filename and optional source URL.

## Unit Type Rules

- `clause = null` becomes `unit_type = article`.
- `clause = 0` or `"0"` becomes `unit_type = article_lead`; its `clause_number` is `null` and it is not retrievable.
- Any other non-null clause becomes `unit_type = clause`.
- `point` is used only if raw data already has an explicit point field. The normalizer does not split `a)`, `b)`, `c)` content.

## Content Rules

`content_raw` keeps legal wording, punctuation, numbering, and point markers exactly as supplied, except that non-string scalar values are converted to strings.

`content_clean` removes numeric footnotes like `[2]` and `[80]`, normalizes line endings to `\n`, trims each line, collapses repeated spaces within a line, and collapses three or more blank lines to at most two newline characters. It does not paraphrase or remove legal numbering.

## Provision Status

If cleaned content contains `được bãi bỏ` or `bị bãi bỏ` case-insensitively, `provision_status` is `repealed` and `is_retrievable` is `false`. Repealed records remain in output. Normal article and clause units with substantive text are retrievable.

## Validation Report

`normalization_report` records input/output counts plus warnings and errors. Errors exclude unusable units, such as missing unit ID, missing article number, duplicate unit ID, non-object records, or invalid content. Warnings keep the unit, such as invalid dates, unknown document status, missing chapter, recoverable tags, and incomplete cross-references.

## Run

From the repository root:

```powershell
python apps/api/scripts/normalize_documents.py
```

Optional arguments:

```powershell
python apps/api/scripts/normalize_documents.py --input-dir data/raw --output-dir data/normalized --overwrite
python apps/api/scripts/normalize_documents.py --file 45_VBHN_VPQH_2025_Luat_Dat_Dai.json --overwrite
python apps/api/scripts/normalize_documents.py --strict --overwrite
```

## Example Unit

```json
{
  "unit_id": "LDD_2024_D3_K5",
  "source_unit_id": "LDD_2024_D3_K5",
  "unit_type": "clause",
  "position": {
    "chapter_number": "1",
    "chapter_title": null,
    "section_number": null,
    "section_title": null,
    "article_number": "3",
    "article_title": "Giải thích từ ngữ",
    "clause_number": "5",
    "point_number": null
  },
  "article_id": "LDD_2024_D3",
  "parent_id": "LDD_2024_D3",
  "content_raw": "5. Bồi thường về đất là...",
  "content_clean": "5. Bồi thường về đất là...",
  "cross_references": [],
  "tags": ["bồi thường", "quyền sử dụng đất"],
  "provision_status": "effective",
  "is_retrievable": true,
  "source": {
    "source_file": "45_VBHN_VPQH_2025_Luat_Dat_Dai.json",
    "source_url": null
  }
}
```

## Not Implemented In This Stage

Point splitting, retrieval JSONL/chunks, embeddings, sparse vectors, BM25 indexes, reranking, LLM parsing, and Qdrant ingestion are intentionally outside this normalization stage.
