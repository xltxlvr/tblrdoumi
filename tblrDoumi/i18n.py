# -*- coding: utf-8 -*-
"""
i18n.py — 경량 다국어(i18n) 지원 모듈

Qt Linguist(.ts/.qm) 같은 외부 빌드 도구 없이, 순수 파이썬 딕셔너리만으로
런타임 언어 전환을 지원합니다.

사용법
------
    from tblrDoumi.i18n import tr, set_language, get_language

    self.setWindowTitle(tr("dlg.colspec.title"))
    QMessageBox.warning(self, tr("msg.error.title"), tr("msg.error.body", name=name))

- tr(key, **kwargs)
    STRINGS[현재 언어][key] 문자열을 반환합니다.
    kwargs가 있으면 str.format(**kwargs)로 치환합니다 (예: "{name} 삭제됨" 형태).
    키가 없으면 (개발 중 실수 방지를 위해) 키 문자열 자체를 그대로 반환합니다.

- set_language("ko" | "en")
    현재 언어를 바꿉니다. 이후 호출되는 모든 tr()은 새 언어를 반영합니다.
    (이미 만들어진 위젯의 텍스트는 자동으로 갱신되지 않으므로, 언어를 바꾼 뒤에는
     화면을 다시 그리는 retranslate_ui() 같은 함수를 직접 호출해 주세요.)

- get_language()
    현재 언어 코드("ko" 또는 "en")를 반환합니다.

- LANGUAGE_CHANGED 시그널이 필요하면 QObject 기반 LanguageManager를 사용하세요.
"""

from PySide6.QtCore import QObject, Signal

# 같은 패키지의 __init__.py에서 __version__ 가져오기
try:
    from . import __version__ as VERSION
except ImportError:
    VERSION = "3.10"  # 예외 상황 대비 폴백

DEFAULT_LANGUAGE = "ko"
SUPPORTED_LANGUAGES = ("ko", "en")

# 현재 활성 언어 (모듈 전역 상태)
_current_language = DEFAULT_LANGUAGE


class _LanguageManager(QObject):
    """언어가 바뀔 때 UI를 일괄 갱신하고 싶은 위젯들이 구독할 수 있는 시그널 브로드캐스터."""
    language_changed = Signal(str)


language_manager = _LanguageManager()


def get_language() -> str:
    return _current_language


def set_language(lang: str) -> None:
    global _current_language
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {lang!r} (supported: {SUPPORTED_LANGUAGES})")
    if lang == _current_language:
        return
    _current_language = lang
    language_manager.language_changed.emit(lang)


def tr(key: str, **kwargs) -> str:
    """현재 언어에 맞는 번역 문자열을 반환. 치환 인자가 있으면 .format(**kwargs) 적용."""
    lang_table = STRINGS.get(_current_language, STRINGS[DEFAULT_LANGUAGE])
    text = lang_table.get(key)
    if text is None:
        # 폴백: 기본 언어(ko)에서 찾아보고, 그래도 없으면 키 자체를 노출해서
        # 번역 누락을 눈에 띄게 만든다.
        text = STRINGS[DEFAULT_LANGUAGE].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


# ==========================================================================
# 번역 테이블
# 키 네이밍 규칙: "<파일/영역>.<맥락>.<세부내용>"
#   예) "colorpalette.copy_name"  -> ColorPalette.py, 우클릭 메뉴, 이름 복사
#       "dlg.colspec.title"      -> Dialogs.py, ColspecDialog, 창 제목
#       "main.menu.new"          -> TblrGenerator.py, 메인 메뉴, 새로 시작
# ==========================================================================
STRINGS = {
    "ko": {},
    "en": {},
}


def register(key: str, ko: str, en: str) -> None:
    """번역 테이블에 항목을 등록하는 헬퍼 (이 파일 하단에서 일괄 등록할 때 사용)."""
    STRINGS["ko"][key] = ko
    STRINGS["en"][key] = en


# --------------------------------------------------------------------------
# ColorPalette.py
# --------------------------------------------------------------------------
register("colorpalette.window_title", "Ninecolors Palette", "Ninecolors Palette")
register("colorpalette.copy_name", "색상 이름 복사", "Copy Color Name")
register("colorpalette.copy_rgb", "RGB 값 복사", "Copy RGB Value")
register("colorpalette.copy_cmyk", "CMYK 값 복사", "Copy CMYK Value")

# --------------------------------------------------------------------------
# Dialogs.py — ColspecDialog
# --------------------------------------------------------------------------
register("dlg.colspec.title", "Colspec 편집", "Edit Colspec")
register("dlg.colspec.label", "manual colspec 입력/수정:", "Enter/edit manual colspec:")

# --------------------------------------------------------------------------
# Dialogs.py — FormatDialog
# 서식 종류(kind) 코드는 "cell" / "row" / "col" / "hline" / "vline" 로 통일.
# (예전에는 "셀서식"/"행괘선" 같은 한국어 문자열 자체를 내부 식별자로 썼기 때문에
#  언어를 바꾸면 로직(예: "괘선" in fmt_type)이 깨졌음 -> kind 코드로 분리)
# --------------------------------------------------------------------------
register("fmt.kind.cell", "셀 서식", "Cell Format")
register("fmt.kind.row", "행 서식", "Row Format")
register("fmt.kind.col", "열 서식", "Column Format")
register("fmt.kind.hline", "가로 괘선", "Horizontal Line")
register("fmt.kind.vline", "세로 괘선", "Vertical Line")

register("dlg.format.title", "{label} 입력", "Enter {label}")
register("dlg.format.range_label", "선택 범위: {range_str}", "Selection: {range_str}")

register("dlg.format.line_style.solid", "solid", "solid")
register("dlg.format.line_style.dashed", "dashed", "dashed")
register("dlg.format.line_style.dotted", "dotted", "dotted")
register("dlg.format.double", "double", "double")
register("dlg.format.thick", "thick", "thick")

register("dlg.format.cell_color.bg", "배경색 (bg=)", "Background (bg=)")
register("dlg.format.cell_color.fg", "글자색 (fg=)", "Text Color (fg=)")
register("dlg.format.cell_color.manual", "직접 입력", "Custom")

register("dlg.format.halign.keep", "가로 유지", "Keep Horizontal")
register("dlg.format.halign.center", "가운데 (c)", "Center (c)")
register("dlg.format.halign.left", "왼쪽 (l)", "Left (l)")
register("dlg.format.halign.right", "오른쪽 (r)", "Right (r)")
register("dlg.format.halign.justify", "좌우정렬 (j)", "Justify (j)")

register("dlg.format.valign.keep", "세로 유지", "Keep Vertical")
register("dlg.format.valign.middle", "중간 (m)", "Middle (m)")
register("dlg.format.valign.top", "위 (t)", "Top (t)")
register("dlg.format.valign.bottom", "아래 (b)", "Bottom (b)")
register("dlg.format.valign.head", "머리 (h)", "Head (h)")
register("dlg.format.valign.foot", "바닥 (f)", "Foot (f)")

register("dlg.format.mode.text", "text", "text")
register("dlg.format.mode.math", "math", "math")
register("dlg.format.mode.dmath", "dmath", "dmath")
register("dlg.format.mode.imath", "imath", "imath")

register("dlg.format.font_group", "글꼴", "Font")
register("dlg.format.font.family_label", "글꼴체:", "Family:")
register("dlg.format.font.rm", "로마체 (rm)", "Roman (rm)")
register("dlg.format.font.sf", "고딕체 (sf)", "Sans-serif (sf)")
register("dlg.format.font.tt", "타자기체 (tt)", "Typewriter (tt)")
register("dlg.format.font.series_label", "굵기:", "Weight:")
register("dlg.format.font.md", "보통 (md)", "Medium (md)")
register("dlg.format.font.bf", "굵게 (bf)", "Bold (bf)")
register("dlg.format.font.shape_label", "모양:", "Shape:")
register("dlg.format.font.up", "직립 (up)", "Upright (up)")
register("dlg.format.font.sl", "기울임 (sl)", "Slanted (sl)")
register("dlg.format.font.it", "이탤릭 (it)", "Italic (it)")
register("dlg.format.font.manual_label", "직접 입력:", "Custom:")
register("dlg.format.font.manual_placeholder", r"예: \fontspec{Noto Sans KR}", r"e.g. \fontspec{Noto Sans KR}")

# --------------------------------------------------------------------------
# Dialogs.py — LatexImportDialog
# --------------------------------------------------------------------------
register("dlg.latex_import.title", "LaTeX 코드 불러오기", "Import LaTeX Code")
register("dlg.latex_import.placeholder",
         "latex 코드(tabularx, tblr, longtblr)를 붙여넣으세요 (Ctrl+V)",
         "Paste LaTeX code (tabularx, tblr, longtblr) here (Ctrl+V)")
register("dlg.latex_import.done", "완료", "Done")

# --------------------------------------------------------------------------
# Dialogs.py — ReplaceDialog
# --------------------------------------------------------------------------
register("dlg.replace.title", "모두 바꾸기", "Replace All")
register("dlg.replace.find_label", "찾을 내용:", "Find:")
register("dlg.replace.replace_label", "바꿀 내용:", "Replace with:")
register("dlg.replace.case_sensitive", "대소문자 구분", "Match Case")
register("dlg.replace.use_regex", "정규표현식 사용", "Use Regex")
register("dlg.replace.replace_btn", "모두 바꾸기", "Replace All")
register("dlg.replace.cancel_btn", "취소", "Cancel")

# --------------------------------------------------------------------------
# Dialogs.py — TemplateDialog
# --------------------------------------------------------------------------
register("dlg.template.title", "템플릿 관리자 (F9)", "Template Manager (F9)")
register("dlg.template.list_label", "📂 저장된 템플릿 목록:", "📂 Saved Templates:")
register("dlg.template.name_placeholder", "새 템플릿 이름 입력...", "Enter new template name...")
register("dlg.template.register_btn", "📌 현재 상태를 템플릿으로 등록", "📌 Save Current State as Template")
register("dlg.template.apply_btn", "템플릿 적용", "Apply Template")
register("dlg.template.delete_btn", "템플릿 삭제", "Delete Template")
register("dlg.template.cancel_btn", "취소", "Cancel")

register("dlg.template.select_title", "선택 확인", "Selection Required")
register("dlg.template.select_delete_body", "삭제할 템플릿을 목록에서 선택해주세요.", "Please select a template to delete.")
register("dlg.template.select_load_body", "불러올 템플릿을 목록에서 선택해주세요.", "Please select a template to load.")

register("dlg.template.delete_confirm_title", "템플릿 삭제 확인", "Confirm Template Deletion")
register("dlg.template.delete_confirm_body",
         "'{name}' 템플릿을 정말로 삭제하시겠습니까?\n삭제된 파일은 복구할 수 없습니다.",
         "Are you sure you want to delete the template '{name}'?\nThis cannot be undone.")

register("dlg.template.done_title", "완료", "Done")
register("dlg.template.delete_done_body", "'{name}' 템플릿이 성공적으로 삭제되었습니다.", "Template '{name}' was deleted successfully.")
register("dlg.template.error_title", "오류", "Error")
register("dlg.template.not_found_body", "해당 템플릿 파일이 존재하지 않습니다.", "The template file does not exist.")
register("dlg.template.delete_failed_body", "템플릿 삭제에 실패했습니다: {err}", "Failed to delete template: {err}")

register("dlg.template.warning_title", "경고", "Warning")
register("dlg.template.name_required_body", "템플릿 이름을 입력해주세요.", "Please enter a template name.")
register("dlg.template.register_done_body", "'{name}' 템플릿이 등록되었습니다.", "Template '{name}' has been saved.")
register("dlg.template.save_failed_body", "템플릿 저장 실패: {err}", "Failed to save template: {err}")

# --------------------------------------------------------------------------
# TblrGenerator.py — 서식 다이얼로그 range_str / target_str 조합 문자열
# --------------------------------------------------------------------------
register("range.row_all", "{r_str}행 전체", "Row {r_str} (All)")
register("range.row_col", "{r_str}행 {c_str}열", "Row {r_str}, Col {c_str}")
register("range.multi_cell", "다중 셀 ({count}개 분리)", "Multiple Cells ({count} separate)")
register("range.row", "{row_range}행", "Row {row_range}")
register("range.col", "{col_range}열", "Col {col_range}")
register("range.row_format_suffix", "{row_range}행 서식{suffix}", "Row {row_range} Format{suffix}")
register("range.row_col_suffix", "{row_range}행 {col_range}열{suffix}", "Row {row_range}, Col {col_range}{suffix}")
register("range.col_format_suffix", "{col_range}열 서식{suffix}", "Col {col_range} Format{suffix}")
register("range.col_row_suffix", "{col_range}열 {row_range}행{suffix}", "Col {col_range}, Row {row_range}{suffix}")
register("range.z_row", "Z행", "Z Row")
register("range.z_col", "Z열", "Z Col")

# 셀 아이템 툴팁 프리픽스 (_apply_format_to_item 의 format_type 인자)
register("fmt.type.row", "행", "Row")
register("fmt.type.col", "열", "Col")
register("fmt.type.cell", "셀", "Cell")
register("fmt.tooltip_prefix", "{format_type} 서식:", "{format_type} Format:")

# --------------------------------------------------------------------------
# TblrGenerator.py — 메인 윈도우 상단 메뉴/툴바
# --------------------------------------------------------------------------
register("main.window_title", "T/B/L/R 도우미 3", "T/B/L/R Helper 3")
register("main.tooltip.import_excel", "Excel 가져오기", "Import Excel")
register("main.menu.new", "✨ 새로 시작 (Ctrl+N)", "✨ New (Ctrl+N)")
register("main.menu.save", "💾 저장하기 (Ctrl+S)", "💾 Save (Ctrl+S)")
register("main.menu.save_as", "💾 새이름으로 (Ctrl+Shift+S)", "💾 Save As (Ctrl+Shift+S)")
register("main.menu.load", "📂 불러오기 (Ctrl+O)", "📂 Open (Ctrl+O)")
register("main.menu.import_excel", "📊 엑셀 들여오기", "📊 Import Excel")
register("main.menu.import_latex", "📥 LaTeX 코드 불러오기...", "📥 Import LaTeX Code...")
register("main.menu.copy_clipboard", "📋 클립보드로 복사 (F4)", "📋 Copy to Clipboard (F4)")
register("main.menu.export_tex", "📄 tex 내보내기 [표만] (Ctrl+T)", "📄 Export .tex [Table Only] (Ctrl+T)")
register("main.menu.export_tex_menu", "📝 tex 내보내기", "📝 Export .tex")
register("main.menu.export_csv", "📊 csv 내보내기", "📊 Export CSV")
register("main.menu.help", "⌨️ 단축키 요약 (F1)", "⌨️ Keyboard Shortcuts (F1)")
register("main.menu.exit", "종료", "Exit")
register("main.menu.language", "🌐 Language / 언어", "🌐 Language / 언어")
register("main.btn.toggle_settings_open", "설정 패널 ▶", "Settings ▶")
register("main.btn.toggle_settings_close", "설정 패널 ◀", "Settings ◀")
register("main.lang.pending_tooltip",
         "다음 실행부터 적용됩니다 (재시작 필요)",
         "Will take effect on next launch (restart required)")
register("main.lang.changed_title", "언어 변경", "Language Changed")
register("main.lang.changed_body",
         "언어 설정이 저장되었습니다. 전체 화면에 반영하려면 프로그램을 다시 시작해주세요.",
         "Language preference saved. Please restart the app for it to fully take effect.")

# --------------------------------------------------------------------------
# TblrGenerator.py — 오른쪽 설정 패널 (기본 설정 탭)
# --------------------------------------------------------------------------
register("panel.env_label", "테이블 환경:", "Table Environment:")
register("panel.table_size", "Table Size:", "Table Size:")
register("panel.rows_label", "행(R):", "Rows:")
register("panel.cols_label", "열(C):", "Cols:")
register("panel.apply_btn", "적용", "Apply")
register("panel.colspec_mode", "Colspec Mode:", "Colspec Mode:")
register("panel.edit_colspec_btn", "colspec 편집", "Edit Colspec")
register("panel.manual_colspec_label", "manual Colspec:", "Manual Colspec:")
register("panel.manual_colspec_placeholder", "[colspec 편집] 버튼을 눌러 입력하세요", "Click [Edit Colspec] to enter a value")
register("panel.tab_basic", "기본 설정", "Basic Settings")
register("panel.tab_longtall", "Long/Tall 설정", "Long/Tall Settings")
register("panel.outer_options_label", "선택 옵션 [...]", "Optional Args [...]")
register("panel.inner_extra_label", "추가 설정 {...}", "Extra Settings {...}")
register("panel.bottomrule_checkbox", r"\end 직전 명령:", r"Command before \end:")
register("panel.bottomrule_placeholder", r"\bottomrule (기본값)", r"\bottomrule (default)")
register("panel.preview_engine_tooltip", "미리보기 컴파일에 사용할 엔진 선택", "Select the engine used for preview compilation")
register("panel.preview_btn", "🔍 PDF 미리보기", "🔍 PDF Preview")
register("panel.preview_btn_tooltip", "표를 컴파일해서 PDF로 미리보기 (Alt+Shift+P)", "Compile the table and preview as PDF (Alt+Shift+P)")

# --------------------------------------------------------------------------
# TblrGenerator.py — colspec 문법 검증 경고 / width 누락 경고
# --------------------------------------------------------------------------
register("colspec.warning_title", "Colspec 문법 경고", "Colspec Syntax Warning")
register("colspec.invalid_chars",
         "colspec에 의도하지 않은 문자가 포함되어 있습니다.\n입력값: {value}",
         "The colspec contains unexpected characters.\nInput: {value}")
register("colspec.count_mismatch",
         "현재 테이블 열 개수({cols}개)와 입력한 설정({tokens}개)이 일치하지 않습니다.",
         "The current table column count ({cols}) doesn't match the entered setting ({tokens}).")
register("colspec.ignore_confirm", "\n\n경고를 무시하고 진행하시겠습니까?", "\n\nIgnore this warning and continue?")
register("colspec.ignore_checkbox", "manual에 대한 문법 검사 계속 무시하기", "Keep ignoring syntax checks for manual mode")

register("colspec.width_missing_title", "Width 설정 누락", "Missing Width Setting")
register("colspec.width_missing_body",
         "X 열이 사용되었지만 Generic 설정에 width가 없습니다.\nwidth=\\linewidth를 자동으로 추가할까요?",
         "An X column is used but Generic settings has no width.\nAdd width=\\linewidth automatically?")
register("excel.open_dialog_title", "Excel 파일 열기", "Open Excel File")

# --------------------------------------------------------------------------
# TblrGenerator.py — 붙여넣기 시 표 크기 확장 여부 확인
# --------------------------------------------------------------------------
register("paste.resize_title", "표 크기 확장", "Resize Table?")
register("paste.resize_body",
         "붙여넣을 내용은 {rows}행 × {cols}열입니다.\n"
         "현재 표는 {cur_rows}행 × {cur_cols}열입니다.\n\n"
         "표 크기를 붙여넣을 내용에 맞게 늘리시겠습니까?\n"
         "('아니요'를 선택하면 현재 표 크기 안에서만 붙여넣습니다.)",
         "The pasted content is {rows} rows × {cols} columns.\n"
         "The current table is {cur_rows} rows × {cur_cols} columns.\n\n"
         "Resize the table to fit the pasted content?\n"
         "(Choosing 'No' will paste only within the current table size.)")

# --------------------------------------------------------------------------
# TblrGenerator.py — 상태바 메시지
# --------------------------------------------------------------------------
register("status.copied", "복사되었음", "Copied")
register("status.saved", "저장되었음", "Saved")
register("status.preview_saved", "preview 저장되었음", "Preview saved")
register("status.reset_2x3", "2x3 크기로 초기화되었습니다.", "Reset to a 2x3 table.")
register("status.app_quitting", "앱을 종료합니다", "Exiting the app")
register("status.template_applied", "템플릿 서식이 성공적으로 적용되었습니다. (파일 경로 보존)", "Template applied successfully. (File path preserved)")
register("status.empty_no_preview", "표 내용이 비어 있어 미리보기를 만들 수 없습니다.", "Table is empty, cannot create a preview.")
register("status.preview_in_progress", "이미 미리보기 컴파일이 진행 중입니다...", "Preview compilation is already in progress...")
register("status.compiling_with", "{engine}(으)로 컴파일 중...", "Compiling with {engine}...")
register("status.preview_launch_failed", "미리보기 컴파일 실행에 실패했습니다.", "Failed to launch preview compilation.")
register("status.preview_done", "미리보기 PDF 생성 완료. 기본 PDF 뷰어로 엽니다.", "Preview PDF generated. Opening with the default PDF viewer.")
register("status.preview_failed", "미리보기 컴파일에 실패했습니다.", "Preview compilation failed.")

# --------------------------------------------------------------------------
# TblrGenerator.py — 찾기/바꾸기 (에디터·테이블 공통)
# --------------------------------------------------------------------------
register("find.input_error_title", "입력 오류", "Input Error")
register("find.input_error_body", "찾을 내용을 입력해주세요.", "Please enter text to find.")
register("find.regex_error_title", "정규식 오류", "Regex Error")
register("find.regex_error_body", "유효하지 않은 정규표현식입니다.\n({err})", "Invalid regular expression.\n({err})")
register("find.replace_done_title", "바꾸기 완료", "Replace Complete")
register("find.replace_done_table_body", "총 {modified}개의 셀에서 {count}개의 항목이 치환되었습니다.", "Replaced {count} occurrence(s) in {modified} cell(s).")
register("find.replace_done_editor_body", "총 {count}개의 항목이 치환되었습니다.", "Replaced {count} occurrence(s).")
register("find.no_result_title", "결과 없음", "No Results")
register("find.no_result_table_body", "테이블에서 '{text}'을(를) 찾을 수 없습니다.", "Could not find '{text}' in the table.")
register("find.no_result_simple_body", "'{text}'을(를) 찾을 수 없습니다.", "Could not find '{text}'.")
register("find.no_result_doc_body", "문서에서 '{text}'을(를) 찾을 수 없습니다.", "Could not find '{text}' in the document.")
register("find.result_title", "검색 결과", "Search Result")
register("find.table_dialog_title", "텍스트 찾기", "Find Text")
register("find.editor_dialog_title", "에디터에서 찾기", "Find in Editor")
register("find.search_label", "검색어:", "Search term:")

# --------------------------------------------------------------------------
# TblrGenerator.py — 행/열/셀로 이동 (Go to)
# --------------------------------------------------------------------------
register("goto.row_title", "행으로 이동", "Go to Row")
register("goto.row_label", "행 번호:", "Row number:")
register("goto.col_title", "열로 이동", "Go to Column")
register("goto.col_label", "열 번호:", "Column number:")
register("goto.cell_title", "특정 셀로 이동", "Go to Cell")
register("goto.cell_label", "행과 열을 쉼표로 구분하여 입력하세요 (예: 15,8):", "Enter row and column separated by a comma (e.g. 15,8):")
register("goto.out_of_range_title", "입력 오류", "Input Error")
register("goto.out_of_range_body", "테이블 범위를 벗어났습니다.\n(행: 1~{max_row}, 열: 1~{max_col})", "Out of table range.\n(Rows: 1~{max_row}, Cols: 1~{max_col})")
register("goto.bad_format_title", "입력 오류", "Input Error")
register("goto.bad_format_body", "형식이 올바르지 않습니다.\n'숫자,숫자' 형식으로 입력해 주세요. (예: 15,8)", "Invalid format.\nPlease use 'number,number' (e.g. 15,8).")

# --------------------------------------------------------------------------
# TblrGenerator.py — 표 우클릭 컨텍스트 메뉴
# --------------------------------------------------------------------------
register("ctx.copy", "복사 (Copy)", "Copy")
register("ctx.cut", "잘라내기 (Cut)", "Cut")
register("ctx.paste", "붙여넣기 (Paste)", "Paste")
register("ctx.delete", "내용 지우기 (Delete)", "Clear Content (Delete)")
register("ctx.reset_width", "열 너비 초기화 (Reset Widths)", "Reset Column Widths")
register("ctx.apply_rel_width", "열 상대 너비 반영 (Apply Relative Widths)", "Apply Relative Column Widths")
register("ctx.insert_row", "아래에 행 추가", "Insert Row Below")
register("ctx.delete_row", "이 행 삭제", "Delete This Row")
register("ctx.insert_col", "오른쪽에 열 추가", "Insert Column to the Right")
register("ctx.delete_col", "이 열 삭제", "Delete This Column")
register("ctx.cell_format", "셀 설정 (Cell Format)", "Cell Format")
register("ctx.row_format", "행 설정 (Row Format)", "Row Format")
register("ctx.column_format", "열 설정 (Column Format)", "Column Format")
register("ctx.adv_cell", "셀(cell) 고급 설정 (에디터로 이동)", "Advanced Cell Settings (Go to Editor)")
register("ctx.adv_row", "행(row) 고급 설정 (에디터로 이동)", "Advanced Row Settings (Go to Editor)")
register("ctx.adv_col", "열(column) 고급 설정 (에디터로 이동)", "Advanced Column Settings (Go to Editor)")
register("ctx.merge", "선택 셀 병합 (Merge Cells)", "Merge Cells")
register("ctx.unmerge", "병합 해제 (Unmerge Cells)", "Unmerge Cells")
register("ctx.hline", "가로괘선 (hline)", "Horizontal Line (hline)")
register("ctx.hline_z", "가로괘선+Z (hline+Z)", "Horizontal Line+Z (hline+Z)")
register("ctx.vline", "세로괘선 (vline)", "Vertical Line (vline)")
register("ctx.vline_z", "세로괘선+Z (vline+Z)", "Vertical Line+Z (vline+Z)")
register("ctx.z_hline", "마지막 가로 괘선 (Z hline)", "Last Horizontal Line (Z hline)")
register("ctx.z_vline", "마지막 세로 괘선 (Z vline)", "Last Vertical Line (Z vline)")
register("ctx.find", "찾기 (Find...)", "Find...")
register("ctx.replace", "모두 바꾸기 (Replace All)", "Replace All")
register("ctx.edit_rc_menu", "행/열 추가/삭제 ▶", "Insert/Delete Row/Col ▶")
register("ctx.line_format_menu", "괘선 설정 (Line Format) ▶", "Line Format ▶")

# --------------------------------------------------------------------------
# TblrGenerator.py — F1 도움말 (macOS / Windows 단축키 요약 텍스트 통째로 번역)
# --------------------------------------------------------------------------
register("help.title", "도움말", "Help")

register("help.mac_text", f"""tblr Doumi, Release {VERSION} (2026-08-10)
        Nova de Hi, 2026. MIT License.
        with Python3 and PySide6(LPPL)

    단축키 (macOS)
    * F4: LaTeX 코드 클립보드로 복사
    * ⌘S: 저장, ⌘O: 불러오기, ⌘⇧S: 새이름으로
    * ⌘N: 모든 작업 초기화, ⌘Q: 종료
    * ⌘T: tex 파일로 (표만) 내보내기
    * ⌘⇧T: tex 파일로 내보내기 (oblivoir)
    * ⌥P: 미리보기로 내보내기, ⌥⇧P: pdf 미리보기
    * F2: LaTeX tblr 코드 가져오기

    * ESC: 테이블 영역으로 포커스 이동
    * ⌘F: 텍스트 찾기, F3: 다음 찾기, ⇧F3: 뒤로 찾기
    * ⌘G: 행으로 가기, ⌘⇧G: 행으로 가기
    * ⌥⇧G: 셀 찾아가기
    * ⌘E: (셀 입력시) 셀 편집기 위치로 즉시 이동
    * PgUp/PgDn: 앞 페이지로, 다음 페이지로
    * Home/End: 첫 열로, 마지막 열로
    * ⌘Home/⌘End: 첫 행으로, 마지막 행으로

    * F10: manual colspec (현재 colspec 복사)
    * F12: colspec 편집
    * ⌘=: 설정 패널 토글

    * ⌘Enter: 행 추가 (행의 마지막 셀에서)
    * ⌘Del: 행 삭제 (⌘<Fn>⌫)
    * F7 열 추가, F8 열 삭제 (1번 행의 셀에서)
    * ⌘M: 병합 (버튼 있음), ⌘U: 병합 풀기

    * F5: 현재 셀 설정; ⇧F5: 고급 셀 설정 
    * F6: 현재 행 설정, ⌘F6: 열 설정
    * ⇧F6: 고급 행 설정, ⌘⇧F6: 고급 열 설정
    * ⌃H: 가로선 설정, ⌃V: 세로선 설정 (⇧=+Z)
    * ⌃Z: 마지막 가로선, ⇧⌃Z: 마지막 세로선

    * F9: 템플릿 선택, 추가
    """,
f"""tblr Doumi, Release {VERSION} (2026-08-10)
        Nova de Hi, 2026. MIT License.
        with Python3 and PySide6(LPPL)

    Shortcuts (macOS)
    * F4: Copy LaTeX code to clipboard
    * \u2318S: Save, \u2318O: Open, \u2318\u21e7S: Save As
    * \u2318N: Reset everything, \u2318Q: Quit
    * \u2318T: Export .tex (table only)
    * \u2318\u21e7T: Export .tex (oblivoir)
    * \u2325P: Export for preview, \u2325\u21e7P: PDF preview
    * F2: Import LaTeX tblr code

    * ESC: Move focus to the table
    * \u2318F: Find text, F3: Find next, \u21e7F3: Find previous
    * \u2318G: Go to row, \u2318\u21e7G: Go to row
    * \u2325\u21e7G: Go to cell
    * \u2318E: (while editing a cell) Jump to the cell editor
    * PgUp/PgDn: Previous/next page
    * Home/End: First/last column
    * \u2318Home/\u2318End: First/last row

    * F10: manual colspec (copy current colspec)
    * F12: Edit colspec
    * \u2318=: Toggle settings panel

    * \u2318Enter: Add row (from the last cell of a row)
    * \u2318Del: Delete row (\u2318<Fn>\u232b)
    * F7 add column, F8 delete column (from a cell in row 1)
    * \u2318M: Merge (button available), \u2318U: Unmerge

    * F5: Current cell settings; \u21e7F5: Advanced cell settings
    * F6: Current row settings, \u2318F6: Column settings
    * \u21e7F6: Advanced row settings, \u2318\u21e7F6: Advanced column settings
    * \u2303H: Horizontal line settings, \u2303V: Vertical line settings (\u21e7=+Z)
    * \u2303Z: Last horizontal line, \u21e7\u2303Z: Last vertical line

    * F9: Select/add template
    """)

register("help.win_text", f"""tblr Doumi, Release {VERSION} (2026-08-10)
        Nova de Hi, 2026. MIT License.
        with Python3 and PySide6(LPPL)

    단축키 (Windows/Linux)
    * F4: LaTeX 코드 클립보드로 복사
    * Ctrl+S: 저장, Ctrl+O: 불러오기, Ctrl+Shift+S: 새 이름으로
    * Ctrl+N: 모든 작업 초기화, Ctrl+Q: 종료
    * Ctrl+T: tex 파일로 (표만) 내보내기
    * Ctrl+Shift+T: tex 파일로 내보내기 (oblivoir)
    * Alt+P: 미리보기로 내보내기, Shift+Alt+P: 미리보기
    * F2: LaTeX tblr 코드 가져오기

    * ESC: 테이블 영역으로 포커스 이동
    * Ctrl+F: 텍스트 찾기, F3: 다음 찾기, Shift+F3: 뒤로 찾기
    * Ctrl+H: 한꺼번에 바꾸기
    * Ctrl+G: 행으로 가기, Ctrl+Shift+G: 열로 가기,
    * Shift+Alt+G: 셀 찾아가기
    * Ctrl+Ins: (셀 입력시) 셀 편집기 위치로 즉시 이동
    * PgUp/PgDn: 앞 페이지로, 다음 페이지로
    * Home/End: 첫 열로, 마지막 열로
    * Ctrl+Home/Ctrl+End: 첫 행으로, 마지막 행으로

    * F10: manual colspec (현재 colspec 복사)
    * F12: colspec 편집
    * Ctrl+=: 설정 패널 토글

    * Ctrl+Enter: 행 추가 (행의 마지막 셀에서)
    * Ctrl+Del: 행 삭제 
    * F7 열 추가, F8 열 삭제 (1번 행의 셀에서)
    * Ctrl+M: 병합 (버튼 있음), Ctrl+U: 병합 풀기

    * F5: 현재 셀 설정; Shift+F5: 고급 셀 설정
    * F6: 현재 행 설정, Ctrl+F6: 열 설정
    * Shift+F6: 고급 행 설정, Shift+Ctrl+F6: 고급 열 설정
    * Alt+H: 가로선 설정, Alt+V: 세로선 설정 (Shift=+Z)
    * Alt+Z: 마지막 가로선, Shift+Alt+Z: 마지막 세로선

    * F9: 템플릿 설정, 추가
    """,
f"""tblr Doumi, Release {VERSION} (2026-08-10)
        Nova de Hi, 2026. MIT License.
        with Python3 and PySide6(LPPL)

    Shortcuts (Windows/Linux)
    * F4: Copy LaTeX code to clipboard
    * Ctrl+S: Save, Ctrl+O: Open, Ctrl+Shift+S: Save As
    * Ctrl+N: Reset everything, Ctrl+Q: Quit
    * Ctrl+T: Export .tex (table only)
    * Ctrl+Shift+T: Export .tex (oblivoir)
    * Alt+P: Export for preview, Shift+Alt+P: PDF preview
    * F2: Import LaTeX tblr code

    * ESC: Move focus to the table
    * Ctrl+F: Find text, F3: Find next, Shift+F3: Find previous
    * Ctrl+H: Replace all
    * Ctrl+G: Go to row, Ctrl+Shift+G: Go to column,
    * Shift+Alt+G: Go to cell
    * Ctrl+Ins: (while editing a cell) Jump to the cell editor
    * PgUp/PgDn: Previous/next page
    * Home/End: First/last column
    * Ctrl+Home/Ctrl+End: First/last row

    * F10: manual colspec (copy current colspec)
    * F12: Edit colspec
    * Ctrl+=: Toggle settings panel

    * Ctrl+Enter: Add row (from the last cell of a row)
    * Ctrl+Del: Delete row
    * F7 add column, F8 delete column (from a cell in row 1)
    * Ctrl+M: Merge (button available), Ctrl+U: Unmerge

    * F5: Current cell settings; Shift+F5: Advanced cell settings
    * F6: Current row settings, Ctrl+F6: Column settings
    * Shift+F6: Advanced row settings, Shift+Ctrl+F6: Advanced column settings
    * Alt+H: Horizontal line settings, Alt+V: Vertical line settings (Shift=+Z)
    * Alt+Z: Last horizontal line, Shift+Alt+Z: Last vertical line

    * F9: Template settings, add
    """)

# --------------------------------------------------------------------------
# TblrGenerator.py — LaTeX 가져오기 파싱 실패/경고
# --------------------------------------------------------------------------
register("parse.fail_title", "파싱 실패", "Parse Failed")
register("parse.warn_title", "파싱 경고", "Parse Warning")
register("parse.no_valid_env", "유효한 tblr/longtblr/talltblr/tabularx 코드를 찾을 수 없습니다.", "Could not find valid tblr/longtblr/talltblr/tabularx code.")
register("parse.tabularx_colspec_warn",
         "tabularx의 열 설정(colspec) 괄호 '{ }' 짝이 맞지 않거나 형식이 어긋나서 열 설정을 가져오지 못했습니다.\n본문이 깨질 수 있으니 원본 코드의 괄호를 확인해 주세요.",
         "The tabularx column spec (colspec) braces '{ }' don't match or the format is off, so the column spec couldn't be imported.\nThe body may break — please check the braces in the original code.")
register("parse.end_tabularx_not_found", "\\end{tabularx} 를 찾을 수 없습니다.", "Could not find \\end{tabularx}.")
register("parse.env_open_brace_not_found", "{env_type} 설정부 괄호 '{{' 를 찾을 수 없습니다.", "Could not find the opening brace '{{' for the {env_type} settings.")
register("parse.close_brace_not_found", "설정을 닫는 '}' 괄호를 찾을 수 없습니다.", "Could not find the closing brace '}' for the settings.")
register("parse.end_env_not_found", "\\end{{{env_type}}} 을 찾을 수 없습니다.", "Could not find \\end{{{env_type}}}.")

# --------------------------------------------------------------------------
# TblrGenerator.py — documentclass 입력 / 미리보기 컴파일 오류
# --------------------------------------------------------------------------
register("export.docclass_title", "Document Class 설정", "Document Class Setting")
register("export.docclass_label", "사용할 documentclass를 입력하세요:", "Enter the documentclass to use:")

register("preview.engine_not_found_title", "엔진을 찾을 수 없음", "Engine Not Found")
register("preview.engine_not_found_body",
         "'{engine}' 실행 파일을 찾을 수 없습니다.\nTeX 배포판이 설치되어 있고 PATH에 등록되어 있는지 확인해주세요.\n\n대신 '📥 tex 내보내기 > preview' 메뉴로 .tex 파일만 저장한 뒤 직접 컴파일하실 수 있습니다.",
         "Could not find the '{engine}' executable.\nPlease make sure a TeX distribution is installed and registered in PATH.\n\nAlternatively, use '📥 Export .tex > preview' to save just the .tex file and compile it manually.")

register("preview.compile_fail_title", "미리보기 컴파일 실패", "Preview Compilation Failed")
register("preview.compile_fail_body", "LaTeX 컴파일 중 오류가 발생했습니다.", "An error occurred while compiling LaTeX.")
register("preview.compile_fail_detail",
         "표 안의 사용자 정의 매크로나 색상/폰트 명령이 원인일 수 있습니다.\n_tblr_prv.tex / _tblr_prv.log 파일이 아래 폴더에 남아있으니 직접 확인/수정하실 수 있습니다:\n{target_dir}",
         "This may be caused by custom macros or color/font commands in the table.\nThe _tblr_prv.tex / _tblr_prv.log files remain in the folder below for you to inspect or edit:\n{target_dir}")
register("preview.open_folder_btn", "폴더 열기", "Open Folder")

# --------------------------------------------------------------------------
# main.py — 파일 열기 에러 메시지
# --------------------------------------------------------------------------
register("msg.file_error.title", "파일 오류", "File Error")
register("msg.error.title", "오류", "Error")
register("msg.file_error.not_found", "파일을 찾을 수 없습니다:\n{filename}", "File not found:\n{filename}")
register("msg.file_error.invalid_format", "올바르지 않은 파일 형식입니다:\n{filename}", "Invalid file format:\n{filename}")
register("msg.file_error.open_failed", "파일을 열 수 없습니다:\n{filename}\n\n{err}", "Could not open the file:\n{filename}\n\n{err}")
