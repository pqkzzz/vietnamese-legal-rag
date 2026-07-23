# Vietnamese Legal RAG

## Data normalization

Normalize raw legal JSON from `data/raw/*.json` into stable intermediate files in `data/normalized/`:

```powershell
python apps/api/scripts/normalize_documents.py --input-dir data/raw --output-dir data/normalized
```

Use `--overwrite` to replace existing normalized files. This stage only produces normalized JSON; it does not create embeddings, retrieval chunks, BM25 indexes, reranking data, or Qdrant ingestion.
