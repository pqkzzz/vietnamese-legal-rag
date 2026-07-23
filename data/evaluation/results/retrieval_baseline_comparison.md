# Dense vs BM25 Retrieval Baselines

## Summary metrics

| Metric | Dense | BM25 | BM25 - Dense |
|---|---:|---:|---:|
| hit@1 | 0.7500 | 0.6458 | -0.1042 |
| recall@1 | 0.6632 | 0.5833 | -0.0799 |
| hit@3 | 0.8958 | 0.7708 | -0.1250 |
| recall@3 | 0.8854 | 0.7292 | -0.1562 |
| hit@5 | 0.9375 | 0.8958 | -0.0417 |
| recall@5 | 0.9271 | 0.8542 | -0.0729 |
| hit@10 | 0.9792 | 0.9167 | -0.0625 |
| recall@10 | 0.9688 | 0.8958 | -0.0729 |
| mrr@10 | 0.8285 | 0.7255 | -0.1030 |
| latency_seconds | 0.3446 | 0.0161 | -0.3285 |

## First relevant rank wins

- Dense better: 14
- BM25 better: 7
- Tie: 27

## Important cases

| Case | Dense rank | BM25 rank | Winner |
|---|---:|---:|---|
| eval_001 | 1 | Not found | dense |
| eval_004 | Not found | 1 | sparse |
| eval_008 | 1 | Not found | dense |
| eval_013 | 1 | Not found | dense |
| eval_015 | 8 | 1 | sparse |
| eval_029 | 7 | 1 | sparse |
| eval_033 | 1 | Not found | dense |
