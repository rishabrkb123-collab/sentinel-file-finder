# Sentinel File Finder Manual

## Purpose

Sentinel File Finder is a local Windows application for finding files by meaning, filename fragments, path fragments, and document contents.

## Quick Start

1. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

2. Start the application:

```powershell
python app.py
```

3. Click `Add Folder` to select one or more directories.
4. Click `Rebuild Index`.
5. Enter a search query such as `resume final version` or `python schedule project`.
6. Optionally apply filters.
7. Press `Search`.

## Filters

- `Extension`
- `Type`
- `Path Contains`
- `Min Size (MB)` and `Max Size (MB)`
- `Modified After` and `Modified Before`
- `Only files with extracted content`
- `Result Limit`

## Wildcard Filename Search

- `**sample`
  Match filenames that end with `sample`
- `sample**`
  Match filenames that start with `sample`
- `**sample**`
  Match filenames that contain `sample`
- `**sample**.pdf`
  Match filenames that contain `sample` and only return `.pdf` files

These wildcard queries work across all indexed file types because they match on the indexed filename itself, not only text-extracted documents.

## Supported Content Extraction

- Plain text and source files
- Markdown
- JSON, YAML, XML
- CSV
- PDF
- DOCX
- XLSX

## Packaging

```powershell
.\build_exe.ps1
```

This builds a Windows GUI application under `dist\SentinelFileFinder\`.

## Limitations

- The current version does not monitor folders in real time.
- The current version rebuilds the index instead of incrementally updating it.
- Binary formats outside the supported list are indexed by metadata only.
