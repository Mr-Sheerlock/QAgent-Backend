# QAgent Backend

A compact project implementing a custom Vector Database that also feeds a Retrieval-Augmented Generation (RAG) pipeline built around Mixtral 8x7B. The system automates unit test generation, bug report creation, and code repair by using high-precision semantic search over curated code–test pairs.

## Highlights


- Custom multilingual Vector Database (Python / Java / extensible) for semantic code-test indexing.
- Advanced indexing strategies: DiskANN, IVF, HNSW for fast, accurate nearest-neighbor search.
- Dataset mining pipeline that curated a high-quality corpus of code–test pairs (1.3M examples).
- Extended to use Retrieval-Augmented Generation (RAG) using Mixtral 8x7B for code-aware generation.

## Results

- Recall: 93.5%
- False-positive rate: 7%

## Architecture & Tech

- Vector store: Custom implementation (multilingual) with pluggable index backends
- Indexing: DiskANN, IVF, HNSW
- Data pipeline: automated dataset mining and quality filters to collect reliable code–test pairs
- LLM: Mixtral 8x7B

## Usage (high level)

1. Ingest code and test artifacts into the Vector DB.
2. Use semantic search to retrieve relevant code–test pairs for a target snippet.
3. (Optionally) Feed retrieved context to Mixtral 8x7B to generate unit tests, bug reports, or repair patches.

## Data & Quality

- Curated corpus: ~1.3M high-value code–test pairs collected via dataset-mining and quality heuristics.
- Quality focus: source provenance, test validity checks, and deduplication to improve signal-to-noise ratio.
