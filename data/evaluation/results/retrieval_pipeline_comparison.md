# Retrieval Pipeline Comparison

## Summary metrics

| Metric | Dense | BM25 | Hybrid | Best pipeline |
|---|---:|---:|---:|---|
| hit@1 | 0.7500 | 0.6458 | 0.7292 | dense |
| recall@1 | 0.6632 | 0.5833 | 0.6562 | dense |
| hit@3 | 0.8958 | 0.7708 | 0.9583 | hybrid |
| recall@3 | 0.8854 | 0.7292 | 0.9132 | hybrid |
| hit@5 | 0.9375 | 0.8958 | 0.9583 | hybrid |
| recall@5 | 0.9271 | 0.8542 | 0.9479 | hybrid |
| hit@10 | 0.9792 | 0.9167 | 1.0000 | hybrid |
| recall@10 | 0.9688 | 0.8958 | 0.9792 | hybrid |
| mrr@10 | 0.8285 | 0.7255 | 0.8386 | hybrid |
| latency_seconds | 0.3446 | 0.0161 | 0.3587 | bm25 |

## First relevant rank wins

- Dense: 4
- BM25: 4
- Hybrid: 3
- Tie: 37

## Important cases

| Case | Dense rank | BM25 rank | Hybrid rank | Winner |
|---|---:|---:|---:|---|
| eval_001 | 1 | Not found | 2 | dense |
| eval_004 | Not found | 1 | 3 | bm25 |
| eval_008 | 1 | Not found | 9 | dense |
| eval_013 | 1 | Not found | 7 | dense |
| eval_015 | 8 | 1 | 2 | bm25 |
| eval_029 | 7 | 1 | 2 | bm25 |
| eval_033 | 1 | Not found | 3 | dense |
