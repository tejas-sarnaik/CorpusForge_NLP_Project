"""Language-agnostic normalization and deterministic near-duplicate search."""
import hashlib
import re
import unicodedata
from collections import defaultdict


def normalize(value):
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"\s+", " ", value).strip()
    return value


def shingles(value, size=3):
    """Character shingles work for space-delimited and non-space-delimited scripts."""
    s = normalize(value)
    if not s:
        return set()
    if len(s) <= size:
        return {s}
    return {s[i:i+size] for i in range(len(s)-size+1)}


def jaccard(a, b):
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _hash64(value):
    return int.from_bytes(hashlib.blake2b(value.encode("utf-8"), digest_size=8).digest(), "big")


def _signature(features, permutations=48):
    if not features:
        return (0,) * permutations
    base = [_hash64(item) for item in features]
    mask = (1 << 64) - 1
    result = []
    for i in range(permutations):
        a = 1103515245 + 104729 * i
        b = 12345 + 1009 * i
        result.append(min(((a * h + b) & mask) for h in base))
    return tuple(result)



def duplicate_pairs(texts, threshold=0.85, ngram=3):
    """Return verified near-duplicate pairs using exact matches + MinHash-LSH candidates.

    LSH is approximate; pairs under the threshold are filtered by exact Jaccard,
    but some pairs above threshold may not be retrieved.
    """
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be in [0,1]")
    features = [shingles(text, ngram) for text in texts]
    candidates = set()
    exact = defaultdict(list)
    for i, value in enumerate(texts):
        canonical = normalize(value)
        for j in exact[canonical]:
            candidates.add((j, i))
        exact[canonical].append(i)
    buckets = defaultdict(list)
    for i, feature in enumerate(features):
        if not feature:
            continue
        signature = _signature(feature)
        for band in range(12):
            key = (band, signature[band*4:(band+1)*4])
            for j in buckets[key]:
                candidates.add((j, i))
            buckets[key].append(i)
    pairs = []
    for i, j in sorted(candidates):
        score = jaccard(features[i], features[j])
        if score >= threshold:
            pairs.append({"left_index": i, "right_index": j, "similarity": round(score, 4),
                          "kind": "exact" if normalize(texts[i]) == normalize(texts[j]) else "near"})
    return pairs
