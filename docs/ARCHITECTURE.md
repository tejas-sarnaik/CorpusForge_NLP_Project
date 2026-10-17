# Architecture and methodological notes

```text
CSV/JSONL -> schema validation -> normalization -> diagnostics
                                     |                |
                                 MinHash-LSH       regex PII hints
                                     |                |
                              Jaccard verification  |
                                     +--------+-------+
                                              |
                                     split comparison
                                              |
                                    JSON + offline HTML
```

## Exact and near duplicates

The normalizer applies Unicode NFKC, casefolding and whitespace collapse. Exact matches are indexed deterministically. Approximate matching uses character 3-gram features and MinHash LSH (48 hashes, 12 bands of 4). Candidate pairs are **verified** with actual Jaccard similarity:

$$J(A,B)=\frac{|A\cap B|}{|A\cup B|}.$$

The LSH banding step can miss real near-duplicates (false negatives). The similarity threshold filters false candidates, but the metric reflects **surface-form** overlap, not semantic identity. Higher thresholds generally increase precision and lower recall. MinHash-LSH behavior varies with document length, script, and corpus.

## Leakage

Any verified duplicate pair across two *explicit, different* split labels is reported as possible cross-split leakage. This is a hygiene signal, not evidence of model contamination. Carefully inspect legitimate shared boilerplate or intentional overlap.

## Privacy

PII patterns can catch emails, dotted IPv4 addresses and some phone candidates; false positives and false negatives are expected. The audit JSON stores **PII type labels only**, not matched values or original dataset text. IDs are copied from the input and may themselves be sensitive: prefer non-identifying IDs. The optional `redact` command produces a new dataset file and does not overwrite inputs.

## Complexity

Exact indexing is approximately O(n) in the number of examples, excluding text processing. Generating MinHash signatures costs O(sum of unique shingles × 48), while LSH candidate storage and verification depend on bucket collisions; worst-case candidate counts can still be O(n²) for highly repetitive corpora. This version is best suited for small to medium data audits and does not claim billion-row scalability.
