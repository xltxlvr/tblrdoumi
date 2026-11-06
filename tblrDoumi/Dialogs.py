import re, sys, os
import glob, json
from PySide6.QtWidgets import (QVBoxLayout, 
                               QHBoxLayout, 
                               QPushButton, QPlainTextEdit, QLabel, 
                               QLineEdit, QDialog, QCheckBox, QComboBox,
                               QDialogButtonBox,
                               QFormLayout,
                               QListWidget,
                               QGroupBox, QButtonGroup,
                               QMessageBox)
from PySide6.QtGui import (QPixmap,
                           QIcon, QColor)
from PySide6.QtCore import QSize

from tblrDoumi.ColorPalette import ColorButton, ColorPalette
from tblrDoumi.i18n import tr

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# ==========================================================
# [추가] "동일 스코프" 서식 줄을 찾아 교체/파싱하기 위한 유틸리티 함수들
# 예) input_cell_format 텍스트 안에서 "cell{1}{2} = {...}" 처럼
#     정확히 같은 스코프(header)를 가진 줄을 찾아 그 안의 옵션을
#     읽어오거나(find_scoped_option_block), 교체할 수 있게 해줍니다.
# ==========================================================

def find_scoped_option_block(text, header_pattern):
    """
    text 안에서 `header_pattern`(이미 re.escape 처리된 헤더, 예: "cell\\{1\\}\\{2\\}")
    바로 뒤에 " = {...}" 형태로 이어지는 옵션 블록을 찾습니다.
    중괄호가 중첩되어 있어도(예: font=\\fontspec{Noto Sans KR}) 괄호 깊이를 세어
    정확한 닫는 중괄호 위치까지 찾아냅니다.

    반환값: (start, end, inner) 튜플 또는 못 찾으면 None
      - start: 헤더가 시작하는 위치 (텍스트 전체 기준)
      - end:   옵션 블록의 닫는 '}' 바로 다음 위치
      - inner: 옵션 블록 중괄호 안의 내용 (예: "font=\\sffamily, c")
    """
    m = re.search(header_pattern + r"\s*=\s*\{", text)
    if not m:
        return None

    open_brace_idx = m.end() - 1  # '{' 위치
    depth = 1
    i = open_brace_idx + 1
    while i < len(text) and depth > 0:
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
        i += 1

    if depth != 0:
        # 괄호 짝이 안 맞으면 안전하게 포기 (기존 텍스트를 건드리지 않음)
        return None

    inner = text[open_brace_idx + 1:i - 1]
    return (m.start(), i, inner)


def split_top_level_commas(s):
    """
    문자열 s를 콤마(,)로 분리하되, 중괄호({}) 안에 있는 콤마는 무시합니다.
    예) "font=\\fontspec{Noto, Sans}, c" -> ["font=\\fontspec{Noto, Sans}", "c"]
    """
    parts = []
    depth = 0
    current = ""
    for ch in s:
        if ch == '{':
            depth += 1
            current += ch
        elif ch == '}':
            depth -= 1
            current += ch
        elif ch == ',' and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += ch
    if current.strip():
        parts.append(current)
    return [p.strip() for p in parts if p.strip()]

class ColspecDialog(QDialog):
    def __init__(self, current_colspec="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.colspec.title"))
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        # 안내 레이블 및 입력창
        layout.addWidget(QLabel(tr("dlg.colspec.label")))
        self.input_edit = QLineEdit(current_colspec)
        layout.addWidget(self.input_edit)

        # 확인/취소 버튼
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_colspec(self):
        return self.input_edit.text()

class FormatDialog(QDialog):
    # fmt_kind: "cell" / "row" / "col" / "hline" / "vline"
    # (예전에는 이 값 자체가 "셀서식"/"행괘선" 같은 한국어 문자열이라, 언어를
    #  바꾸면 "괘선" in fmt_type 같은 내부 로직까지 깨졌음. 표시용 라벨은
    #  fmt.kind.* 번역 키로 따로 분리했다.)
    LINE_KINDS = ("hline", "vline")

    def __init__(self, fmt_kind, range_str, parent=None, existing_options=None):
        super().__init__(parent)
        self.fmt_kind = fmt_kind
        label = tr(f"fmt.kind.{fmt_kind}")
        self.setWindowTitle(tr("dlg.format.title", label=label))

        self.is_line_format = fmt_kind in self.LINE_KINDS

        layout = QVBoxLayout(self)
        self.range_label = QLabel(tr("dlg.format.range_label", range_str=range_str))
        layout.addWidget(self.range_label)

        self.line_edit = QLineEdit("{}")
        self.line_edit.setCursorPosition(1)

        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(24, 24)
        self.color_btn.setIcon(QIcon(resource_path("btnicon.png")))
        self.color_btn.setIconSize(QSize(24, 24))
        self.color_btn.setStyleSheet("border: 1px solid gray;")  # 배경색은 아이콘이 있으니 생략 가능
        self.color_btn.clicked.connect(self.open_color_palette)

        # [기존] 괘선 전용 옵션들
        self.line_style_combo = QComboBox()
        self.line_style_combo.addItems([
            tr("dlg.format.line_style.solid"),
            tr("dlg.format.line_style.dashed"),
            tr("dlg.format.line_style.dotted"),
        ])
        self.line_style_combo.setVisible(self.is_line_format)

        self.double_checkbox = QCheckBox(tr("dlg.format.double"))
        self.double_checkbox.setVisible(self.is_line_format)

        self.thick_checkbox = QCheckBox(tr("dlg.format.thick"))
        self.thick_checkbox.setVisible(self.is_line_format)

        # [기존] 셀/행/열 전용: 색상 선택
        self.cell_color_combo = QComboBox()
        self.cell_color_combo.addItems([
            tr("dlg.format.cell_color.bg"),
            tr("dlg.format.cell_color.fg"),
            tr("dlg.format.cell_color.manual"),
        ])
        self.cell_color_combo.setVisible(not self.is_line_format)

        # ==========================================
        # [추가] 수평(가로) 정렬 콤보박스
        # ==========================================
        self.halign_combo = QComboBox()
        self.halign_combo.addItems([
            tr("dlg.format.halign.keep"),
            tr("dlg.format.halign.center"),
            tr("dlg.format.halign.left"),
            tr("dlg.format.halign.right"),
            tr("dlg.format.halign.justify"),
        ])
        self.halign_combo.setVisible(not self.is_line_format)

        # ==========================================
        # [추가] 수직(세로) 정렬 콤보박스
        # ==========================================
        self.valign_combo = QComboBox()
        self.valign_combo.addItems([
            tr("dlg.format.valign.keep"),
            tr("dlg.format.valign.middle"),
            tr("dlg.format.valign.top"),
            tr("dlg.format.valign.bottom"),
            tr("dlg.format.valign.head"),
            tr("dlg.format.valign.foot"),
        ])
        self.valign_combo.setVisible(not self.is_line_format)

        # ==========================================
        # [추가] 수식 모드(Mode) 선택 콤보박스
        # ==========================================
        self.mode_combo = QComboBox()
        # 표시될 텍스트와 실제 매핑될 값을 고려하여 아이템 추가
        # (내부적으로는 currentText()를 그대로 LaTeX 값(mode=...)에 쓰므로
        #  이 콤보박스의 항목 자체는 번역하지 않고 원문(text/math/...)을 유지한다)
        self.mode_combo.addItems([
            tr("dlg.format.mode.text"),
            tr("dlg.format.mode.math"),
            tr("dlg.format.mode.dmath"),
            tr("dlg.format.mode.imath"),
        ])
        self.mode_combo.setVisible(not self.is_line_format)

        # ==========================================
        # [수정] 글꼴(font) 선택을 콤보박스 대신 "배타적 체크박스 그룹"으로 구성
        # (family / series / shape 각 축은 QButtonGroup(exclusive=True)로 묶어
        #  라디오처럼 동작하되, 체크박스라 이미 선택된 걸 다시 눌러 해제("유지" 상태)도 가능)
        # ==========================================
        self.font_group_box = QGroupBox(tr("dlg.format.font_group"))
        self.font_group_box.setVisible(not self.is_line_format)
        font_group_layout = QVBoxLayout(self.font_group_box)

        # --- family: rm / sf / tt ---
        family_row = QHBoxLayout()
        family_row.addWidget(QLabel(tr("dlg.format.font.family_label")))
        self.cb_font_rm = QCheckBox(tr("dlg.format.font.rm"))
        self.cb_font_sf = QCheckBox(tr("dlg.format.font.sf"))
        self.cb_font_tt = QCheckBox(tr("dlg.format.font.tt"))
        self._setup_exclusive_checkboxes([self.cb_font_rm, self.cb_font_sf, self.cb_font_tt])
        for cb in (self.cb_font_rm, self.cb_font_sf, self.cb_font_tt):
            family_row.addWidget(cb)
        family_row.addStretch()
        font_group_layout.addLayout(family_row)

        # --- series: md / bf ---
        series_row = QHBoxLayout()
        series_row.addWidget(QLabel(tr("dlg.format.font.series_label")))
        self.cb_font_md = QCheckBox(tr("dlg.format.font.md"))
        self.cb_font_bf = QCheckBox(tr("dlg.format.font.bf"))
        self._setup_exclusive_checkboxes([self.cb_font_md, self.cb_font_bf])
        for cb in (self.cb_font_md, self.cb_font_bf):
            series_row.addWidget(cb)
        series_row.addStretch()
        font_group_layout.addLayout(series_row)

        # --- shape: up / sl / it ---
        shape_row = QHBoxLayout()
        shape_row.addWidget(QLabel(tr("dlg.format.font.shape_label")))
        self.cb_font_up = QCheckBox(tr("dlg.format.font.up"))
        self.cb_font_sl = QCheckBox(tr("dlg.format.font.sl"))
        self.cb_font_it = QCheckBox(tr("dlg.format.font.it"))
        self._setup_exclusive_checkboxes([self.cb_font_up, self.cb_font_sl, self.cb_font_it])
        for cb in (self.cb_font_up, self.cb_font_sl, self.cb_font_it):
            shape_row.addWidget(cb)
        shape_row.addStretch()
        font_group_layout.addLayout(shape_row)

        # [유지] 직접 입력용 LineEdit (예: luatex/fontspec 전용 명령 등 자유 입력)
        extra_row = QHBoxLayout()
        extra_row.addWidget(QLabel(tr("dlg.format.font.manual_label")))
        self.font_extra_edit = QLineEdit()
        self.font_extra_edit.setPlaceholderText(tr("dlg.format.font.manual_placeholder"))
        extra_row.addWidget(self.font_extra_edit, stretch=1)
        font_group_layout.addLayout(extra_row)

        # 레이아웃 구성
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.line_edit)
        hlayout.addWidget(self.color_btn)
        hlayout.addWidget(self.line_style_combo)
        hlayout.addWidget(self.double_checkbox)
        hlayout.addWidget(self.thick_checkbox)
        hlayout.addWidget(self.cell_color_combo)
        
        # 정렬 콤보박스들 추가
        hlayout.addWidget(self.halign_combo)
        hlayout.addWidget(self.valign_combo)
        # 수식 모드 콤보박스 레이아웃에 추가
        hlayout.addWidget(self.mode_combo)

        layout.addLayout(hlayout)

        # [추가] 글꼴 선택 그룹박스 추가
        layout.addWidget(self.font_group_box)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # [추가] 동일 스코프의 기존 서식이 있으면 다이얼로그를 그 값으로 미리 채움
        if existing_options is not None:
            self._prefill_from_existing(existing_options)

    # ==========================================
    # [추가] 체크박스 목록을 "배타적"으로 동작하게 만드는 헬퍼
    # QButtonGroup(exclusive=True)와 달리, 이미 체크된 항목을 다시 클릭하면
    # 그대로 해제되어 "선택 안 함(유지)" 상태로 돌아갈 수 있습니다.
    # ==========================================
    def _setup_exclusive_checkboxes(self, checkboxes):
        def make_handler(box):
            def handler(checked):
                if checked:
                    for other in checkboxes:
                        if other is not box and other.isChecked():
                            other.blockSignals(True)
                            other.setChecked(False)
                            other.blockSignals(False)
            return handler

        for box in checkboxes:
            box.toggled.connect(make_handler(box))

    # ==========================================
    # [추가] 기존 옵션 문자열을 파싱해서 위젯 초기 상태로 반영
    # ==========================================
    def _prefill_from_existing(self, options_str):
        tokens = split_top_level_commas(options_str)
        leftover = []

        # font= 값 파싱용 표준 명령어 -> 체크박스 매핑
        family_cmds = {r"\rmfamily": "cb_font_rm", r"\sffamily": "cb_font_sf", r"\ttfamily": "cb_font_tt"}
        series_cmds = {r"\mdseries": "cb_font_md", r"\bfseries": "cb_font_bf"}
        shape_cmds = {r"\upshape": "cb_font_up", r"\slshape": "cb_font_sl", r"\itshape": "cb_font_it"}

        for tok in tokens:
            if self.is_line_format:
                if tok in ("dashed", "dotted"):
                    self.line_style_combo.setCurrentText(tok)
                elif tok == "double":
                    self.double_checkbox.setChecked(True)
                elif tok == "thick":
                    self.thick_checkbox.setChecked(True)
                else:
                    leftover.append(tok)
                continue

            if tok == "c":
                self.halign_combo.setCurrentIndex(1)
            elif tok == "l":
                self.halign_combo.setCurrentIndex(2)
            elif tok == "r":
                self.halign_combo.setCurrentIndex(3)
            elif tok == "j":
                self.halign_combo.setCurrentIndex(4)
            elif tok == "m":
                self.valign_combo.setCurrentIndex(1)
            elif tok == "t":
                self.valign_combo.setCurrentIndex(2)
            elif tok == "b":
                self.valign_combo.setCurrentIndex(3)
            elif tok == "h":
                self.valign_combo.setCurrentIndex(4)
            elif tok == "f":
                self.valign_combo.setCurrentIndex(5)
            elif tok.startswith("mode="):
                value = tok[len("mode="):].strip()
                idx = self.mode_combo.findText(value)
                if idx >= 0:
                    self.mode_combo.setCurrentIndex(idx)
                else:
                    leftover.append(tok)
            elif tok.startswith("font="):
                remaining = tok[len("font="):].strip()
                for pattern, attr_name in family_cmds.items():
                    if pattern in remaining:
                        getattr(self, attr_name).setChecked(True)
                        remaining = remaining.replace(pattern, "", 1)
                for pattern, attr_name in series_cmds.items():
                    if pattern in remaining:
                        getattr(self, attr_name).setChecked(True)
                        remaining = remaining.replace(pattern, "", 1)
                for pattern, attr_name in shape_cmds.items():
                    if pattern in remaining:
                        getattr(self, attr_name).setChecked(True)
                        remaining = remaining.replace(pattern, "", 1)
                remaining = remaining.strip()
                if remaining:
                    self.font_extra_edit.setText(remaining)
            else:
                leftover.append(tok)

        if leftover:
            self.line_edit.setText("{" + ", ".join(leftover) + "}")
            self.line_edit.setCursorPosition(len(self.line_edit.text()) - 1)

    def get_line_format_info(self):
        """선 모양, 이중선 여부, 두꺼운 선 여부를 반환"""
        if not self.is_line_format:
            return "", False, False

        style = self.line_style_combo.currentText()
        is_double = self.double_checkbox.isChecked()
        is_thick = self.thick_checkbox.isChecked()

        final_style = "" if style == "solid" else style
        return final_style, is_double, is_thick

    def open_color_palette(self):
        palette = ColorPalette(self)
        palette.color_selected.connect(self.insert_color_name)

        btn_pos = self.color_btn.mapToGlobal(self.color_btn.rect().bottomLeft())
        palette.move(btn_pos)
        palette.exec()

    def get_line_style(self):
        # [수정 3] isVisible() 대신 저장해둔 변수로 확인! (다이얼로그가 닫혀도 값 유지됨)
        if not self.is_line_format:
            return ""
        
        style = self.line_style_combo.currentText()
        
        # 'solid'는 기본값이므로 코드 깔끔하게 생략
        if style == "solid":
            return ""
            
        return style

    def insert_color_name(self, name: str):
        # 1. 현재 텍스트에서 괄호 {} 제거해서 알맹이만 가져옴
        text = self.line_edit.text().strip().strip("{}")
        
        prefix = ""
        if not self.is_line_format:
            opt = self.cell_color_combo.currentText()
            if "bg=" in opt:
                prefix = "bg="
            elif "fg=" in opt:
                prefix = "fg="

        # 2. 정규식으로 fg= 또는 bg= 패턴을 찾아 영리하게 교체하거나 추가
        if prefix == "bg=":
            if re.search(r"bg=[a-zA-Z0-9_]+", text):
                text = re.sub(r"bg=[a-zA-Z0-9_]+", f"bg={name}", text)
            else:
                text = f"{text}, bg={name}" if text else f"bg={name}"
                
        elif prefix == "fg=":
            if re.search(r"fg=[a-zA-Z0-9_]+", text):
                text = re.sub(r"fg=[a-zA-Z0-9_]+", f"fg={name}", text)
            else:
                text = f"{text}, fg={name}" if text else f"fg={name}"
                
        else: # "직접 입력" 등
            text = f"{text}, {name}" if text else name

        # 3. 괄호를 다시 씌우고 라인에디트 업데이트
        self.line_edit.setText(f"{{{text}}}")
        self.line_edit.setCursorPosition(len(self.line_edit.text()) - 1)

        # ========================================================
        # [수정] AttributeError 방지를 위한 타입 체크 및 변환 로직
        # ========================================================
        ninecolors_dict = ColorPalette.ninecolors
        
        # 만약 ninecolors가 JSON 문자열(str) 상태로 들어가 있다면 딕셔너리로 파싱
        if isinstance(ninecolors_dict, str):
            try:
                ninecolors_dict = json.loads(ninecolors_dict)
            except Exception:
                ninecolors_dict = {}

        # 안전하게 딕셔너리에서 rgb 값 추출
        rgb = None
        if isinstance(ninecolors_dict, dict):
            rgb = ninecolors_dict.get(name, {}).get("rgb") if name in ninecolors_dict else None

        if rgb:
            pixmap = QPixmap(24, 24)
            pixmap.fill(QColor(*rgb))
            self.color_btn.setIcon(QIcon(pixmap))
            self.color_btn.setIconSize(QSize(24, 24))
            self.color_btn.setStyleSheet("")

    def get_mode_info(self):
        """
        수식 모드(math, dmath, imath) 정보를 리스트 형태로 반환합니다.
        괘선 서식이거나 'text' 선택 시에는 빈 리스트를 반환합니다.
        """
        if self.is_line_format:
            return []

        modes = []
        # 현재 선택된 텍스트 확인
        current_mode = self.mode_combo.currentText()

        # 'text'가 아닐 때만 "mode=값" 형태로 추가
        if current_mode != "text":
            modes.append(f"mode={current_mode}")

        return modes

    # ==========================================
    # [추가] 선택된 정렬 옵션들을 리스트로 반환
    # ==========================================
    def get_align_info(self):
        if self.is_line_format:
            return []
        
        aligns = []
        
        # 가로 정렬 확인
        h_idx = self.halign_combo.currentIndex()
        if h_idx == 1: aligns.append("c")
        elif h_idx == 2: aligns.append("l")
        elif h_idx == 3: aligns.append("r")
        elif h_idx == 4: aligns.append("j")

        # 세로 정렬 확인
        v_idx = self.valign_combo.currentIndex()
        if v_idx == 1: aligns.append("m")
        elif v_idx == 2: aligns.append("t")
        elif v_idx == 3: aligns.append("b")
        elif v_idx == 4: aligns.append("h")
        elif v_idx == 5: aligns.append("f")

        return aligns

    # ==========================================
    # [추가] 글꼴(font) 옵션을 "font=..." 형태의 문자열 리스트로 반환
    # 콤보박스로 조합된 표준 명령(\sffamily\bfseries\itshape 등)에
    # 직접 입력한 내용을 이어붙여 하나의 font= 값으로 합칩니다.
    # (luatex/fontspec 같은 임의 명령도 직접 입력란에 넣을 수 있도록 지원)
    # ==========================================
    def get_font_info(self):
        if self.is_line_format:
            return []

        cmd = ""

        if self.cb_font_rm.isChecked(): cmd += r"\rmfamily"
        elif self.cb_font_sf.isChecked(): cmd += r"\sffamily"
        elif self.cb_font_tt.isChecked(): cmd += r"\ttfamily"

        if self.cb_font_md.isChecked(): cmd += r"\mdseries"
        elif self.cb_font_bf.isChecked(): cmd += r"\bfseries"

        if self.cb_font_up.isChecked(): cmd += r"\upshape"
        elif self.cb_font_sl.isChecked(): cmd += r"\slshape"
        elif self.cb_font_it.isChecked(): cmd += r"\itshape"

        extra = self.font_extra_edit.text().strip()
        if extra:
            cmd += extra

        if cmd:
            return [f"font={cmd}"]
        return []

class LatexImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.latex_import.title"))
        self.resize(450, 300)  # 다이얼로그 크기 적절히 설정
        
        layout = QVBoxLayout(self)
        
        # 텍스트 입력창
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setPlaceholderText(tr("dlg.latex_import.placeholder"))
        layout.addWidget(self.text_edit)
        
        # 완료 버튼
        self.btn_done = QPushButton(tr("dlg.latex_import.done"), self)
        self.btn_done.clicked.connect(self.accept)  # 클릭 시 창을 닫고 Accepted 상태 반환
        layout.addWidget(self.btn_done)
        
    def get_text(self):
        return self.text_edit.toPlainText()

class ReplaceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.replace.title"))
        self.setMinimumWidth(300)

        # 메인 레이아웃
        layout = QVBoxLayout(self)

        # 폼 레이아웃 (라벨과 입력창을 나란히 배치)
        form_layout = QFormLayout()
        self.find_input = QLineEdit(self)
        self.replace_input = QLineEdit(self)
        
        form_layout.addRow(tr("dlg.replace.find_label"), self.find_input)
        form_layout.addRow(tr("dlg.replace.replace_label"), self.replace_input)
        layout.addLayout(form_layout)

        # ---------------------------------------------------------
        # [추가된 부분] 옵션 체크박스 레이아웃
        # ---------------------------------------------------------
        checkbox_layout = QHBoxLayout()
        self.case_checkbox = QCheckBox(tr("dlg.replace.case_sensitive"), self)
        self.regex_checkbox = QCheckBox(tr("dlg.replace.use_regex"), self)
        
        checkbox_layout.addWidget(self.case_checkbox)
        checkbox_layout.addWidget(self.regex_checkbox)
        checkbox_layout.addStretch() # 체크박스들을 왼쪽으로 밀착시키기 위함
        
        layout.addLayout(checkbox_layout)
        # ---------------------------------------------------------

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        self.replace_btn = QPushButton(tr("dlg.replace.replace_btn"), self)
        self.cancel_btn = QPushButton(tr("dlg.replace.cancel_btn"), self)
        
        button_layout.addWidget(self.replace_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        # 버튼 클릭 이벤트 연결
        self.replace_btn.clicked.connect(self.accept) # 확인(Accepted) 상태로 창 닫기
        self.cancel_btn.clicked.connect(self.reject)  # 취소(Rejected) 상태로 창 닫기

    # ---------------------------------------------------------
    # [수정된 부분] 체크박스 상태도 함께 반환하도록 변경
    # ---------------------------------------------------------
    def get_data(self):
        """찾을 내용, 바꿀 내용, 대소문자 구분 여부, 정규식 사용 여부를 튜플로 반환합니다."""
        return (
            self.find_input.text(), 
            self.replace_input.text(),
            self.case_checkbox.isChecked(),
            self.regex_checkbox.isChecked()
        )

class TemplateDialog(QDialog):
    def __init__(self, template_dir, current_data_callback, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.template.title"))
        self.resize(400, 350)
        self.template_dir = template_dir
        self.get_current_data = current_data_callback # 현재 상태를 딕셔너리로 받아올 콜백 함수
        self.selected_file_path = None

        layout = QVBoxLayout(self)

        # 1. 템플릿 목록 레이블
        layout.addWidget(QLabel(tr("dlg.template.list_label")))

        # 2. 템플릿 목록 리스트위젯
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        self.list_widget.itemDoubleClicked.connect(self.load_selected_template)

        # 목록 채우기
        self.refresh_template_list()

        # 3. 현재 상태 등록 영역 (가로 배치)
        reg_layout = QHBoxLayout()
        self.input_template_name = QLineEdit()
        self.input_template_name.setPlaceholderText(tr("dlg.template.name_placeholder"))
        self.btn_register = QPushButton(tr("dlg.template.register_btn"))
        self.btn_register.clicked.connect(self.register_current_template)
        reg_layout.addWidget(self.input_template_name, 1)
        reg_layout.addWidget(self.btn_register)
        layout.addLayout(reg_layout)

        # 4. 하단 결정 버튼들 (가로 배치)
        btn_layout = QHBoxLayout()
        
        # [변경] 템플릿 적용 버튼 (기존 불러오기)
        self.btn_load = QPushButton(tr("dlg.template.apply_btn"))
        self.btn_load.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.btn_load.clicked.connect(self.load_selected_template)
        
        # [추가] 템플릿 삭제 버튼
        self.btn_delete = QPushButton(tr("dlg.template.delete_btn"))
        self.btn_delete.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;") # 삭제 버튼은 직관적인 빨간색 스타일
        self.btn_delete.clicked.connect(self.delete_selected_template)
        
        # 취소 버튼
        self.btn_cancel = QPushButton(tr("dlg.template.cancel_btn"))
        self.btn_cancel.clicked.connect(self.reject)
        
        # 버튼 순서대로 레이아웃에 추가 (적용 - 삭제 - 취소)
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    # ==========================================
    # 선택한 템플릿 파일 삭제 메서드
    # ==========================================
    def delete_selected_template(self):
        """목록에서 선택한 템플릿 파일을 templates/ 폴더에서 영구 삭제"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, tr("dlg.template.select_title"), tr("dlg.template.select_delete_body"))
            return
            
        name = selected_items[0].text()
        file_path = os.path.join(self.template_dir, f"{name}.tblr")
        
        # 실수로 지우는 것을 방지하기 위해 확인 대화상자를 띄웁니다.
        reply = QMessageBox.question(
            self, 
            tr("dlg.template.delete_confirm_title"), 
            tr("dlg.template.delete_confirm_body", name=name), 
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    QMessageBox.information(self, tr("dlg.template.done_title"), tr("dlg.template.delete_done_body", name=name))
                    self.refresh_template_list() # 목록 새로고침
                else:
                    QMessageBox.warning(self, tr("dlg.template.error_title"), tr("dlg.template.not_found_body"))
            except Exception as e:
                QMessageBox.critical(self, tr("dlg.template.error_title"), tr("dlg.template.delete_failed_body", err=str(e)))

    def refresh_template_list(self):
        """templates/ 폴더 내의 .tblr 파일을 읽어 목록에 표시"""
        self.list_widget.clear()
        if not os.path.exists(self.template_dir):
            return
            
        # .tblr 확장자를 가진 파일들을 수집
        files = glob.glob(os.path.join(self.template_dir, "*.tblr"))
        for f in files:
            filename = os.path.basename(f)
            # 확장자를 제외한 이름만 리스트에 노출
            name_only, _ = os.path.splitext(filename)
            item = self.list_widget.addItem(name_only)

    def register_current_template(self):
        """현재 테이블 설정 상태를 파일로 저장"""
        name = self.input_template_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("dlg.template.warning_title"), tr("dlg.template.name_required_body"))
            return

        # 윈도우 파일명 불가능 문자 정제
        safe_name = re.sub(r'[\\/*?:"<>|]', "", name)
        file_path = os.path.join(self.template_dir, f"{safe_name}.tblr")

        # 메인 윈도우로부터 현재 상태 데이터 딕셔너리 수집
        data = self.get_current_data()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, tr("dlg.template.done_title"), tr("dlg.template.register_done_body", name=name))
            self.input_template_name.clear()
            self.refresh_template_list()
        except Exception as e:
            QMessageBox.critical(self, tr("dlg.template.error_title"), tr("dlg.template.save_failed_body", err=str(e)))

    def load_selected_template(self, item=None):
        """목록에서 선택(또는 더블클릭)한 템플릿 파일을 타겟으로 설정하고 다이얼로그 종료"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, tr("dlg.template.select_title"), tr("dlg.template.select_load_body"))
            return
            
        name = selected_items[0].text()
        self.selected_file_path = os.path.join(self.template_dir, f"{name}.tblr")
        self.accept() # 이 호출이 성공해야 메인 코드의 dialog.exec() == QDialog.Accepted 분기로 진입합니다.
