# Progress Log

## 2026-08-09

Repository maintenance pass:

- documented setup, structure, responsible data handling and current commands;
- consolidated the public sample under `examples/`;
- moved executable corpus counting code from `docs/` to `scripts/`;
- added command-line paths and validation to the chunking workflow;
- added unit tests and a minimal GitHub Actions workflow.

Next steps:

- add sentence-extraction fixtures for historical Portuguese;
- validate the metadata CSV schema before processing;
- make the remaining scripts accept explicit input and output paths;
- document a small end-to-end corpus example;
- define retrieval-quality evaluation criteria.

## 2026-05-11

Initial public structure created, with corpus-processing scripts, methodology notes and small examples.
