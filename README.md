# tblr Doumi

A PySide6 desktop app for visually building LaTeX table code for the
`tabularray` package's `tblr` / `longtblr` / `talltblr` environments.
Edit rows, columns, cells, merges, and borders with the mouse and dialogs,
and the finished LaTeX code appears instantly in the preview pane on the right.

- **Release**: 3.9.12 (2026-08-08)
- **License**: MIT (this application) — bundled libraries (PySide6/LGPL, openpyxl/MIT)
  are covered by their own licenses.
- **Languages**: Korean / English, switchable from within the app.

---

## Features

- **Table editor**: click-and-drag cell selection like a spreadsheet, with cell
  merge/unmerge, row/column insert/delete, and copy/cut/paste (Excel-style
  TSV compatible).
- **Format dialogs**: set horizontal/vertical alignment, font family/weight/shape
  (rm/sf/tt, md/bf, up/sl/it), background/text color, and math mode
  (text/math/dmath/imath) per cell, row, or column through a GUI — the
  corresponding `\SetCell{...}` and related LaTeX options are generated
  automatically.
- **Border (line) settings**: add horizontal (hline) and vertical (vline)
  rules over a selected range, with solid/dashed/dotted styles plus double
  and thick options, drawn live on top of the table as you edit.
- **Colspec management**: supports automatic `natural` / `linewidth` / `X`
  modes as well as a manual mode for hand-written colspecs, with a syntax
  warning if the token count doesn't match the column count.
- **Long/Tall table support**: separate tabs for the outer options `[...]`
  and inner extra settings `{...}` used by `longtblr` and `talltblr`.
- **Excel import**: open an `.xlsx` file and bring in both values and merged
  cell layout as-is.
- **LaTeX code import**: paste existing `tabularx` / `tblr` / `longtblr` /
  `talltblr` code and it's parsed back into the table, formatting, and colspec.
- **Export**:
  - Copy to clipboard (F4)
  - Save a `.tex` file containing just the table (Ctrl+T)
  - Save a standalone `.tex` file with a chosen document class (e.g. `article`,
    `oblivoir`)
  - Export to `.csv`
- **PDF preview**: pick pdflatex / xelatex / lualatex and compile the table
  for real, then open the result in the system's default PDF viewer. A
  failed compile won't crash the app — it shows a summary of the errors
  from the log instead.
- **Template manager (F9)**: save the current table state (formatting, data,
  structure) under a name and re-apply it later, including to a different table.
- **Find & Replace**: search the table cells or any of the settings editors
  (Lines / Row·Col Format / Cell Format / Generic), with next/previous
  navigation (F3, Shift+F3) and regex-based replace-all.
- **Multilingual (i18n) support**: switch between Korean and English from the
  menu `🌐 Language / 언어`. Built on a lightweight, self-contained
  dictionary (`i18n.py`) — no Qt Linguist or `.ts`/`.qm` build step required.

---

## Requirements

| Item | Version / Notes |
|---|---|
| Python | 3.9+ recommended |
| [PySide6](https://pypi.org/project/PySide6/) | Qt6 bindings (GUI) |
| [openpyxl](https://pypi.org/project/openpyxl/) | Excel (.xlsx) import |
| A TeX distribution (optional) | Needed only for the PDF preview feature (TeX Live / MacTeX / MiKTeX, etc.) — `pdflatex`/`xelatex`/`lualatex` must be on PATH |
| The `tabularray` LaTeX package | Required in your `.tex` document to actually compile the generated code |

PDF preview is an optional feature — editing, code generation, and export all
work fine without a TeX distribution installed.

---

## Installation

```bash
pip install PySide6 openpyxl
```

Or, if you keep a `requirements.txt`:

```
PySide6
openpyxl
```

```bash
pip install -r requirements.txt
```

---

## Project layout

```
project-root/
├── main.py                     # entry point
├── tblrdoumi.ico                # app icon (used at runtime and by PyInstaller)
└── tblrDoumi/
    ├── __init__.py               # (add an empty file here if it's not already present)
    ├── i18n.py                   # ko/en string table and the tr() helper
    ├── ColorPalette.py            # color-picker palette widget
    ├── Dialogs.py                 # dialogs (Colspec / Format / Template / Find-Replace, etc.)
    ├── TableBorderDelegate.py     # QStyledItemDelegate that paints table borders
    └── TblrGenerator.py           # main window and application logic
```

## Running

```bash
python main.py
```

`main.py` is the actual entry point used by this app:

```python
import sys, os
from PySide6.QtWidgets import (QApplication, QMessageBox)
from PySide6.QtGui import QIcon
import json 

from tblrDoumi.TblrGenerator import TblrGenerator

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use the Fusion style instead of the OS default

    icon_path = resource_path("tblrdoumi.ico")
    app.setWindowIcon(QIcon(icon_path))

    window = TblrGenerator()
    window.show()

    # Handle a file passed as a command-line argument
    if len(sys.argv) > 1 and sys.argv[1].endswith(".tblr"):
        filename = sys.argv[1]
        try:
            window.load_table(filename)
        except FileNotFoundError:
            QMessageBox.critical(window, "File Error", f"File not found:\n{filename}")
        except json.JSONDecodeError:
            QMessageBox.critical(window, "File Error", f"Invalid file format:\n{filename}")
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Could not open the file:\n{filename}\n\n{str(e)}")

    sys.exit(app.exec())
```

A few things worth knowing about this entry point:

- **UI style**: forces the `Fusion` style rather than the OS-native one, so the
  app looks consistent across Windows/macOS/Linux.
- **App icon**: loaded via `resource_path("tblrdoumi.ico")`. Keep
  `tblrdoumi.ico` next to `main.py` in development, and make sure it's bundled
  as a data file when packaging with PyInstaller (see below).
- **Open-with support**: if a `.tblr` file path is passed as the first CLI
  argument (e.g. via "Open with..." or double-clicking a registered file
  type), it's loaded automatically on startup. Missing files, malformed JSON,
  and any other load error are each reported with their own message box
  instead of crashing.

### Packaging with PyInstaller

The `resource_path()` helper is written for a PyInstaller `--onefile` build
(it checks `sys._MEIPASS`, the temp extraction folder PyInstaller sets at
runtime). When bundling, make sure `tblrdoumi.ico` is included as a data file
and, on Windows, also pass it as the `--icon` so the `.exe` itself carries
the icon, e.g.:

```bash
pyinstaller --onefile --windowed --icon=tblrdoumi.ico --add-data "tblrdoumi.ico;." main.py
```

(On macOS/Linux use `--add-data "tblrdoumi.ico:."` — colon instead of semicolon.)

---

## Basic workflow

1. **Set the table size**: in the right-hand settings panel, enter rows (R)
   and columns (C) under `Table Size`, then click `Apply`.
2. **Edit cells**: click a cell in the table and type into the cell editor
   at the bottom left.
3. **Apply formatting**: select a cell/row/column, then use the right-click
   menu or a shortcut (F5/F6/Ctrl+F6) to open a format dialog for alignment,
   color, font, and math mode.
4. **Add borders**: select the row/column boundary you want and press
   `Alt+H` (horizontal) or `Alt+V` (vertical) to set line options.
5. **Check the colspec**: use the automatic modes (`natural`/`linewidth`) or
   switch to `manual` mode and edit it directly via the `Edit Colspec` button.
6. **Check the result**: the finished LaTeX code updates live in the output
   pane on the right. Use `📋 Copy to Clipboard` (F4) or `📄 Export .tex` to
   save it.
7. **(Optional) Preview as PDF**: pick a compiler engine and press
   `🔍 PDF Preview` (Alt+Shift+P) to actually compile and open it in a PDF
   viewer.

---

## Keyboard shortcuts

### macOS

| Shortcut | Action |
|---|---|
| F4 | Copy LaTeX code to clipboard |
| ⌘S / ⌘O / ⌘⇧S | Save / Open / Save As |
| ⌘N / ⌘Q | Reset everything / Quit |
| ⌘T / ⌘⇧T | Export .tex (table only) / Export .tex (oblivoir) |
| ⌥P / ⌥⇧P | Export for preview / PDF preview |
| F2 | Import LaTeX tblr code |
| ESC | Move focus to the table |
| ⌘F / F3 / ⇧F3 | Find text / Find next / Find previous |
| ⌘G / ⌘⇧G | Go to row |
| ⌥⇧G | Go to cell |
| ⌘E | (while editing a cell) Jump to the cell editor |
| PgUp/PgDn, Home/End, ⌘Home/⌘End | Page / column / row navigation |
| F10 / F12 | Copy manual colspec / Edit colspec |
| ⌘= | Toggle settings panel |
| ⌘Enter / ⌘Del | Add row / Delete row |
| F7 / F8 | Add column / Delete column |
| ⌘M / ⌘U | Merge cells / Unmerge cells |
| F5 / ⇧F5 | Cell settings / Advanced cell settings |
| F6 / ⌘F6 | Row settings / Column settings |
| ⇧F6 / ⌘⇧F6 | Advanced row settings / Advanced column settings |
| ⌃H / ⌃V | Horizontal line settings / Vertical line settings (⇧=+Z) |
| ⌃Z / ⇧⌃Z | Last horizontal line / Last vertical line |
| F9 | Template manager |

### Windows / Linux

| Shortcut | Action |
|---|---|
| F4 | Copy LaTeX code to clipboard |
| Ctrl+S / Ctrl+O / Ctrl+Shift+S | Save / Open / Save As |
| Ctrl+N / Ctrl+Q | Reset everything / Quit |
| Ctrl+T / Ctrl+Shift+T | Export .tex (table only) / Export .tex (oblivoir) |
| Alt+P / Shift+Alt+P | Export for preview / PDF preview |
| F2 | Import LaTeX tblr code |
| ESC | Move focus to the table |
| Ctrl+F / F3 / Shift+F3 | Find text / Find next / Find previous |
| Ctrl+H | Replace all |
| Ctrl+G / Ctrl+Shift+G | Go to row / Go to column |
| Shift+Alt+G | Go to cell |
| Ctrl+Ins | (while editing a cell) Jump to the cell editor |
| PgUp/PgDn, Home/End, Ctrl+Home/Ctrl+End | Page / column / row navigation |
| F10 / F12 | Copy manual colspec / Edit colspec |
| Ctrl+= | Toggle settings panel |
| Ctrl+Enter / Ctrl+Del | Add row / Delete row |
| F7 / F8 | Add column / Delete column |
| Ctrl+M / Ctrl+U | Merge cells / Unmerge cells |
| F5 / Shift+F5 | Cell settings / Advanced cell settings |
| F6 / Ctrl+F6 | Row settings / Column settings |
| Shift+F6 / Shift+Ctrl+F6 | Advanced row settings / Advanced column settings |
| Alt+H / Alt+V | Horizontal line settings / Vertical line settings (Shift=+Z) |
| Alt+Z / Shift+Alt+Z | Last horizontal line / Last vertical line |
| F9 | Template manager |

> The same summary is available any time from `F1` or the main menu's
> `⌨️ Keyboard Shortcuts` item.

---

## Multilingual support (i18n)

- Main menu → **🌐 Language / 언어** → choose `한국어` (Korean) or `English`.
- The chosen language is saved in `QSettings` (organization: `ktug.org`,
  application: `tblrDoumi`) and persists across restarts.
- **Note**: the current implementation does not live-retranslate every widget
  on the fly, so a **restart is required** for the language change to take
  full effect (the app shows a notice when you switch).
- To add a new language or edit existing text, just edit the `STRINGS`
  dictionary in `tblrDoumi/i18n.py` (or the `register("key", "Korean text",
  "English text")` calls) — no `.ts`/`.qm` compilation step needed.

---

## Known limitations

- PDF preview shells out to whatever TeX distribution is installed locally.
  If `pdflatex` (or the selected engine) isn't on PATH, you'll get a warning
  and the feature is simply unavailable. In that case, use
  `📥 Export .tex > preview` to save just the `.tex` file and compile it
  yourself.
- Language switching requires an app restart to fully apply, as noted above.
- If the table uses custom macros or color/font commands not available in
  your TeX distribution, the preview compile can fail — again, without
  crashing the app. You'll get a summary of the error and the location of
  `_tblr_prv.tex` / `_tblr_prv.log` for manual inspection.
- `main.py`'s file-loading error dialogs ("File Error" / "Error") are
  currently hardcoded in Korean and not yet wired into the `i18n.py`
  translation system used by the rest of the app. If you want these to
  follow the language setting too, they can be routed through `tr(...)`
  the same way the rest of the codebase was converted.

---

## License

This application is distributed under the MIT License. Bundled libraries
(PySide6, openpyxl, etc.) are distributed under their own respective licenses.
