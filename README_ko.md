# tblr 도우미 (tblr Doumi)

`tabularray` 패키지의 `tblr` / `longtblr` / `talltblr` 환경을 위한 LaTeX 표 코드를
GUI에서 시각적으로 편집하고 생성하는 PySide6 데스크톱 앱입니다.
행/열/셀 서식, 병합, 괘선(테두리), colspec 등을 마우스와 다이얼로그로 조작하면
오른쪽 미리보기 창에 완성된 LaTeX 코드가 즉시 만들어집니다.

- **Release**: 3.10.3 (2026-08-20)
- **License**: MIT (앱 자체) — 사용하는 라이브러리(PySide6/LGPL, openpyxl/MIT)는 각자의 라이선스를 따릅니다.
- **언어**: 한국어 / English (앱 내에서 전환 가능)

---

## 주요 기능

- **표 편집기**: 스프레드시트처럼 셀을 클릭·드래그로 선택하고, 셀 병합/해제,
  행·열 추가/삭제, 텍스트 붙여넣기/잘라내기/복사(Excel 스타일 TSV 호환)를 지원합니다.
- **서식 다이얼로그**: 셀/행/열 단위로 정렬(가로/세로), 폰트(rm/sf/tt, md/bf, up/sl/it),
  배경색·글자색, 수식 모드(text/math/dmath/imath)를 GUI로 설정하면
  `\SetCell{...}` 등 해당 LaTeX 옵션 문자열이 자동으로 만들어집니다.
- **괘선(테두리) 설정**: 가로선(hline)·세로선(vline)을 범위 지정으로 추가하고,
  solid/dashed/dotted, double, thick 옵션을 지원하며 표 위에 실시간으로 미리 그려줍니다.
- **Colspec 관리**: `natural` / `linewidth` / `X` 등 자동 계산 모드와, 직접 입력하는
  manual 모드를 모두 지원하며, 열 개수와 맞지 않을 때 문법 경고를 표시합니다.
- **Long/Tall 표 지원**: `longtblr`, `talltblr` 환경의 바깥쪽 옵션([...])과
  안쪽 추가 설정({...})을 별도 탭에서 편집할 수 있습니다.
- **Excel 가져오기**: `.xlsx` 파일을 열어 값과 병합 정보를 그대로 표로 불러옵니다.
- **LaTeX 코드 가져오기**: 기존 `tabularx` / `tblr` / `longtblr` / `talltblr` 코드를
  붙여넣으면 파싱해서 표·서식·colspec으로 역변환합니다.
- **내보내기**:
  - 클립보드로 복사 (F4)
  - 표만 담은 `.tex` 파일로 저장 (Ctrl+T)
  - `article` / `oblivoir` 등 문서 클래스를 포함한 독립 실행 가능한 `.tex` 파일로 저장
  - `.csv` 내보내기
- **PDF 미리보기**: pdflatex / xelatex / lualatex 중 선택해 실제로 컴파일한 뒤
  기본 PDF 뷰어로 열어줍니다. 실패해도 앱이 죽지 않고 로그에서 에러 요약만 보여줍니다.
- **템플릿 관리자 (F9)**: 현재 표 상태(서식·데이터·구조)를 이름 붙여 저장했다가
  나중에 다시 불러오거나 다른 표에 적용할 수 있습니다.
- **찾기/바꾸기**: 표 셀과 각 설정 에디터(Lines / Row·Col Format / Cell Format / Generic)
  양쪽 모두에서 텍스트 찾기(F3, Shift+F3)와 정규식 지원 모두 바꾸기를 제공합니다.
- **다국어(i18n) 지원**: 상단 메뉴 `🌐 Language / 언어`에서 한국어 ↔ English 전환.
  가벼운 자체 딕셔너리 기반(`i18n.py`)으로 동작하며, Qt Linguist 같은 별도
  빌드 도구가 필요 없습니다.

---

## 요구 사항

| 항목 | 버전/비고 |
|---|---|
| Python | 3.9 이상 권장 |
| [PySide6](https://pypi.org/project/PySide6/) | Qt6 바인딩 (GUI) |
| [openpyxl](https://pypi.org/project/openpyxl/) | Excel(.xlsx) 가져오기 |
| TeX 배포판 (선택) | PDF 미리보기 기능을 쓰려면 필요 (TeX Live / MacTeX / MiKTeX 등, `pdflatex`/`xelatex`/`lualatex` 가 PATH에 등록되어 있어야 함) |
| `tabularray` LaTeX 패키지 | 생성된 코드를 실제로 컴파일하려면 문서에 `\usepackage{tabularray}` 필요 |

PDF 미리보기는 선택 기능이라, TeX 배포판이 없어도 코드 생성/편집/내보내기는 모두 정상 동작합니다.

---

## 설치

```bash
pip install PySide6 openpyxl
```

또는 프로젝트 루트에 `requirements.txt`를 두고 관리하는 경우:

```
PySide6
openpyxl
```

```bash
pip install -r requirements.txt
```

---

## 실행

이 저장소는 `tblrDoumi` 패키지 형태로 구성되어 있습니다.

```
프로젝트-루트/
└── tblrDoumi/
    ├── __init__.py          # (없다면 빈 파일로 하나 만들어 주세요)
    ├── i18n.py               # 다국어(ko/en) 문자열 테이블 및 tr() 헬퍼
    ├── ColorPalette.py        # 색상 선택 팔레트 위젯
    ├── Dialogs.py             # 각종 다이얼로그 (Colspec/서식/템플릿/찾기-바꾸기 등)
    ├── TableBorderDelegate.py # 표 괘선을 그리는 QStyledItemDelegate
    └── TblrGenerator.py       # 메인 윈도우 및 전체 애플리케이션 로직
```

`tblrDoumi` 패키지를 import할 수 있는 위치에서, 아래와 같이 `QApplication`을 만들고
`TblrGenerator` 메인 윈도우를 띄우는 짧은 실행 스크립트(`main.py`)를 프로젝트 루트에
두고 실행하는 구조를 권장합니다.

```python
# main.py
import sys
from PySide6.QtWidgets import QApplication
from tblrDoumi.TblrGenerator import TblrGenerator

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TblrGenerator()
    window.show()
    sys.exit(app.exec())
```

```bash
python main.py
```

> 이미 별도의 진입점 스크립트를 갖고 계시다면 위 예시는 참고만 하시고 기존 스크립트를 그대로 쓰시면 됩니다.

---

## 기본 사용 흐름

1. **표 크기 지정**: 오른쪽 설정 패널의 `Table Size`에서 행(R)·열(C)을 입력하고 `적용`.
2. **셀 편집**: 표에서 셀을 클릭하면 하단 좌측 셀 에디터에서 내용을 입력/수정합니다.
3. **서식 지정**: 셀/행/열을 선택한 뒤 우클릭 메뉴 또는 단축키(F5/F6/Ctrl+F6)로
   서식 다이얼로그를 열어 정렬·색상·폰트·수식 모드를 지정합니다.
4. **괘선 지정**: 원하는 행/열 경계를 선택하고 `Alt+H`(가로) / `Alt+V`(세로)로
   괘선 옵션을 지정합니다.
5. **Colspec 확인**: 자동(`natural`/`linewidth`) 모드를 쓰거나, `manual` 모드로 바꾼 뒤
   `colspec 편집` 버튼으로 직접 입력할 수 있습니다.
6. **결과 확인**: 오른쪽 출력창에 완성된 LaTeX 코드가 실시간으로 갱신됩니다.
   `📋 클립보드로 복사`(F4)로 바로 복사하거나, `📄 tex 내보내기`로 파일로 저장합니다.
7. **(선택) PDF로 미리보기**: 컴파일 엔진을 고른 뒤 `🔍 PDF 미리보기`(Alt+Shift+P)를
   누르면 실제로 컴파일해서 PDF 뷰어로 열어줍니다.

---

## 단축키

### macOS

| 단축키 | 기능 |
|---|---|
| F4 | LaTeX 코드 클립보드로 복사 |
| ⌘S / ⌘O / ⌘⇧S | 저장 / 불러오기 / 새 이름으로 저장 |
| ⌘N / ⌘Q | 모든 작업 초기화 / 종료 |
| ⌘T / ⌘⇧T | tex 내보내기(표만) / tex 내보내기(oblivoir) |
| ⌥P / ⌥⇧P | 미리보기용으로 내보내기 / PDF 미리보기 |
| F2 | LaTeX tblr 코드 가져오기 |
| ESC | 테이블 영역으로 포커스 이동 |
| ⌘F / F3 / ⇧F3 | 텍스트 찾기 / 다음 찾기 / 뒤로 찾기 |
| ⌘G / ⌘⇧G | 행으로 가기 |
| ⌥⇧G | 셀 찾아가기 |
| ⌘E | (셀 입력 중) 셀 편집기로 즉시 이동 |
| PgUp/PgDn, Home/End, ⌘Home/⌘End | 페이지·행·열 이동 |
| F10 / F12 | manual colspec 복사 / colspec 편집 |
| ⌘= | 설정 패널 토글 |
| ⌘Enter / ⌘Del | 행 추가 / 행 삭제 |
| F7 / F8 | 열 추가 / 열 삭제 |
| ⌘M / ⌘U | 셀 병합 / 병합 해제 |
| F5 / ⇧F5 | 셀 설정 / 고급 셀 설정 |
| F6 / ⌘F6 | 행 설정 / 열 설정 |
| ⇧F6 / ⌘⇧F6 | 고급 행 설정 / 고급 열 설정 |
| ⌃H / ⌃V | 가로선 / 세로선 설정 (⇧=+Z) |
| ⌃Z / ⇧⌃Z | 마지막 가로선 / 마지막 세로선 |
| F9 | 템플릿 관리자 |

### Windows / Linux

| 단축키 | 기능 |
|---|---|
| F4 | LaTeX 코드 클립보드로 복사 |
| Ctrl+S / Ctrl+O / Ctrl+Shift+S | 저장 / 불러오기 / 새 이름으로 저장 |
| Ctrl+N / Ctrl+Q | 모든 작업 초기화 / 종료 |
| Ctrl+T / Ctrl+Shift+T | tex 내보내기(표만) / tex 내보내기(oblivoir) |
| Alt+P / Shift+Alt+P | 미리보기용으로 내보내기 / PDF 미리보기 |
| F2 | LaTeX tblr 코드 가져오기 |
| ESC | 테이블 영역으로 포커스 이동 |
| Ctrl+F / F3 / Shift+F3 | 텍스트 찾기 / 다음 찾기 / 뒤로 찾기 |
| Ctrl+H | 모두 바꾸기 |
| Ctrl+G / Ctrl+Shift+G | 행으로 가기 / 열로 가기 |
| Shift+Alt+G | 셀 찾아가기 |
| Ctrl+Ins | (셀 입력 중) 셀 편집기로 즉시 이동 |
| PgUp/PgDn, Home/End, Ctrl+Home/Ctrl+End | 페이지·행·열 이동 |
| F10 / F12 | manual colspec 복사 / colspec 편집 |
| Ctrl+= | 설정 패널 토글 |
| Ctrl+Enter / Ctrl+Del | 행 추가 / 행 삭제 |
| F7 / F8 | 열 추가 / 열 삭제 |
| Ctrl+M / Ctrl+U | 셀 병합 / 병합 해제 |
| F5 / Shift+F5 | 셀 설정 / 고급 셀 설정 |
| F6 / Ctrl+F6 | 행 설정 / 열 설정 |
| Shift+F6 / Shift+Ctrl+F6 | 고급 행 설정 / 고급 열 설정 |
| Alt+H / Alt+V | 가로선 / 세로선 설정 (Shift=+Z) |
| Alt+Z / Shift+Alt+Z | 마지막 가로선 / 마지막 세로선 |
| F9 | 템플릿 관리자 |

> 앱 내 `F1` 또는 메인 메뉴 `⌨️ 단축키 요약`에서 언제든 같은 내용을 다시 볼 수 있습니다.

---

## 다국어(i18n)

- 메인 메뉴 → **🌐 Language / 언어** → `한국어` 또는 `English` 선택.
- 선택한 언어는 `QSettings`(조직: `ktug.org`, 앱: `tblrDoumi`)에 저장되어 다음 실행에도 유지됩니다.
- **주의**: 지금 방식은 실행 중 모든 위젯을 실시간으로 다시 그리지는 않으므로,
  언어를 바꾼 뒤 전체 화면에 완전히 반영하려면 **앱을 재시작**해야 합니다
  (전환 시 안내 메시지가 표시됩니다).
- 새 언어를 추가하거나 문구를 수정하려면 `tblrDoumi/i18n.py`의 `STRINGS` 딕셔너리
  (또는 `register("키", "한국어 문구", "English phrase")` 호출부)만 편집하면 됩니다.
  별도의 `.ts`/`.qm` 컴파일 과정이 필요 없습니다.

---

## 알려진 제한 사항

- PDF 미리보기는 로컬에 설치된 TeX 배포판을 그대로 호출하므로, `pdflatex` 등 실행 파일이
  PATH에 없으면 안내 메시지와 함께 기능이 비활성화됩니다. 이 경우 `📥 tex 내보내기 > preview`로
  `.tex` 파일만 저장한 뒤 직접 컴파일해서 확인할 수 있습니다.
- 언어 전환은 위에서 설명한 대로 재시작이 필요한 부분이 있습니다.
- 표 안에서 사용하는 사용자 정의 매크로/색상/폰트 명령이 TeX 배포판에 없으면 미리보기
  컴파일이 실패할 수 있습니다 — 이 경우도 앱이 죽지 않고 실패 로그 요약과
  `_tblr_prv.tex` / `_tblr_prv.log` 파일 위치를 안내합니다.

---

## 라이선스

이 애플리케이션은 MIT License를 따릅니다. 함께 사용되는 라이브러리(PySide6, openpyxl 등)는
각각의 라이선스 조건을 따릅니다.
