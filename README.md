# AI Corpus Lab

Experimental Python workflows for building inspectable text corpora from OCR and TXT sources, with a focus on Portuguese historical material.

The repository documents a learning and research process rather than a finished software package. Its current tools cover corpus inventory, sentence extraction, metadata assembly and overlapping text chunks for later semantic search or retrieval-augmented generation (RAG).

## What is included

- corpus and token counting;
- sentence extraction with common Portuguese abbreviations;
- construction of a JSON master corpus from CSV metadata and TXT documents;
- overlapping text chunks that preserve document metadata;
- methodology notes and a public progress log;
- a small neutral text sample for local experiments.

## Repository structure

```text
ai-corpus-lab/
|-- docs/       Methodology and progress notes
|-- examples/   Small, non-sensitive input samples
|-- scripts/    Standalone corpus-processing scripts
|-- tests/      Automated checks for reusable functions
`-- README.md
```

Raw research corpora and generated outputs are deliberately not included. Before publishing source material, verify copyright, privacy and archival conditions.

## Quick start

Requirements:

- Python 3.10 or newer;
- `tiktoken` only for the optional model-token count.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

The scripts currently use paths relative to the directory from which they are run. Copy a small input into a separate working directory, then invoke the required script from there.

Examples:

```bash
python scripts/count_corpus.py examples
python scripts/contador.py examples/sample_text.txt
python scripts/criar_corpus_mestre.py --metadata metadados_corpus_revisto.csv
python scripts/criar_chunks.py --input corpus_mestre.json --output corpus_chunks.json
```

Run the automated checks with:

```bash
python -m unittest discover -s tests -v
```

## Data model

`criar_corpus_mestre.py` combines one metadata row with one TXT document. The resulting JSON records retain identifiers, title, date, interpretative period, genre, themes, source, notes and the original text.

`criar_chunks.py` produces overlapping fragments while carrying the relevant document metadata into every chunk. This keeps retrieval results traceable to their source document.

## Project status

Active experimental work. The next priorities are:

1. make every script independent of the current working directory;
2. add fixtures and tests for sentence extraction and metadata validation;
3. define a documented metadata schema;
4. add semantic indexing and retrieval experiments;
5. record evaluation criteria for retrieval quality.

See [the methodology](docs/metodologia.md) and [progress log](docs/progress_log.md) for additional context.

## Responsible use

- keep raw and processed data separate;
- preserve provenance and metadata;
- do not commit private, copyrighted or confidential corpora;
- inspect retrieval context before relying on generated analysis;
- treat OCR cleanup and automated metadata as reviewable transformations.

## License

No open-source license has been selected yet. Until one is added, copyright remains with the repository owner and reuse is not automatically granted.
