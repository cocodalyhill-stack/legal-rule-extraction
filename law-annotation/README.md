# Judicial ratio annotation with OpenRouter

Extract source-grounded annotations from your own PDF or UTF-8 TXT judgments, save a CSV/JSON dataset, and plot doctrinal counts. No cases or annotations are invented. Python 3.11+ recommended.

## Setup and execution

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` locally and put your OpenRouter key after `OPENROUTER_API_KEY=`. Never paste it into source code or chat. `.env`, the virtual environment, input documents, results, and cache are ignored by Git. Set `OPENROUTER_MODEL` or use `--model` to change the model. Put one judgment per file in `documents/`, then run:

```sh
python annotate.py --input documents
```

For the supplied 131-page reader, use the verified manifest. Copy the original PDF into `documents/` without renaming it, then run:

```sh
python annotate.py --input 'documents/2026 - Liebert Intro Course Reader .pdf' --manifest reader_manifest.json
```

The manifest separates eight cases using inclusive, one-based PDF page ranges, excluding the cover, table of contents and footer-only blank separators. It contains only source boundaries, not predetermined legal conclusions. Do not use it for a different edition. For another compilation, make your own manifest with `source` matching the filename and a `cases` array containing `label`, `start_page`, and `end_page`. A directory run otherwise assumes one judgment per file; it cannot reliably split an arbitrary compilation automatically.

This reader concerns reproductive privacy and constitutional rights, so the default categories are constitutional. For company law:

```sh
python annotate.py --input documents --categories company
```

Run extraction and output generation without transmitting source text:

```sh
python annotate.py --input 'documents/2026 - Liebert Intro Course Reader .pdf' --manifest reader_manifest.json --prepare-only
```

## Methodology

1. Extract every page in each case range with pypdf; retain full extracted text under `results/extracted_text/` with PDF page labels and source/text hashes.
2. Preflight the model against OpenRouter's public catalog for structured-output support. Default: `openai/gpt-4.1-mini`, listed by OpenRouter at $0.40 per million input tokens and $1.60 per million output tokens when checked on 11 October 2026. Prices and availability can change. [Model information](https://openrouter.ai/openai/gpt-4.1-mini) and [structured-output documentation](https://openrouter.ai/docs/guides/features/structured-outputs).
3. Send the complete extracted case text to the real `/api/v1/chat/completions` endpoint with a strict JSON schema and providers that support the requested parameters. Validate locally with jsonschema. Embedded document instructions are treated as evidence, never task instructions.
4. Ask for the majority's necessary legal reasoning in 1–3 sentences, a contiguous exact supporting quotation, metadata, category, confidence/explanation, rule status, opinion basis, and ambiguity flags. Missing metadata is null. Rules applied by a court are distinguished from rules established or modified.
5. Check the quotation by exact substring search in the unmodified extracted page text. No whitespace or punctuation normalization hides mismatch. Derive PDF page references programmatically from its location; paragraph references and reporter pinpoints are not guessed. PDF page numbers differ from reporter pagination. A first match can be ambiguous if a quotation occurs more than once; inspect the opinion manually.
6. Save `results/annotations.csv`, `results/annotations.json`, and `results/doctrinal_categories.png`. JSON retains exact strings; CSV cells starting with spreadsheet formula characters are prefixed with an apostrophe for safer spreadsheet opening.

## Full-document handling and failures

No text is silently truncated. The default full-source limit is 240,000 characters. A conservative UTF-8-byte upper bound plus a 6,000-token reserve is also compared with the live model context size. Sparse/empty pages, oversized documents and extraction failures are flagged before a paid request. Increase `--max-source-chars` only with a suitable model after inspecting extraction. This project intentionally flags documents beyond the budget rather than performing potentially lossy chunk-summary synthesis. Scanned PDFs require OCR outside this project; inspect extraction against the PDF before relying on annotations.

HTTP 429/502/503/504 responses receive at most three attempts with bounded backoff. Network failures and malformed/schema-invalid responses are not automatically repeated because the first call may have been billed. A fingerprint of source text, model, schema and prompt version caches valid responses and failed attempts in `.cache/`. Re-running reuses valid responses; use `--retry-failed` to explicitly retry cached failures after troubleshooting. Do not delete the cache casually. Non-success output indicates partial/unprocessed records; exit code 2 means review or configuration work remains. Model-preflight failure makes no paid requests and leaves existing results intact. Output files represent the most recent run, so use `--output` for separate datasets.

## Interpretation and limitations

Each row includes all requested annotation fields plus provenance, processing status, quotation verification, usage and review flags. `not_processed`, `manual_review`, `api_failed`, and `extraction_failed` rows are workflow records, not legal findings. Missing keys produce honest unprocessed outputs. A zero chart headed “No completed LLM annotations” means no classifications were obtained, not that the reader has no cases.

The chart counts one principal category for each successfully annotated judgment, including those whose quotations need review. Do not submit the chart as validated empirical evidence until you have reviewed flagged rows. Categories simplify cases with multiple holdings. Confidence is the model's qualitative assessment, not calibrated probability. An exact quotation establishes textual presence only; it does not establish that the passage is a ratio, belongs to the majority, or supports the legal claim.

The supplied reader explicitly states that judgments were edited and some footnotes, concurrences and dissents omitted. Every reader annotation is therefore flagged for review. Casey's opinion structure and independent holdings require particular care; no automated check can establish majority agreement. Historical ratios are not statements of current law. This tool does not research later treatment, overruling or precedent status beyond the supplied text. Review every ratio, quotation, opinion attribution and page against the source before submission.

Only selected case text is sent to OpenRouter; the key is used solely as an Authorization header. API/provider processing terms apply to that text. Errors do not print server response bodies or authorization values. Do not commit `.env`, copyrighted course material or private judgments. Include reviewed results in a submission only if permitted, selecting them explicitly rather than committing the ignored results directory wholesale.

## Verification in this delivered project

Dependencies were installed and preparation mode was executed against the actual supplied reader. The CSV/JSON and PNG were checked for eight honest unprocessed records and zero completed annotations. No OpenRouter completion success is claimed without a key and an actual live run. See `results/run_report.json` for this run's evidence. The supplied PDF is not bundled in the GitHub project; copy it from its original location using the command above.

Run offline regression checks with `python -m unittest discover -p "test_*.py"`. These checks use mock responses and make no live completion calls.
