# Vietnamese Legal RAG

![Python](https://img.shields.io/badge/Python-Application-3776AB?logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active%20Development-orange)
![Qdrant](https://img.shields.io/badge/Vector%20Database-Qdrant-DC244C?logo=qdrant&logoColor=white)
![Embeddings](https://img.shields.io/badge/Embeddings-BGE--M3-2563EB)
![Retrieval](https://img.shields.io/badge/Retrieval-Dense%20%7C%20BM25%20%7C%20Hybrid-16A34A)
![Evidence Tests](https://img.shields.io/badge/Evidence%20Tests-74%20Passing-brightgreen)
![LLM API](https://img.shields.io/badge/External%20LLM%20API-Not%20Required-0EA5E9)

A retrieval-augmented generation foundation for Vietnamese legal documents.

The project currently focuses on building a reliable legal retrieval and evidence-analysis pipeline before integrating answer generation.

## Implemented Features

- Legal document normalization
- Parent-child legal chunk construction
- Dense retrieval with a fine-tuned BGE-M3 model
- Sparse BM25 retrieval
- Hybrid retrieval using Reciprocal Rank Fusion
- Query understanding and metadata-aware retrieval routing
- Exact legal citation lookup
- Legal provision hierarchy indexing
- Legal reference parsing and resolution
- Rule-based legal dependency detection

The currently implemented pipeline does not require an external LLM API.

---

## Current Pipeline

```text
Raw Legal Documents
        ↓
Document Normalization
        ↓
Parent-Child Legal Chunking
        ↓
Dense and Sparse Indexing
        ↓
Query Understanding
        ↓
Metadata Filter Planning
        ↓
Query-Aware Retrieval
   ├── Exact Citation Lookup
   ├── Filtered Hybrid Retrieval
   └── Broad Hybrid Retrieval
        ↓
Legal Provision Hierarchy
        ↓
Reference Parsing and Resolution
        ↓
Dependency Detection
```

The following stages are planned but have not yet been implemented:

```text
Anchor Candidate Reranking
        ↓
Adaptive Evidence Expansion
        ↓
Evidence Group Construction
        ↓
Evidence Group Reranking
        ↓
Evidence Grading
        ↓
Citation-Bound Answer Generation
        ↓
Answer Verification
```

---

## Repository Structure

```text
vietnamese-legal-rag/
├── apps/
│   └── api/
│       ├── app/
│       │   ├── infrastructure/
│       │   │   └── qdrant/
│       │   └── modules/
│       │       ├── ingestion/
│       │       ├── query_understanding/
│       │       ├── retrieval/
│       │       └── evidence/
│       ├── scripts/
│       └── tests/
├── data/
│   ├── raw/
│   ├── normalized/
│   ├── retrieval/
│   └── evaluation/
├── models/
└── README.md
```

---

## 1. Data Normalization

Normalize raw legal JSON documents from:

```text
data/raw/*.json
```

into stable intermediate representations under:

```text
data/normalized/
```

Run:

```powershell
python apps/api/scripts/normalize_documents.py `
  --input-dir data/raw `
  --output-dir data/normalized
```

Use `--overwrite` to replace existing normalized files:

```powershell
python apps/api/scripts/normalize_documents.py `
  --input-dir data/raw `
  --output-dir data/normalized `
  --overwrite
```

This stage only produces normalized legal JSON.

It does not:

- Generate embeddings
- Build retrieval chunks
- Create BM25 indexes
- Connect to Qdrant
- Run retrieval evaluation

---

## 2. Build Retrieval Chunks

Build parent-child legal retrieval chunks from normalized documents:

```powershell
python apps/api/scripts/build_chunks.py --overwrite
```

The script creates:

```text
data/retrieval/*_chunks.jsonl
data/retrieval/*_chunk_report.json
```

The retrieval structure preserves the Vietnamese legal hierarchy:

```text
Law
└── Article
    ├── Clause
    │   ├── Point
    │   ├── Point
    │   └── Point
    └── Clause
```

Parent clauses containing point lists are retained as contextual nodes, while individual points can be indexed as retrievable chunks.

Example:

```text
LDD_2024_D121_K1
├── LDD_2024_D121_K1_DA
├── LDD_2024_D121_K1_DB
├── LDD_2024_D121_K1_DC
└── ...
```

A parent clause may have:

```text
is_retrievable = false
```

while its point children remain retrievable.

This avoids returning duplicated content during retrieval while preserving the clause introduction for later evidence expansion.

### Current Retrieval Dataset

| Provision type | Count |
|---|---:|
| Article chunks | 168 |
| Clause chunks | 5,516 |
| Point chunks | 4,407 |
| **Total chunks** | **10,091** |

---

## 3. Dense Retrieval

Dense retrieval uses a fine-tuned BGE-M3 embedding model:

```text
models/bge-m3-finetuned
```

The configured Qdrant collection is:

```text
legal_units_bge_m3_finetuned
```

Dense vectors use normalized 1,024-dimensional CLS embeddings.

### Dense Evaluation Dataset

The gold-standard dense retrieval dataset is stored at:

```text
data/evaluation/dense_eval.jsonl
```

Gold chunk IDs must be selected by reading and validating the legal content directly.

They must not be generated from retrieval top-k outputs.

Validate the evaluation dataset:

```powershell
python apps/api/scripts/validate_dense_eval_dataset.py
```

Run a small dense retrieval evaluation sample:

```powershell
python apps/api/scripts/evaluate_dense_retrieval.py --limit 5
```

### Current Dense Retrieval Results

Evaluation set size: 48 queries.

| Metric | Score |
|---|---:|
| Hit@1 | 0.7500 |
| Hit@3 | 0.8958 |
| Hit@5 | 0.9375 |
| Hit@10 | 0.9792 |
| Recall@1 | 0.6632 |
| Recall@3 | 0.8854 |
| Recall@5 | 0.9271 |
| Recall@10 | 0.9688 |
| MRR@10 | 0.8285 |
| Average latency | 0.345 s |

---

## 4. Sparse BM25 Retrieval

Sparse retrieval uses FastEmbed BM25 with the Qdrant sparse collection:

```text
legal_units_bm25
```

Sparse vector name:

```text
bm25
```

Current configuration:

```text
Model: Qdrant/bm25
Language: English
Stemming: Disabled
```

BM25 is useful for exact legal terminology, article numbers, named entities and lexical matches.

### Current Sparse Retrieval Results

| Metric | Score |
|---|---:|
| Hit@1 | 0.6458 |
| Hit@3 | 0.7708 |
| Hit@5 | 0.8958 |
| Hit@10 | 0.9167 |
| Recall@1 | 0.5833 |
| Recall@3 | 0.7292 |
| Recall@5 | 0.8542 |
| Recall@10 | 0.8958 |
| MRR@10 | 0.7255 |
| Average latency | 0.016 s |

---

## 5. Hybrid Retrieval

Hybrid retrieval combines dense and sparse results using Reciprocal Rank Fusion.

Current fusion configuration:

```text
Dense candidate limit: 50
Sparse candidate limit: 50
RRF constant k: 60
Dense weight: 1.0
Sparse weight: 1.0
Deduplication key: chunk_id
```

Each hybrid result preserves:

- Dense rank
- Sparse rank
- Dense score
- Sparse score
- RRF score
- Original payload

### Current Hybrid Retrieval Results

| Metric | Score |
|---|---:|
| Hit@1 | 0.7292 |
| Hit@3 | 0.9583 |
| Hit@5 | 0.9583 |
| Hit@10 | 1.0000 |
| Recall@1 | 0.6563 |
| Recall@3 | 0.9132 |
| Recall@5 | 0.9479 |
| Recall@10 | 0.9792 |
| MRR@10 | 0.8386 |
| Average latency | 0.359 s |

Hybrid retrieval currently provides the highest MRR and complete Hit@10 coverage on the evaluation dataset.

---

## 6. Query Understanding

The query-understanding module extracts structured legal information from a user question.

It supports:

- Query normalization
- Legal citation parsing
- Law name and alias resolution
- Legal intent classification
- Metadata filter planning
- Retrieval route selection

Main models include:

- `LegalCitation`
- `ResolvedLaw`
- `QueryUnderstandingResult`
- `MetadataFilterPlan`

Example query:

```text
điểm b khoản 1 Điều 121 Luật Đất đai 2024
```

Structured result:

```text
law_id = LDD_2024
article_number = 121
clause_number = 1
point_number = b
```

### Current Query Understanding Results

Evaluation set size: 48 queries.

```text
Law filter accuracy when a gold law is available: 100%
False-positive law filters: 0
```

---

## 7. Query-Aware Retrieval

`QueryAwareRetriever` selects one of three retrieval routes:

```text
exact_citation_lookup
filtered_hybrid
broad_hybrid
```

### Exact Citation Lookup

Used when the query explicitly identifies a legal provision.

Examples:

```text
Điều 121 Luật Đất đai 2024
Khoản 1 Điều 121 Luật Đất đai 2024
Điểm b khoản 1 Điều 121 Luật Đất đai 2024
```

Exact citation lookup determines a precise legal scope.

A citation can map to:

- One point chunk
- A parent clause and its child points
- Multiple chunks belonging to one article

An exact citation therefore identifies a legal scope, not necessarily one physical chunk.

### Filtered Hybrid Retrieval

Used when the target law is known but the query does not specify a complete provision location.

The hybrid search can be restricted with metadata such as:

```text
law_id
document_status
provision_status
is_retrievable
```

### Broad Hybrid Retrieval

Used when no reliable law filter can be inferred.

The search runs across the complete indexed corpus.

---

## 8. Legal Provision Hierarchy Index

The hierarchy index is built directly from:

```text
data/retrieval/*_chunks.jsonl
```

Retrieval JSONL is used instead of normalized JSON because it contains the final parent-clause and point-chunk structure used by the retrievers.

The index supports:

```python
get_node(chunk_id)
get_parent(chunk_id)
get_children(chunk_id)
get_siblings(chunk_id)
get_previous_sibling(chunk_id)
get_next_sibling(chunk_id)

lookup(
    law_id,
    article_number,
    clause_number=None,
    point_number=None,
)

get_article_nodes(law_id, article_number)
get_clause_nodes(law_id, article_number, clause_number)
```

Legal order is derived deterministically from:

1. Sorted retrieval filenames
2. JSONL line order inside each file

Chunk IDs are not used as the primary ordering mechanism because Vietnamese point labels such as `d` and `đ` may not sort correctly lexicographically.

### Inspect the Hierarchy

```powershell
python apps/api/scripts/inspect_hierarchy.py `
  --law-id LDD_2024 `
  --article 121 `
  --clause 1 `
  --point b
```

Example hierarchy:

```text
LDD_2024_D121_K1
└── LDD_2024_D121_K1_DB
```

For point `b`:

```text
Parent: LDD_2024_D121_K1
Previous sibling: LDD_2024_D121_K1_DA
Next sibling: LDD_2024_D121_K1_DC
```

The complete hierarchy currently builds in approximately 1.5 seconds for 10,091 nodes.

---

## 9. Legal Reference Parsing

The reference parser detects legal references from two sources:

1. Structured `cross_references` metadata
2. Regex fallback over `content_clean`

Structured metadata is preferred, but the parser still scans the text for references that may not have been extracted during ingestion.

Supported patterns include:

```text
Điều 34
khoản 2 Điều 34
điểm b khoản 1 Điều 121
điểm đ khoản 2 Điều 30
các Điều 34, 35 và 36
khoản 1 Điều này
Điều này
```

Ambiguous references are not guessed automatically:

```text
khoản trên
khoản dưới
điểm này
điều liền trước
điều liền sau
```

The parser deduplicates structured and regex references by canonical legal target while preserving structured metadata as the preferred source.

Example:

```text
Structured metadata: Điều 34
Content text: Điều 34 and Điều 35
```

Final parsed references:

```text
Điều 34 — structured metadata
Điều 35 — content regex
```

---

## 10. Legal Reference Resolution

The reference resolver maps parsed references to real hierarchy nodes.

Resolution priority:

```text
target_unit_id
        ↓
law + article + clause + point
        ↓
law + article + clause
        ↓
law + article
        ↓
unresolved
```

A reference to an article can be resolved successfully even when no physical article chunk exists.

For example:

```text
target_unit_id = BLTTDS_2015_D70
```

If `BLTTDS_2015_D70` is only a virtual article container, the resolver falls back to the real clause and point chunks belonging to Article 70.

It does not create a synthetic article chunk.

### Inspect References

```powershell
python apps/api/scripts/inspect_references.py `
  --chunk-id LDD_2024_D120_K4 `
  --show-content `
  --show-raw
```

Example content:

```text
Việc cho thuê đất quy định tại Điều này được thực hiện
theo quy định tại các điều 124, 125 và 126 của Luật này.
```

Parsed references:

```text
Điều 120
Điều 124
Điều 125
Điều 126
```

---

## 11. Legal Dependency Detection

The dependency detector determines whether a legal chunk can be understood independently.

It produces signals such as:

```text
needs_parent
needs_children
needs_siblings
needs_previous_neighbor
needs_next_neighbor
needs_references
is_self_contained
```

The detector is rule-based and query-independent.

It combines:

- Provision level
- Parent and child metadata
- Clause introductions
- Legal reference markers
- List structures
- Exception markers
- Previous and next sibling availability
- Procedural markers

### Example: Point Dependency

Chunk:

```text
LDD_2024_D121_K1_DB
```

Content:

```text
b) Chuyển đất nông nghiệp sang đất phi nông nghiệp;
```

Detected signals:

```text
needs_parent = true
needs_siblings = true
is_self_contained = false
```

The point needs its parent clause because the parent provides the list introduction.

The sibling signal indicates that the point belongs to a structured list. The later evidence-expansion policy will decide whether all sibling points should be included.

### Example: Parent Clause

Chunk:

```text
LDD_2024_D121_K1
```

Detected signals:

```text
needs_children = true
needs_parent = false
```

The clause introduces a list and therefore depends on its point children.

It does not require an article parent merely because the article container is not physically stored as a chunk.

### Example: Reference Dependency

Chunk:

```text
LDD_2024_D120_K4
```

Detected signal:

```text
needs_references = true
```

The detector identifies reference dependencies but does not follow or insert the target provisions.

### Inspect Dependencies

```powershell
python apps/api/scripts/inspect_dependencies.py `
  --chunk-id LDD_2024_D121_K1_DB `
  --show-content `
  --show-parent `
  --show-siblings `
  --show-references
```

The dependency detector only produces signals.

It does not perform evidence expansion.

---

## 12. Tests

Current unit and regression coverage includes:

- Legal hierarchy construction
- Exact provision lookup
- Parent-child relationships
- Sibling and neighbor ordering
- Virtual article containers
- Legal reference parsing
- Structured and regex reference deduplication
- Supplemental regex references
- Legal reference resolution
- Cross-law reference resolution
- Legal dependency detection
- Self-contained provision detection
- Exception and list markers

Current evidence-related regression result:

```text
74 tests passed
```

Run the current evidence test suite with a Python environment that has `pytest` installed:

```powershell
python -m pytest `
  apps/api/tests/unit/test_dependency_detector.py `
  apps/api/tests/unit/test_reference_parser.py `
  apps/api/tests/unit/test_reference_resolver.py `
  apps/api/tests/unit/test_hierarchy_index.py `
  -q
```

The current project `.venv` does not include `pytest`, so tests are currently executed using an available Python environment that provides it.

Runtime scripts and import checks should still be run with the project `.venv`.

---

## Current Development Status

| Component | Status |
|---|---|
| Raw document normalization | Completed |
| Parent-child chunking | Completed |
| Dense retrieval | Completed |
| Sparse BM25 retrieval | Completed |
| Hybrid RRF retrieval | Completed |
| Query understanding | Completed |
| Metadata filter planning | Completed |
| Query-aware routing | Completed |
| Legal hierarchy index | Completed |
| Reference parser | Completed |
| Reference resolver | Completed |
| Dependency detector | Completed |
| Anchor Cross-Encoder reranking | Not implemented |
| Adaptive evidence expansion | Not implemented |
| Evidence grouping | Not implemented |
| Token budget controller | Not implemented |
| Evidence group reranking | Not implemented |
| Evidence grader | Not implemented |
| Citation-bound generator | Not implemented |
| Answer verifier | Not implemented |

---

## Next Milestone

The next development stage is an intent-aware evidence expansion policy.

The policy will use:

- Query intent
- Anchor provision level
- Hierarchy relationships
- Dependency signals
- Resolved legal references
- Context limits

to decide whether to include:

- Parent clauses
- Child points
- Relevant siblings
- Previous or next provisions
- Referenced provisions

The policy will remain separate from the evidence-expansion implementation so that its rules can be tested independently.

---

## Design Principles

- Do not guess legal provision locations when metadata is available.
- Preserve exact citation anchors.
- Keep retrieval scores and provenance.
- Do not create synthetic legal chunks.
- Do not cross law boundaries without an explicit reference.
- Prefer unresolved output over unsafe reference guessing.
- Keep rule-based legal analysis independent from LLM APIs.
- Separate retrieval, reranking, evidence expansion, generation and verification responsibilities.
- Maintain backward compatibility with existing retriever interfaces.
