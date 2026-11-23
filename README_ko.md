# tblr Doumi

`tabularray` 패키지의 `tblr` / `longtblr` / `talltblr` 환경용 LaTeX 표 코드를
시각적으로 만들어 주는 PySide6 데스크톱 앱입니다.
마우스와 대화상자로 행, 열, 셀, 병합, 테두리를 편집하면
완성된 LaTeX 코드가 오른쪽 미리보기 창에 즉시 나타납니다.
바로 실행할 수 있는 설치 프로그램(installer)을 내려받을 수 있으므로,
Python을 직접 설치하지 않아도 앱을 사용할 수 있습니다.

- **Windows**: [설치 프로그램 다운로드](https://drive.google.com/file/d/1Cl7mFlCCglPIparzbPl1TaDgJM6YiGxs/view?usp=drive_link)
- **macOS**: [설치 프로그램 다운로드](https://drive.google.com/file/d/1xwYCKApnErLcE-Ukwj_rUf9dQ8CUGysg/view?usp=drive_link)

- **릴리스**: 3.10.3 (2026-08-20)
- **라이선스**: MIT (이 애플리케이션) — 함께 사용되는 라이브러리(PySide6/LGPL, openpyxl/MIT)는
  각각의 라이선스를 따릅니다.
- **언어**: 한국어 / 영어, 앱 안에서 전환할 수 있습니다.

---

## 기능

- **표 편집기**: 스프레드시트처럼 클릭 후 드래그로 셀을 선택할 수 있으며,
  셀 병합/병합 해제, 행/열 삽입/삭제, 복사/잘라내기/붙여넣기(엑셀 방식의
  TSV 호환)를 지원합니다.
- **서식 대화상자**: 가로/세로 정렬, 글꼴 계열/굵기/모양
  (rm/sf/tt, md/bf, up/sl/it), 배경색/글자색, 수식 모드
  (text/math/dmath/imath)를 셀, 행, 열 단위로 GUI에서 설정할 수 있으며,
  해당하는 `\SetCell{...}` 등 LaTeX 옵션이 자동으로 생성됩니다.
- **테두리(선) 설정**: 선택한 범위에 가로선(hline)과 세로선(vline)을 추가할 수 있습니다.
  실선/파선/점선 스타일과 이중선, 굵은 선 옵션을 제공하며,
  편집하는 동안 표 위에 실시간으로 그려집니다.
- **Colspec 관리**: 자동 `natural` / `linewidth` / `X` 모드와
  직접 colspec을 작성하는 수동 모드를 지원하며, 토큰 수가 열 수와
  맞지 않으면 문법 경고를 표시합니다.
- **Long/Tall 표 지원**: `longtblr`, `talltblr`에서 쓰는 바깥 옵션 `[...]`과
  안쪽 추가 설정 `{...}`을 위한 별도의 탭이 있습니다.
- **Excel 가져오기**: `.xlsx` 파일을 열어 값과 셀 병합 구조를 그대로
  가져옵니다.
- **LaTeX 코드 가져오기**: 기존의 `tabularx` / `tblr` / `longtblr` /
  `talltblr` 코드를 붙여넣으면 표, 서식, colspec으로 다시 분석(parsing)합니다.
- **내보내기**:
  - 클립보드로 복사 (F4)
  - 표만 담은 `.tex` 파일 저장 (Ctrl+T)
  - 선택한 문서 클래스(예: `article`, `oblivoir`)를 포함한 독립 실행형
    `.tex` 파일 저장
  - `.csv`로 내보내기
- **PDF 미리보기**: pdflatex / xelatex / lualatex 중에서 골라 표를 실제로
  컴파일한 뒤, 결과를 시스템 기본 PDF 뷰어에서 엽니다. 컴파일에 실패해도
  앱이 종료되지 않고, 로그에서 추린 오류 요약을 보여 줍니다.
- **템플릿 관리자 (F9)**: 현재 표의 상태(서식, 데이터, 구조)를 이름을 붙여
  저장해 두었다가, 나중에 다른 표에도 다시 적용할 수 있습니다.
- **찾기 및 바꾸기**: 표의 셀 또는 설정 편집기(Lines / Row·Col Format /
  Cell Format / Generic) 어디서든 검색할 수 있으며, 다음/이전 이동(F3, Shift+F3)과
  정규식 기반의 모두 바꾸기를 지원합니다.
- **다국어(i18n) 지원**: 메뉴 `🌐 Language / 언어`에서 한국어와 영어를
  전환할 수 있습니다. 가볍고 독립적인 사전(`i18n.py`)을 기반으로 하므로
  Qt Linguist나 `.ts`/`.qm` 빌드 과정이 필요 없습니다.

---

## 요구 사항

| 항목 | 버전 / 비고 |
|---|---|
| Python | 3.9 이상 권장 |
| [PySide6](https://pypi.org/project/PySide6/) | Qt6 바인딩 (GUI) |
| [openpyxl](https://pypi.org/project/openpyxl/) | Excel (.xlsx) 가져오기 |
| TeX 배포판 (선택) | PDF 미리보기 기능에만 필요 (TeX Live / MacTeX / MiKTeX 등) — `pdflatex`/`xelatex`/`lualatex`가 PATH에 있어야 함 |
| LaTeX `tabularray` 패키지 | 생성된 코드를 실제로 컴파일하려면 `.tex` 문서에서 필요 |

PDF 미리보기는 선택 기능입니다. 편집, 코드 생성, 내보내기는 TeX 배포판이
설치되어 있지 않아도 모두 정상적으로 동작합니다.

---

## 설치

```bash
pip install PySide6 openpyxl
```

`requirements.txt`를 사용한다면 다음과 같이 작성합니다.

```
PySide6
openpyxl
```

```bash
pip install -r requirements.txt
```

---

## 프로젝트 구조

```
project-root/
├── main.py                     # 진입점
├── tblrdoumi.ico                # 앱 아이콘 (실행 시와 PyInstaller에서 사용)
└── tblrDoumi/
    ├── __init__.py               # (없다면 빈 파일을 추가하세요)
    ├── i18n.py                   # 한/영 문자열 표와 tr() 헬퍼
    ├── ColorPalette.py            # 색상 선택 팔레트 위젯
    ├── Dialogs.py                 # 대화상자 (Colspec / 서식 / 템플릿 / 찾기·바꾸기 등)
    ├── TableBorderDelegate.py     # 표 테두리를 그리는 QStyledItemDelegate
    └── TblrGenerator.py           # 메인 창과 애플리케이션 로직
```

## 실행

```bash
python main.py
```

`main.py`가 이 앱에서 실제로 사용하는 진입점입니다.

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

이 진입점에 대해 알아 둘 점은 다음과 같습니다.

- **UI 스타일**: OS 기본 스타일 대신 `Fusion` 스타일을 강제로 사용하므로,
  Windows/macOS/Linux에서 앱이 일관된 모습으로 보입니다.
- **앱 아이콘**: `resource_path("tblrdoumi.ico")`로 불러옵니다. 개발 중에는
  `tblrdoumi.ico`를 `main.py`와 같은 위치에 두고, PyInstaller로 패키징할 때는
  데이터 파일로 포함되도록 해야 합니다(아래 참고).
- **연결 프로그램(Open with) 지원**: `.tblr` 파일 경로가 첫 번째 명령줄 인자로
  전달되면(예: "연결 프로그램" 메뉴나 등록된 파일 형식 더블클릭) 시작할 때
  자동으로 불러옵니다. 파일 없음, 잘못된 JSON, 그 밖의 불러오기 오류는
  각각 별도의 메시지 상자로 알려 주며 앱이 종료되지 않습니다.

### PyInstaller로 패키징하기

`resource_path()` 헬퍼는 PyInstaller `--onefile` 빌드를 염두에 두고 작성되었습니다
(PyInstaller가 실행 시 설정하는 임시 압축 해제 폴더인 `sys._MEIPASS`를 확인합니다).
패키징할 때는 `tblrdoumi.ico`를 데이터 파일로 포함해야 하며, Windows에서는
`.exe` 자체에도 아이콘이 들어가도록 `--icon`으로도 지정합니다. 예:

```bash
pyinstaller --onefile --windowed --icon=tblrdoumi.ico --add-data "tblrdoumi.ico;." main.py
```

(macOS/Linux에서는 세미콜론 대신 콜론을 써서 `--add-data "tblrdoumi.ico:."`로 지정합니다.)

---

## 기본 사용 순서

1. **표 크기 설정**: 오른쪽 설정 패널의 `Table Size`에서 행(R)과 열(C)의 수를
   입력한 뒤 `Apply`를 누릅니다.
2. **셀 편집**: 표에서 셀을 클릭하고 왼쪽 아래의 셀 편집기에 입력합니다.
3. **서식 적용**: 셀/행/열을 선택한 뒤 오른쪽 클릭 메뉴나 단축키
   (F5/F6/Ctrl+F6)로 정렬, 색상, 글꼴, 수식 모드를 설정하는 서식 대화상자를 엽니다.
4. **테두리 추가**: 원하는 행/열 경계를 선택하고 `Alt+H`(가로) 또는
   `Alt+V`(세로)를 눌러 선 옵션을 설정합니다.
5. **colspec 확인**: 자동 모드(`natural`/`linewidth`)를 쓰거나, `manual` 모드로
   바꾼 뒤 `Edit Colspec` 버튼으로 직접 편집합니다.
6. **결과 확인**: 완성된 LaTeX 코드가 오른쪽 출력 창에서 실시간으로 갱신됩니다.
   `📋 Copy to Clipboard`(F4) 또는 `📄 Export .tex`로 저장할 수 있습니다.
7. **(선택) PDF로 미리보기**: 컴파일러 엔진을 고르고 `🔍 PDF Preview`
   (Alt+Shift+P)를 누르면 실제로 컴파일하여 PDF 뷰어에서 엽니다.

---

## 키보드 단축키

### macOS

| 단축키 | 동작 |
|---|---|
| F4 | LaTeX 코드를 클립보드로 복사 |
| ⌘S / ⌘O / ⌘⇧S | 저장 / 열기 / 다른 이름으로 저장 |
| ⌘N / ⌘Q | 모두 초기화 / 종료 |
| ⌘T / ⌘⇧T | .tex 내보내기(표만) / .tex 내보내기(oblivoir) |
| ⌥P / ⌥⇧P | 미리보기용 내보내기 / PDF 미리보기 |
| F2 | LaTeX tblr 코드 가져오기 |
| ESC | 표로 포커스 이동 |
| ⌘F / F3 / ⇧F3 | 텍스트 찾기 / 다음 찾기 / 이전 찾기 |
| ⌘G / ⌘⇧G | 행으로 이동 |
| ⌥⇧G | 셀로 이동 |
| ⌘E | (셀 편집 중) 셀 편집기로 이동 |
| PgUp/PgDn, Home/End, ⌘Home/⌘End | 페이지 / 열 / 행 이동 |
| F10 / F12 | 수동 colspec 복사 / colspec 편집 |
| ⌘= | 설정 패널 표시/숨김 |
| ⌘Enter / ⌘Del | 행 추가 / 행 삭제 |
| F7 / F8 | 열 추가 / 열 삭제 |
| ⌘M / ⌘U | 셀 병합 / 셀 병합 해제 |
| F5 / ⇧F5 | 셀 설정 / 셀 고급 설정 |
| F6 / ⌘F6 | 행 설정 / 열 설정 |
| ⇧F6 / ⌘⇧F6 | 행 고급 설정 / 열 고급 설정 |
| ⌃H / ⌃V | 가로선 설정 / 세로선 설정 (⇧=+Z) |
| ⌃Z / ⇧⌃Z | 마지막 가로선 / 마지막 세로선 |
| F9 | 템플릿 관리자 |

### Windows / Linux

| 단축키 | 동작 |
|---|---|
| F4 | LaTeX 코드를 클립보드로 복사 |
| Ctrl+S / Ctrl+O / Ctrl+Shift+S | 저장 / 열기 / 다른 이름으로 저장 |
| Ctrl+N / Ctrl+Q | 모두 초기화 / 종료 |
| Ctrl+T / Ctrl+Shift+T | .tex 내보내기(표만) / .tex 내보내기(oblivoir) |
| Alt+P / Shift+Alt+P | 미리보기용 내보내기 / PDF 미리보기 |
| F2 | LaTeX tblr 코드 가져오기 |
| ESC | 표로 포커스 이동 |
| Ctrl+F / F3 / Shift+F3 | 텍스트 찾기 / 다음 찾기 / 이전 찾기 |
| Ctrl+H | 모두 바꾸기 |
| Ctrl+G / Ctrl+Shift+G | 행으로 이동 / 열로 이동 |
| Shift+Alt+G | 셀로 이동 |
| Ctrl+Ins | (셀 편집 중) 셀 편집기로 이동 |
| PgUp/PgDn, Home/End, Ctrl+Home/Ctrl+End | 페이지 / 열 / 행 이동 |
| F10 / F12 | 수동 colspec 복사 / colspec 편집 |
| Ctrl+= | 설정 패널 표시/숨김 |
| Ctrl+Enter / Ctrl+Del | 행 추가 / 행 삭제 |
| F7 / F8 | 열 추가 / 열 삭제 |
| Ctrl+M / Ctrl+U | 셀 병합 / 셀 병합 해제 |
| F5 / Shift+F5 | 셀 설정 / 셀 고급 설정 |
| F6 / Ctrl+F6 | 행 설정 / 열 설정 |
| Shift+F6 / Shift+Ctrl+F6 | 행 고급 설정 / 열 고급 설정 |
| Alt+H / Alt+V | 가로선 설정 / 세로선 설정 (Shift=+Z) |
| Alt+Z / Shift+Alt+Z | 마지막 가로선 / 마지막 세로선 |
| F9 | 템플릿 관리자 |

> 같은 요약을 `F1` 키나 메인 메뉴의 `⌨️ Keyboard Shortcuts` 항목에서
> 언제든지 볼 수 있습니다.

---

## 다국어 지원 (i18n)

- 메인 메뉴 → **🌐 Language / 언어** → `한국어` 또는 `English`를 선택합니다.
- 선택한 언어는 `QSettings`(조직: `ktug.org`, 애플리케이션: `tblrDoumi`)에
  저장되어 재시작 후에도 유지됩니다.
- **참고**: 현재 구현은 모든 위젯을 즉시 다시 번역하지는 않으므로, 언어 변경이
  완전히 적용되려면 **재시작이 필요합니다**(전환할 때 앱이 안내 메시지를 표시합니다).
- 새 언어를 추가하거나 기존 문구를 수정하려면 `tblrDoumi/i18n.py`의 `STRINGS`
  사전(또는 `register("key", "한국어 문구", "English text")` 호출)만
  수정하면 됩니다. `.ts`/`.qm` 컴파일 과정은 필요 없습니다.

---

## 알려진 제한 사항

- PDF 미리보기는 로컬에 설치된 TeX 배포판을 호출하여 동작합니다.
  `pdflatex`(또는 선택한 엔진)가 PATH에 없으면 경고가 표시되고 해당 기능은
  사용할 수 없습니다. 이 경우 `📥 Export .tex > preview`로 `.tex` 파일만
  저장한 뒤 직접 컴파일하세요.
- 위에서 설명했듯이, 언어 전환이 완전히 적용되려면 앱을 재시작해야 합니다.
- 표에 사용 중인 TeX 배포판에서 쓸 수 없는 사용자 매크로나 색상/글꼴 명령이
  포함되어 있으면 미리보기 컴파일이 실패할 수 있으며, 이때도 앱은 종료되지
  않습니다. 오류 요약과 함께, 직접 확인할 수 있도록 `_tblr_prv.tex` /
  `_tblr_prv.log`의 위치가 표시됩니다.
- `main.py`의 파일 불러오기 오류 대화상자("File Error" / "Error")는 현재
  한국어로 하드코딩되어 있으며, 앱의 다른 부분에서 쓰는 `i18n.py` 번역 체계에
  아직 연결되어 있지 않습니다. 이 대화상자도 언어 설정을 따르게 하려면,
  나머지 코드베이스를 변환한 것과 같은 방식으로 `tr(...)`을 거치도록 바꾸면 됩니다.

---

## 라이선스

이 애플리케이션은 MIT 라이선스로 배포됩니다. 함께 사용되는 라이브러리
(PySide6, openpyxl 등)는 각각의 라이선스에 따라 배포됩니다.
