# Vietnamese Legal RAG

## Data normalization

Normalize raw legal JSON from `data/raw/*.json` into stable intermediate files in `data/normalized/`:

```powershell
python apps/api/scripts/normalize_documents.py --input-dir data/raw --output-dir data/normalized
```

Use `--overwrite` to replace existing normalized files. This stage only produces normalized JSON; it does not create embeddings, retrieval chunks, BM25 indexes, reranking data, or Qdrant ingestion.

## Build retrieval chunks

Build parent-child retrieval JSONL files from normalized data:

```powershell
python apps/api/scripts/build_chunks.py --overwrite
```

This stage creates `data/retrieval/*_chunks.jsonl` and per-law reports without generating vectors or connecting to Qdrant.

## Dense retrieval evaluation

`data/evaluation/dense_eval.jsonl` is a gold-standard dataset for dense legal retrieval evaluation. Gold chunk IDs are selected from `data/retrieval/*_chunks.jsonl` by reading the legal content first; they must not be generated from retrieval top-k results.

Validate the dataset before running retrieval metrics:

```powershell
python .\apps\api\scripts\validate_dense_eval_dataset.py
```

Run a quick dense retrieval evaluation sample against the configured Qdrant collection and embedding model:

```powershell
python .\apps\api\scripts\evaluate_dense_retrieval.py --limit 5
```
