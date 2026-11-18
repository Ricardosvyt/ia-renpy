# Renplay AI - Demo v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a modular, clean, and production-ready Python repository for Renplay AI in `d:\Projetos-Renplay\inteligência artificial` ready to be pushed to GitHub, accompanied by a Google Colab notebook (`renplay_ai_colab.ipynb`) for training and translation with Qwen3.5-4B, Pixeldrain downloading, continuous game queue, and single-file drop-in patch generation with in-game language selection.

---

### Architecture & Key Units

```
d:\Projetos-Renplay\inteligência artificial\
├── core\
│   ├── __init__.py
│   ├── pixeldrain_downloader.py   # Downloads games via Pixeldrain API with resume & auto-extract
│   ├── queue_manager.py          # JSON/Drive queue for background processing of games
│   ├── renpy_extractor.py        # Scans game/ folder, parses .rpy/.rpyc dialogs & strings
│   ├── tag_protector.py          # Deterministic masking of {tags}, [vars], escapes
│   ├── language_injector.py      # Generates 00_renplay_idiomas.rpy to inject language tab in preferences
│   ├── patch_builder.py          # Builds the single-file drop-in patch (.rpy / .rpa)
│   └── sqlite_memory.py          # SQLite translation memory & correction cache
├── colab\
│   ├── renplay_ai_colab.ipynb    # Organized Jupyter notebook for Colab T4 GPU
│   └── colab_requirements.txt    # Colab environment dependencies
├── templates\
│   └── renplay_language_ui.rpy   # Drop-in Ren'Py screen template for language selection
├── tests\
│   ├── __init__.py
│   ├── test_tag_protector.py     # Verification tests for syntax preservation
│   └── test_patch_builder.py     # Verification tests for single-file patch generation
├── config.py                     # Global paths, language codes, model defaults
├── requirements.txt              # Standard Python dependencies
├── .gitignore                    # Ignore downloaded game zips, extracted folders, temp caches
└── README.md                     # GitHub repository documentation
```

---

### Proposed Tasks

#### Task 1: Environment & Repository Scaffolding
- [ ] Create `.gitignore` to prevent committing game dumps, `.rpa` extractions, `.venv`, or local caches.
- [ ] Create `requirements.txt` and `config.py` with base paths, default language mappings (pt-BR, es, fr, en), and Pixeldrain API endpoints.
- [ ] Create `README.md` with clear instructions on GitHub usage, Colab setup, and single-file patch distribution.

#### Task 2: Pixeldrain Downloader & Queue Manager
- [ ] Implement `core/pixeldrain_downloader.py`:
  - Support `pixeldrain.com/u/{id}` and `pixeldrain.com/api/file/{id}`.
  - Stream download with chunking and progress bar (`tqdm`).
  - Auto-extract `.zip`, `.rar`, and `.7z` into a staging folder.
- [ ] Implement `core/queue_manager.py`:
  - Read/write `fila_jogos.json`.
  - Methods: `add_game(url, name, target_languages)`, `get_next_pending()`, `mark_completed()`, `mark_failed()`.

#### Task 3: Tag Protection & SQLite Memory
- [ ] Implement `core/tag_protector.py`:
  - Protect Ren'Py formatting tags: `{i}`, `{b}`, `{color=...}`, `{size=...}`, `{cps=...}`.
  - Protect variable interpolations: `[variable]`, `%(name)s`, `[persistent.route]`.
  - Protect escape sequences: `\"`, `\n`.
  - Provide `protect(text)` and `restore(translated_text, mask_map)`.
- [ ] Implement `core/sqlite_memory.py`:
  - SQLite database for storing `(original_text, translated_text, language, character, context)`.
  - Exact match lookup and fuzzy matching to reuse existing verified translations.

#### Task 4: Ren'Py Extractor, Language Injector & Patch Builder
- [ ] Implement `core/renpy_extractor.py`:
  - Scan `game/` folder for `.rpy` scripts and dialog lines (`character "dialog"`, `menu:`, `strings:`).
  - Extract translatable units to JSONL format.
- [ ] Implement `core/language_injector.py`:
  - Generate standalone Ren'Py script `00_renplay_idiomas.rpy`.
  - Hooks into `screen preferences` to inject a clean language switcher matching the game's native button styles.
  - Adds hotkey/quick menu toggle for language switching.
- [ ] Implement `core/patch_builder.py`:
  - Merge the translated dialogue blocks (`translate portuguese ...`) and string translations (`translate portuguese strings: ...`) with `00_renplay_idiomas.rpy`.
  - Output ONE single standalone drop-in file: `99_renplay_traducao_ptbr.rpy` (or `.rpa`), ready to drop into `game/`.

#### Task 5: Automated Unit Tests
- [ ] Implement `tests/test_tag_protector.py`: Test preserving complex tags, nested brackets, and quotes.
- [ ] Implement `tests/test_patch_builder.py`: Test generating a valid single-file patch with language screen injection.
- [ ] Run test suite with `python -m unittest discover tests` and verify 100% pass rate.

#### Task 6: Google Colab Notebook
- [ ] Create `colab/renplay_ai_colab.ipynb`:
  - Formatted with structured Markdown sections, badges, and clean headers.
  - Section 1: GPU check (NVIDIA T4 detection and float16 confirmation).
  - Section 2: Git clone repository & Google Drive mount for persistence.
  - Section 3: Queue management (add Pixeldrain links, list queue).
  - Section 4: Load Unsloth Qwen3.5-4B with `dtype=torch.float16`.
  - Section 5: Batch translation pipeline with TagProtector, SQLite memory, and validation.
  - Section 6: Export single-file drop-in patch to Google Drive ready for download.

