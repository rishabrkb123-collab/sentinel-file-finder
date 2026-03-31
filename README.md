# Sentinel File Finder

Sentinel File Finder is a Windows desktop application that builds a local searchable file index and combines metadata filtering, extracted document text, fuzzy matching, and ML-based semantic ranking. It is designed to be stronger than plain filename search while staying free and fully local.

## What It Does

- Indexes one or more folders on Windows.
- Extracts searchable text from `txt`, `md`, `json`, `csv`, `pdf`, `docx`, and `xlsx` files.
- Supports AI-style semantic search using a local TF-IDF ranking model trained on filenames, paths, and extracted file content.
- Adds practical filters for extension, type, path, size range, modification date range, result count, and content availability.
- Lets you open files, reveal them in Explorer, and export search results to CSV.
- Can be packaged into a Windows executable with PyInstaller.

## Stack

| Layer | Technology | Where it is used | Why it is used |
|---|---|---|---|
| Desktop UI | PySide6 | `sentinel_finder/ui.py` | Rich Windows desktop UI toolkit |
| Core language | Python 3.12 | Entire project | Fast iteration and strong local-ML support |
| Search index | SQLite | `sentinel_finder/database.py` | Zero-setup persistent local index |
| ML ranking | scikit-learn TF-IDF | `sentinel_finder/indexer.py`, `sentinel_finder/search_engine.py` | Free local semantic-ish ranking |
| Model persistence | joblib | `sentinel_finder/indexer.py` | Saves the trained search artifacts |
| Content extraction | PyPDF2, python-docx, openpyxl | `sentinel_finder/text_extractors.py` | Extracts searchable text from common documents |
| Packaging | PyInstaller | `build_exe.ps1` | Builds a Windows executable |

## Architecture

See:

- [MANUAL.md](./MANUAL.md)
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- [docs/FLOW_DIAGRAMS.md](./docs/FLOW_DIAGRAMS.md)

## Features

- Natural-language-style file search
- Semantic relevance scoring
- Keyword and fuzzy matching blended into ranking
- Search across filename, full path, and extracted content
- Extension filter
- File type filter
- Path contains filter
- Minimum and maximum size filters
- Modified-after and modified-before filters
- Content-only filter
- Result limit control
- Preview panel
- CSV export
- Open file
- Open containing folder

## Setup

```powershell
python -m pip install -r requirements.txt
python app.py
```

## Windows Batch Launchers

- `install_dependencies.bat`
  Installs all Python dependencies and keeps the terminal open so you can read any errors.
- `start_sentinel_file_finder.bat`
  Starts the desktop application without the usual console flash by relaunching itself hidden.

## Build Windows Executable

```powershell
.\build_exe.ps1
```

The packaged app will be placed in `dist\SentinelFileFinder\`.

## Notes

- The current implementation rebuilds the index from scratch when you click `Rebuild Index`.
- For very large folders, indexing will take longer because content extraction and model training are local.
- The app is fully offline and does not call any cloud AI service.
