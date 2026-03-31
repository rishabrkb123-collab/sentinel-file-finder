# Architecture

## Overview

Sentinel File Finder uses a local three-layer design:

1. Presentation layer in `sentinel_finder/ui.py`
2. Application/search layer in `sentinel_finder/indexer.py` and `sentinel_finder/search_engine.py`
3. Persistence layer in `sentinel_finder/database.py` and `index_store/search_model.joblib`

## Component Responsibilities

- UI: collects queries, shows results, controls indexing, opens files, exports CSV
- Indexer: scans folders, extracts metadata and content, stores rows, trains TF-IDF model
- Search engine: applies SQL filters, computes similarity, blends ranking signals
- Database: stores roots and indexed file rows

## Design Choices

- Local ML instead of cloud AI: private, free, offline, and easy to ship
- TF-IDF instead of heavier embeddings: lightweight, free, no separate model download
- SQLite: zero-setup persistence for a desktop app

## Future Upgrades

- Real-time file watching
- Incremental re-indexing
- OCR for scanned documents
- Duplicate detection
- Local embedding models
