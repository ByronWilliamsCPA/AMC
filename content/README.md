# Content bundle

The data the app serves, plus the contract and validator that keep it correct.
See [`CONTENT_CONTRACT.md`](CONTENT_CONTRACT.md) for the exact schema and
[`CONSTANTS.md`](CONSTANTS.md) for the scoring, bands, gates, and recommendation
logic.

## Files

| File | Status | What it is |
|------|--------|------------|
| `diag_data.json` | ✅ present | 10 placement diagnostics (218 items), the course ladder, and the catalog. Validates clean against the contract. |
| `amc_data.json` | ⏳ pending | The nine AMC papers (225 problems, ~4 MB, base64 images). Not yet delivered into the repo — see below. |
| `CONTENT_CONTRACT.md` | ✅ | Field-by-field schema for both files and the invariants the loader enforces. |
| `CONSTANTS.md` | ✅ | Scoring modes, performance bands, AMC gates, ladder, pass thresholds, and the recommendation + auto-grader algorithms. |
| `validate_content.py` | ✅ | Contract validator; exits 0 on pass, 1 with a list of problems. |

## `amc_data.json` is pending

The ~4 MB papers file could not be transferred into the build environment (only
inline text reaches the container; large file attachments do not). Drop it in
here and everything downstream is ready:

```bash
# 1. Validate against the contract
python content/validate_content.py content/amc_data.json content/diag_data.json

# 2. Seed it (also seeds diagnostics)
python -m amc.seed --amc content/amc_data.json --diag content/diag_data.json
```

Adding more papers later is the same two steps: conform to the contract shape,
re-run the validator, re-seed. The seed is idempotent, so re-running replaces a
paper's problems rather than duplicating them.

## Note on size

`amc_data.json` embeds images as base64 `data:` URIs, so it is large and changes
rarely. Consider Git LFS for it if the repository's host enforces file-size
limits.
