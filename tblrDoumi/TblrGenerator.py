# main class
import sys, os, re
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTableWidget, QTableWidgetItem, 
                               QPushButton, QPlainTextEdit, QTextEdit,
                               QFormLayout, QSpinBox, QLabel, QFileDialog, QSplitter,
                               QLineEdit, QHeaderView, QRadioButton, QButtonGroup, 
                               QInputDialog, QMessageBox,
                               QAbstractItemView, QMenu, QDialog, QCheckBox, QComboBox,
                               QTabWidget, QDockWidget, QAbstractScrollArea)
from PySide6.QtGui import (QKeySequence, QShortcut, QPalette, 
                           QGuiApplication, QAction, QTextCursor, QIcon, QColor,
                           QFont, QBrush, QPen, QTextDocument, QDesktopServices)
from PySide6.QtCore import Qt, QEvent, QSettings, QFileInfo, QProcess, QUrl, QProcessEnvironment
from openpyxl import load_workbook
import json 
import platform
import html, csv
import glob
import shutil

from tblrDoumi.Dialogs import (ColspecDialog, FormatDialog, LatexImportDialog, ReplaceDialog, TemplateDialog,
                               find_scoped_option_block, split_top_level_commas)
from tblrDoumi.TableBorderDelegate import TableBorderDelegate
from tblrDoumi.i18n import tr, set_language, get_language, language_manager

class TblrGenerator(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("ktug.org", "tblrDoumi")

        # [추가] 저장된 언어 설정 불러오기 (없으면 기본값 ko)
        saved_lang = self.settings.value("language", "ko")
        if saved_lang in ("ko", "en"):
            set_language(saved_lang)

        # 이번 세션(창)이 실제로 어떤 언어로 만들어졌는지 고정해서 기억해 둠.
        # get_language()는 change_language()가 호출되면 즉시 바뀌지만,
        # 이미 만들어진 위젯 텍스트는 재시작 전까지 그대로이므로,
        # "현재 화면에 실제로 반영된 언어"와 "다음 실행부터 적용될 언어"를 구분해야 함.
        self.active_language = get_language()

        self.setWindowTitle(tr("main.window_title"))
        self.resize(1000, 720)
        # self.setWindowIcon(QIcon("tblrdoumi.ico"))
        if sys.platform == "darwin":
            icon_file = "tblrdoumi.icns"
        else:
            icon_file = "tblrdoumi.ico"    
        self.setWindowIcon(QIcon(icon_file))

        self.current_file = None 
        self.update_window_title()

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # ---------------------------------------------------------
        # 1. 메인 스플리터 (위/아래 나누기)
        # ---------------------------------------------------------
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # 위쪽 영역 컨테이너
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        # --- Colspec preview와 우측 버튼들을 나란히 배치 ---
        preview_layout = QHBoxLayout()
        
        # Mac용 key-modifier
        self.alt_mod = Qt.KeyboardModifier.MetaModifier if sys.platform == "darwin" else Qt.KeyboardModifier.AltModifier

        # colspec preview
        self.colspec_preview = QPlainTextEdit()
        self.colspec_preview.setReadOnly(True)
        self.colspec_preview.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.colspec_preview.setFixedHeight(50)
        
        if sys.platform == "darwin":
            self.colspec_preview.setStyleSheet("font-family: Menlo; padding:4px;")
        else:
            self.colspec_preview.setStyleSheet("font-family: Consolas; padding:4px;")
        
        preview_layout.addWidget(self.colspec_preview, stretch=1)

        # 버튼 영역
        self.btn_import_excel = QPushButton("📊")
        self.btn_import_excel.setToolTip(tr("main.tooltip.import_excel"))
        self.btn_import_excel.setFixedSize(30, 30)
        self.btn_import_excel.setStyleSheet("background-color:#4CAF50; color:white; font-weight:bold; border-radius:4px;")
        self.btn_import_excel.clicked.connect(self.import_excel_with_merge)
        preview_layout.addWidget(self.btn_import_excel)

        self.btn_copy = QPushButton("📋")
        # self.btn_copy.setToolTip("코드 클립보드에 복사")
        self.btn_copy.setFixedSize(30, 30)
        self.btn_copy.setStyleSheet("background-color:#2196F3; color:white; font-weight:bold; border-radius:4px;")
        # self.btn_copy.clicked.connect(self.copy_to_clipboard)
        # preview_layout.addWidget(self.btn_copy)
        # --- 드롭다운 메뉴(QMenu) 생성 ---
        option_menu = QMenu(self)

        # 0. 새로 시작
        action_new = option_menu.addAction(tr("main.menu.new"))
        action_new.triggered.connect(self.new_task)

        # 1. 파일 입출력 관련
        action_save = option_menu.addAction(tr("main.menu.save"))
        action_save.triggered.connect(self.save_table_action)

        action_save_as = option_menu.addAction(tr("main.menu.save_as"))
        action_save_as.triggered.connect(self.save_as_dialog)

        action_load = option_menu.addAction(tr("main.menu.load"))
        action_load.triggered.connect(self.load_table_dialog)

        action_import = option_menu.addAction(tr("main.menu.import_excel"))
        action_import.triggered.connect(self.import_excel_with_merge)

        action_import_latex_action = option_menu.addAction(tr("main.menu.import_latex"))
        # 2. 전역 단축키 설정 (F2)
        action_import_latex_action.setShortcut(QKeySequence("F2"))
        action_import_latex_action.triggered.connect(self.open_latex_import_dialog)

        # 구분선 추가
        option_menu.addSeparator()

        # 2. 복사 및 내보내기 관련
        action_copy = option_menu.addAction(tr("main.menu.copy_clipboard"))
        action_copy.triggered.connect(self.copy_to_clipboard)

        action_export_tex = option_menu.addAction(tr("main.menu.export_tex"))
        action_export_tex.triggered.connect(self.export_tex)

        # 기존의 단일 action 대신 Menu를 추가합니다.
        export_menu = option_menu.addMenu(tr("main.menu.export_tex_menu"))

        # 1. oblivoir
        action_oblivoir = export_menu.addAction("oblivoir")
        action_oblivoir.setShortcut("Shift+Ctrl+T") # 단축키 유지
        action_oblivoir.triggered.connect(lambda: self.export_tex_with_class("oblivoir"))

        # 2. standalone
        action_standalone = export_menu.addAction("standalone")
        action_standalone.triggered.connect(lambda: self.export_tex_with_class("standalone"))

        # 3. article
        action_article = export_menu.addAction("article")
        action_article.triggered.connect(lambda: self.export_tex_with_class("article"))

        # 추가. 미리보기
        action_preview = export_menu.addAction("preview (Alt+P)")
        action_preview.triggered.connect(self.export_preview_tex)
        action_preview.setShortcut(QKeySequence("Alt+P"))

        # 4. another class
        action_custom = export_menu.addAction("class selection...")
        action_custom.triggered.connect(self.prompt_custom_class_and_export)

        action_export_csv = option_menu.addAction(tr("main.menu.export_csv"))
        action_export_csv.triggered.connect(self.export_csv)

        # 구분선 추가 (도움말 영역 분리)
        option_menu.addSeparator()

        # 3. 도움말
        action_help = option_menu.addAction(tr("main.menu.help")) 
        action_help.triggered.connect(self.show_help)

        # [추가] 언어 선택 서브메뉴 (경량 자체 i18n: ko/en 즉시 전환)
        # 체크 표시(✓) = 지금 화면에 실제로 적용되어 있는 언어(activie_language)
        # 다른 표시(◆)  = 방금 선택했지만 재시작 전까지는 아직 적용되지 않은 "대기 중" 언어
        language_menu = option_menu.addMenu(tr("main.menu.language"))
        self.action_lang_ko = language_menu.addAction("한국어")
        self.action_lang_ko.setCheckable(True)
        self.action_lang_ko.triggered.connect(lambda: self.change_language("ko"))

        self.action_lang_en = language_menu.addAction("English")
        self.action_lang_en.setCheckable(True)
        self.action_lang_en.triggered.connect(lambda: self.change_language("en"))

        # 메뉴가 열릴 때마다(언어를 바꾼 뒤 다시 열어도) 체크/대기 표시를 최신 상태로 갱신
        option_menu.aboutToShow.connect(self._refresh_language_menu)
        self._refresh_language_menu()

        option_menu.addSeparator()

        action_exit = option_menu.addAction(tr("main.menu.exit"))
        action_exit.triggered.connect(self.quit_and_copy)

        # --- 버튼에 메뉴 연결 및 레이아웃에 추가 ---
        self.btn_copy.setMenu(option_menu)
        preview_layout.addWidget(self.btn_copy) # 이 부분은 기존 코드에 맞춰서 유지!

        self.btn_toggle_settings = QPushButton(tr("main.btn.toggle_settings_open"))
        self.btn_toggle_settings.setCheckable(True)
        self.btn_toggle_settings.setFixedHeight(30)
        self.btn_toggle_settings.setFixedWidth(100)
        self.btn_toggle_settings.setStyleSheet("color: white; font-weight: bold; background-color: #333333;") 
        self.btn_toggle_settings.toggled.connect(self._on_settings_toggled)
        preview_layout.addWidget(self.btn_toggle_settings)

        # 단축키 설정
        self.toggle_shortcut = QShortcut(QKeySequence("Ctrl+="), self)
        self.toggle_shortcut.activated.connect(self.btn_toggle_settings.toggle)
        
        top_layout.addLayout(preview_layout)

        # ---------------------------------------------------------
        # 2. 콘텐츠 스플리터 (표 + 설정 패널 가로 분할)
        # ---------------------------------------------------------
        content_splitter = QSplitter(Qt.Horizontal)
        top_layout.addWidget(content_splitter)

        # --- 표 (Table) ---
        self.table = QTableWidget()
        if sys.platform == "darwin":
            consolas_font = QFont("Menlo", 10)
        else:
            consolas_font = QFont("Consolas", 10)
        self.table.setFont(consolas_font)
        self.table.setShowGrid(False)  # QTableView의 기본 괘선을 숨깁니다.

        self.table.currentCellChanged.connect(lambda *args: self.table.viewport().update())
        self.table.itemSelectionChanged.connect(lambda *args: self.table.viewport().update())
        self.table.setStyleSheet("QTableWidget { outline: none; }")

        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.installEventFilter(self)
        
        self.border_delegate = TableBorderDelegate(self.table)
        self.table.setItemDelegate(self.border_delegate)

        content_splitter.addWidget(self.table)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # ---------------------------------------------------------
        # 3. 오른쪽 설정 패널
        # ---------------------------------------------------------
        self.settings_panel = QWidget()
        self.settings_panel.setFixedWidth(450)
        settings_main_layout = QVBoxLayout(self.settings_panel)
        settings_main_layout.setContentsMargins(0, 0, 0, 0)

        # 환경 선택 콤보박스
        env_layout = QHBoxLayout()
        env_layout.addWidget(QLabel(tr("panel.env_label")))
        self.env_combobox = QComboBox()
        self.env_combobox.addItems(["tblr", "longtblr", "talltblr"])
        env_layout.addWidget(self.env_combobox)
        settings_main_layout.addLayout(env_layout)

        # 탭 위젯 생성
        self.settings_tabs = QTabWidget()
        settings_main_layout.addWidget(self.settings_tabs)

        # =========================================================
        # ★ [수정된 부분] 탭 1: 기본 설정 (내부에 QMainWindow 삽입)
        # =========================================================
        self.tab_basic = QWidget()
        tab_basic_layout = QVBoxLayout(self.tab_basic)
        tab_basic_layout.setContentsMargins(5, 5, 5, 5)

        # (1) 상단 고정 영역 (Table Size, Colspec Mode 등)
        top_fixed_widget = QWidget()
        settings_form_layout = QFormLayout(top_fixed_widget)
        tab_basic_layout.addWidget(top_fixed_widget)

        # 표 크기 설정
        size_layout = QHBoxLayout()
        size_layout.setSpacing(5)
        
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 999)
        self.spin_rows.setValue(2)
        self.spin_rows.setFixedWidth(75)

        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(1, 99)
        self.spin_cols.setValue(3)
        self.spin_cols.setFixedWidth(75)

        self.btn_resize = QPushButton(tr("panel.apply_btn"))
        self.btn_resize.setStyleSheet("background-color:#9C27B0; color:white; font-weight:bold;")
        
        size_layout.addWidget(QLabel(tr("panel.rows_label")))
        size_layout.addWidget(self.spin_rows)
        size_layout.addWidget(QLabel(tr("panel.cols_label")))
        size_layout.addWidget(self.spin_cols)
        size_layout.addWidget(self.btn_resize)
        
        settings_form_layout.addRow(tr("panel.table_size"), size_layout)

        self.btn_resize.clicked.connect(lambda: self.resize_table(self.spin_rows.value(), self.spin_cols.value()))

        # 라디오 버튼 (Colspec Mode)
        self.radio_natural = QRadioButton("natural")
        self.radio_linewidth = QRadioButton("linewidth")
        self.radio_manual = QRadioButton("manual")
        self.radio_linewidth.setChecked(True)

        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.radio_natural)
        self.mode_group.addButton(self.radio_linewidth)
        self.mode_group.addButton(self.radio_manual)

        self.btn_edit_colspec = QPushButton(tr("panel.edit_colspec_btn"))
        self.btn_edit_colspec.setMinimumWidth(100)
        self.btn_edit_colspec.clicked.connect(self.open_colspec_dialog)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.radio_natural)
        radio_layout.addWidget(self.radio_linewidth)
        radio_layout.addWidget(self.radio_manual)
        radio_layout.addStretch()
        radio_layout.addWidget(self.btn_edit_colspec)

        settings_form_layout.addRow(tr("panel.colspec_mode"), radio_layout)

        # manual Colspec 표시부
        self.input_colspec = QLineEdit()
        self.input_colspec.setReadOnly(True)
        self.input_colspec.setPlaceholderText(tr("panel.manual_colspec_placeholder"))
        if sys.platform == "darwin":
            self.input_colspec.setMinimumWidth(255)
            
        settings_form_layout.addRow(tr("panel.manual_colspec_label"), self.input_colspec)

        # ---------------------------------------------------------
        # (2) 하단 도킹 영역 (여기서 에디터 4개를 떼어낼 수 있습니다!)
        # ---------------------------------------------------------
        self.inner_dock_window = QMainWindow()
        self.inner_dock_window.setWindowFlags(Qt.Widget) # 위젯처럼 동작하도록 설정
        tab_basic_layout.addWidget(self.inner_dock_window, 1) # 남는 공간 채우기

        # 중앙을 비워두기 위한 더미 위젯
        dummy_central = QWidget()
        dummy_central.setFixedSize(0, 0)
        self.inner_dock_window.setCentralWidget(dummy_central)

        # --- 개별 에디터 위젯 생성 및 DockWidget으로 포장 ---
        # 사용할 DockWidget 옵션 (이동 가능, 띄우기 가능 / 단, 닫기 버튼은 없음)
        dock_features = QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable

        # 1. Lines
        self.input_lines = QPlainTextEdit("")
        self.input_lines.setMinimumHeight(50)
        dock_lines = QDockWidget("Lines", self.inner_dock_window)
        dock_lines.setFeatures(dock_features) # <--- 닫기 버튼 제거 설정 적용
        dock_lines.setWidget(self.input_lines)
        self.inner_dock_window.addDockWidget(Qt.BottomDockWidgetArea, dock_lines)

        # 2. Row/Col Format
        self.input_row_format = QTextEdit("row{odd} = {bg=gray!10}")
        self.input_row_format.setMinimumHeight(50)
        dock_row = QDockWidget("Row/Col Format", self.inner_dock_window)
        dock_row.setFeatures(dock_features) # <--- 닫기 버튼 제거 설정 적용
        dock_row.setWidget(self.input_row_format)
        self.inner_dock_window.addDockWidget(Qt.BottomDockWidgetArea, dock_row)

        # 3. Cell Format
        self.input_cell_format = QTextEdit()
        self.input_cell_format.setMinimumHeight(50)
        dock_cell = QDockWidget("Cell Format", self.inner_dock_window)
        dock_cell.setFeatures(dock_features) # <--- 닫기 버튼 제거 설정 적용
        dock_cell.setWidget(self.input_cell_format)
        self.inner_dock_window.addDockWidget(Qt.BottomDockWidgetArea, dock_cell)

        # 4. Generic
        self.input_general_settings = QTextEdit()
        self.input_general_settings.setMinimumHeight(30)
        dock_general = QDockWidget("Generic", self.inner_dock_window)
        dock_general.setFeatures(dock_features) # <--- 닫기 버튼 제거 설정 적용
        dock_general.setWidget(self.input_general_settings)
        self.inner_dock_window.addDockWidget(Qt.BottomDockWidgetArea, dock_general)

        # 4개의 위젯이 탭 안에서 세로로 정돈되도록 분할 배치
        self.inner_dock_window.splitDockWidget(dock_lines, dock_row, Qt.Vertical)
        self.inner_dock_window.splitDockWidget(dock_row, dock_cell, Qt.Vertical)
        self.inner_dock_window.splitDockWidget(dock_cell, dock_general, Qt.Vertical)

        # 완성된 기본 설정 탭을 추가
        self.settings_tabs.addTab(self.tab_basic, tr("panel.tab_basic"))

        # --- 탭 2: Long/Tall 설정 ---
        self.tab_longtall = QWidget()
        layout_longtall = QVBoxLayout(self.tab_longtall)

        layout_longtall.addWidget(QLabel(tr("panel.outer_options_label")))
        self.outer_options_input = QPlainTextEdit() 
        self.outer_options_input.setMinimumHeight(80)
        layout_longtall.addWidget(self.outer_options_input, 1)
        if sys.platform == "darwin":
            self.outer_options_input.setStyleSheet("font-family: Menlo; padding:4px;")
        else:
            self.outer_options_input.setStyleSheet("font-family: Consolas; padding:4px;")

        self.inner_extra_label = QLabel(tr("panel.inner_extra_label"))
        layout_longtall.addWidget(self.inner_extra_label)
        
        self.inner_extra_input = QPlainTextEdit()
        self.inner_extra_input.setMinimumHeight(80)
        if sys.platform == "darwin":
            self.inner_extra_input.setStyleSheet("font-family: Menlo; padding:4px;")
        else:
            self.inner_extra_input.setStyleSheet("font-family: Consolas; padding:4px;")

        layout_longtall.addWidget(self.inner_extra_input, 1)

        self.settings_tabs.addTab(self.tab_longtall, tr("panel.tab_longtall"))

        # ---------------------------------------------------------
        # 조립 및 시그널 연결
        # ---------------------------------------------------------
        content_splitter.addWidget(self.settings_panel)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 0)

        # 이벤트 및 초기화
        self.env_combobox.currentTextChanged.connect(self.update_tab_state)
        self.update_tab_state(self.env_combobox.currentText())

        self.env_combobox.currentTextChanged.connect(self.generate_latex)
        self.outer_options_input.textChanged.connect(self.generate_latex)
        self.inner_extra_input.textChanged.connect(self.generate_latex)
        
        self.radio_natural.toggled.connect(self.generate_latex)
        self.radio_linewidth.toggled.connect(self.generate_latex)
        self.radio_manual.toggled.connect(self.generate_latex)

        self.ignore_colspec_validation = False
        self.radio_linewidth.toggled.connect(self.reset_colspec_validation)
        self.radio_natural.toggled.connect(self.reset_colspec_validation)
        self.radio_manual.toggled.connect(self.reset_colspec_validation)

        # 최상단 위젯을 메인 스플리터에 추가
        splitter.addWidget(top_widget)

        # ---------------------------------------------------------
        # 4. 하단 영역 스플리터
        # ---------------------------------------------------------
        bottom_splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(bottom_splitter)

        # 1. 셀 에디터 (하단 좌측)
        self.cell_editor = QPlainTextEdit()
        # self.cell_editor.setFixedHeight(50) <-- 세로 고정 제한 해제! 
        bottom_splitter.addWidget(self.cell_editor)

        if sys.platform == "darwin":
            self.cell_editor.setStyleSheet("font-family: Menlo; padding:4px;")
        else:
            self.cell_editor.setStyleSheet("font-family: Consolas; padding:4px;")

        # 2. 코드 프리뷰(output_text) (하단 우측)
        
        # --- 프리뷰 영역을 묶을 최상위 컨테이너와 수직 레이아웃 ---
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        # --- 메인 프리뷰 (출력창) 설정 ---
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        if sys.platform == "darwin":
            self.output_text.setStyleSheet("font-family: Menlo; padding:4px;")
        else:
            self.output_text.setStyleSheet("font-family: Consolas; padding:4px;")

        palette = self.output_text.palette()
        palette.setColor(QPalette.Base, QApplication.palette().color(QPalette.Base))
        palette.setColor(QPalette.Text, QApplication.palette().color(QPalette.Text))
        self.output_text.setPalette(palette)

        # --- 예외 케이스 처리용 컨트롤 영역 (가로 배치) ---
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 5, 0, 0) # 위쪽 출력창과 약간의 여백만 부여
        
        self.bottomrule_checkbox = QCheckBox(tr("panel.bottomrule_checkbox"))
        self.bottomrule_checkbox.setChecked(False)
        self.bottomrule_checkbox.toggled.connect(self.generate_latex)

        self.extra_cmd_input = QLineEdit()
        self.extra_cmd_input.setPlaceholderText(tr("panel.bottomrule_placeholder"))
        self.extra_cmd_input.setMaximumWidth(200)
        self.extra_cmd_input.textChanged.connect(self.generate_latex) 

        # 시선을 빼앗지 않도록 흐리게(Dim) 처리
        dim_style = "color: #888888; font-size: 11px;"
        self.bottomrule_checkbox.setStyleSheet(dim_style)
        # 입력창도 테두리를 연하게 하고 배경을 투명하게 빼서 존재감을 없앰
        self.extra_cmd_input.setStyleSheet("color: #888888; font-size: 11px; border: 1px solid #cccccc; background: transparent;")

        # 컨트롤 레이아웃에 위젯 추가
        control_layout.addWidget(self.bottomrule_checkbox)
        control_layout.addWidget(self.extra_cmd_input)
        control_layout.addStretch()

        # ==========================================
        # [추가] PDF 미리보기 컴파일 (엔진 선택 + 실행 버튼)
        # 컴파일은 QProcess로 비동기 실행하며, 성공 시 시스템 기본 PDF 뷰어로 열고
        # 실패해도 앱은 죽지 않고 로그 요약만 보여줌 (자세한 건 .log 파일에서 직접 확인)
        # ==========================================
        self.preview_engine_combo = QComboBox()
        self.preview_engine_combo.addItems(["pdflatex", "xelatex", "lualatex"])
        self.preview_engine_combo.setToolTip(tr("panel.preview_engine_tooltip"))
        self.preview_engine_combo.setMaximumWidth(100)
        saved_engine = self.settings.value("preview_engine", "pdflatex")
        idx = self.preview_engine_combo.findText(saved_engine)
        if idx >= 0:
            self.preview_engine_combo.setCurrentIndex(idx)
        self.preview_engine_combo.currentTextChanged.connect(
            lambda text: self.settings.setValue("preview_engine", text)
        )
        control_layout.addWidget(self.preview_engine_combo)

        self.btn_compile_preview = QPushButton(tr("panel.preview_btn"))
        self.btn_compile_preview.setToolTip(tr("panel.preview_btn_tooltip"))
        self.btn_compile_preview.clicked.connect(self.compile_preview_pdf)
        control_layout.addWidget(self.btn_compile_preview)

        self.preview_process = None  # QProcess 인스턴스 보관용
        self._preview_target_dir = None  # 컴파일 대상 폴더 (finished 콜백에서 참조)

        QShortcut(QKeySequence("Alt+Shift+P"), self).activated.connect(self.compile_preview_pdf)

        # --- 메인 수직 레이아웃에 조립 (순서: 1. 출력창 -> 2. 컨트롤 영역) ---
        preview_layout.addWidget(self.output_text)
        preview_layout.addLayout(control_layout)

        # --- 공통 폰트 설정 ---
        if sys.platform == "darwin":
            fixed_font = QFont("Menlo", 10)
        else:
            fixed_font = QFont("Consolas", 10)

        # 적용할 위젯 리스트
        for widget in [
            self.input_lines,
            self.input_row_format,
            self.input_cell_format,
            self.input_general_settings,
            self.input_colspec
        ]:
            widget.setFont(fixed_font)

        # --- 최종 컨테이너를 스플리터에 추가 ---
        bottom_splitter.addWidget(preview_container)

        # 하단 영역 내부의 좌우 비율 설정 (예: 셀 에디터 1 : 프리뷰 3)
        bottom_splitter.setStretchFactor(0, 1)
        bottom_splitter.setStretchFactor(1, 3)
        # ---------------------------------------------------------

        # 초기 크기 비율 설정
        splitter.setStretchFactor(0, 0)   # 위쪽은 고정
        splitter.setStretchFactor(1, 1)   # 아래쪽은 늘어나도록
        splitter.setSizes([400, 250])     # 시작 비율

        # 1. 상태 표시줄 설정
        self.statusbar = self.statusBar()
        
        # 2. 평상시 위치를 보여줄 영구 라벨 설정
        self.pos_label = QLabel("(0, 0)")
        # 영구 위젯으로 추가하여 임시 메시지에 가려지거나 밀리지 않게 함
        self.statusbar.addPermanentWidget(self.pos_label)

        # 3. QTableWidget 시그널 연결 (객체 이름이 self.table_widget 이라 가정)
        self.table.currentCellChanged.connect(self.update_position)

        # 시그널 연결
        self.table.itemChanged.connect(self.generate_latex)
        self.input_lines.textChanged.connect(self.generate_latex)
        self.input_row_format.textChanged.connect(self.generate_latex)
        self.input_cell_format.textChanged.connect(self.generate_latex)
        self.input_general_settings.textChanged.connect(self.generate_latex)
        # self.input_colspec.textChanged.connect(self.sync_colspec_preview)

        # 셀 에디터 ↔ 표 동기화
        self.cell_editor.textChanged.connect(self.sync_editor_to_cell)
        self.table.currentCellChanged.connect(self.sync_cell_to_editor)

        # [Ctrl+Q]
        self.shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.shortcut_quit.activated.connect(self.quit_and_copy)

        # [F4 단축키 설정] 앱 전체에서 작동하도록 QShortcut 사용
        self.shortcut_copy = QShortcut(QKeySequence("F4"), self)
        self.shortcut_copy.activated.connect(self.copy_to_clipboard)

        # # F5 및 저장/로드 단축키
        QShortcut(QKeySequence("F5"), self).activated.connect(self.insert_cell_format)
        
        # 새로 추가하는 단축키 연결
        QShortcut(QKeySequence("F6"), self).activated.connect(self.insert_row_format)
        QShortcut(QKeySequence("Ctrl+F6"), self).activated.connect(self.insert_column_format)

        # --- 도우미 함수 ---
        def trigger_advanced_format(format_type):
            # 0-based 인덱스를 1-based 인덱스로 변환하기 위해 +1 추가!
            row = self.table.currentRow() + 1
            col = self.table.currentColumn() + 1
            
            # 선택된 셀이 있을 때만 실행 (기본값이 -1이므로 +1을 하면 0이 됨)
            if row > 0 and col > 0:
                self.goto_or_create_format(format_type, row, col)

        # --- 단축키 할당 ---
        QShortcut(QKeySequence("Shift+F5"), self).activated.connect(lambda: self.goto_or_create_format('cell'))
        QShortcut(QKeySequence("Shift+F6"), self).activated.connect(lambda: self.goto_or_create_format('row'))
        QShortcut(QKeySequence("Shift+Ctrl+F6"), self).activated.connect(lambda: self.goto_or_create_format('col'))

        # F1 → 도움말 표시
        shortcut = QShortcut(QKeySequence("F1"), self)
        shortcut.activated.connect(self.show_help)

        # [추가] 셀 에디터로 포커스 이동 (Ctrl+Ins)
        shortcut_focus_editor = QShortcut(QKeySequence("Ctrl+Insert"), self)
        shortcut_focus_editor = QShortcut(QKeySequence("Ctrl+E"), self)
        shortcut_focus_editor.activated.connect(self.move_focus_to_cell_editor)
        # ---------------------------------------------------------

        # ESC 누르면 탭 위젯으로 포커스 이동
        shortcut_focus_tabs = QShortcut(QKeySequence("Escape"), self.cell_editor)
        shortcut_focus_tabs.activated.connect(self.move_focus_to_tabs)

        # Ctrl+T: 일반 tex 파일 내보내기
        self.shortcut_export_tex = QShortcut(QKeySequence("Ctrl+T"), self)
        self.shortcut_export_tex.activated.connect(self.export_tex)

        self.setup_shortcuts()   # 반드시 호출해야 함

        # --- 텍스트 위젯 일괄 단축키 설정 ---
        text_widgets = [self.input_lines, self.input_row_format, self.input_cell_format]

        for widget in text_widgets:
            # Ctrl+F (찾기)
            shortcut_f = QShortcut(QKeySequence("Ctrl+F"), widget)
            shortcut_f.setContext(Qt.WidgetShortcut)
            # lambda w=widget: 파이썬의 클로저(Closure) 특성을 이용해 현재 위젯을 안전하게 넘김
            shortcut_f.activated.connect(lambda w=widget: self.find_in_text_widget(w))

            # Ctrl+H (모두 바꾸기)
            shortcut_h = QShortcut(QKeySequence("Ctrl+H"), widget)
            shortcut_h.setContext(Qt.WidgetShortcut)
            shortcut_h.activated.connect(lambda w=widget: self.replace_in_text_widget(w))

        # 초기 표 생성
        self.resize_table(2, 3)
        header = self.table.horizontalHeader()
        
        # Fixed 대신 Interactive 적용: 마우스 드래그 조절 허용
        header.setSectionResizeMode(QHeaderView.Interactive) 
        
        # 초기 기본 셀 가로폭은 80픽셀로 유지 (사용자가 필요하면 직접 늘려 씀)
        header.setDefaultSectionSize(80)

        # [추가] 열 너비가 조절될 때 발생하는 시그널 연결
        header.sectionResized.connect(self.sync_column_widths)

        # input_cell_format의 텍스트가 바뀔 때마다 sync_table_highlights 함수 실행
        self.input_cell_format.textChanged.connect(self.sync_table_highlights)

        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)

        self.input_lines.textChanged.connect(self.update_borders_preview)

        # 초기 상태 반영
        self.update_borders_preview()

        # --- [수정된 템플릿 폴더 경로 계산 로직] ---
        if getattr(sys, 'frozen', False):
            # PyInstaller로 빌드된 패키지 환경일 때
            if platform.system() == "Darwin":
                # 🍏 macOS App 번들 내부에는 쓰기가 불가능하므로 유저 홈의 Documents(문서) 폴더 활용
                self.template_dir = os.path.join(
                    os.path.expanduser("~"), "Documents", "tblrDoumi", "templates"
                )
            else:
                # 🪟 Windows 환경 (Inno Setup 배포본 위치 기준)
                self.template_dir = os.path.join(os.path.dirname(sys.executable), "templates")
        else:
            # 일반 python 스크립트 개발/테스트 환경일 때
            self.template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        
        # 지정된 경로에 templates 폴더가 없으면 자동으로 생성해 둡니다.
        # templates 폴더가 없으면 새로 만들고, 번들 안의 기본 샘플 복사하기
        if not os.path.exists(self.template_dir):
            try:
                os.makedirs(self.template_dir)
                
                # macOS 번들 안에 임베드된 원본 기본 템플릿 경로 탐색 (_MEIPASS 활용)
                if getattr(sys, 'frozen', False) and platform.system() == "Darwin":
                    import shutil
                    import glob
                    
                    # PyInstaller가 임시 압축 해제하는 내부 경로
                    bundle_template_src = os.path.join(getattr(sys, '_MEIPASS', ''), 'templates')
                    
                    if os.path.exists(bundle_template_src):
                        # 내부의 .tblr 파일들을 새로 만든 유저 문서 폴더로 복사
                        for f_path in glob.glob(os.path.join(bundle_template_src, "*.tblr")):
                            shutil.copy(f_path, self.template_dir)
                            
            except Exception as e:
                # print(f"템플릿 초기화 실패: {str(e)}")
                pass

        # 처음 실행 시 2x3 빈 상태로 시작 (3)
        self.spin_rows.setValue(2)
        self.spin_cols.setValue(3)
        self.clear_all_settings_to_default(r=2, c=3)

    # +++++++++++++++++++++++++++
    # Methods
    # +++++++++++++++++++++++++++

    def update_window_title(self):
        base_title = tr("main.window_title")
        if self.current_file:
            filename = QFileInfo(self.current_file).fileName()
            self.setWindowTitle(f"{filename} - {base_title}")
        else:
            self.setWindowTitle(base_title)

    def _on_settings_toggled(self, checked):
        # 1. 패널 보이기/숨기기
        self.settings_panel.setVisible(not checked)

        # 2. 버튼 텍스트 변경
        if checked:
            self.btn_toggle_settings.setText(tr("main.btn.toggle_settings_close"))
        else:
            self.btn_toggle_settings.setText(tr("main.btn.toggle_settings_open"))

    def update_borders_preview(self):
        """텍스트를 파싱하여 Delegate에 펜 데이터를 전달합니다."""
        h_pens, v_pens = self.parse_lines_text_to_pens()
        self.border_delegate.set_border_data(h_pens, v_pens)

    def parse_lines_text_to_pens(self):
        """self.input_lines의 텍스트를 분석하여 펜 데이터를 생성합니다."""
        parsed_hlines = {} 
        parsed_vlines = {}

        # =========================================================
        # [신규 추가] 현재 테이블의 배경색을 읽어와서 다크 테마인지 판별합니다.
        # =========================================================
        palette = self.table.palette()
        bg_color = palette.color(QPalette.ColorRole.Base)
        # 배경색의 밝기(lightness)가 128보다 작으면 어두운 색(다크 모드)으로 간주
        is_dark_theme = bg_color.lightness() < 128 

        # 테마에 따른 맞춤형 색상 팔레트 준비
        default_color = QColor("white") if is_dark_theme else QColor("black")
        thick_color = QColor("#ffb74d") if is_dark_theme else QColor("darkbrown") # 다크: 밝은 오렌지
        double_color = QColor("#4fc3f7") if is_dark_theme else QColor("blue")     # 다크: 밝은 하늘색
        # =========================================================

        text = self.input_lines.toPlainText()
        lines = text.split('\n')

        num_rows = self.table.rowCount()
        num_cols = self.table.columnCount()

        pattern = re.compile(r'^(hline|vline)\s*\{([^}]+)\}\s*=\s*(.*)')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 주석 라인 중 hline/vline 패턴이 있으면 '%' 제거 후 파싱
            if line.startswith('%'):
                if line.lstrip('%').strip().startswith(('hline', 'vline')):
                    line = line.lstrip('%').strip()
                else:
                    continue

            # --- 단독 명령어(hlines, vlines)를 정규식 포맷에 맞게 치환 ---
            if line == 'hlines':
                line = 'hline{1-Z} = {}'
            elif line == 'vlines':
                line = 'vline{1-Z} = {}'
            # --------------------------------------------------------

            match = pattern.match(line)

            if match:
                line_type = match.group(1) 
                range_str = match.group(2) 
                rhs = match.group(3).lower()

                # =========================================================
                # [핵심 수정 파트] Z값을 두 가지 의미로 완벽하게 분리
                # =========================================================
                # 1. 대상 선 (Target Line): 외곽을 닫아야 하므로 개수 + 1
                target_max = (num_rows + 1) if line_type == 'hline' else (num_cols + 1)
                
                # 2. 적용 범위 (Extent Cell): 
                # 가로선을 그을 땐 열(Col) 끝까지, 세로선을 그을 땐 행(Row) 끝까지
                extent_max = num_cols if line_type == 'hline' else num_rows
                # =========================================================

                # --- 1. 대상 선(Target)의 Z, Y, X 치환 ---
                range_str = re.sub(r'[Zz]', str(target_max), range_str)
                range_str = re.sub(r'[Yy]', str(target_max - 1), range_str)
                range_str = re.sub(r'[Xx]', str(target_max - 2), range_str)

                # --- 펜 스타일 설정 ---
                pen = QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.SolidLine) 
                is_double = 'double' in rhs

                pt_match = re.search(r"(\d+\.?\d*)pt", rhs)
                pt_value = float(pt_match.group(1)) if pt_match else 0.0
                is_thick = pt_value >= 0.8 or 'thick' in rhs

                is_dotted = 'dotted' in rhs
                is_dashed = 'dashed' in rhs

                # 기본값 설정 (초기화)
                # pen.setColor(QColor("black"))
                # pen.setWidthF(0.8)
                # pen.setStyle(Qt.PenStyle.SolidLine)
                pen.setColor(default_color)
                pen.setWidthF(0.8)
                pen.setStyle(Qt.PenStyle.SolidLine)

                # 두께 및 색상 결정
                if is_thick:
                    pen.setColor(thick_color)
                    pen.setWidthF(2.8)

                if is_double:
                    pen.setColor(double_color)
                    pen.setWidthF(2.5) 

                # 선 스타일 결정
                if is_dotted:
                    pen.setStyle(Qt.PenStyle.DotLine)
                elif is_dashed:
                    pen.setStyle(Qt.PenStyle.DashLine)

                # --- 적용 범위 분석 ---
                # target_max를 이용해 어떤 선(Line)들에 그릴지 확정
                targets = self._expand_range_string(range_str, target_max) 
                sub_range_cols = "-" 

                # --- 2. 적용 범위(Extent Cell)의 Z, Y, X 치환 ---
                blocks = re.findall(r'\{([^}]*)\}', match.group(3))
                for block in blocks:
                    block = block.strip()
                    if re.match(r'^[\d\-,\sZzXxYy]+$', block):
                        
                        # 기존: block = re.sub(r'[ZzXxYy]', str(extent_max), block)
                        
                        # 변경 후: 셀 범위도 똑같이 Z, Y, X의 비율에 맞춰 줄여줍니다.
                        block = re.sub(r'[Zz]', str(extent_max), block)
                        block = re.sub(r'[Yy]', str(extent_max - 1), block)
                        block = re.sub(r'[Xx]', str(extent_max - 2), block)
                        
                        sub_range_cols = self._expand_range_string(block, extent_max)
    
                # --- 데이터 구조에 채워 넣기 ---
                data_dict = parsed_hlines if line_type == 'hline' else parsed_vlines
                
                for target in targets:
                    if target not in data_dict:
                        data_dict[target] = {}
                    
                    if isinstance(sub_range_cols, list):
                        for col in sub_range_cols:
                             if col != "-":
                                 try:
                                     data_dict[target][int(col)] = pen
                                 except ValueError:
                                     print(f"디버그 - 경고: '{col}'을(를) 정수로 변환할 수 없어 건너뜁니다.")
                    else:
                        data_dict[target]["-"] = pen

        return parsed_hlines, parsed_vlines

    # 헬퍼 함수: "1,3, 5-7" 같은 문자열을 [1, 3, 5, 6, 7] 리스트로 반환
    def _expand_range_string(self, range_str, max_val):
        if range_str.strip() == "-": return "-" 

        result = []
        # X와 Y를 모두 현재 테이블의 최대치(max_val)로 치환합니다.
        range_str = (
            range_str.upper()
            .replace('X', str(max_val - 1))
            .replace('Y', str(max_val))
        )

        parts = range_str.split(',')
        for part in parts:
            part = part.strip()
            if not part: continue
            
            if part == 'Z':
                result.append('Z')
            elif '-' in part:
                try:
                    start_str, end_str = part.split('-')
                    start = int(start_str)
                    
                    # [수정된 부분] 끝자리가 'Z'일 경우의 예외 처리 추가
                    if end_str == 'Z':
                        result.extend(range(start, max_val + 1)) # start부터 Y(max_val)까지 추가
                        result.append('Z') # Z는 문자열 그대로 추가
                    else:
                        end = int(end_str)
                        result.extend(range(start, end + 1))
                except ValueError: 
                    # 숫자로 변환할 수 없는 이상한 값이 들어오면 무시
                    pass
            elif part.isdigit():
                result.append(int(part))
                
        return list(set(result))

    def on_table_selection_changed(self):
        indexes = self.table.selectedIndexes()
        if not indexes:
            return
            
        # 현재 활성화된 첫 번째 셀 기준
        current_idx = indexes[0]
        
        # 사용자 눈에 보이는 행/열 번호 (1부터 시작)
        row_num = current_idx.row() + 1
        col_num = current_idx.column() + 1
        
        target_row_keyword = None
        target_cell_keyword = f"cell{{{row_num}}}" # cell은 행/열이 다 맞아야 하므로 유지

        # 인자 이름을 명시해서 호출 (순서 사고 방지!)
        self.highlight_target_format(
            text_edit=self.input_row_format, 
            target_keyword=target_row_keyword, 
            focus_row=row_num
        )

        # 2. Cell 포맷 박스 업데이트 (행과 열 번호 모두 전달!)
        self.highlight_target_format(
            text_edit=self.input_cell_format, 
            target_keyword=f"cell{{{row_num}}}{{{col_num}}}", # 정확히 일치하는 셀 강조용
            focus_row=row_num,
            focus_col=col_num
        )

        # on_table_selection_changed 내부 예시
        self.highlight_target_format(
            text_edit=self.input_row_format, # 예시 에디터
            target_keyword=None, # 특정 키워드 없으면 None
            focus_row=row_num,
            focus_col=col_num # << 이 부분이 있어야 column{...}이 동작합니다!
        )

    def insert_row_action(self, row_idx=None):
        if row_idx is None:
            row_idx = self.table.currentRow()
            # Ctrl+Enter의 기본 동작(현재 행 아래에 추가)을 맞추려면 +1
            if row_idx >= 0:
                 row_idx += 1 
            else:
                 row_idx = self.table.rowCount()
                 
        self.table.insertRow(row_idx)
        self.shift_format_entries('insert', 'row', row_idx + 1)
        self.shift_format_entries('insert', 'cell', row_idx + 1, scope='row')
        self.shift_format_entries('insert', 'hline', row_idx + 1)
        self._refresh_headers()
        self.spin_rows.setValue(self.table.rowCount())
        self.generate_latex()

    def delete_row_action(self, row_idx=None):
        if self.table.rowCount() == 0:
            return
        if row_idx is None:
            row_idx = self.table.currentRow()
            
        if row_idx >= 0:
            self.table.removeRow(row_idx)
            self.shift_format_entries('delete', 'row', row_idx + 1)
            self.shift_format_entries('delete', 'cell', row_idx + 1, scope='row')
            self.shift_format_entries('delete', 'hline', row_idx + 1)
            self._refresh_headers()
            self.spin_rows.setValue(self.table.rowCount())
            self.generate_latex()

    def insert_column_action(self, col_idx=None):
        if col_idx is None:
            col_idx = self.table.currentColumn()
            if col_idx >= 0:
                col_idx += 1
            else:
                col_idx = self.table.columnCount()
                
        self.table.insertColumn(col_idx)
        self.shift_format_entries('insert', 'column', col_idx + 1)
        self.shift_format_entries('insert', 'cell', col_idx + 1, scope='column')
        self.shift_format_entries('insert', 'vline', col_idx + 1)
        self._refresh_headers()
        self.spin_cols.setValue(self.table.columnCount())
        self.generate_latex()

    def delete_column_action(self, col_idx=None):
        if self.table.columnCount() == 0:
            return
        if col_idx is None:
            col_idx = self.table.currentColumn()
            
        if col_idx >= 0:
            self.table.removeColumn(col_idx)
            self.shift_format_entries('delete', 'column', col_idx + 1)
            self.shift_format_entries('delete', 'cell', col_idx + 1, scope='column')
            self.shift_format_entries('delete', 'vline', col_idx + 1)
            self._refresh_headers()
            self.spin_cols.setValue(self.table.columnCount())
            self.generate_latex()

    # 열 너비 조절
    def sync_column_widths(self, logicalIndex, oldSize, newSize):
        """선택된 여러 열 중 하나를 드래그해서 크기를 조절하면, 선택된 다른 열들도 같은 크기로 맞춤"""
        
        # 현재 선택된 모든 셀의 열(column) 인덱스를 중복 없이 수집
        selected_cols = set(idx.column() for idx in self.table.selectedIndexes())
        
        # 방금 너비를 조절한 열(logicalIndex)이 선택된 영역 안에 포함되어 있을 때만 동작
        if logicalIndex in selected_cols:
            header = self.table.horizontalHeader()
            
            # [매우 중요] 코드로 너비를 조절할 때 다시 sectionResized 시그널이 발생하여 
            # 무한 루프에 빠지는 것을 막기 위해 잠시 시그널을 차단합니다.
            header.blockSignals(True)
            
            for col in selected_cols:
                if col != logicalIndex:
                    header.resizeSection(col, newSize)
                    
            # 크기 조절이 끝난 후 다시 시그널 활성화
            header.blockSignals(False)

    # colspec dialog
    def open_colspec_dialog(self):
        # 1. 현재 테이블 열 개수 파악
        cols = self.table.columnCount()
        
        # 2. 다이얼로그에 띄울 초기값만 계산 (UI 상태는 아직 변경하지 않음!)
        if self.radio_linewidth.isChecked():
            # ==========================================
            # [수정됨] 단순 반복 대신 '상대 열 너비'를 계산하여 초기값으로 제안
            # ==========================================
            if cols > 0:
                widths = [self.table.columnWidth(col) for col in range(cols)]
                min_width = min(widths)
                if min_width <= 0: min_width = 80
                
                colspecs = []
                for w in widths:
                    rel_width = round(w / min_width, 1)
                    rel_str = str(int(rel_width)) if rel_width.is_integer() else str(rel_width)
                    colspecs.append(f"X[{rel_str},c,m]")
                
                proposed_colspec = " ".join(colspecs)
            else:
                proposed_colspec = ""
                
        elif self.radio_natural.isChecked():
            proposed_colspec = " ".join(["l"] * cols)
        else: # 이미 manual 모드인 경우
            proposed_colspec = self.input_colspec.text()

        # 3. 계산된 초기값을 다이얼로그에 전달하며 열기
        dialog = ColspecDialog(proposed_colspec, self)
        
        # 4. 사용자가 다이얼로그에서 '확인'을 눌렀을 때만 실제 상태 업데이트
        if dialog.exec():
            new_colspec = dialog.get_colspec()
            
            # QLineEdit 값 먼저 업데이트
            self.input_colspec.setText(new_colspec)
            
            # 라디오 버튼을 Manual 모드로 전환
            self.radio_manual.setChecked(True)
            
            # 확실한 갱신을 위해 LaTeX 생성 함수 명시적 호출
            # (이미 manual 상태였다면 setChecked가 시그널을 발생시키지 않을 수 있으므로)
            self.generate_latex()

    # 포커스 이동 함수 정의
    def move_focus_to_tabs(self):
        self.table.setFocus()

    def eventFilter(self, source, event):
        if source is self.table and event.type() == QEvent.KeyPress:
            # Ctrl+Enter → 현재 행의 아래에 새 행 추가
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                # 단, 기존 코드처럼 마지막 열에서만 동작하게 하려면 조건 추가
                if self.table.currentColumn() == self.table.columnCount() - 1:
                    self.insert_row_action()
                return True

            # Ctrl+Del → 현재 행 삭제
            if event.key() == Qt.Key_Delete and event.modifiers() == Qt.ControlModifier:
                self.delete_row_action()
                return True

            # F7 → 열 추가 (1번 행에서만 동작하도록 제한하는 기존 조건 유지)
            if event.key() == Qt.Key_F7:
                if self.table.currentRow() == 0:
                    self.insert_column_action()
                return True

            # F8 → 열 삭제 (1번 행에서만 동작하도록 제한하는 기존 조건 유지)
            if event.key() == Qt.Key_F8:
                if self.table.currentRow() == 0:
                    self.delete_column_action()
                return True

            # Ctrl+Home → 첫 행으로 이동
            if event.key() == Qt.Key_Home and event.modifiers() == Qt.ControlModifier:
                self.table.setCurrentCell(0, self.table.currentColumn())
                return True

            # Ctrl+End → 마지막 행으로 이동
            if event.key() == Qt.Key_End and event.modifiers() == Qt.ControlModifier:
                last_row = self.table.rowCount() - 1
                self.table.setCurrentCell(last_row, self.table.currentColumn())
                return True

            if event.modifiers() == Qt.ControlModifier:
                if event.key() == Qt.Key_M:
                    self.merge_cells()
                    return True
                elif event.key() == Qt.Key_U: # Unmerge의 U
                    self.unmerge_cells()
                    return True

            # Shift+Alt(Mac은 Ctrl)+H → hline 삽입 (현재 행 + 맨 아랫줄 Z 포함)
            if event.modifiers() == (self.alt_mod | Qt.ShiftModifier) and event.key() == Qt.Key_H:
                self.insert_hline_format(include_z=True)
                return True
                
            # Alt(Mac은 Ctrl)+H → hline 삽입 (현재 행만)
            elif event.modifiers() == self.alt_mod and event.key() == Qt.Key_H:
                self.insert_hline_format(include_z=False)
                return True

            # Shift+Alt(Mac은 Ctrl)+V → vline 삽입 (현재 열 + 맨 끝 열 Z 포함)
            if event.modifiers() == (self.alt_mod | Qt.ShiftModifier) and event.key() == Qt.Key_V:
                self.insert_vline_format(include_z=True)
                return True

            # Alt(Mac은 Ctrl)+V → vline 삽입 (현재 열만)
            elif event.modifiers() == self.alt_mod and event.key() == Qt.Key_V:
                self.insert_vline_format(include_z=False)
                return True

            # Alt(Mac은 Ctrl)+Z → 마지막 행 괘선
            if event.modifiers() == self.alt_mod and event.key() == Qt.Key_Z:
                self.insert_z_line_format(is_horizontal=True)
                return True

            # Shift+Alt(Mac은 Ctrl)+Z → 마지막 열 괘선
            if event.modifiers() == (self.alt_mod | Qt.ShiftModifier) and event.key() == Qt.Key_Z:
                self.insert_z_line_format(is_horizontal=False)
                return True

            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_F10:
                
                # 1. 현재 테이블 열 개수 파악
                cols = self.table.columnCount()
                current_colspec = ""

                # 2. F10을 누른 시점의 상태에 따라 colspec 뼈대 생성
                if self.radio_linewidth.isChecked():
                    current_colspec = " ".join(["X[c,m]"] * cols)
                elif self.radio_natural.isChecked():
                    current_colspec = " ".join(["l"] * cols)
                
                # 3. '직접 입력' 필드에 값 채우기 
                # (이미 manual 모드인 상태에서 F10을 실수로 눌렀을 때 기존 입력값을 날리지 않도록 방어)
                if current_colspec: 
                    self.input_colspec.setText(current_colspec)

                # 4. 무조건 Manual 모드로 전환 및 포커스 이동 (가장 중요한 부분)
                self.radio_manual.setChecked(True)
                self.input_colspec.setFocus()

                return True

            if event.key() == Qt.Key_N and event.modifiers() & Qt.ControlModifier:
                self.new_task()
                return True

            if event.type() == QEvent.Type.KeyPress and source is self.table:
                if event.matches(QKeySequence.StandardKey.Copy):
                    self.copy_selection()
                    return True
                elif event.matches(QKeySequence.StandardKey.Paste):
                    self.paste_selection()
                    return True
                elif event.matches(QKeySequence.StandardKey.Cut):
                    self.cut_selection()
                    return True
                elif event.key() == Qt.Key.Key_Delete: # Delete 키 처리 추가
                    self.delete_selection()
                    return True

            # if source is self.table and event.type() == QEvent.KeyPress:
            #     if event.key() == Qt.Key_F2:
            #         # 메인 윈도우(self)를 부모로 지정하여 다이얼로그 생성
            #         dialog = LatexImportDialog(self)
                    
            #         if dialog.exec() == QDialog.Accepted:
            #             latex_code = dialog.get_text()
                        
            #             if latex_code.strip():
            #                 # 1. 여기서 메인 윈도우의 new_task()를 먼저 호출해 기존 찌꺼기를 싹 날립니다.
            #                 self.new_task()
                            
            #                 # 2. 깨끗해진 상태에서 파싱 함수를 실행해 새로운 데이터를 덮어씌웁니다.
            #                 self.import_latex_code(latex_code)
                            
            #         return True

        return super().eventFilter(source, event)

    def apply_relative_column_widths(self):
        """현재 테이블 열 너비를 기반으로 상대 너비 문자열을 생성하고 UI 및 LaTeX에 반영"""
        col_count = self.table.columnCount()
        if col_count == 0:
            return

        # 1. 모든 열의 현재 너비 가져오기
        widths = [self.table.columnWidth(col) for col in range(col_count)]
        
        # 2. 기준이 될 최소 너비 찾기
        min_width = min(widths)
        if min_width <= 0: 
            min_width = 80 # 0으로 나누는 것을 방지

        # 3. 상대 비율이 적용된 spec 리스트 생성
        colspecs = []
        for w in widths:
            rel_width = round(w / min_width, 1)
            rel_str = str(int(rel_width)) if rel_width.is_integer() else str(rel_width)
            colspecs.append(f"X[{rel_str},c,m]")
            
        proposed_colspec = " ".join(colspecs)
        
        # ==========================================
        # 4. UI 상태 업데이트 (open_colspec_dialog 흐름과 동일하게 처리)
        # ==========================================
        # QLineEdit 값 먼저 업데이트
        self.input_colspec.setText(proposed_colspec)
        
        # 라디오 버튼을 Manual 모드로 전환
        self.radio_manual.setChecked(True)
        
        # 확실한 갱신을 위해 LaTeX 생성 함수 명시적 호출
        self.generate_latex()

    # ==========================================
    # colspec preview 동기화
    # ==========================================
    def sync_colspec_preview(self):
        # 직접 setText 하지 않고 generate_latex 호출
        self.generate_latex()

    def generate_latex_with_colspec(self, colspec_str):
        # ---------------------------------------------------------
        # 1. 환경 파악 및 선택 옵션 ([]) 구성
        # ---------------------------------------------------------
        env_type = self.env_combobox.currentText()
        outer_options_str = ""
        
        if env_type in ['longtblr', 'talltblr']:
            raw_outer = self.outer_options_input.toPlainText()
            # 빈 줄 무시하고 추출
            outer_items = [line.strip() for line in raw_outer.split('\n') if line.strip()]
            if outer_items:
                # 콤마 뒤에 줄바꿈(\n)과 들여쓰기(공백 2칸) 추가
                joined_items = ",\n  ".join(outer_items)
                # 대괄호 시작과 끝에도 줄바꿈을 넣어 보기 좋게 감싸기
                outer_options_str = f"[\n  {joined_items}\n]"

        lines = []

        # \begin{환경}[옵션]{ 형식으로 시작
        lines.append(f"\\begin{{{env_type}}}{outer_options_str}{{")

        cols = self.table.columnCount()
        # width 체크를 위해 미리 일반 설정을 가져옴
        general_settings_text = self.input_general_settings.toPlainText()

        if self.radio_linewidth.isChecked():
            final_colspec = " ".join(["X[c,m]"] * cols)
            lines.append("  width = \\linewidth,")
            lines.append(f"  colspec = {{{final_colspec}}},")
            self.colspec_preview.setPlainText(f"colspec = {{{final_colspec}}} (linewidth)")

            # ==========================================
            # [추가됨] linewidth: 모든 열을 가운데 정렬(c)로 시각화
            # ==========================================
            self.table.blockSignals(True)
            align_flag = Qt.AlignmentFlag.AlignCenter
            for col_idx in range(cols):
                for row_idx in range(self.table.rowCount()):
                    self._apply_format_to_item(row_idx, col_idx, align_flag, "X[c,m]", tr("fmt.type.col"))
            self.table.blockSignals(False)

        elif self.radio_natural.isChecked():
            final_colspec = " ".join(["l"] * cols)
            lines.append(f"  colspec = {{{final_colspec}}},")
            self.colspec_preview.setPlainText(f"colspec = {{{final_colspec}}} (natural)")

            # ==========================================
            # [추가됨] natural: 모든 열을 왼쪽 정렬(l)로 시각화
            # ==========================================
            self.table.blockSignals(True)
            align_flag = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            for col_idx in range(cols):
                for row_idx in range(self.table.rowCount()):
                    self._apply_format_to_item(row_idx, col_idx, align_flag, "l", tr("fmt.type.col"))
            self.table.blockSignals(False)

        elif self.radio_manual.isChecked():
            final_colspec = colspec_str.strip()
            clean_colspec = None

            if final_colspec:
                # 1. 공백 및 세로선(|) 제거
                clean_colspec = final_colspec.replace(" ", "").replace("|", "")
                
                # 2. 문자열을 순회하며 *{n}{...} 블록을 실제 문자열로 전개 (Expand)
                expanded_colspec = ""
                i = 0
                while i < len(clean_colspec):
                    match = re.match(r'\*\{(\d+)\}\{', clean_colspec[i:])
                    if match:
                        repeat_count = int(match.group(1))
                        i += match.end() 
                        
                        brace_level = 1
                        inner_content = ""
                        while i < len(clean_colspec) and brace_level > 0:
                            if clean_colspec[i] == '{':
                                brace_level += 1
                            elif clean_colspec[i] == '}':
                                brace_level -= 1
                            
                            if brace_level > 0:
                                inner_content += clean_colspec[i]
                            i += 1
                        
                        # 추출한 내용을 반복 횟수만큼 추가 (예: *{3}{c} -> ccc)
                        expanded_colspec += inner_content * repeat_count
                    else:
                        expanded_colspec += clean_colspec[i]
                        i += 1
                
                # 3. 전개된 문자열(expanded_colspec)에서 일반 토큰 추출
                pattern_standard = r'([QXS](?:\[[^\]]*\])?|[pmb]\{[^\}]*\}|[lcrs])'
                standard_tokens = re.findall(pattern_standard, expanded_colspec)
                total_token_count = len(standard_tokens)
                
                # ==========================================
                # [추가됨] 추출된 토큰을 바탕으로 표 시각적 정렬 업데이트
                # ==========================================
                align_pattern = re.compile(r'\b([rcl])\b', re.IGNORECASE)
                num_rows = self.table.rowCount()

                # 1. [핵심] 테이블 업데이트 중 시그널 중복 발생 차단
                self.table.blockSignals(True)
                
                for col_idx, token in enumerate(standard_tokens):
                    if col_idx >= cols:
                        break  
                        
                    align_match = align_pattern.search(token)
                    if align_match:
                        opt = align_match.group(1).lower()
                        align_flag = None
                        if opt == 'l':
                            align_flag = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                        elif opt == 'c':
                            align_flag = Qt.AlignmentFlag.AlignCenter
                        elif opt == 'r':
                            align_flag = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                        
                        for row_idx in range(num_rows):
                            self._apply_format_to_item(row_idx, col_idx, align_flag, token, tr("fmt.type.col"))
                
                # 2. [핵심] 테이블 업데이트 완료 후 시그널 다시 활성화
                self.table.blockSignals(False)
                # ==========================================

                # 4. 유효하지 않은 문자(찌꺼기) 검사 (기존 remaining_colspec 대신 expanded_colspec 사용)
                matched_string = "".join(standard_tokens)
                has_invalid_chars = len(matched_string) != len(expanded_colspec)
                
                # 5. 경고창 출력 로직 (기존 코드 유지)
                if not getattr(self, 'ignore_colspec_validation', False):
                    if has_invalid_chars or total_token_count != cols:
                        msg_box = QMessageBox(self)
                        msg_box.setIcon(QMessageBox.Warning)

                        msg_box.setWindowTitle(tr("colspec.warning_title"))
                        
                        if has_invalid_chars:
                            error_msg = tr("colspec.invalid_chars", value=final_colspec)
                        else:
                            # token_count 대신 total_token_count 출력
                            error_msg = tr("colspec.count_mismatch", cols=cols, tokens=total_token_count)
                            
                        msg_box.setText(error_msg + tr("colspec.ignore_confirm"))
                        
                        cb = QCheckBox(tr("colspec.ignore_checkbox"))
                        msg_box.setCheckBox(cb)
                        
                        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                        msg_box.setDefaultButton(QMessageBox.No)
                        
                        ret = msg_box.exec()
                        
                        if ret == QMessageBox.No:
                            return 
                        
                        if cb.isChecked():
                            self.ignore_colspec_validation = True
 
            # --- X 열 체크 로직 ---
            has_x_column = False

            if clean_colspec:
                has_x_column = 'X' in clean_colspec
            
                if has_x_column and 'width' not in general_settings_text:
                    if not getattr(self, 'ignore_width_warning', False):
                        reply = QMessageBox.question(
                            self, tr("colspec.width_missing_title"),
                            tr("colspec.width_missing_body"),
                            QMessageBox.Yes | QMessageBox.No
                        )
                        
                        if reply == QMessageBox.Yes:
                            self.input_general_settings.blockSignals(True)
                            if general_settings_text.strip():
                                self.input_general_settings.setPlainText(general_settings_text.strip() + "\nwidth=\\linewidth")
                            else:
                                self.input_general_settings.setPlainText("width=\\linewidth")
                            self.input_general_settings.blockSignals(False)
                            general_settings_text = self.input_general_settings.toPlainText()
                        else:
                            self.ignore_width_warning = True
            # -------------------------
    
            lines.append(f"  colspec = {{{final_colspec}}},")
            self.colspec_preview.setPlainText(f"colspec = {{{final_colspec}}} (manual)")

        # ---------------------------------------------------------
        # 2. 필수 설정부 ({}) 옵션들 추가
        # ---------------------------------------------------------
        def add_multiline_settings(text, exclude_width=False):
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                
                # 이미 width가 설정된 경우 무시
                if exclude_width and line.startswith("width"):
                    continue
                
                lines.append(f"  {line},")

        # 각 섹션별 설정 추가
        add_multiline_settings(self.input_lines.toPlainText())
        add_multiline_settings(self.input_row_format.toPlainText())
        add_multiline_settings(self.input_cell_format.toPlainText())

        # width 중복 체크 및 general_settings 추가 (중복 호출 버그 수정)
        # has_already_width = any("width" in l for l in lines)
        has_already_width = any(l.strip().startswith("width") for l in lines)
        add_multiline_settings(self.input_general_settings.toPlainText(), exclude_width=has_already_width)

        # Long/Tall 환경의 추가 설정 (rowhead=1 등)을 같은 방식으로 병합!
        if env_type in ['longtblr', 'talltblr']:
            add_multiline_settings(self.inner_extra_input.toPlainText())

        # ---------------------------------------------------------
        # 3. 셀 병합 정보 수집
        # ---------------------------------------------------------
        skip_cells = set()
        merge_specs = []
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                if (r, c) in skip_cells:
                    continue
                row_span = self.table.rowSpan(r, c)
                col_span = self.table.columnSpan(r, c)
                if row_span > 1 or col_span > 1:
                    merge_specs.append(
                        f"  cell{{{r+1}}}{{{c+1}}} = {{r={row_span}, c={col_span}}}{{}},"
                    )
                    for dr in range(row_span):
                        for dc in range(col_span):
                            if dr == 0 and dc == 0:
                                continue
                            skip_cells.add((r+dr, c+dc))
        if merge_specs:
            lines.extend(merge_specs)

        lines.append("}")  # 필수 설정부({}) 닫기

        # ---------------------------------------------------------
        # 4. 표 본문 (행/열 데이터) 출력
        # ---------------------------------------------------------
        for r in range(self.table.rowCount()):
            row_content = []
            for c in range(self.table.columnCount()):
                if (r, c) in skip_cells:
                    row_content.append("")
                else:
                    item = self.table.item(r, c)
                    row_content.append(item.text() if item else "")
            lines.append("  " + " & ".join(row_content) + " \\\\")

        # === 체크박스 및 텍스트 입력값 확인 ===
        if self.bottomrule_checkbox.isChecked():
            # 양쪽 공백을 제거한 텍스트를 가져옴
            extra_cmd = self.extra_cmd_input.text().strip()
            
            # 입력창이 비어있으면 기본값 사용, 아니면 입력값 사용
            if not extra_cmd:
                extra_cmd = r"\bottomrule"
                
            lines.append("  " + extra_cmd)
        # =======================================================

        # 동적 환경 닫기
        lines.append(f"\\end{{{env_type}}}")

        # 최종 LaTeX 코드 문자열로 합치기
        latex_code = "\n".join(lines)

        # 출력창(QTextEdit 등)에 반영
        self.output_text.setPlainText(latex_code)

    def _refresh_headers(self):
        # 행 헤더 다시 그리기
        for r in range(self.table.rowCount()):
            self.table.setVerticalHeaderItem(r, QTableWidgetItem(str(r+1)))

        # 열 헤더 다시 그리기
        for c in range(self.table.columnCount()):
            self.table.setHorizontalHeaderItem(c, QTableWidgetItem(str(c+1)))

    # 행/열/셀 삽입 삭제시 좌표 변환
    def shift_format_entries(self, action: str, target: str, index: int, scope: str = None):
        """
        action: 'insert' 또는 'delete'
        target: 'row', 'column', 'hline', 'vline', 'cell'
        index: 삽입/삭제된 위치 (1-based)
        scope: cell 처리 시 'row' 또는 'column' 지정 필요
        """

        # --- 1. 대상 input 영역 선택 ---
        if target in ('row', 'column'):
            editor = self.input_row_format
            pattern = re.compile(rf'^({target})\s*\{{([^}}]+)\}}\s*=\s*\{{(.*)\}}')
        elif target in ('hline', 'vline'):
            editor = self.input_lines
            pattern = re.compile(rf'^({target})\s*\{{([^}}]+)\}}\s*=\s*\{{(.*)\}}')
        elif target == 'cell':
            editor = self.input_cell_format
            # pattern = re.compile(r'^(cell)\s*\{(\d+)\}\{(\d+)\}\s*=\s*\{(.*)\}')
            pattern = re.compile(r'^(cell)\s*\{(\d+)\}\{(\d+)\}\s*=\s*\{(.*)\}')
        else:
            return

        text = editor.toPlainText()
        lines = text.split('\n')
        new_lines = []

        # --- 2. 토큰 shift 보조 함수 ---
        def _shift_range(start: int, end: int, action: str, index: int):
            if action == "insert":
                if index <= start:
                    start += 1; end += 1
                elif start < index <= end:
                    end += 1
            elif action == "delete":
                if index < start:
                    start -= 1; end -= 1
                elif start <= index <= end:
                    end -= 1
                    if index == start:
                        start += 1
            return start, end

        def _shift_token(token: str, action: str, index: int):
            # 특수 키워드는 그대로 둠
            if token.lower() in ("odd", "even", "x", "y", "z"):
                return token

            # 범위 처리
            if "-" in token:
                start, end = token.split("-")
                start = _shift_token(start.strip(), action, index)
                end = _shift_token(end.strip(), action, index)
                if start is None or end is None:
                    return None
                return f"{start}-{end}"

            # 숫자 처리
            if token.isdigit():
                num = int(token)
                if action == "insert":
                    if num > index:
                        num += 1
                elif action == "delete":
                    if num > index:
                        num -= 1
                    elif num == index:
                        return None
                return str(num)

            # 그 외는 그대로 둠
            return token

        # --- 3. 라인별 처리 ---
        for line in lines:
            match = pattern.match(line.strip())
            if match:
                if target == 'cell':
                    cmd_type, r_str, c_str, options = match.groups()
                    r, c = int(r_str), int(c_str)

                    if action == 'insert':
                        if scope == 'row' and r >= index:
                            r += 1
                        elif scope == 'column' and c >= index:
                            c += 1
                    elif action == 'delete':
                        if scope == 'row':
                            if r > index:
                                r -= 1
                            elif r == index:
                                continue
                        elif scope == 'column':
                            if c > index:
                                c -= 1
                            elif c == index:
                                continue

                    new_line = f"{cmd_type}{{{r}}}{{{c}}} = {{{options}}}"
                    new_lines.append(new_line)

                else:
                    cmd_type, range_str, options = match.groups()
                    tokens = [t.strip() for t in range_str.split(",")]
                    shifted_tokens = []
                    for tok in tokens:
                        new_tok = _shift_token(tok, action, index)
                        if new_tok is not None:
                            shifted_tokens.append(new_tok)
                    if shifted_tokens:
                        new_range = ",".join(shifted_tokens)
                        new_line = f"{cmd_type}{{{new_range}}} = {{{options}}}"
                        new_lines.append(new_line)
            else:
                new_lines.append(line)

        # --- 4. 결과 반영 ---
        editor.setPlainText("\n".join(new_lines))

    # ==========================================
    # 표 크기 조정
    # ==========================================
    def resize_table(self, rows, cols):
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)
        self.generate_latex()

    # ==========================================
    # 셀 병합
    # ==========================================
    def merge_cells(self):
        selected = self.table.selectedRanges()
        if not selected:
            return
        
        rng = selected[0]
        top_row = rng.topRow()
        bottom_row = rng.bottomRow()
        left_col = rng.leftColumn()
        right_col = rng.rightColumn()

        # 1. 병합할 영역 내부에 이미 병합된 셀이 있다면 모두 강제 해제 (안전장치)
        for r in range(top_row, bottom_row + 1):
            for c in range(left_col, right_col + 1):
                if self.table.rowSpan(r, c) > 1 or self.table.columnSpan(r, c) > 1:
                    self.table.setSpan(r, c, 1, 1)

        # 2. 깔끔해진 영역 위에 전체 병합 덮어씌우기
        self.table.setSpan(top_row, left_col, rng.rowCount(), rng.columnCount())
        
        # 3. 변경된 구조로 LaTeX 갱신
        self.generate_latex()

    # ==========================================
    # 셀 병합 해제
    # ==========================================
    def unmerge_cells(self):
        # 현재 선택된 영역들을 가져옴
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return

        for rng in selected_ranges:
            # 선택된 범위 내의 모든 셀을 순회
            for r in range(rng.topRow(), rng.bottomRow() + 1):
                for c in range(rng.leftColumn(), rng.rightColumn() + 1):
                    # 핵심: 행이나 열의 Span 값이 1보다 클 때(즉, 병합된 셀의 좌상단 기준점일 때)만 해제
                    if self.table.rowSpan(r, c) > 1 or self.table.columnSpan(r, c) > 1:
                        self.table.setSpan(r, c, 1, 1)
        
        self.generate_latex() # (또는 현재 사용하시는 generate 함수)

    # ==========================================
    # Excel 가져오기 (값 + 병합 반영)
    # ==========================================
    def import_excel_with_merge(self):
        last_dir = self.settings.value("last_excel_dir", "")
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("excel.open_dialog_title"), last_dir, "Excel Files (*.xlsx)"
        )
        if not file_path:
            return

        # 1. 파일 세팅 중 불필요한 경고 메시지가 뜨는 것을 방지하기 위해 먼저 natural로 설정
        self.radio_natural.setChecked(True)

        self.settings.setValue("last_excel_dir", QFileInfo(file_path).absolutePath())

        # 수식 대신 결과값 가져오기
        wb = load_workbook(file_path, data_only=True)
        ws = wb.active

        rows, cols = ws.max_row, ws.max_column

        # 1. 테이블 초기화 (기존 병합/데이터 모두 삭제)
        self.table.clearContents()
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)
        self.spin_rows.setValue(rows)
        self.spin_cols.setValue(cols)

        # 2. 데이터 채우기 (중괄호 래핑 및 개행 처리 적용)
        for r in range(1, rows + 1):
            for c in range(1, cols + 1):
                cell = ws.cell(row=r, column=c)
                value = cell.value

                if value is None:
                    # 빈 셀
                    formatted_text = "{}"
                elif isinstance(value, (int, float)) and not isinstance(value, bool):
                    # float형이면서 소수점 아래가 없는 경우(예: 1290.0) 정수로 변환하여 '.0' 제거
                    if isinstance(value, float) and value.is_integer():
                        formatted_text = str(int(value))
                    else:
                        formatted_text = str(value)
                else:
                    # 문자열, 날짜 등
                    text_content = str(value).replace('\n', r' \\ ')
                    formatted_text = f"{{{text_content}}}"

                self.table.setItem(r-1, c-1, QTableWidgetItem(formatted_text))

        # 3. 병합(Span) 적용 (setItem 이후 수행)
        self.table.clearSpans()

        for merged_range in ws.merged_cells.ranges:
            min_col, min_row, max_col, max_row = merged_range.bounds

            row_span = max_row - min_row + 1
            col_span = max_col - min_col + 1

            self.table.setSpan(min_row - 1, min_col - 1, row_span, col_span)

        # LaTeX 생성 함수 호출
        self.generate_latex()


    def generate_latex(self):
        colspec_str = self.input_colspec.text().strip()
        self.generate_latex_with_colspec(colspec_str)
        
        # --- [추가] 표(Table)를 조작하기 전에 시그널 발생을 차단 ---
        self.table.blockSignals(True)
        
        try:
            # 텍스트 상자들의 내용을 바탕으로 표 UI 최신화
            self.apply_row_col_formats_to_table()
            self.apply_cell_formats_to_table()
            
            # (만약 선 긋기 함수도 있다면 여기서 같이 호출)
            # self.parse_lines_text_to_pens() 
            self.update_borders_preview()
        finally:
            # --- [추가] 조작이 끝나면 무조건 시그널 차단 해제 ---
            self.table.blockSignals(False)

    def get_range_string(self, indices):
        if not indices:
            return ""
            
        ranges = []
        start = indices[0]
        end = indices[0]

        for i in range(1, len(indices)):
            if indices[i] == end + 1:
                end = indices[i]
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = indices[i]
                end = indices[i]
                
        # 마지막 그룹 추가
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
            
        return ",".join(ranges)

    def get_selected_rows_and_cols(self):
        indexes = self.table.selectedIndexes()
        if not indexes:
            return [], [], False

        selected_rows_set = set()
        selected_cols_set = set()

        # 1. 선택된 인덱스를 순회하며 병합된 숨은 영역까지 모두 찾아냅니다.
        for idx in indexes:
            r = idx.row()
            c = idx.column()
            
            row_span = self.table.rowSpan(r, c)
            col_span = self.table.columnSpan(r, c)

            # 병합된 폭과 높이만큼 1-based 인덱스로 변환하여 set에 추가 (중복 방지)
            for i in range(row_span):
                selected_rows_set.add(r + i + 1)
            for j in range(col_span):
                selected_cols_set.add(c + j + 1)

        # 2. 정렬된 리스트로 변환
        selected_rows = sorted(list(selected_rows_set))
        selected_cols = sorted(list(selected_cols_set))

        total_columns = self.table.columnCount()

        # 3. 전체 행 선택 여부 확인 로직 (기존 유지)
        full_row_selected = bool(self.table.selectionModel().selectedRows())

        if full_row_selected:
            selected_cols = list(range(1, total_columns + 1))

        return selected_rows, selected_cols, full_row_selected

    # ==========================================
    # 텍스트 에디터 변경 시 테이블 시각 효과 동기화
    # ==========================================
    def sync_table_highlights(self):
        # 1. 초기화: 셀 뱃지 및 헤더 원상복구
        for r in range(self.table.rowCount()):
            # 수직 헤더(행 번호) 초기화
            v_header = self.table.verticalHeaderItem(r)
            if not v_header:
                v_header = QTableWidgetItem(str(r + 1))
                self.table.setVerticalHeaderItem(r, v_header)
            
            v_header.setText(str(r + 1)) # 원래 번호로 복구
            v_header.setForeground(QBrush(Qt.GlobalColor.black)) # 글자색 복구
            v_header.setFont(QFont()) # 폰트 굵기 초기화
            v_header.setToolTip("")

            # 셀 뱃지 초기화
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole + 1, False)
                    item.setToolTip("")
        
        # 2. 텍스트 파싱
        text = self.input_cell_format.toPlainText()

        # 3. [Row 설정]: row{...} = {...} -> 수직 헤더에 뱃지 표시
        row_pattern = re.compile(r"row\{([0-9\-\,\s]+)\}\s*=\s*\{([^}]*)\}")
        for match in row_pattern.finditer(text):
            r_str, options = match.groups()
            rows = self.parse_range_string(r_str)
            
            for r in rows:
                row_idx = r - 1
                if 0 <= row_idx < self.table.rowCount():
                    v_header = self.table.verticalHeaderItem(row_idx)
                    
                    # 마커 추가 및 스타일 변경 (초록색 텍스트 & 볼드 처리)
                    v_header.setText(f"{row_idx + 1} ●") 
                    v_header.setForeground(QBrush(QColor("#34A853")))

                    font = v_header.font()
                    font.setBold(True)
                    v_header.setFont(font)
                    
                    # 헤더 툴팁에 설정값 표시
                    current_tip = v_header.toolTip()
                    new_tip = f"Row Settings: {options}"
                    v_header.setToolTip(f"{current_tip}\n{new_tip}".strip())
                        
        # 4. [Cell 설정]: cell{...}{...} = {...} -> 기존처럼 개별 셀에 파란 점 표시
        cell_pattern = re.compile(r"cell\{([0-9\-\,\s]+)\}\{([0-9\-\,\s]+)\}\s*=\s*\{([^}]*)\}")
        for match in cell_pattern.finditer(text):
            r_str, c_str, options = match.groups()
            rows = self.parse_range_string(r_str)
            cols = self.parse_range_string(c_str)
            
            for r in rows:
                for c in cols:
                    row_idx, col_idx = r - 1, c - 1
                    if 0 <= row_idx < self.table.rowCount() and 0 <= col_idx < self.table.columnCount():
                        item = self.table.item(row_idx, col_idx)
                        if item:
                            # 툴팁 조작 없이, 내부 데이터(UserRole)에 서식 유무만 마킹
                            item.setData(Qt.ItemDataRole.UserRole + 1, True)

    # 고급 설정
    def goto_or_create_format(self, target_type):        
        # 1. 대상 타입에 따라 텍스트 에디터 위젯을 분기하여 할당
        if target_type == 'cell':
            target_editor = self.input_cell_format
        elif target_type in ['row', 'col']:
            target_editor = self.input_row_format
        else:
            return 

        # --- [핵심 변경점] 선택된 영역을 모두 가져와서 범위로 묶습니다 ---
        indexes = self.table.selectedIndexes()
        if not indexes:
            return

        selected_rows = sorted(set(idx.row() + 1 for idx in indexes))
        selected_cols = sorted(set(idx.column() + 1 for idx in indexes))

        # 범위 문자열 생성 (예: [1, 2, 3] -> "1-3")
        r_str = self.get_range_string(selected_rows)
        c_str = self.get_range_string(selected_cols)
        # -------------------------------------------------------------

        text = target_editor.toPlainText()
        cursor = target_editor.textCursor()
        
        num_rows = self.table.rowCount()
        num_cols = self.table.columnCount()
        
        # --- [추가] 키워드를 실제 숫자 목록으로 변환하는 내부 도우미 함수 ---
        def expand_keywords(range_str, max_val):
            # 1. odd / even 변환 (1부터 max_val까지의 홀/짝수 쉼표 문자열 생성)
            odd_nums = ",".join(str(i) for i in range(1, max_val + 1, 2))
            even_nums = ",".join(str(i) for i in range(2, max_val + 1, 2))
            
            # 단어 단위(\b)로 대소문자 무시하고 치환
            s = re.sub(r'\bodd\b', odd_nums, range_str, flags=re.IGNORECASE)
            s = re.sub(r'\beven\b', even_nums, s, flags=re.IGNORECASE)
            
            # 2. X, Y, Z 치환 (기존 로직)
            s = re.sub(r'[ZzXxYy]', str(max_val), s)
            return s
        # -------------------------------------------------------------

        found_match = None
        min_len = float('inf') 

        # 2. 타입에 따른 정규식 검색 (명시도 우선순위 + 확장 키워드 적용)
        if target_type == 'cell':
            # 정규식 확장: [0-9\-\,\sZzXxYy] -> [a-zA-Z0-9\-\,\s] 로 변경하여 odd, even도 허용
            pattern = re.compile(r"cell\{([a-zA-Z0-9\-\,\s]+)\}\{([a-zA-Z0-9\-\,\s]+)\}\s*=\s*\{([^}]*)\}")
            for match in pattern.finditer(text):
                match_r, match_c, _ = match.groups()
                
                # 도우미 함수로 키워드 해석
                parsed_r = set(self.parse_range_string(expand_keywords(match_r, num_rows)))
                parsed_c = set(self.parse_range_string(expand_keywords(match_c, num_cols)))
                
                sel_r = set(selected_rows)
                sel_c = set(selected_cols)

                if sel_r == parsed_r and sel_c == parsed_c:
                    found_match = match
                    break
                
                if sel_r.issubset(parsed_r) and sel_c.issubset(parsed_c):
                    current_len = len(parsed_r) + len(parsed_c)
                    if current_len < min_len:
                        found_match = match
                        min_len = current_len

        elif target_type == 'row':
            pattern = re.compile(r"row\{([a-zA-Z0-9\-\,\s]+)\}\s*=\s*\{([^}]*)\}")
            for match in pattern.finditer(text):
                match_r, _ = match.groups()
                
                parsed_r = set(self.parse_range_string(expand_keywords(match_r, num_rows)))
                sel_r = set(selected_rows)
                
                if sel_r == parsed_r:
                    found_match = match
                    break
                
                if sel_r.issubset(parsed_r):
                    current_len = len(parsed_r)
                    if current_len < min_len:
                        found_match = match
                        min_len = current_len

        elif target_type == 'col':
            pattern = re.compile(r"column\{([a-zA-Z0-9\-\,\s]+)\}\s*=\s*\{([^}]*)\}")
            for match in pattern.finditer(text):
                match_c, _ = match.groups()
                
                parsed_c = set(self.parse_range_string(expand_keywords(match_c, num_cols)))
                sel_c = set(selected_cols)
                
                if sel_c == parsed_c:
                    found_match = match
                    break
                
                if sel_c.issubset(parsed_c):
                    current_len = len(parsed_c)
                    if current_len < min_len:
                        found_match = match
                        min_len = current_len

        # 3. 결과 처리 (이동 또는 생성)
        if found_match:
            cursor.setPosition(found_match.start())
            cursor.setPosition(found_match.end(), QTextCursor.MoveMode.KeepAnchor)
        else:
            cursor.movePosition(QTextCursor.MoveOperation.End)
            if text and not text.endswith('\n'):
                cursor.insertText('\n')
                
            # 단일 숫자가 아닌 r_str, c_str 범위 문자열을 삽입합니다.
            if target_type == 'cell':
                new_text = f"cell{{{r_str}}}{{{c_str}}} = {{}}"
            elif target_type == 'row':
                new_text = f"row{{{r_str}}} = {{}}"
            elif target_type == 'col':
                new_text = f"column{{{c_str}}} = {{}}"
                
            cursor.insertText(new_text)
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, 1)

        # 4. 최종적으로 선택된 에디터에 커서와 포커스 적용
        target_editor.setTextCursor(cursor)
        target_editor.setFocus()

    # ==========================================
    # 문자열(예: "1-3, 5")을 숫자 리스트([1,2,3,5])로 변환하는 헬퍼 함수
    # ==========================================
    def parse_range_string(self, range_str):
        indexes = []
        # 쉼표로 분리
        for part in range_str.split(','):
            part = part.strip()
            if not part: continue
            
            if '-' in part: # "1-3" 형태인 경우
                try:
                    start, end = map(int, part.split('-'))
                    indexes.extend(range(start, end + 1))
                except ValueError:
                    pass
            elif part.isdigit(): # "5" 처럼 단일 숫자인 경우
                indexes.append(int(part))
        return indexes

    def apply_alignments_from_text(self):
        """input_cell_format의 텍스트를 읽어 테이블 셀 정렬을 시각적으로 업데이트합니다."""
        text = self.input_cell_format.toPlainText()
        lines = text.split('\n')
        
        num_rows = self.table.rowCount()
        num_cols = self.table.columnCount()

        # 정규식: row{..} = {..} 또는 cell{..}{..} = {..} 매칭
        # group(1): row|cell, group(2): 행 범위, group(3): 열 범위(선택), group(4): 속성들
        pattern = re.compile(r'^(row|cell)\s*\{([^}]+)\}(?:\s*\{([^}]+)\})?\s*=\s*\{(.*)\}')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('%'): continue

            match = pattern.match(line)
            if match:
                cmd_type = match.group(1)
                row_str = match.group(2)
                col_str = match.group(3) if match.group(3) else "1-Z" # row 명령어면 전체 열 적용
                properties = match.group(4).lower()

                # 속성에서 l, c, r 찾기
                align_char = None
                for p in properties.split(','):
                    p = p.strip()
                    if p in ['l', 'c', 'r']:
                        align_char = p
                        break
                
                if not align_char:
                    continue # l, c, r이 없으면 패스

                # Qt 정렬 플래그 매핑
                align_flag = Qt.AlignmentFlag.AlignCenter
                if align_char == 'l':
                    align_flag = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                elif align_char == 'r':
                    align_flag = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

                # 범위 확장 (기존에 만드신 헬퍼 함수 활용)
                target_rows = self._expand_range_string(row_str, num_rows)
                target_cols = self._expand_range_string(col_str, num_cols)

                # 테이블에 반영 (주의: QTableWidget은 0-based index이므로 -1을 해줍니다)
                for r in target_rows:
                    if r == 'Z': r = num_rows # Z 처리
                    for c in target_cols:
                        if c == 'Z': c = num_cols # Z 처리
                        
                        row_idx = int(r) - 1
                        col_idx = int(c) - 1
                        
                        if 0 <= row_idx < num_rows and 0 <= col_idx < num_cols:
                            item = self.table.item(row_idx, col_idx)
                            if not item:
                                item = QTableWidgetItem("")
                                self.table.setItem(row_idx, col_idx, item)
                            item.setTextAlignment(align_flag)

    # ==========================================
    # [추가] 동일 스코프(header)의 기존 서식 줄을 찾아 옵션 문자열을 반환
    # (완전히 동일한 스코프일 때만 매치되도록 설계 - 부분적으로 겹치는 범위는 무시)
    # ==========================================
    def _find_existing_format_options(self, text_edit, header):
        text = text_edit.toPlainText()
        found = find_scoped_option_block(text, re.escape(header))
        if found:
            return found[2]  # inner 옵션 문자열
        return None

    # ==========================================
    # [추가] 동일 스코프의 기존 서식 줄이 있으면 교체하고, 없으면 새 줄로 추가
    # ==========================================
    def _upsert_format_line(self, text_edit, header, new_full_line):
        text = text_edit.toPlainText()
        found = find_scoped_option_block(text, re.escape(header))
        if found:
            start, end, _inner = found
            new_text = text[:start] + new_full_line + text[end:]
            text_edit.setPlainText(new_text)
            cursor = text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            text_edit.setTextCursor(cursor)
        else:
            text_edit.append(new_full_line)

    # ==========================================
    # F5 단축키: 현재 셀 또는 다중 셀 템플릿 삽입
    # ==========================================
    def insert_cell_format(self):
        # 1. 행/열 범위 및 전체 행 선택 여부 파악
        selected_rows, selected_cols, full_row_selected = self.get_selected_rows_and_cols()
        if not selected_rows:
            return

        # 2. 개별 셀 좌표 세트 확보
        indexes = self.table.selectedIndexes()
        cells = set((idx.row() + 1, idx.column() + 1) for idx in indexes)

        # 3. 직사각형(인접 셀) 여부 판별 (외따로 떨어진 셀 필터링용)
        min_r, max_r = selected_rows[0], selected_rows[-1]
        min_c, max_c = selected_cols[0], selected_cols[-1]
        expected_count = (max_r - min_r + 1) * (max_c - min_c + 1)
        is_rectangle = (len(cells) == expected_count)

        # 4. 찾으신 함수를 활용해 범위 문자열을 우아하게 생성!
        r_str = self.get_range_string(selected_rows)
        c_str = self.get_range_string(selected_cols)

        # 5. 다이얼로그 타이틀용 문자열 생성
        if full_row_selected:
            target_str = tr("range.row_all", r_str=r_str)
        elif len(cells) == 1:
            target_str = tr("range.row_col", r_str=r_str, c_str=c_str)
        elif is_rectangle:
            target_str = tr("range.row_col", r_str=r_str, c_str=c_str)
        else:
            target_str = tr("range.multi_cell", count=len(cells))

        # 5-1. [추가] 완전히 동일한 스코프의 기존 서식이 있으면 다이얼로그에 미리 채워줌
        # (직사각형 범위이거나 셀 1개만 선택된 "단일 스코프"인 경우에만 프리필 시도.
        #  여러 개의 개별 셀이 섞인 다중 선택은 스코프가 여러 개라 프리필하지 않음)
        existing_options = None
        if is_rectangle:
            existing_header = f"cell{{{r_str}}}{{{c_str}}}"
            existing_options = self._find_existing_format_options(self.input_cell_format, existing_header)
        elif len(cells) == 1:
            only_r, only_c = next(iter(cells))
            existing_header = f"cell{{{only_r}}}{{{only_c}}}"
            existing_options = self._find_existing_format_options(self.input_cell_format, existing_header)

        # 6. 서식 입력 다이얼로그 호출
        dialog = FormatDialog("cell", target_str, self, existing_options=existing_options)
        if dialog.exec() == QDialog.Accepted:
            user_input_clean = dialog.line_edit.text().strip().strip('{}')
            aligns = dialog.get_align_info()
            # [추가] 수식 모드 정보 가져오기
            modes = dialog.get_mode_info()
            # [추가] 글꼴 정보 가져오기 (font=... 형태)
            fonts = dialog.get_font_info()
            
            parts = []
            
            # 1. 정렬 정보 추가 (c, l, r, m, t 등)
            if aligns:
                parts.extend(aligns)
                
            # 2. 수식 모드 정보 추가 (mode=math 등)
            if modes:
                parts.extend(modes)

            # 2-1. [추가] 글꼴 정보 추가 (font=\sffamily 등)
            if fonts:
                parts.extend(fonts)
                
            # 3. 사용자 직접 입력 내용 추가
            if user_input_clean:
                parts.append(user_input_clean)
                
            # 모든 요소를 쉼표로 연결
            combined = ", ".join(parts)
            options_part = f"{{{combined}}}" if combined else "{}"

            # 7. 상황에 맞는 LaTeX 코드 생성 (수정됨)
            # 행 전체 선택 여부(full_row_selected)와 상관없이 
            # 직사각형 범위(is_rectangle)라면 무조건 cell{...}{...} 문법을 사용합니다.
            if is_rectangle:
                # 행 전체 선택 시에도 c_str에 전체 컬럼 범위(예: 1-5)가 들어있으므로 
                # cell{1}{1-5} 형태로 예쁘게 생성됩니다.
                # [수정] 동일 스코프의 기존 줄이 있으면 append 대신 교체(upsert)
                header = f"cell{{{r_str}}}{{{c_str}}}"
                self._upsert_format_line(self.input_cell_format, header, f"{header} = {options_part}")
            else:
                # 외따로 떨어진 셀: 개별 줄로 분리 출력
                # [수정] 각 셀별로 동일 스코프(cell{r}{c})의 기존 줄이 있으면 교체, 없으면 추가
                for r, c in sorted(cells):
                    header = f"cell{{{r}}}{{{c}}}"
                    self._upsert_format_line(self.input_cell_format, header, f"{header} = {options_part}")
                    
            self.generate_latex()

    # ==========================================
    # F6 단축키: 선택된 다중 행 기반 row 템플릿 삽입
    # ==========================================
    def insert_row_format(self):
        indexes = self.table.selectedIndexes()
        if not indexes:
            return

        # selected_rows = sorted(set(idx.row() + 1 for idx in indexes))
        selected_rows, _, _ = self.get_selected_rows_and_cols()
        if not selected_rows:
            return

        row_range = self.get_range_string(selected_rows)

        # [추가] 동일 스코프(row{row_range})의 기존 서식이 있으면 다이얼로그에 미리 채워줌
        row_header = f"row{{{row_range}}}"
        existing_options = self._find_existing_format_options(self.input_row_format, row_header)

        dialog = FormatDialog("row", tr("range.row", row_range=row_range), self, existing_options=existing_options)
        if dialog.exec() == QDialog.Accepted:
            user_input_clean = dialog.line_edit.text().strip().strip('{}')
            style, is_double, is_thick = dialog.get_line_format_info()
            
            # 1. 정렬 정보 가져오기
            aligns = dialog.get_align_info()
            # 2. 수식 모드 정보 가져오기 [추가]
            modes = dialog.get_mode_info()
            # [추가] 글꼴 정보 가져오기 (font=... 형태)
            fonts = dialog.get_font_info()

            parts = []
            
            # 정렬 정보 추가
            if aligns:
                parts.extend(aligns)

            # 수식 모드 정보 추가 [추가]
            if modes:
                parts.extend(modes)

            # [추가] 글꼴 정보 추가
            if fonts:
                parts.extend(fonts)

            # 직접 입력 내용 추가
            if user_input_clean:
                parts.append(user_input_clean)

            # 선 스타일 정보 추가 (행/열 서식에서 사용 시)
            if style:
                parts.append(style)

            # 최종 문자열 조립
            combined = ", ".join(parts)
            options_part = f"{{{combined}}}" if combined else "{}"

            # [수정] 동일 스코프의 기존 줄이 있으면 append 대신 교체(upsert)
            self._upsert_format_line(self.input_row_format, row_header, f"{row_header} = {options_part}")
            self.generate_latex()

    # ==========================================
    # Ctrl+F6 단축키: 선택된 다중 열 기반 column 템플릿 삽입
    # ==========================================
    def insert_column_format(self):
        indexes = self.table.selectedIndexes()
        if not indexes:
            return

        selected_cols = sorted(set(idx.column() + 1 for idx in indexes))
        col_range = self.get_range_string(selected_cols)

        # [추가] 동일 스코프(column{col_range})의 기존 서식이 있으면 다이얼로그에 미리 채워줌
        # (column{} 줄도 input_row_format 텍스트에 함께 저장되므로 같은 위젯에서 검색)
        col_header = f"column{{{col_range}}}"
        existing_options = self._find_existing_format_options(self.input_row_format, col_header)

        dialog = FormatDialog("col", tr("range.col", col_range=col_range), self, existing_options=existing_options)
        if dialog.exec() == QDialog.Accepted:
            user_input_clean = dialog.line_edit.text().strip().strip('{}')
            style, is_double, is_thick = dialog.get_line_format_info()

            # 1. 정렬 정보 가져오기
            aligns = dialog.get_align_info()
            # 2. 수식 모드 정보 가져오기 [추가]
            modes = dialog.get_mode_info()
            # [추가] 글꼴 정보 가져오기 (font=... 형태)
            fonts = dialog.get_font_info()

            parts = []
            
            # 정렬 정보가 있으면 병합
            if aligns:
                parts.extend(aligns)

            # 수식 모드 정보가 있으면 병합 [추가]
            if modes:
                parts.extend(modes)

            # [추가] 글꼴 정보가 있으면 병합
            if fonts:
                parts.extend(fonts)

            # 직접 입력 내용 추가
            if user_input_clean:
                parts.append(user_input_clean)

            # 선 스타일 정보 추가
            if style:
                parts.append(style)

            # 최종 문자열 조립
            combined = ", ".join(parts)
            options_part = f"{{{combined}}}" if combined else "{}"

            # [수정] 동일 스코프의 기존 줄이 있으면 append 대신 교체(upsert)
            self._upsert_format_line(self.input_row_format, col_header, f"{col_header} = {options_part}")
            self.generate_latex()

    def clean_line_options(self, raw_input):
        """LaTeX 괘선 옵션에서 중복된 단일 속성(색상 등)을 정리하여 마지막 값만 반환합니다."""
        options = [opt.strip() for opt in raw_input.split(',') if opt.strip()]
        
        kv_options = []
        standalone_options = []
        
        for opt in options:
            if '=' in opt:
                kv_options.append(opt)
            else:
                standalone_options.append(opt)
        
        if standalone_options:
            kv_options.append(standalone_options[-1])
            
        return ", ".join(kv_options)

    def highlight_target_format(self, text_edit, target_keyword, focus_row=None, focus_col=None):
        plain_text = text_edit.toPlainText()
        if not plain_text.strip(): return

        try:
            f_row = int(focus_row) if focus_row is not None else None
            f_col = int(focus_col) if focus_col is not None else None
        except ValueError:
            f_row, f_col = None, None

        lines = plain_text.split('\n')
        html_lines = []

        # 정규표현식: 숫자, 범위뿐만 아니라 odd, even 단어도 잡을 수 있도록 수정
        row_pattern = r"row\{([0-9,\-\sXYZz|odd|even|ODD|EVEN]+)\}"
        col_pattern = r"column\{([0-9,\-\sXYZz|odd|even|ODD|EVEN]+)\}"
        cell_pattern = r"cell\{([0-9,\-\sXYZz|odd|even|ODD|EVEN]+)\}\{([0-9,\-\sXYZz|odd|even|ODD|EVEN]+)\}"

        max_row = self.table.rowCount() if hasattr(self, 'table') else 1000
        max_col = self.table.columnCount() if hasattr(self, 'table') else 100

        for line in lines:
            escaped_line = html.escape(line)
            is_row_cell_match = False
            is_col_match = False

            # --- 1. 타겟 키워드 매칭 ---
            # 특정 키워드가 라인에 존재하면 일단 매칭되었다고 판단 (필요에 따라 주석 처리 가능)
            if target_keyword and target_keyword in line:
                is_row_cell_match = True

            # --- 2. Row 범위/홀짝 체크 ---
            if not is_row_cell_match and f_row is not None:
                match = re.search(row_pattern, line)
                if match:
                    content = match.group(1).strip().lower()
                    if content == "odd":
                        if f_row % 2 != 0: is_row_cell_match = True
                    elif content == "even":
                        if f_row % 2 == 0: is_row_cell_match = True
                    else:
                        valid_rows = self._expand_range_string(content, max_row)
                        if str(f_row) in valid_rows or f_row in valid_rows: 
                            is_row_cell_match = True

            # --- 3. Cell 범위/홀짝 체크 ---
            if not is_row_cell_match and f_row is not None and f_col is not None:
                match = re.search(cell_pattern, line)
                if match:
                    contents = [match.group(1).strip().lower(), match.group(2).strip().lower()]
                    res = []
                    # 행(i=0)과 열(i=1) 각각 홀짝/범위 판별
                    for i, c in enumerate(contents):
                        val = f_row if i == 0 else f_col
                        mx = max_row if i == 0 else max_col
                        if c == "odd": res.append(val % 2 != 0)
                        elif c == "even": res.append(val % 2 == 0)
                        else:
                            v_list = self._expand_range_string(c, mx)
                            res.append(str(val) in v_list or val in v_list)
                    
                    if len(res) == 2 and all(res): 
                        is_row_cell_match = True

            # --- 4. Column 매칭 (Blue) ---
            if not is_row_cell_match and f_col is not None:
                match = re.search(col_pattern, line)
                if match:
                    content = match.group(1).strip().lower()
                    if content == "odd":
                        if f_col % 2 != 0: is_col_match = True
                    elif content == "even":
                        if f_col % 2 == 0: is_col_match = True
                    else:
                        valid_cols = self._expand_range_string(content, max_col)
                        if str(f_col) in valid_cols or f_col in valid_cols: 
                            is_col_match = True

            # --- 5. 색상 적용 ---
            if is_row_cell_match:
                # Row나 Cell 매칭일 경우 보라빛/파란빛
                formatted_line = f'<b><span style="color: #594FCE;">{escaped_line}</span></b>'
            elif is_col_match:
                # Column 매칭일 경우 빨간빛
                formatted_line = f'<b><span style="color: #FF0000;">{escaped_line}</span></b>'
            else:
                formatted_line = escaped_line
            
            html_lines.append(formatted_line)

        # HTML 설정 (이때 커서 위치가 초기화될 수 있으므로 blockSignals 사용)
        text_edit.blockSignals(True)
        text_edit.setHtml("<br>".join(html_lines))
        text_edit.blockSignals(False)
    
    # ==========================================
    # input_row_format 텍스트를 분석하여 표 시각화 업데이트
    # ==========================================
    def apply_row_col_formats_to_table(self):
        text = self.input_row_format.toPlainText()
        lines = text.split('\n')
        
        num_rows = self.table.rowCount()
        num_cols = self.table.columnCount()

        # --- [추가됨] 1. 실행 전 헤더 초기화 (뱃지 지우기) ---
        # 수직 헤더 (행 번호) 초기화
        for r in range(num_rows):
            v_item = self.table.verticalHeaderItem(r)
            if not v_item:
                v_item = QTableWidgetItem(str(r + 1))
                self.table.setVerticalHeaderItem(r, v_item)
            v_item.setText(str(r + 1)) # 원래 번호로 복구
            v_item.setForeground(QBrush(Qt.GlobalColor.black)) # 검은색 복구
            font = v_item.font()
            font.setBold(False)
            v_item.setFont(font)

        # 수평 헤더 (열 번호/알파벳) 초기화
        for c in range(num_cols):
            h_item = self.table.horizontalHeaderItem(c)
            if not h_item:
                h_item = QTableWidgetItem(str(c + 1)) # 열 문자가 따로 있다면 그걸 사용하세요
                self.table.setHorizontalHeaderItem(c, h_item)
            
            # 기존 텍스트에서 뱃지만 제거 (예: "A ●" -> "A")
            base_text = h_item.text().replace(" ●", "").strip()
            h_item.setText(base_text)
            h_item.setForeground(QBrush(Qt.GlobalColor.black))
            font = h_item.font()
            font.setBold(False)
            h_item.setFont(font)

        pattern = re.compile(r'^(row|column)\s*\{([^}]+)\}\s*=\s*\{(.*)\}')
        align_pattern = re.compile(r'\b([rcl])\b', re.IGNORECASE)

        for line in lines:
            line = line.strip()
            if not line or line.startswith('%'): continue

            match = pattern.match(line)
            if match:
                cmd_type = match.group(1).lower()
                range_str = match.group(2)
                options = match.group(3)

                align_flag = None
                align_match = align_pattern.search(options)
                
                if align_match:
                    opt = align_match.group(1).lower()
                    if opt == 'l':
                        align_flag = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    elif opt == 'c':
                        align_flag = Qt.AlignmentFlag.AlignCenter
                    elif opt == 'r':
                        align_flag = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

                # 범위 확장 및 odd/even 처리
                max_val = num_rows if cmd_type == 'row' else num_cols
                range_str_clean = range_str.strip().lower()

                if range_str_clean == "odd":
                    # 홀수 번호만 추출 (기존 로직과 호환되도록 문자열 리스트로 만듭니다)
                    targets = [str(i) for i in range(1, max_val + 1) if i % 2 != 0]
                elif range_str_clean == "even":
                    # 짝수 번호만 추출
                    targets = [str(i) for i in range(1, max_val + 1) if i % 2 == 0]
                else:
                    # 기존 숫자/범위/Z 패턴
                    targets = self._expand_range_string(range_str, max_val)

                # 행(row) 명령어일 경우
                if cmd_type == 'row':
                    for r in targets:
                        if r == 'Z': r = num_rows
                        row_idx = int(r) - 1
                        
                        # --- [수정됨] 수직 헤더에 ● 뱃지 추가 ---
                        v_header = self.table.verticalHeaderItem(row_idx)
                        if v_header:
                            v_header.setText(f"{row_idx + 1} ●")
                            v_header.setForeground(QBrush(QColor("#34A853"))) # 텍스트 기호라 이 색상이 예쁘게 적용됨
                            font = v_header.font()
                            font.setBold(True)
                            v_header.setFont(font)
                        # ----------------------------------------

                        for col_idx in range(num_cols):
                            self._apply_format_to_item(row_idx, col_idx, align_flag, options, tr("fmt.type.row"))

                # 열(column) 명령어일 경우
                elif cmd_type == 'column':
                    for c in targets:
                        if c == 'Z': c = num_cols
                        col_idx = int(c) - 1

                        # --- [수정됨] 수평 헤더에 ● 뱃지 추가 ---
                        h_header = self.table.horizontalHeaderItem(col_idx)
                        if h_header:
                            # 기존 뱃지가 있다면 먼저 제거
                            base_text = h_header.text().replace(" ●", "").strip()
                            h_header.setText(f"{base_text} ●")
                            h_header.setForeground(QBrush(QColor("#FBBC05"))) # 주황색 (문자에 색상이 바로 적용됨)
                            font = h_header.font()
                            font.setBold(True)
                            h_header.setFont(font)
                        # ----------------------------------------                        

                        for row_idx in range(num_rows):
                            self._apply_format_to_item(row_idx, col_idx, align_flag, options, tr("fmt.type.col"))

    # ==========================================
    # input_cell_format 텍스트를 분석하여 표 시각화 업데이트 (가장 높은 우선순위)
    # ==========================================
    def apply_cell_formats_to_table(self):
        text = self.input_cell_format.toPlainText()
        lines = text.split('\n')
        
        num_rows = self.table.rowCount()
        num_cols = self.table.columnCount()

        # 정규식: cell{행}{열} = {옵션}
        pattern = re.compile(r'^cell\s*\{([^}]+)\}\s*\{([^}]+)\}\s*=\s*\{(.*)\}')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('%'): continue

            match = pattern.match(line)
            if match:
                row_str = match.group(1)
                col_str = match.group(2)
                options = match.group(3)

                # 옵션에서 정렬(l, c, r) 파싱
                align_flag = None
                for opt in options.split(','):
                    opt = opt.strip().lower()
                    if opt == 'l':
                        align_flag = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    elif opt == 'c':
                        align_flag = Qt.AlignmentFlag.AlignCenter
                    elif opt == 'r':
                        align_flag = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

                # 범위 확장
                target_rows = self._expand_range_string(row_str, num_rows)
                target_cols = self._expand_range_string(col_str, num_cols)

                # 지정된 셀들에 서식 덮어쓰기
                for r in target_rows:
                    if r == 'Z': r = num_rows
                    row_idx = int(r) - 1
                    for c in target_cols:
                        if c == 'Z': c = num_cols
                        col_idx = int(c) - 1
                        
                        self._apply_format_to_item(row_idx, col_idx, align_flag, options, tr("fmt.type.cell"))

    # 셀 렌더링을 돕는 내부 헬퍼 함수 (기존 _apply_highlight의 간략화 버전)
    def _apply_format_to_item(self, row_idx, col_idx, align_flag, options, format_type):
        if not (0 <= row_idx < self.table.rowCount() and 0 <= col_idx < self.table.columnCount()):
            return
            
        item = self.table.item(row_idx, col_idx)
        if not item:
            item = QTableWidgetItem("")
            self.table.setItem(row_idx, col_idx, item)
            
        if align_flag is not None:
            item.setTextAlignment(align_flag)
            
        # 툴팁 수정 및 추가 (예: "행 서식: {c, double}")
        if options.strip():
            prefix = tr("fmt.tooltip_prefix", format_type=format_type)
            new_line = f"{prefix} {{{options.strip()}}}"
            current_tooltip = item.toolTip()
            
            if current_tooltip:
                # 기존 툴팁을 줄 단위로 쪼개기
                lines = current_tooltip.split('\n')
                updated = False
                
                # 같은 서식 타입(prefix)으로 시작하는 줄이 찾아서 덮어쓰기
                for i, line in enumerate(lines):
                    if line.startswith(prefix):
                        lines[i] = new_line
                        updated = True
                        break
                
                # 기존에 같은 서식 타입이 없었다면 맨 뒤에 추가
                if not updated:
                    lines.append(new_line)
                    
                # 리스트를 다시 줄바꿈으로 합쳐서 적용
                item.setToolTip('\n'.join(lines))
            else:
                # 기존 툴팁이 아예 없었다면 그냥 바로 적용
                item.setToolTip(new_line)

    def insert_hline_format(self, include_z=False):
        selected_rows, selected_cols, full_row_selected = self.get_selected_rows_and_cols()
        if not selected_rows:
            return

        row_range = self.get_range_string(selected_rows)
        col_range = self.get_range_string(selected_cols)

        title_suffix = " (+Z)" if include_z else ""
        title_text = tr("range.row_format_suffix", row_range=row_range, suffix=title_suffix) if full_row_selected else tr("range.row_col_suffix", row_range=row_range, col_range=col_range, suffix=title_suffix)
        dialog = FormatDialog("hline", title_text, self)

        if dialog.exec() == QDialog.Accepted:
            # 헬퍼 함수를 사용하여 한 줄로 깔끔하게 정리!
            raw_input = dialog.line_edit.text().strip().strip('{}')
            user_input_clean = self.clean_line_options(raw_input)
           
            # 이후 기존 코드 그대로 진행
            style, is_double, is_thick = dialog.get_line_format_info()

            grouped_rows = row_range
            if include_z:
                grouped_rows = f"{grouped_rows},Z" if grouped_rows else "Z"

            combined_parts = [p for p in (style, user_input_clean) if p]
            if is_thick:
                combined_parts.append("0.8pt") # 두꺼운 선 굵기 지정
                
            combined = ", ".join(combined_parts)
            options_part = f"{{{combined}}}" if combined else "{}"

            # 전체 행 선택 여부에 따라 공통 range_part 생성
            # 단일 선일 때는 생략(""), 이중선일 때는 "{-}" 사용
            if full_row_selected:
                range_part = "{-}" if is_double else "" 
            else:
                range_part = f"{{{col_range}}}"

            if is_double:
                # 두 줄 추가
                self.input_lines.appendPlainText(f"hline{{{grouped_rows}}} = {{1}}{range_part}{options_part}, % double")
                self.input_lines.appendPlainText(f"hline{{{grouped_rows}}} = {{2}}{range_part}{options_part}, % double")
            else:
                self.input_lines.appendPlainText(f"hline{{{grouped_rows}}} = {range_part}{options_part}")

            self.generate_latex()

    def insert_vline_format(self, include_z=False):
        indexes = self.table.selectedIndexes()
        if not indexes:
            return

        selected_rows = sorted(set(idx.row() + 1 for idx in indexes))
        selected_cols = sorted(set(idx.column() + 1 for idx in indexes))

        total_rows = self.table.rowCount()

        # 열 전체 선택 여부를 selectionModel로 판별
        full_col_selected = bool(self.table.selectionModel().selectedColumns())

        # 열 전체 선택이면 병합 셀 무시하고 전체 행 강제 (아주 훌륭한 처리입니다!)
        if full_col_selected:
            row_range = self.get_range_string(range(1, total_rows + 1))
        else:
            row_range = self.get_range_string(selected_rows)

        col_range = self.get_range_string(selected_cols)

        title_suffix = " (+Z)" if include_z else ""
        title_text = tr("range.col_format_suffix", col_range=col_range, suffix=title_suffix) if full_col_selected else tr("range.col_row_suffix", col_range=col_range, row_range=row_range, suffix=title_suffix)
        dialog = FormatDialog("vline", title_text, self)

        if dialog.exec() == QDialog.Accepted:
            # 헬퍼 함수를 사용하여 한 줄로 깔끔하게 정리!
            raw_input = dialog.line_edit.text().strip().strip('{}')
            user_input_clean = self.clean_line_options(raw_input)
            style, is_double, is_thick = dialog.get_line_format_info()

            grouped_cols = col_range
            if include_z:
                grouped_cols = f"{grouped_cols},Z" if grouped_cols else "Z"

            combined_parts = [p for p in (style, user_input_clean) if p]
            if is_thick:
                combined_parts.append("0.8pt")
            
            combined = ", ".join(combined_parts)
            options_part = f"{{{combined}}}" if combined else "{}"

            # 전체 열 선택 여부에 따라 공통 range_part 생성
            # 단일 선일 때는 생략(""), 이중선일 때는 "{-}" (전체 행) 명시
            if full_col_selected:
                range_part = "{-}" if is_double else ""
            else:
                range_part = f"{{{row_range}}}"

            # range_part를 통일하여 중복 코드 제거
            if is_double:
                self.input_lines.appendPlainText(f"vline{{{grouped_cols}}} = {{1}}{range_part}{options_part}, % double")
                self.input_lines.appendPlainText(f"vline{{{grouped_cols}}} = {{2}}{range_part}{options_part}, % double")
            else:
                self.input_lines.appendPlainText(f"vline{{{grouped_cols}}} = {range_part}{options_part}")

            self.generate_latex()

    def insert_z_line_format(self, is_horizontal=True):
        indexes = self.table.selectedIndexes()
        if not indexes:
            return

        if is_horizontal:
            # Z행 (맨 아래 가로선) 처리
            selected_cols = sorted(set(idx.column() + 1 for idx in indexes))
            total_columns = self.table.columnCount()

            # [핵심 수정] 헤더 클릭뿐만 아니라, 드래그로 전체 셀을 잡은 경우도 정확하게 판별!
            full_selected = (len(selected_cols) == total_columns)
            
            if full_selected:
                range_str = self.get_range_string(range(1, total_columns + 1))
            else:
                range_str = self.get_range_string(selected_cols)

            fmt_type = "hline"
            title_range = tr("range.z_row")
            line_cmd = "hline"

        else:
            # Z열 (맨 오른쪽 세로선) 처리
            selected_rows = sorted(set(idx.row() + 1 for idx in indexes))
            total_rows = self.table.rowCount()

            # [핵심 수정] 행 전체 선택 여부를 더 안전하게 판별
            full_selected = (len(selected_rows) == total_rows)
            
            if full_selected:
                range_str = self.get_range_string(range(1, total_rows + 1))
            else:
                range_str = self.get_range_string(selected_rows)

            fmt_type = "vline"
            title_range = tr("range.z_col")
            line_cmd = "vline"

        dialog = FormatDialog(fmt_type, title_range, self)
        if dialog.exec() == QDialog.Accepted:
            # 헬퍼 함수를 사용하여 한 줄로 깔끔하게 정리!
            raw_input = dialog.line_edit.text().strip().strip('{}')
            user_input_clean = self.clean_line_options(raw_input)
            style, is_double, is_thick = dialog.get_line_format_info()

            combined_parts = [p for p in (style, user_input_clean) if p]
            if is_thick:
                combined_parts.append("0.8pt")
                
            combined = ", ".join(combined_parts)
            options_part = f"{{{combined}}}" if combined else "{}"

            # 전체 선택 여부에 따라 range_part 통일 (hline, vline과 완벽히 동일한 구조)
            if full_selected:
                range_part = "{-}" if is_double else ""
            else:
                range_part = f"{{{range_str}}}"

            if is_double:
                self.input_lines.appendPlainText(f"{line_cmd}{{Z}} = {{1}}{range_part}{options_part}, % double")
                self.input_lines.appendPlainText(f"{line_cmd}{{Z}} = {{2}}{range_part}{options_part}, % double")
            else:
                self.input_lines.appendPlainText(f"{line_cmd}{{Z}} = {range_part}{options_part}")

            self.generate_latex()

    # ==========================================
    # 클립보드 복사
    # ==========================================
    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.output_text.toPlainText())
        
        # 상태 표시줄 좌측 하단에 3초(3000ms) 동안 메시지 표시
        self.statusbar.showMessage(tr("status.copied"), 3000)

    # ==========================================
    # 상태 표시줄 셀 위치 업데이트
    # ==========================================
    def update_position(self, current_row, current_col, previous_row, previous_col):
        # 포커스가 해제되거나 표가 초기화될 때(-1)를 대비한 예외 처리
        if current_row >= 0 and current_col >= 0:
            # QTableWidget은 0부터 시작하므로 직관적인 1 기반 인덱스로 변환
            m = current_row + 1
            n = current_col + 1
            self.pos_label.setText(f"({m}, {n})")
        else:
            self.pos_label.setText("(-, -)")
    
    # ==========================================
    # 셀 에디터 ↔ 표 동기화
    # ==========================================
    def sync_cell_to_editor(self, row, col, prev_row, prev_col):
        if row >= 0 and col >= 0:
            item = self.table.item(row, col)
            self.cell_editor.blockSignals(True)
            self.cell_editor.setPlainText(item.text() if item else "")
            self.cell_editor.blockSignals(False)

    def sync_editor_to_cell(self):
        row, col = self.table.currentRow(), self.table.currentColumn()
        if row < 0 or col < 0:
            return
        text = self.cell_editor.toPlainText()
        if not self.table.item(row, col):
            self.table.setItem(row, col, QTableWidgetItem())
        self.table.item(row, col).setText(text)
        self.generate_latex()

    def save_table_action(self):
        """'저장(Save)' 기능: 파일이 있으면 덮어쓰고, 없으면 '다른 이름으로 저장' 실행"""
        if self.current_file:
            self.save_table(self.current_file)
            self.statusbar.showMessage(tr("status.saved"), 3000)
        else:
            # 저장된 적이 없는 새 파일인 경우
            self.save_as_dialog()

    def save_as_dialog(self):
        """'다른 이름으로 저장(Save As)' 기능"""
        last_dir = self.settings.value("last_tblr_dir", "")
        
        file_filter = "Tabularray Files (*.tblr);;JSON Files (*.json);;All Files (*)"
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Table As", last_dir, file_filter
        )
        
        if filename:
            if not filename.endswith('.tblr') and not filename.endswith('.json'):
                filename += '.tblr'
                
            # 현재 파일 상태 업데이트 및 설정 저장
            self.current_file = filename
            self.settings.setValue("last_tblr_dir", QFileInfo(filename).absolutePath())
            
            # 실제 저장 로직 호출 및 창 제목 업데이트
            self.save_table(filename)
            self.update_window_title()

    def load_table_dialog(self):
        """'불러오기(Open)' 기능"""
        last_dir = self.settings.value("last_tblr_dir", "")
        
        file_filter = "Tabularray Files (*.tblr);;JSON Files (*.json);;All Files (*)"
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Table", last_dir, file_filter
        )
        
        if filename:
            # # 현재 파일 상태 업데이트 및 설정 저장
            # self.current_file = filename
            # self.settings.setValue("last_tblr_dir", QFileInfo(filename).absolutePath())
            
            # 실제 로드 로직 호출 및 창 제목 업데이트
            self.load_table(filename)
            # self.update_window_title()

    def save_table(self, filename):
        rows = self.spin_rows.value()
        cols = self.spin_cols.value()

        cells = []
        for r in range(rows):
            row_data = []
            for c in range(cols):
                item = self.table.item(r, c)
                text = item.text() if item else ""
                row_data.append({
                    "text": text,
                    "row_span": self.table.rowSpan(r, c),
                    "col_span": self.table.columnSpan(r, c),
                })
            cells.append(row_data)

        # ---------------------------------------------------------
        # [추가된 부분] 현재 각 열의 너비 정보 수집
        # ---------------------------------------------------------
        column_widths = [self.table.columnWidth(c) for c in range(cols)]

        data = {
            "tblr_format_version": "3.9",
            "env_type": self.env_combobox.currentText(),
            "outer_options": self.outer_options_input.toPlainText(),
            "inner_extra": self.inner_extra_input.toPlainText(),
            "lines": self.input_lines.toPlainText(),
            "rows": rows,
            "cols": cols,
            "row_format": self.input_row_format.toPlainText(),
            "cell_format": self.input_cell_format.toPlainText(),
            "generic_option": self.input_general_settings.toPlainText(),
            "colspec": self.input_colspec.text(),
            "latex_code": self.output_text.toPlainText(),
            "cells": cells,
            "column_widths": column_widths,
            "radio_state": (
                "linewidth" if self.radio_linewidth.isChecked() else
                "natural" if self.radio_natural.isChecked() else
                "manual"
            ),
            # ---------------------------------------------------------
            # [추가된 부분] 체크박스 및 추가 명령어 텍스트 상태 저장
            # ---------------------------------------------------------
            "bottomrule_checked": self.bottomrule_checkbox.isChecked(),
            "extra_cmd_text": self.extra_cmd_input.text()
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_table(self, filename):
        # 1. 파일 세팅 중 불필요한 경고 메시지가 뜨는 것을 방지하기 위해 먼저 natural로 설정
        self.radio_natural.setChecked(True)

        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        if filename:
            # 현재 파일 상태 업데이트 및 설정 저장
            self.current_file = filename
            self.settings.setValue("last_tblr_dir", QFileInfo(filename).absolutePath())
            
            # 창 제목 업데이트
            self.update_window_title()

        version = data.get("tblr_format_version", "1.0")
        # 현재는 사용하지 않지만, 나중에 버전별 처리 분기 가능

        rows = data.get("rows", 0)
        cols = data.get("cols", 0)
        
        # 여기서 값이 세팅될 때 natural 상태이므로 경고가 발생하지 않음
        self.spin_rows.setValue(rows)
        self.spin_cols.setValue(cols)
        self.resize_table(rows, cols)

        # ---------------------------------------------------------
        # [추가된 부분] 테이블 크기 할당 직후 열 너비 복원
        # ---------------------------------------------------------
        column_widths = data.get("column_widths", [])
        if column_widths:
            header = self.table.horizontalHeader()
            header.blockSignals(True) # 설정 중 sectionResized 시그널 방지
            for c, w in enumerate(column_widths):
                if c < cols: # 현재 생성된 열 개수 범위 내에서만 안전하게 적용
                    self.table.setColumnWidth(c, w)
            header.blockSignals(False)
        # ---------------------------------------------------------

        self.input_lines.setPlainText(data.get("lines", ""))
        
        row_format_text = data.get("row_format", "")
        cell_format_text = data.get("cell_format", "")
        
        self.input_row_format.setPlainText(row_format_text)
        self.input_cell_format.setPlainText(cell_format_text)
        self.input_general_settings.setPlainText(data.get("generic_option", ""))
        self.input_colspec.setText(data.get("colspec", ""))
        self.output_text.setPlainText(data.get("latex_code", ""))

        # --- 환경 설정 및 Long/Tall 탭 옵션 복구 ---
        env_type = data.get("env_type", "tblr")
        self.env_combobox.setCurrentText(env_type) 
        
        saved_outer = data.get("outer_options", "")
        if saved_outer:
            self.outer_options_input.setPlainText(saved_outer)
            
        saved_inner = data.get("inner_extra", "")
        if saved_inner:
            self.inner_extra_input.setPlainText(saved_inner)
        # ---------------------------------------------------------
        
        # 2. 모든 데이터 세팅이 끝난 후, 저장되어 있던 원래 라디오 버튼 상태로 복구
        radio_state = data.get("radio_state", "manual")
        if radio_state == "linewidth":
            self.radio_linewidth.setChecked(True)
        elif radio_state == "natural":
            self.radio_natural.setChecked(True)
        else:
            self.radio_manual.setChecked(True)

        # ---------------------------------------------------------
        # [추가된 부분] 체크박스 및 추가 명령어 텍스트 상태 복원
        # ---------------------------------------------------------
        self.bottomrule_checkbox.setChecked(data.get("bottomrule_checked", False))
        self.extra_cmd_input.setText(data.get("extra_cmd_text", ""))
        # ---------------------------------------------------------

        # 셀 데이터 및 병합 상태 복원
        cells = data.get("cells", [])
        for r in range(len(cells)):
            for c in range(len(cells[r])):
                cell_info = cells[r][c]
                text = cell_info.get("text", "")
                
                # QTableWidgetItem 객체 생성 후 테이블에 삽입
                item = QTableWidgetItem(text)
                self.table.setItem(r, c, item)
                
                row_span = cell_info.get("row_span", 1)
                col_span = cell_info.get("col_span", 1)
                
                if row_span > 1 or col_span > 1:
                    self.table.setSpan(r, c, row_span, col_span)

        # ---------------------------------------------------------
        # [배경색 복원 로직 추가] cell_format을 파싱하여 배경색 칠하기
        # ---------------------------------------------------------
        if cell_format_text:
            # 정규식: cell{row}{col} = { ... bg=color ... } 패턴 검색
            # (LaTeX의 row, col 인덱스는 1부터 시작하므로 -1 처리 필요)
            pattern = r"cell\{(\d+)\}\{(\d+)\}\s*=\s*\{[^}]*bg=([^,}]+)[^}]*\}"
            
            for match in re.finditer(pattern, cell_format_text):
                r_idx = int(match.group(1)) - 1
                c_idx = int(match.group(2)) - 1
                color_str = match.group(3).strip()
                
                # LaTeX 혼합 색상(예: red!20) 처리
                if "!" in color_str:
                    base_color_str, percent_str = color_str.split("!")
                    try:
                        percent = int(percent_str) / 100.0
                    except ValueError:
                        percent = 1.0
                    
                    base_color = QColor(base_color_str)
                    if base_color.isValid():
                        # 배경(흰색)과 지정한 비율로 혼합하여 파스텔 톤 색상 생성
                        r_col = int(base_color.red() * percent + 255 * (1 - percent))
                        g_col = int(base_color.green() * percent + 255 * (1 - percent))
                        b_col = int(base_color.blue() * percent + 255 * (1 - percent))
                        qcolor = QColor(r_col, g_col, b_col)
                    else:
                        qcolor = QColor("white")
                else:
                    qcolor = QColor(color_str)
                
                # 유효한 인덱스인지 확인 후 아이템에 배경색 적용
                if 0 <= r_idx < self.table.rowCount() and 0 <= c_idx < self.table.columnCount():
                    item = self.table.item(r_idx, c_idx)
                    if item and qcolor.isValid():
                        item.setBackground(qcolor)
        # ---------------------------------------------------------

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+G"), self).activated.connect(self.goto_row)
        QShortcut(QKeySequence("Ctrl+Shift+G"), self).activated.connect(self.goto_column)
        QShortcut(QKeySequence("Alt+Shift+G"), self).activated.connect(self.goto_specific_cell)
        QShortcut(QKeySequence("Ctrl+Alt+G"), self).activated.connect(self.goto_specific_cell)

        # 1. Ctrl+F (찾기)
        self.shortcut_find = QShortcut(QKeySequence("Ctrl+F"), self.table)
        self.shortcut_find.setContext(Qt.WidgetShortcut) # 핵심: 테이블 포커스 시에만 작동!
        self.shortcut_find.activated.connect(self.find_text)

        # 2. Ctrl+H (모두 바꾸기)
        self.shortcut_replace = QShortcut(QKeySequence("Ctrl+H"), self.table)
        self.shortcut_replace.setContext(Qt.WidgetShortcut)
        self.shortcut_replace.activated.connect(self.replace_all)

        # 3. F3 (다음 찾기)
        self.shortcut_f3 = QShortcut(QKeySequence("F3"), self)  # self.table -> self로 변경
        self.shortcut_f3.setContext(Qt.WindowShortcut)          # WidgetShortcut -> WindowShortcut으로 변경
        self.shortcut_f3.activated.connect(self.find_next)

        # 4. Shift+F3 (이전 찾기)
        self.shortcut_shift_f3 = QShortcut(QKeySequence("Shift+F3"), self) # 동일하게 변경
        self.shortcut_shift_f3.setContext(Qt.WindowShortcut)               # 동일하게 변경
        self.shortcut_shift_f3.activated.connect(self.find_prev)

        # Ctrl+S → 저장
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_table_action)
        save_as_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        save_as_shortcut.activated.connect(self.save_as_dialog)

        # Ctrl+O → 불러오기
        open_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        open_shortcut.activated.connect(self.load_table_dialog)

        # F12 => colspec 편집
        QShortcut(QKeySequence("F12"), self).activated.connect(self.open_colspec_dialog)

        # [F9] 단축키 기존 클리어 기능 제거 -> Template 기능으로 대체
        self.shortcut_template = QShortcut(QKeySequence("F9"), self)
        self.shortcut_template.activated.connect(self.open_template_manager)

    def replace_all(self):
        dialog = ReplaceDialog(self)
        
        if dialog.exec():
            target_text, replace_text, is_case_sensitive, is_regex = dialog.get_data()

            if not target_text:
                QMessageBox.warning(self, tr("find.input_error_title"), tr("find.input_error_body"))
                return

            # 1. 대소문자 구분 및 정규식 옵션에 따른 패턴 준비
            flags = 0 if is_case_sensitive else re.IGNORECASE
            
            # 정규식 모드가 아니면 특수문자들을 일반 문자로 취급하도록 이스케이프 처리
            pattern_str = target_text if is_regex else re.escape(target_text)

            # 정규식 문법 오류 처리
            try:
                pattern = re.compile(pattern_str, flags)
            except re.error as e:
                QMessageBox.warning(self, tr("find.regex_error_title"), tr("find.regex_error_body", err=str(e)))
                return

            replace_count = 0
            modified_cells = 0

            # 2. 테이블 순회 및 치환
            for r in range(self.table.rowCount()):
                for c in range(self.table.columnCount()):
                    item = self.table.item(r, c)
                    
                    if item:
                        original_text = item.text()
                        if not original_text:
                            continue

                        # 정규식 모드: replace_text 내의 \1 등 캡처 그룹을 허용
                        # 일반 모드: replace_text를 순수 리터럴 문자로 취급 (람다 함수로 치환 텍스트 고정)
                        repl = replace_text if is_regex else lambda m: replace_text

                        # subn은 (변경된 문자열, 치환된 횟수) 튜플을 반환합니다.
                        new_text, count = pattern.subn(repl, original_text)
                        
                        if count > 0:
                            item.setText(new_text)
                            replace_count += count
                            modified_cells += 1

            # 3. 결과 안내
            if modified_cells > 0:
                QMessageBox.information(self, tr("find.replace_done_title"), tr("find.replace_done_table_body", modified=modified_cells, count=replace_count))
            else:
                QMessageBox.information(self, tr("find.no_result_title"), tr("find.no_result_table_body", text=target_text))


    def find_text(self):
        text, ok = QInputDialog.getText(self, tr("find.table_dialog_title"), tr("find.search_label"))
        if ok and text:
            self.search_results = []
            # 대소문자 무시 검색을 위해 소문자로 통일
            search_query = text.lower() 
            
            for r in range(self.table.rowCount()):
                for c in range(self.table.columnCount()):
                    item = self.table.item(r, c)
                    # item.text()도 소문자로 변환하여 비교
                    if item and search_query in item.text().lower():
                        self.search_results.append((r, c))
                        
            self.search_index = 0
            
            if self.search_results:
                r, c = self.search_results[0]
                self.table.setCurrentCell(r, c)
            else:
                # 결과가 없을 때 알림창 표시
                QMessageBox.information(self, tr("find.result_title"), tr("find.no_result_simple_body", text=text))

    def find_next(self):
        """F3 단축키가 눌렸을 때 호출되는 함수"""
        
        # 현재 포커스가 텍스트 에디터에 있거나, 마지막으로 검색한 위젯이 텍스트 에디터라면
        focused_widget = self.focusWidget()
        
        if isinstance(focused_widget, (QTextEdit, QPlainTextEdit)) or \
           (hasattr(self, "last_search_widget") and self.last_search_widget == focused_widget):
            self.find_next_in_text()
            
        # 그 외의 경우(또는 테이블에 포커스가 있는 경우) 기존 테이블 검색 로직 실행
        else:
            if hasattr(self, "search_results") and self.search_results:
                self.search_index = (self.search_index + 1) % len(self.search_results)
                r, c = self.search_results[self.search_index]
                self.table.setCurrentCell(r, c)

    def find_prev(self):
        """Shift+F3 단축키가 눌렸을 때 호출되는 함수"""
        focused_widget = self.focusWidget()
        
        # 텍스트 에디터 영역일 때
        if isinstance(focused_widget, (QTextEdit, QPlainTextEdit)) or \
           (hasattr(self, "last_search_widget") and self.last_search_widget == focused_widget):
            self.find_prev_in_text()
            
        # 테이블 영역일 때
        else:
            if hasattr(self, "search_results") and self.search_results:
                # 역순 순환 (0에서 -1이 되면 자동으로 마지막 인덱스로 이동)
                self.search_index = (self.search_index - 1) % len(self.search_results)
                r, c = self.search_results[self.search_index]
                self.table.setCurrentCell(r, c)

    def find_in_text_widget(self, widget):
        """넘겨받은 텍스트 위젯에서 텍스트를 검색합니다."""
        text, ok = QInputDialog.getText(self, tr("find.editor_dialog_title"), tr("find.search_label"))

        if ok and text:
            # 상태 기록: "지금부터는 텍스트 에디터 검색을 추적해라"
            self.last_search_target = "text" 
            
            self.last_search_text = text
            self.last_search_widget = widget
            
            self.find_next_in_text()
 
    def find_next_in_text(self):
        """저장된 검색어와 위젯 정보를 바탕으로 다음 텍스트를 찾습니다."""
        if not hasattr(self, "last_search_text") or not self.last_search_text:
            return
            
        widget = self.last_search_widget
        text = self.last_search_text
        
        widget.setFocus()
        
        # 1. 현재 커서 위치에서 아래로 찾기
        found = widget.find(text)
        
        # 2. 아래에 없으면 문서 맨 위로 커서를 이동시켜서 다시 찾기 (순환)
        if not found:
            cursor = widget.textCursor()
            # PySide6 엄격한 Enum 적용
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            widget.setTextCursor(cursor)
            
            found = widget.find(text)
            
            if not found:
                QMessageBox.information(self, tr("find.result_title"), tr("find.no_result_doc_body", text=text))

    def find_prev_in_text(self):
        """저장된 검색어와 위젯 정보를 바탕으로 이전 텍스트(역방향)를 찾습니다."""
        if not hasattr(self, "last_search_text") or not self.last_search_text:
            return
            
        widget = self.last_search_widget
        text = self.last_search_text
        
        widget.setFocus()
        
        # 1. 현재 커서 위치에서 위로(역방향) 찾기
        # find() 함수의 두 번째 인자로 FindBackward 플래그를 전달합니다.
        found = widget.find(text, QTextDocument.FindFlag.FindBackward)
        
        # 2. 위에 더 이상 없으면 문서 맨 아래(End)로 커서를 이동시켜서 다시 찾기 (순환)
        if not found:
            cursor = widget.textCursor()
            # 문서의 맨 끝으로 이동
            cursor.movePosition(QTextCursor.MoveOperation.End)
            widget.setTextCursor(cursor)
            
            # 다시 역방향 검색
            found = widget.find(text, QTextDocument.FindFlag.FindBackward)
            
            if not found:
                QMessageBox.information(self, tr("find.result_title"), tr("find.no_result_doc_body", text=text))

    def replace_in_text_widget(self, widget):
        """넘겨받은 텍스트 위젯에서 텍스트를 모두 찾아 바꿉니다."""
        dialog = ReplaceDialog(self)
        
        if dialog.exec():
            widget.setFocus()
            target_text, replace_text = dialog.get_texts()

            if not target_text:
                return

            full_text = widget.toPlainText()
            
            if target_text in full_text:
                replace_count = full_text.count(target_text)
                new_text = full_text.replace(target_text, replace_text)
                
                # 위젯에 치환된 텍스트 덮어쓰기
                widget.setPlainText(new_text)
                
                QMessageBox.information(self, tr("find.replace_done_title"), tr("find.replace_done_editor_body", count=replace_count))
            else:
                QMessageBox.information(self, tr("find.no_result_title"), tr("find.no_result_doc_body", text=target_text))

    def goto_row(self):
        row, ok = QInputDialog.getInt(
            self,
            tr("goto.row_title"),
            tr("goto.row_label"),
            value=0,
            minValue=0,
            maxValue=self.table.rowCount()
        )
        if ok:
            self.table.setCurrentCell(row - 1, 0)

    def goto_column(self):
        # 1. 현재 선택된 행의 인덱스를 가져옵니다.
        current_row = self.table.currentRow()
        
        # 만약 선택된 셀이 하나도 없다면 기본값으로 0(첫 번째 행)을 지정할 수 있습니다.
        if current_row < 0:
            current_row = 0

        # 2. 사용자에게 이동할 열 번호를 입력받습니다.
        col, ok = QInputDialog.getInt(
            self,
            tr("goto.col_title"),
            tr("goto.col_label"),
            value=1,  # 기본값
            minValue=1, # 1열부터 시작
            maxValue=self.table.columnCount() # 테이블의 전체 열 개수를 최댓값으로 설정
        )
        
        # 3. 입력이 정상적으로 완료되었다면 해당 셀로 이동합니다.
        if ok:
            # 사용자가 입력한 번호는 1부터 시작하므로, 인덱스(0부터 시작)에 맞게 -1을 해줍니다.
            self.table.setCurrentCell(current_row, col - 1)

    def goto_specific_cell(self):
        # 1. 사용자에게 텍스트 형태로 행과 열을 입력받습니다.
        text, ok = QInputDialog.getText(
            self,
            tr("goto.cell_title"),
            tr("goto.cell_label")
        )

        if ok and text:
            try:
                # 2. 쉼표(,)를 기준으로 입력받은 문자열을 두 개로 나눕니다.
                parts = text.split(',')
                
                # 입력값이 두 부분(행, 열)으로 나뉘지 않으면 에러를 발생시킵니다.
                if len(parts) != 2:
                    raise ValueError
                
                # 3. 공백을 제거하고 정수(숫자)로 변환합니다.
                row = int(parts[0].strip())
                col = int(parts[1].strip())

                # 4. 입력한 숫자가 테이블 범위 안에 있는지 확인합니다.
                max_row = self.table.rowCount()
                max_col = self.table.columnCount()

                if 1 <= row <= max_row and 1 <= col <= max_col:
                    # 인덱스는 0부터 시작하므로 각각 1을 빼고 이동합니다.
                    self.table.setCurrentCell(row - 1, col - 1)
                else:
                    # 범위를 벗어난 숫자를 입력했을 때의 경고창
                    QMessageBox.warning(
                        self, 
                        tr("goto.out_of_range_title"), 
                        tr("goto.out_of_range_body", max_row=max_row, max_col=max_col)
                    )

            except ValueError:
                # 숫자가 아닌 문자를 적었거나, 쉼표 없이 적었을 때의 경고창
                QMessageBox.warning(
                    self, 
                    tr("goto.bad_format_title"), 
                    tr("goto.bad_format_body")
                )

    def _refresh_language_menu(self):
        """언어 서브메뉴를 열 때마다 호출되어 체크 표시를 최신 상태로 맞춘다.

        - 체크(✓): self.active_language, 즉 지금 이 창에 실제로 그려져 있는 언어.
        - 대기 표시(◆): QSettings에 저장된 언어가 active_language와 다를 때
          (= 언어를 바꿨지만 아직 재시작 전이라 화면엔 반영 안 된 상태).
          이 경우 두 항목 모두 체크로 보이는 대신, 활성 언어만 체크되고
          "다음 실행부터 적용될" 언어 쪽에는 ◆ 표시가 붙는다.
        """
        pending_lang = self.settings.value("language", self.active_language)
        if pending_lang not in ("ko", "en"):
            pending_lang = self.active_language

        labels = {"ko": "한국어", "en": "English"}
        actions = {"ko": self.action_lang_ko, "en": self.action_lang_en}

        for lang, action in actions.items():
            is_active = (lang == self.active_language)
            is_pending = (lang == pending_lang and pending_lang != self.active_language)

            action.setChecked(is_active)
            suffix = "  ◆" if is_pending else ""
            action.setText(labels[lang] + suffix)
            action.setToolTip(tr("main.lang.pending_tooltip") if is_pending else "")

    def change_language(self, lang: str):
        """[추가] 언어 전환: 설정을 저장하고, 프로그램을 재시작해야 전체 UI에 반영됨을 안내."""
        if lang == self.settings.value("language", self.active_language):
            return
        set_language(lang)
        self.settings.setValue("language", lang)
        self._refresh_language_menu()
        QMessageBox.information(
            self,
            tr("main.lang.changed_title"),
            tr("main.lang.changed_body"),
        )

    def new_task(self):
        """Ctrl+N: 아무것도 없이 2x3 행/열만 지정한 깨끗한 상태로 만듦"""
        self.current_file = None
        self.update_window_title()
        
        self.spin_rows.setValue(2)
        self.spin_cols.setValue(3)
        
        # 2x3 테이블로 완전히 비워진 초기 상태 생성
        self.clear_all_settings_to_default(r=2, c=3)
        self.statusbar.showMessage(tr("status.reset_2x3"), 3000)

    def clear_all_settings_to_default(self, r=2, c=3):
        """테이블 크기를 r x c로 바꾸고 모든 괘선 및 서식 설정을 기본값으로 클리어"""
        self.table.blockSignals(True)
        self.table.clear()
        self.table.setRowCount(r)
        self.table.setColumnCount(c)
        
        # 빈 아이템들로 채우기
        for row in range(r):
            for col in range(c):
                self.table.setItem(row, col, QTableWidgetItem(""))
        self.table.blockSignals(False)
        
        # 에디터 및 설정창 초기화
        self.input_lines.setPlainText("")
        self.input_row_format.clear()
        self.input_cell_format.clear()
        self.input_general_settings.clear()
        self.outer_options_input.clear()
        self.inner_extra_input.clear()
        self.input_colspec.clear()
        
        self.radio_linewidth.setChecked(True)
        self._refresh_headers()
        self.generate_latex()

    ############################
    ## 도움말
    ############################
    def show_help(self):
        is_mac = platform.system() == "Darwin"

        if is_mac:
            help_text = tr("help.mac_text")
        else:
            help_text = tr("help.win_text")

        QMessageBox.information(self, tr("help.title"), help_text)

    def reset_column_widths(self):
        """모든 열의 너비를 기본값(80)으로 일괄 초기화"""
        header = self.table.horizontalHeader()
        
        # 시그널을 잠시 차단하여 불필요한 연산 방지
        header.blockSignals(True)
        
        for col in range(self.table.columnCount()):
            header.resizeSection(col, 80)
            
        header.blockSignals(False)

    def show_context_menu(self, pos):
        """우클릭 시 메뉴를 생성하고 표시"""
        row_idx = self.table.rowAt(pos.y())
        col_idx = self.table.columnAt(pos.x())

        # 마지막 행 아래나 마지막 열 오른쪽처럼, 표 위젯 영역 안이지만
        # 실제 셀이 없는 여백을 우클릭한 경우에도 메뉴가 뜨도록
        # 가장 가까운 유효한 행/열로 대체한다. (표 자체가 비어 있을 때만 취소)
        if row_idx < 0:
            row_idx = self.table.rowCount() - 1
        if col_idx < 0:
            col_idx = self.table.columnCount() - 1
        if row_idx < 0 or col_idx < 0:
            return

        target_row = row_idx + 1
        target_col = col_idx + 1

        menu = QMenu(self)

        copy_action = QAction(tr("ctx.copy"), self)
        cut_action = QAction(tr("ctx.cut"), self)
        paste_action = QAction(tr("ctx.paste"), self)
        delete_action = QAction(tr("ctx.delete"), self)

        reset_width_action = QAction(tr("ctx.reset_width"), self)
        apply_rel_width_action = QAction(tr("ctx.apply_rel_width"), self)

        # --- [추가 1] 행/열 추가 삭제 액션 생성 ---
        insert_row_action = QAction(tr("ctx.insert_row"), self)
        delete_row_action = QAction(tr("ctx.delete_row"), self)
        insert_col_action = QAction(tr("ctx.insert_col"), self)
        delete_col_action = QAction(tr("ctx.delete_col"), self)
        # ----------------------------------------

        cell_format_action = QAction(tr("ctx.cell_format"), self)
        row_format_action = QAction(tr("ctx.row_format"), self)
        column_format_action = QAction(tr("ctx.column_format"), self)

        adv_cell_action = QAction(tr("ctx.adv_cell"), self)
        adv_row_action = QAction(tr("ctx.adv_row"), self)
        adv_col_action = QAction(tr("ctx.adv_col"), self)

        merge_action = QAction(tr("ctx.merge"), self)
        unmerge_action = QAction(tr("ctx.unmerge"), self)

        hline_action = QAction(tr("ctx.hline"), self)
        hline_z_action = QAction(tr("ctx.hline_z"), self)
        vline_action = QAction(tr("ctx.vline"), self)
        vline_z_action = QAction(tr("ctx.vline_z"), self)
        
        z_hline_action = QAction(tr("ctx.z_hline"), self)
        z_vline_action = QAction(tr("ctx.z_vline"), self)

        # 2. 검색 및 수정 기능
        find_action = QAction(tr("ctx.find"), self)
        replace_action = QAction(tr("ctx.replace"), self)

        selected_indexes = self.table.selectedIndexes()
        
        if not selected_indexes:
            merge_action.setEnabled(False)
            unmerge_action.setEnabled(False)
        else:
            has_merged_cell = False
            for idx in selected_indexes:
                r, c = idx.row(), idx.column()
                if self.table.rowSpan(r, c) > 1 or self.table.columnSpan(r, c) > 1:
                    has_merged_cell = True
                    break

            # 1. 선택된 전체 영역의 크기(Bounding Box) 계산
            min_row = min(idx.row() for idx in selected_indexes)
            max_row = max(idx.row() for idx in selected_indexes)
            min_col = min(idx.column() for idx in selected_indexes)
            max_col = max(idx.column() for idx in selected_indexes)
            
            span_rows = max_row - min_row + 1
            span_cols = max_col - min_col + 1
            
            # 2. 선택된 영역이 '정확히 1개의 병합된 셀' 자체인지 확인
            top_left_row_span = self.table.rowSpan(min_row, min_col)
            top_left_col_span = self.table.columnSpan(min_row, min_col)
            
            is_single_logical_cell = (span_rows == top_left_row_span) and (span_cols == top_left_col_span)

            # [병합 해제] 병합된 셀이 하나라도 영역에 포함되어 있으면 무조건 활성화
            unmerge_action.setEnabled(has_merged_cell)
            
            # [셀 병합] 전체 선택 영역이 2칸 이상이면서, 딱 1개의 병합 셀만 선택한 게 아닐 때 활성화
            if (span_rows * span_cols > 1) and not is_single_logical_cell:
                merge_action.setEnabled(True)
            else:
                merge_action.setEnabled(False)
        # ---------------------------------------------------------

        # 5. 단축키 텍스트 표시 설정
        copy_action.setShortcut("Ctrl+C")
        cut_action.setShortcut("Ctrl+X")
        paste_action.setShortcut("Ctrl+V")
        
        # --- [추가 2] 단축키 표시 설정 ---
        insert_row_action.setShortcut("Ctrl+Return")
        delete_row_action.setShortcut("Ctrl+Del")
        insert_col_action.setShortcut("F7")
        delete_col_action.setShortcut("F8")
        # -------------------------------

        cell_format_action.setShortcut("F5")
        row_format_action.setShortcut("F6")
        column_format_action.setShortcut("Ctrl+F6")
        
        merge_action.setShortcut("Ctrl+M")
        unmerge_action.setShortcut("Ctrl+U")

        hline_action.setShortcut("Alt+H")
        hline_z_action.setShortcut("Shift+Alt+H")
        vline_action.setShortcut("Alt+V")
        vline_z_action.setShortcut("Shift+Alt+V")
        
        z_hline_action.setShortcut("Alt+Z")
        z_vline_action.setShortcut("Shift+Alt+Z")

        # 6. 시그널 연결
        copy_action.triggered.connect(self.copy_selection)
        cut_action.triggered.connect(self.cut_selection)
        paste_action.triggered.connect(self.paste_selection)
        delete_action.triggered.connect(self.delete_selection)

        # --- [추가 3] 시그널 연결 (클릭한 행/열의 인덱스를 메서드로 전달) ---
        # 람다식의 기본값(_=False)을 주어 QAction.triggered가 보내는 불리언 값과 충돌하지 않게 처리합니다.
        insert_row_action.triggered.connect(lambda _: self.insert_row_action(row_idx + 1))
        delete_row_action.triggered.connect(lambda _: self.delete_row_action(row_idx))
        insert_col_action.triggered.connect(lambda _: self.insert_column_action(col_idx + 1))
        delete_col_action.triggered.connect(lambda _: self.delete_column_action(col_idx))
        # -----------------------------------------------------------

        cell_format_action.triggered.connect(self.insert_cell_format)
        row_format_action.triggered.connect(self.insert_row_format)
        column_format_action.triggered.connect(self.insert_column_format)

        adv_cell_action.triggered.connect(lambda: self.goto_or_create_format('cell'))
        adv_row_action.triggered.connect(lambda: self.goto_or_create_format('row'))
        adv_col_action.triggered.connect(lambda: self.goto_or_create_format('col'))

        merge_action.triggered.connect(self.merge_cells)
        unmerge_action.triggered.connect(self.unmerge_cells)
        
        reset_width_action.triggered.connect(self.reset_column_widths)
        apply_rel_width_action.triggered.connect(self.apply_relative_column_widths)

        hline_action.triggered.connect(lambda *args: self.insert_hline_format(include_z=False))
        hline_z_action.triggered.connect(lambda *args: self.insert_hline_format(include_z=True))
        vline_action.triggered.connect(lambda *args: self.insert_vline_format(include_z=False))
        vline_z_action.triggered.connect(lambda *args: self.insert_vline_format(include_z=True))
        
        z_hline_action.triggered.connect(lambda *args: self.insert_z_line_format(is_horizontal=True))
        z_vline_action.triggered.connect(lambda *args: self.insert_z_line_format(is_horizontal=False))

        find_action.triggered.connect(lambda: self.find_text())
        replace_action.triggered.connect(lambda: self.replace_all())

        # 7. 메인 메뉴 구성
        menu.addAction(copy_action)
        menu.addAction(cut_action)
        menu.addAction(paste_action)
        menu.addAction(delete_action)

        menu.addSeparator()  # --- 구분선 ---

        # --- [추가 4] "행/열 추가/삭제" 서브 메뉴 생성 및 부착 ---
        edit_rc_menu = menu.addMenu(tr("ctx.edit_rc_menu"))
        edit_rc_menu.addAction(insert_row_action)
        edit_rc_menu.addAction(delete_row_action)
        edit_rc_menu.addSeparator()
        edit_rc_menu.addAction(insert_col_action)
        edit_rc_menu.addAction(delete_col_action)
        
        menu.addSeparator()  # --- 구분선 ---
        # ----------------------------------------------------
        
        menu.addAction(find_action)      # 찾기 추가
        menu.addAction(replace_action)   # 바꾸기 추가

        menu.addSeparator()
        menu.addAction(merge_action)
        menu.addAction(unmerge_action)

        menu.addSeparator() 
        menu.addAction(cell_format_action)
        menu.addAction(row_format_action)
        menu.addAction(column_format_action)

        menu.addAction(adv_cell_action)
        menu.addAction(adv_row_action)
        menu.addAction(adv_col_action)

        menu.addSeparator() 

        menu.addAction(reset_width_action) 
        menu.addAction(apply_rel_width_action) 
        
        menu.addSeparator()
        line_format_menu = menu.addMenu(tr("ctx.line_format_menu"))
        
        line_format_menu.addAction(hline_action)
        line_format_menu.addAction(hline_z_action)
        line_format_menu.addAction(vline_action)
        line_format_menu.addAction(vline_z_action)
        
        line_format_menu.addSeparator() 
        line_format_menu.addAction(z_hline_action)
        line_format_menu.addAction(z_vline_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def copy_selection(self):
        selection = self.table.selectedIndexes()
        if not selection: return
        
        rows = sorted(index.row() for index in selection)
        cols = sorted(index.column() for index in selection)
        row_min, row_max = rows[0], rows[-1]
        col_min, col_max = cols[0], cols[-1]

        copy_text = ""
        for r in range(row_min, row_max + 1):
            row_data = []
            for c in range(col_min, col_max + 1):
                item = self.table.item(r, c)
                row_data.append(item.text() if item else "")
            copy_text += "\t".join(row_data) + "\n"
        QGuiApplication.clipboard().setText(copy_text.strip())

    def cut_selection(self):
        self.copy_selection()
        self.delete_selection()

    def paste_selection(self):
        clipboard_text = QGuiApplication.clipboard().text()
        if not clipboard_text: return

        current = self.table.currentIndex()
        start_row, start_col = current.row(), current.column()

        # --- 붙여넣을 TSV의 행/열 크기 계산 ---
        # Excel/Google Sheets에서 복사하면 끝에 개행이 하나 더 붙어 오는 경우가
        # 많아서(빈 마지막 행), 그로 인해 실제보다 1행 더 필요하다고 오판하지
        # 않도록 트레일링 빈 줄 하나만 제거한다.
        lines = clipboard_text.split('\n')
        if len(lines) > 1 and lines[-1] == "":
            lines.pop()

        pasted_rows = len(lines)
        pasted_cols = max((len(line.split('\t')) for line in lines), default=0)

        needed_rows = start_row + pasted_rows
        needed_cols = start_col + pasted_cols

        current_rows = self.table.rowCount()
        current_cols = self.table.columnCount()

        # --- 현재 표 크기를 벗어나면, 표를 늘릴지 사용자에게 확인 ---
        if needed_rows > current_rows or needed_cols > current_cols:
            reply = QMessageBox.question(
                self,
                tr("paste.resize_title"),
                tr("paste.resize_body",
                   rows=pasted_rows, cols=pasted_cols,
                   cur_rows=current_rows, cur_cols=current_cols),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                new_rows = max(needed_rows, current_rows)
                new_cols = max(needed_cols, current_cols)
                self.resize_table(new_rows, new_cols)
                self.spin_rows.setValue(new_rows)
                self.spin_cols.setValue(new_cols)
            # 'No'를 선택하면 기존처럼 현재 표 크기 안에서만 붙여넣는다.

        for i, row_text in enumerate(lines):
            for j, column_text in enumerate(row_text.split('\t')):
                r, c = start_row + i, start_col + j
                if r < self.table.rowCount() and c < self.table.columnCount():
                    self.table.setItem(r, c, QTableWidgetItem(column_text))

    def delete_selection(self):
        """선택된 셀들의 텍스트만 삭제"""
        for index in self.table.selectedIndexes():
            item = self.table.item(index.row(), index.column())
            if item:
                item.setText("")

    def import_latex_code(self, latex_text):        
        # =========================================================
        # [1] 도우미 함수 모음 (전처리 및 파싱용)
        # =========================================================
        def remove_comments(text):
            cleaned_lines = []
            for line in text.split('\n'):
                out_line = ""
                i = 0
                while i < len(line):
                    if line[i] == '%':
                        backslashes = 0
                        j = i - 1
                        while j >= 0 and line[j] == '\\':
                            backslashes += 1
                            j -= 1
                        if backslashes % 2 == 0:
                            break
                        else:
                            out_line += line[i]
                    else:
                        out_line += line[i]
                    i += 1
                cleaned_lines.append(out_line)
            return '\n'.join(cleaned_lines)

        def get_brace_content(text):
            """문자열이 '{'로 시작할 때 괄호 내부 문자열과 남은 문자열을 분리 반환"""
            text = text.strip()
            if not text.startswith('{'): 
                return "", text
            depth = 0
            for i, char in enumerate(text):
                if char == '{': depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        return text[1:i].strip(), text[i+1:].strip()
            return "", text

        def parse_multicolumn(cell_str):
            """\\multicolumn{n}{align}{content}를 파싱하여 (순수텍스트, colspan) 반환"""
            idx = cell_str.find(r"\multicolumn")
            if idx == -1: 
                return cell_str, 1

            prefix = cell_str[:idx]
            remains = cell_str[idx + len(r"\multicolumn"):].strip()

            span_str, remains = get_brace_content(remains)
            col_span = int(span_str) if span_str.isdigit() else 1

            _, remains = get_brace_content(remains) # align은 버림

            content_str, remains = get_brace_content(remains)

            clean_text = prefix + content_str + remains
            return clean_text.strip(), col_span

        def convert_tabularx_colspec(colspec):
            """tabularx의 p, m, b 열 형식을 tabularray의 Q 형식으로 변환"""
            colspec = re.sub(r'p\{([^}]+)\}', r'Q[\1]', colspec)
            colspec = re.sub(r'm\{([^}]+)\}', r'Q[m,\1]', colspec)
            colspec = re.sub(r'b\{([^}]+)\}', r'Q[b,\1]', colspec)
            return colspec

        def convert_alignment_commands(text):
            """셀 내부의 레거시 정렬 명령을 \\SetCell로 변환"""
            text = re.sub(r'\\arraybackslash(?:\{\})?\s*', '', text)
            text = re.sub(r'\\centering\s*', r'\\SetCell{c} ', text)
            text = re.sub(r'\\raggedright\s*', r'\\SetCell{l} ', text)
            text = re.sub(r'\\raggedleft\s*', r'\\SetCell{r} ', text)
            return text.strip()

        def split_options(opt_string):
            """중첩 괄호를 무시하고 쉼표(,) 기준으로 문자열을 안전하게 분리"""
            opts = []
            current = []
            depth = 0
            for char in opt_string:
                if char == '{': depth += 1; current.append(char)
                elif char == '}': depth -= 1; current.append(char)
                elif char == ',' and depth == 0:
                    opts.append(''.join(current).strip())
                    current = []
                else:
                    current.append(char)
            if current:
                opts.append(''.join(current).strip())
            return [o for o in opts if o]

        def parse_multirow(cell_str):
            """\\multirow{n}{...}{content} 또는 \\multirow{n}*{content} 파싱"""
            idx = cell_str.find(r"\multirow")
            if idx == -1:
                return cell_str, 1  # 기본 row span = 1

            prefix = cell_str[:idx]
            remains = cell_str[idx + len(r"\multirow"):].strip()

            # 첫 번째 인자: row span
            row_span_str, remains = get_brace_content(remains)
            row_span = int(row_span_str) if row_span_str.isdigit() else 1

            # 두 번째 인자: width 또는 * (무시 가능)
            if remains.startswith('*'):
                remains = remains[1:].strip()
            else:
                _, remains = get_brace_content(remains)  # width는 버림

            # 세 번째 인자: content
            content_str, remains = get_brace_content(remains)

            clean_text = prefix + content_str + remains
            return clean_text.strip(), row_span

        # =========================================================
        # [2] 초기 설정 및 환경 파싱
        # =========================================================
        latex_text = remove_comments(latex_text)

        self.spin_rows.blockSignals(True)
        self.spin_cols.blockSignals(True)
        self.radio_natural.setChecked(True)

        match = re.search(r"\\begin\{(tblr|longtblr|talltblr|tabularx)\}", latex_text)
        if not match:
            QMessageBox.warning(self, tr("parse.fail_title"), tr("parse.no_valid_env"))
            self.spin_rows.blockSignals(False)
            self.spin_cols.blockSignals(False)
            return

        env_type = match.group(1)
        text_after_begin = latex_text[match.end():].strip()

        category_lines = []
        category_rowcols = []
        category_cells = []
        category_generic = []
        category_inner_extra = []
        outer_options_str = ""
        colspec_extracted = ""
        body_str = ""
      
        # tabularx 환경 처리
        if env_type == "tabularx":
            width_str, text_after_begin = get_brace_content(text_after_begin)
            
            # [추가된 방어 로직 1] 너비와 colspec 사이에 [c], [t] 같은 위치 옵션이 있으면 건너뛰기
            text_after_begin = text_after_begin.strip()
            if text_after_begin.startswith('['):
                pos_end = text_after_begin.find(']')
                if pos_end != -1:
                    text_after_begin = text_after_begin[pos_end+1:].strip()
            
            # colspec 추출
            colspec_extracted, text_after_begin = get_brace_content(text_after_begin)
            
            # [추가된 방어 로직 2] 괄호 짝이 안 맞아서 추출에 실패한 경우 팝업으로 알림
            if not colspec_extracted:
                QMessageBox.warning(self, tr("parse.warn_title"), tr("parse.tabularx_colspec_warn"))
            
            # 추출 성공 시 변환 적용
            if width_str:
                category_generic.append(f"width={width_str}")
            if colspec_extracted:
                colspec_extracted = convert_tabularx_colspec(colspec_extracted)
            
            idx_end = text_after_begin.find(r"\end{tabularx}")
            if idx_end == -1:
                QMessageBox.warning(self, tr("parse.fail_title"), tr("parse.end_tabularx_not_found"))
                self.spin_rows.blockSignals(False); self.spin_cols.blockSignals(False); return
            body_str = text_after_begin[:idx_end].strip()

        # tblr, longtblr, talltblr 환경 처리
        else:
            if text_after_begin.startswith('['):
                depth = 0
                for i, char in enumerate(text_after_begin):
                    if char == '[': depth += 1
                    elif char == ']':
                        depth -= 1
                        if depth == 0:
                            outer_options_str = text_after_begin[1:i].strip()
                            text_after_begin = text_after_begin[i+1:].strip()
                            break

            if not text_after_begin.startswith('{'):
                QMessageBox.warning(self, tr("parse.fail_title"), tr("parse.env_open_brace_not_found", env_type=env_type))
                self.spin_rows.blockSignals(False); self.spin_cols.blockSignals(False); return

            depth = 0
            options_end_idx = -1
            for i, char in enumerate(text_after_begin):
                if char == '{': depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        options_end_idx = i
                        break

            if options_end_idx == -1:
                QMessageBox.warning(self, tr("parse.fail_title"), tr("parse.close_brace_not_found"))
                self.spin_rows.blockSignals(False); self.spin_cols.blockSignals(False); return

            inner_options_str = text_after_begin[1:options_end_idx].strip()
            body_start_idx = options_end_idx + 1
            idx_end = text_after_begin.find(f"\\end{{{env_type}}}", body_start_idx)
            
            if idx_end == -1:
                QMessageBox.warning(self, tr("parse.fail_title"), tr("parse.end_env_not_found", env_type=env_type))
                self.spin_rows.blockSignals(False); self.spin_cols.blockSignals(False); return
            body_str = text_after_begin[body_start_idx:idx_end].strip()

            parsed_inner_options = split_options(inner_options_str)
            for opt in parsed_inner_options:
                opt_clean = opt.strip().rstrip(',') 
                if not opt_clean: continue
                
                if opt_clean.replace(" ", "").startswith("colspec="):
                    colspec_extracted = opt_clean.split("=", 1)[1].strip()
                    # 외부 중괄호 제거
                    if colspec_extracted.startswith('{') and colspec_extracted.endswith('}'):
                        colspec_extracted = colspec_extracted[1:-1].strip()
                    continue
                
                if env_type in ['longtblr', 'talltblr'] and re.match(r"^(rowhead|rowfoot|firsthead|lastfoot|head|foot|theme)", opt_clean):
                    category_inner_extra.append(opt_clean)
                    continue
                if re.match(r"^[hv]lines?", opt_clean):
                    category_lines.append(opt_clean)
                    continue
                if re.match(r"^(row|column)s?", opt_clean):
                    category_rowcols.append(opt_clean)
                    continue
                if opt_clean.startswith("cell"):
                    if re.search(r"[rc]\s*=\s*\d+", opt_clean):
                        continue
                    category_cells.append(opt_clean)
                    continue
                category_generic.append(opt_clean)

        # =========================================================
        # [3] 파싱된 옵션을 UI에 반영
        # =========================================================
        self.env_combobox.setCurrentText(env_type if env_type != "tabularx" else "tblr")

        if outer_options_str:
            parsed_outer = split_options(outer_options_str)
            self.outer_options_input.setPlainText("\n".join(parsed_outer))
        elif env_type in ['longtblr', 'talltblr']:
            self.outer_options_input.clear()

        if category_inner_extra:
            self.inner_extra_input.setPlainText("\n".join(category_inner_extra))
        elif env_type in ['longtblr', 'talltblr']:
            self.inner_extra_input.clear()

        if colspec_extracted:
            self.input_colspec.setText(colspec_extracted)
        else:
            self.input_colspec.clear()
            
        self.input_lines.setPlainText(",\n".join(category_lines))
        self.input_row_format.setPlainText(",\n".join(category_rowcols))
        self.input_cell_format.setPlainText(",\n".join(category_cells))
        self.input_general_settings.setPlainText(",\n".join(category_generic))

        # =========================================================
        # [4] 본문 파싱 및 테이블 구성 (Dummy 셀 처리 포함)
        # =========================================================
        # ---------------------------------------------------------
        # [추가된 청소 로직] 본문(body_str)에서 레거시 괘선 명령 완벽 제거
        # ---------------------------------------------------------
        # 1. \hline 제거
        body_str = re.sub(r'\\hline\s*', '', body_str)
        
        # 2. \cline{...} 제거 (괄호 안의 내용까지 한 번에 날림)
        body_str = re.sub(r'\\cline\{[^}]+\}\s*', '', body_str)
        
        # 3. booktabs 패키지 괘선 (\toprule, \midrule, \bottomrule) 제거
        body_str = re.sub(r'\\(?:top|mid|bottom)rule\s*', '', body_str)
        # ---------------------------------------------------------

        table_data = []
        current_row = []
        current_cell = []
        brace_depth = 0
        i = 0

        def append_cell_to_row(cell_chars):
            raw_text = "".join(cell_chars).strip()
            if not raw_text:
                current_row.append({"text": "", "span": 1})
                return
            
            # \multicolumn 추출 및 텍스트 정리
            clean_text, col_span = parse_multicolumn(raw_text)

            # \multirow 처리
            clean_text, row_span = parse_multirow(clean_text)

            clean_text = convert_alignment_commands(clean_text)
            
            # current_row.append({"text": clean_text, "span": col_span})
            # # 병합될 공간만큼 더미(Dummy) 데이터 삽입
            # for _ in range(col_span - 1):
            #     current_row.append({"text": "__DUMMY__", "span": 0})

            current_row.append({"text": clean_text, "col_span": col_span, "row_span": row_span})

            # col_span 더미 삽입
            for _ in range(col_span - 1):
                current_row.append({"text": "__DUMMY__", "col_span": 0, "row_span": 0})

        while i < len(body_str):
            if body_str[i:i+2] == '\\\\':
                if brace_depth == 0:
                    append_cell_to_row(current_cell)
                    table_data.append(current_row)
                    current_row = []
                    current_cell = []
                    i += 2
                    continue
                else:
                    current_cell.append('\\\\')
                    i += 2
                    continue

            # if body_str[i] == '&' and brace_depth == 0:
            #     append_cell_to_row(current_cell)
            #     current_cell = []
            #     i += 1
            #     continue
            if body_str[i] == '&' and brace_depth == 0:
                # 바로 앞 문자가 '\'이면 텍스트로 취급
                if i > 0 and body_str[i-1] == '\\':
                    current_cell.append('&')
                    i += 1
                    continue
                # 그렇지 않으면 셀 구분자로 처리
                append_cell_to_row(current_cell)
                current_cell = []
                i += 1
                continue

            if body_str[i] == '{': brace_depth += 1
            elif body_str[i] == '}': brace_depth -= 1

            current_cell.append(body_str[i])
            i += 1

        if current_cell or current_row:
            append_cell_to_row(current_cell)
            if current_row:
                table_data.append(current_row)

        # --- 여기서 마지막 행이 앰퍼샌드만 남은 경우 제거 ---
        if table_data:
            last_row = table_data[-1]
            # 모든 셀이 빈 문자열인지 확인
            if all(cell["text"] == "__DUMMY__" or cell["text"].strip() == "" for cell in last_row):
                table_data.pop()

        row_count = len(table_data)
        col_count = max([len(row) for row in table_data]) if table_data else 0

        self.spin_rows.setValue(row_count)
        self.spin_cols.setValue(col_count)
        self.resize_table(row_count, col_count)

        # =========================================================
        # [5] QTableWidget에 데이터 채우기 및 병합(Span) 복원
        # =========================================================
        for r_idx, row_data in enumerate(table_data):
            for c_idx, cell_info in enumerate(row_data):
                if cell_info["text"] == "__DUMMY__":
                    continue  # 더미 셀은 스킵

                # 셀 텍스트 채우기
                self.table.setItem(r_idx, c_idx, QTableWidgetItem(cell_info["text"]))

                # 병합 처리: row_span과 col_span 모두 반영
                row_span = cell_info.get("row_span", 1)
                col_span = cell_info.get("col_span", 1)

                if row_span > 1 or col_span > 1:
                    self.table.setSpan(r_idx, c_idx, row_span, col_span)

        self.spin_rows.blockSignals(False)
        self.spin_cols.blockSignals(False)
        
        # 마지막으로 LaTeX 코드 재생성
        self.generate_latex_with_colspec("")


    # ==========================================================
    # 💡 바로 여기! __init__ 함수가 끝난 다음 줄에 동일한 들여쓰기로 위치해야 합니다.
    # ==========================================================
    def update_tab_state(self, env_text):
        if env_text == "tblr":
            self.settings_tabs.setTabEnabled(1, False)
            self.outer_options_input.clear()
            self.inner_extra_input.clear()
            
        elif env_text == "longtblr":
            self.settings_tabs.setTabEnabled(1, True)
            # 콤마 제거, 줄바꿈만 유지
            self.outer_options_input.setPlainText("caption={}\nlabel={}")
            self.inner_extra_label.setVisible(True)
            self.inner_extra_input.setVisible(True)
            self.inner_extra_input.setPlainText("rowhead = 1")
            
        elif env_text == "talltblr":
            self.settings_tabs.setTabEnabled(1, True)
            # 콤마 제거, 줄바꿈만 유지
            self.outer_options_input.setPlainText("caption={}\nlabel={}\nnote{}={}")
            self.inner_extra_label.setVisible(False)
            self.inner_extra_input.setVisible(False)
            self.inner_extra_input.clear()

    def quit_and_copy(self):
        """(4) 앱 종료 전 _tblr_prv.* 임시 파일들을 모두 삭제"""
        # 미리보기를 한 번이라도 실행해서 폴더 경로가 기록되어 있다면
        if hasattr(self, 'last_preview_dir') and self.last_preview_dir:
            # 해당 폴더 내의 _tblr_prv.* 파일들을 찾음
            pattern = os.path.join(self.last_preview_dir, "_tblr_prv.*")
            temp_files = glob.glob(pattern)
            
            for file_path in temp_files:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting temp file {file_path}: {e}")
                    
        # 최종적으로 창 닫기
        self.close()

    def move_focus_to_cell_editor(self):
        """Ctrl+E 입력 시 하단 셀 에디터로 포커스를 이동하고 입력 중이던 텍스트를 보존합니다."""
        current_item = self.table.currentItem()
        if not current_item:
            return

        # 1. 포커스를 셀 에디터로 이동 (이 순간 테이블 셀에서 편집 중이던 텍스트가 확정/저장됨)
        self.cell_editor.setFocus()

        # 2. 확정된 최신 텍스트를 가져옴
        text = current_item.text()

        # 3. 셀 에디터의 텍스트가 최신 상태가 아니라면 갱신 (무한 루프 방지를 위해 시그널 블록)
        if self.cell_editor.toPlainText() != text:
            self.cell_editor.blockSignals(True)
            self.cell_editor.setPlainText(text)
            self.cell_editor.blockSignals(False)

        # 4. 사용자가 바로 이어서 타이핑할 수 있도록 커서를 텍스트 맨 끝으로 이동
        cursor = self.cell_editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.cell_editor.setTextCursor(cursor)

    def reset_colspec_validation(self):
        """라디오 버튼 전환 등 설정이 변경될 때 검사 무시 상태를 초기화합니다."""
        self.ignore_colspec_validation = False

    def closeEvent(self, event):
        """앱이 종료될 때 호출되는 이벤트"""
        try:
            # 종료 직전 마지막으로 LaTeX 생성 및 복사 함수 호출
            # self.generate_latex()      # 최신 데이터를 반영하기 위해 한 번 더 호출
            # self.copy_to_clipboard()   # 클립보드로 복사
            self.statusbar.showMessage(tr("status.app_quitting"), 3000)
        except Exception as e:
            print(f"종료 실패: {e}")

        # 실제 앱 종료 허가
        event.accept()

    def export_csv(self):
        # 1. 파일 저장 다이얼로그 열기 (last_csv_dir 같은 변수가 있다면 활용하세요)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV File",
            "",  # 기본 경로가 필요하다면 여기에 입력
            "CSV Files (*.csv);;All Files (*)"
        )

        # 사용자가 취소를 누른 경우 그대로 종료
        if not file_path:
            return

        # 2. 파일 저장 로직
        try:
            # newline='' 옵션은 윈도우에서 줄바꿈이 두 번 들어가는 것을 방지합니다.
            # encoding='utf-8-sig'는 엑셀에서 한글 깨짐을 방지해주는 BOM(Byte Order Mark)을 추가합니다.
            with open(file_path, 'w', encoding='utf-8-sig', newline='') as file:
                writer = csv.writer(file)
                
                for r in range(self.table.rowCount()):
                    row_content = []
                    for c in range(self.table.columnCount()):
                        item = self.table.item(r, c)
                        text = item.text() if item else ""
                        row_content.append(text)
                    
                    # csv 모듈이 쉼표, 따옴표, 줄바꿈 처리를 자동으로 해줍니다.
                    writer.writerow(row_content)
                    
            print(f"CSV 파일이 성공적으로 저장되었습니다: {file_path}")

        except Exception as e:
            print(f"파일 저장 중 오류가 발생했습니다: {e}")

    def export_tex(self):
        """테이블 코드만 .tex 파일로 저장 (Ctrl+T)"""
        table_code = self.output_text.toPlainText()
        
        # 출력창이 비어있으면 저장하지 않음
        if not table_code.strip():
            return

        # 1. 마지막으로 TeX을 export했던 폴더 경로 불러오기
        last_tex_dir = self.settings.value("last_tex_dir", "")

        # 2. 파일 저장 다이얼로그 열기 (기본 경로로 last_tex_dir 사용)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export TeX File",
            last_tex_dir,  # 여기에 불러온 경로를 넣어줍니다.
            "TeX Files (*.tex);;All Files (*)"
        )

        # 3. 사용자가 다이얼로그에서 취소하지 않고 경로를 선택했다면
        if file_path:
            # 선택한 파일의 '폴더 경로'만 추출해서 다음을 위해 저장
            current_dir = os.path.dirname(file_path)
            self.settings.setValue("last_tex_dir", current_dir)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(table_code)

    def prompt_custom_class_and_export(self):
        """사용자에게 직접 documentclass 이름을 입력받아 export 진행"""
        class_name, ok = QInputDialog.getText(
            self, 
            tr("export.docclass_title"), 
            tr("export.docclass_label"), 
            text="report" # 빈칸 대신 보여줄 기본값
        )
        
        # 사용자가 '확인'을 눌렀고, 입력값이 비어있지 않은 경우에만 실행
        if ok and class_name.strip():
            self.export_tex_with_class(class_name.strip())

    def export_tex_with_class(self, doc_class):
        """지정된 클래스로 컴파일 가능한 독립적인 .tex 파일로 저장"""
        table_code = self.output_text.toPlainText()
        
        if not table_code.strip():
            return
            
        # f-string 안에서 {doc_class} 변수 삽입
        standalone_code = f"""\\documentclass{{{doc_class}}}
\\usepackage{{xcolor}}
\\usepackage{{ninecolors}}
\\usepackage{{tabularray}}
\\IfFileExists{{mytblrpreamble.tex}}{{\\input{{mytblrpreamble.tex}}}}{{}}
\\begin{{document}}

{table_code}

\\end{{document}}"""

        # 1. 마지막으로 TeX을 export했던 폴더 경로 불러오기
        last_tex_dir = self.settings.value("last_tex_dir", "")

        # 2. 파일 저장 다이얼로그 열기 (타이틀에 클래스 이름도 표시해주면 더 좋습니다)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export TeX File ({doc_class})",
            last_tex_dir,
            "TeX Files (*.tex);;All Files (*)"
        )

        # 3. 사용자가 다이얼로그에서 취소하지 않고 경로를 선택했다면
        if file_path:
            current_dir = os.path.dirname(file_path)
            self.settings.setValue("last_tex_dir", current_dir)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(standalone_code)

    def _resolve_preview_target_dir(self):
        """
        미리보기(.tex 저장 및 컴파일)에 사용할 대상 폴더를 결정합니다.
        1) 이미 저장된 파일이 있으면 그 폴더 사용
        2) 없으면 이전에 지정해둔 preview_dir 사용, 없으면 한 번만 물어봄
        취소하면 None을 반환합니다.
        """
        if hasattr(self, 'current_file') and self.current_file:
            return os.path.dirname(self.current_file)

        if not hasattr(self, 'preview_dir') or not self.preview_dir:
            last_dir = self.settings.value("last_tblr_dir", "")
            selected_dir = QFileDialog.getExistingDirectory(
                self,
                "Select Directory for Preview",
                last_dir
            )
            if not selected_dir:
                return None
            self.preview_dir = selected_dir

        return self.preview_dir

    def _build_preview_standalone_code(self):
        """미리보기용 standalone LaTeX 소스 생성 (kotex 포함, article 클래스)"""
        table_code = self.output_text.toPlainText()
        return f"""\\documentclass{{article}}
\\usepackage{{kotex}}
\\usepackage{{xcolor}}
\\usepackage{{ninecolors}}
\\usepackage{{tabularray}}
\\IfFileExists{{mytblrpreamble.tex}}{{\\input{{mytblrpreamble.tex}}}}{{}}
\\begin{{document}}

{table_code}

\\end{{document}}"""

    def export_preview_tex(self):
        """(1), (2) 미리보기를 위해 kotex이 포함된 _tblr_prv.tex 파일을 생성"""
        table_code = self.output_text.toPlainText()
        
        if not table_code.strip():
            return

        target_dir = self._resolve_preview_target_dir()
        if not target_dir:
            return  # 사용자가 폴더 선택을 취소함

        standalone_code = self._build_preview_standalone_code()

        # --- [파일 저장] ---
        file_path = os.path.join(target_dir, "_tblr_prv.tex")
        
        # 나중에 앱 종료 시 삭제하기 위해 마지막으로 미리보기를 생성한 폴더를 기록
        self.last_preview_dir = target_dir

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(standalone_code)
        self.statusbar.showMessage(tr("status.preview_saved"), 3000)

    # ==========================================================
    # [추가] PDF 미리보기 컴파일: _tblr_prv.tex을 실제로 컴파일해서
    # 성공하면 시스템 기본 PDF 뷰어로 열고, 실패해도 앱은 죽지 않고
    # 로그에서 에러 요약만 뽑아 보여줍니다. (자세한 진단은 .log 파일로)
    # ==========================================================
    def compile_preview_pdf(self):
        table_code = self.output_text.toPlainText()
        if not table_code.strip():
            self.statusbar.showMessage(tr("status.empty_no_preview"), 3000)
            return

        # 이미 컴파일이 진행 중이면 중복 실행 방지
        if self.preview_process is not None and self.preview_process.state() != QProcess.NotRunning:
            self.statusbar.showMessage(tr("status.preview_in_progress"), 3000)
            return

        engine = self.preview_engine_combo.currentText()

        # --- [추가] macOS PyInstaller 앱 번들 PATH 문제 해결 ---
        if sys.platform == "darwin":
            mac_paths = ["/Library/TeX/texbin", "/opt/homebrew/bin", "/usr/local/bin"]
            current_path = os.environ.get("PATH", "")
            path_list = current_path.split(os.pathsep)
            
            # 우선순위를 유지하며 맨 앞에 추가하기 위해 reversed 사용
            for p in reversed(mac_paths):
                if p not in path_list:
                    path_list.insert(0, p)
            
            # 갱신된 PATH를 현재 프로세스 환경에 적용 (shutil.which가 인식하도록 함)
            os.environ["PATH"] = os.pathsep.join(path_list)
        # --------------------------------------------------------

        # 엔진이 실제로 설치되어 있는지 사전 확인 (조용히 폴백)
        if shutil.which(engine) is None:
            QMessageBox.warning(
                self,
                tr("preview.engine_not_found_title"),
                tr("preview.engine_not_found_body", engine=engine)
            )
            return

        target_dir = self._resolve_preview_target_dir()
        if not target_dir:
            return

        standalone_code = self._build_preview_standalone_code()
        tex_path = os.path.join(target_dir, "_tblr_prv.tex")
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(standalone_code)

        self.last_preview_dir = target_dir
        self._preview_target_dir = target_dir

        # --- [비동기 컴파일 실행] ---
        self.btn_compile_preview.setEnabled(False)
        self.statusbar.showMessage(tr("status.compiling_with", engine=engine))

        self.preview_process = QProcess(self)
        
        # --- [추가] QProcess가 갱신된 PATH를 사용하도록 환경변수 명시적 설정 ---
        if sys.platform == "darwin":
            # 주의: 상단에 QProcessEnvironment가 임포트되어 있어야 합니다.
            env = QProcessEnvironment.systemEnvironment()
            env.insert("PATH", os.environ["PATH"])
            self.preview_process.setProcessEnvironment(env)
        # ------------------------------------------------------------------------
        
        self.preview_process.setWorkingDirectory(target_dir)
        self.preview_process.setProgram(engine)
        self.preview_process.setArguments([
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            "_tblr_prv.tex",
        ])
        self.preview_process.finished.connect(self._on_preview_compile_finished)
        self.preview_process.errorOccurred.connect(self._on_preview_compile_error)
        self.preview_process.start()

    def _on_preview_compile_error(self, error):
        """QProcess 자체를 실행하지 못한 경우(예: 실행 권한 문제 등)"""
        self.btn_compile_preview.setEnabled(True)
        self.statusbar.showMessage(tr("status.preview_launch_failed"), 4000)

    def _on_preview_compile_finished(self, exit_code, exit_status):
        self.btn_compile_preview.setEnabled(True)
        target_dir = self._preview_target_dir
        if not target_dir:
            return

        pdf_path = os.path.join(target_dir, "_tblr_prv.pdf")
        log_path = os.path.join(target_dir, "_tblr_prv.log")

        if exit_code == 0 and os.path.exists(pdf_path):
            self.statusbar.showMessage(tr("status.preview_done"), 4000)
            QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
            return

        # --- [실패 처리] : 앱을 죽이지 않고, 로그에서 에러 요약만 추출 ---
        error_summary = self._extract_log_errors(log_path)
        self.statusbar.showMessage(tr("status.preview_failed"), 4000)

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(tr("preview.compile_fail_title"))
        msg_box.setText(tr("preview.compile_fail_body"))
        if error_summary:
            msg_box.setDetailedText(error_summary)
        msg_box.setInformativeText(
            tr("preview.compile_fail_detail", target_dir=target_dir)
        )
        open_folder_btn = msg_box.addButton(tr("preview.open_folder_btn"), QMessageBox.ActionRole)
        msg_box.addButton(QMessageBox.Ok)
        msg_box.exec()

        if msg_box.clickedButton() == open_folder_btn:
            QDesktopServices.openUrl(QUrl.fromLocalFile(target_dir))

    def _extract_log_errors(self, log_path):
        """
        .log 파일에서 '!' 로 시작하는 에러 라인들과 그 다음 몇 줄(주로 위치 정보)만 뽑아
        간단한 요약 문자열로 반환합니다. 로그가 없거나 못 읽으면 빈 문자열 반환.
        """
        if not os.path.exists(log_path):
            return ""
        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception:
            return ""

        summary_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("!"):
                # 에러 라인 + 바로 다음 2줄 정도(보통 "l.123 ..." 위치 정보 포함) 같이 수집
                summary_lines.append(line.rstrip())
                for j in range(1, 3):
                    if i + j < len(lines):
                        nxt = lines[i + j].rstrip()
                        if nxt:
                            summary_lines.append(nxt)
                summary_lines.append("")  # 에러 블록 사이 구분
            i += 1

        if not summary_lines:
            # "!" 패턴을 못 찾았으면 로그 마지막 부분이라도 보여줌 (최대 30줄)
            summary_lines = [l.rstrip() for l in lines[-30:]]

        return "\n".join(summary_lines)

    def open_latex_import_dialog(self):
        """LaTeX 코드를 들여오는 다이얼로그를 열고 처리하는 메서드"""
        print("디버그: LaTeX 들여오기 실행됨") # 작동 확인용
        
        # 사용자의 다이얼로그 클래스 생성 (self는 메인윈도우)
        dialog = LatexImportDialog(self)
        
        if dialog.exec() == QDialog.Accepted:
            latex_code = dialog.get_text()
            
            if latex_code and latex_code.strip():
                # 1. 메인 윈도우의 기능을 실행
                self.new_task()
                
                # 2. 파싱 함수 실행
                self.import_latex_code(latex_code)

    ### Template
    def get_current_state_dict(self):
        """현재 프로그램의 모든 입력 상태를 딕셔너리로 덤프 (템플릿 저장용)"""
        rows = self.spin_rows.value()
        cols = self.spin_cols.value()

        # [보완 1] 각 셀의 텍스트뿐만 아니라 행/열 병합(Span) 정보까지 함께 수집
        cells = []
        for r in range(rows):
            row_data = []
            for c in range(cols):
                item = self.table.item(r, c)
                row_data.append({
                    "text": item.text() if item else "",
                    "row_span": self.table.rowSpan(r, c),
                    "col_span": self.table.columnSpan(r, c),
                })
            cells.append(row_data)

        # 라디오 버튼 상태 수집
        if hasattr(self, 'radio_linewidth') and self.radio_linewidth.isChecked():
            radio_state = "linewidth"
        elif hasattr(self, 'radio_natural') and self.radio_natural.isChecked():
            radio_state = "natural"
        else:
            radio_state = "manual"

        # [통일 및 보완 3] save_table과 동일한 구조 및 키 이름으로 반환
        return {
            "env_type": self.env_combobox.currentText(),  # [추가] 환경 타입(tblr, longtblr 등)
            "outer_options": self.outer_options_input.toPlainText(),
            "inner_extra": self.inner_extra_input.toPlainText(),
            "lines": self.input_lines.toPlainText(),
            "rows": rows,
            "cols": cols,
            "row_format": self.input_row_format.toPlainText(),
            "cell_format": self.input_cell_format.toPlainText(),
            "generic_option": self.input_general_settings.toPlainText(),  # [명칭 변경] general_settings -> generic_option
            "colspec": self.input_colspec.text(),                         # [명칭 변경] manual_colspec -> colspec
            "cells": cells,                                               # [보완] 병합 정보가 포함된 셀 데이터
            "radio_state": radio_state,
            "bottomrule_checked": self.bottomrule_checkbox.isChecked(),
            "extra_cmd_text": self.extra_cmd_input.text()                 # [명칭 변경] extra_cmd -> extra_cmd_text
        }

    def load_template_pure_data(self, file_path):
        """
        F9 템플릿 전용 로더:
        현재 편집 중인 파일 경로(self.current_file) 및 타이틀바를 절대 변경하지 않고,
        테이블의 서식, 데이터, 셀 병합 및 배경색만 안전하게 가져옵니다.
        """
        if not file_path or not os.path.exists(file_path):
            return
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 1. 파일 세팅 중 불필요한 경고 메시지가 뜨는 것을 방지하기 위해 먼저 natural로 설정
            if hasattr(self, 'radio_natural') and self.radio_natural:
                self.radio_natural.setChecked(True)

            rows = data.get("rows", 0)
            cols = data.get("cols", 0)
            
            # SpinBox 컴포넌트 세팅 및 테이블 리사이즈 (원본 로직 준수)
            if hasattr(self, 'spin_rows') and self.spin_rows:
                self.spin_rows.setValue(rows)
            if hasattr(self, 'spin_cols') and self.spin_cols:
                self.spin_cols.setValue(cols)
                
            if hasattr(self, 'resize_table'):
                self.table.clearSpans() # 기존에 얽혀있던 모든 셀 병합 구조를 깨끗이 초기화
                self.resize_table(rows, cols)
            else:
                self.table.setRowCount(rows)
                self.table.setColumnCount(cols)

            # 2. 열 너비(column_widths) 복원
            column_widths = data.get("column_widths", [])
            if column_widths and hasattr(self.table, 'horizontalHeader'):
                header = self.table.horizontalHeader()
                header.blockSignals(True)
                for c, w in enumerate(column_widths):
                    if c < cols:
                        self.table.setColumnWidth(c, w)
                header.blockSignals(False)

            # 3. 각종 텍스트 에디터 서식 데이터 주입 (json 키 명칭 원본 싱크 완벽 매칭)
            if hasattr(self, 'input_lines'):
                self.input_lines.setPlainText(data.get("lines", ""))
            
            cell_format_text = data.get("cell_format", "")
            if hasattr(self, 'input_row_format'):
                self.input_row_format.setPlainText(data.get("row_format", ""))
            if hasattr(self, 'input_cell_format'):
                self.input_cell_format.setPlainText(cell_format_text)
                
            # 📌 주의: 변수명 및 json 키 싱크 맞춤
            if hasattr(self, 'input_general_settings'):
                self.input_general_settings.setPlainText(data.get("generic_option", ""))
            if hasattr(self, 'input_colspec'):
                self.input_colspec.setText(data.get("colspec", ""))
            if hasattr(self, 'output_text'):
                self.output_text.setPlainText(data.get("latex_code", ""))

            # 4. 환경 설정 및 Long/Tall 탭 옵션 복구
            env_type = data.get("env_type", "tblr")
            if hasattr(self, 'env_combobox'):
                self.env_combobox.setCurrentText(env_type) 
                
            if hasattr(self, 'outer_options_input'):
                self.outer_options_input.setPlainText(data.get("outer_options", ""))
            if hasattr(self, 'inner_extra_input'):
                self.inner_extra_input.setPlainText(data.get("inner_extra", ""))

            # 5. 원래 저장되어 있던 라디오 버튼 상태로 복구
            radio_state = data.get("radio_state", "manual")
            if radio_state == "linewidth" and hasattr(self, 'radio_linewidth'):
                self.radio_linewidth.setChecked(True)
            elif radio_state == "natural" and hasattr(self, 'radio_natural'):
                self.radio_natural.setChecked(True)
            elif hasattr(self, 'radio_manual'):
                self.radio_manual.setChecked(True)

            # 6. 체크박스 및 추가 명령어 텍스트 상태 복원
            if hasattr(self, 'bottomrule_checkbox'):
                self.bottomrule_checkbox.setChecked(data.get("bottomrule_checked", False))
            if hasattr(self, 'extra_cmd_input'):
                self.extra_cmd_input.setText(data.get("extra_cmd_text", ""))

            # 7. 📌 셀 데이터 및 병합 상태 복원 (이 부분이 완전히 수정되었습니다)
            cells = data.get("cells", [])
            for r in range(len(cells)):
                for c in range(len(cells[r])):
                    if r < self.table.rowCount() and c < self.table.columnCount():
                        cell_info = cells[r][c]
                        text = cell_info.get("text", "")
                        
                        # QTableWidgetItem 객체 생성 후 테이블에 삽입
                        item = QTableWidgetItem(text)
                        self.table.setItem(r, c, item)
                        
                        row_span = cell_info.get("row_span", 1)
                        col_span = cell_info.get("col_span", 1)
                        
                        if row_span > 1 or col_span > 1:
                            self.table.setSpan(r, c, row_span, col_span)

            # 8. 🎨 배경색 복원 로직 적용
            if cell_format_text:
                pattern = r"cell\{(\d+)\}\{(\d+)\}\s*=\s*\{[^}]*bg=([^,}]+)[^}]*\}"
                for match in re.finditer(pattern, cell_format_text):
                    r_idx = int(match.group(1)) - 1
                    c_idx = int(match.group(2)) - 1
                    color_str = match.group(3).strip()
                    
                    if "!" in color_str:
                        base_color_str, percent_str = color_str.split("!")
                        try:
                            percent = int(percent_str) / 100.0
                        except ValueError:
                            percent = 1.0
                        
                        base_color = QColor(base_color_str)
                        if base_color.isValid():
                            r_col = int(base_color.red() * percent + 255 * (1 - percent))
                            g_col = int(base_color.green() * percent + 255 * (1 - percent))
                            b_col = int(base_color.blue() * percent + 255 * (1 - percent))
                            qcolor = QColor(r_col, g_col, b_col)
                        else:
                            qcolor = QColor("white")
                    else:
                        qcolor = QColor(color_str)
                    
                    if 0 <= r_idx < self.table.rowCount() and 0 <= c_idx < self.table.columnCount():
                        item = self.table.item(r_idx, c_idx)
                        if item and qcolor.isValid():
                            item.setBackground(qcolor)

            # 9. 화면 헤더 및 상태바 리프레시 알림
            if hasattr(self, '_refresh_headers'):
                self._refresh_headers()
            if hasattr(self, 'generate_latex'):
                self.generate_latex()

            if hasattr(self, 'statusbar') and self.statusbar:
                self.statusbar.showMessage(tr("status.template_applied"), 3000)

        except Exception as e:
            # 혹시나 파싱 중 에러가 있다면 디버깅을 위해 주석을 해제하여 확인 가능합니다.
            # print(f"템플릿 로드 실패 원인: {str(e)}")
            pass

    def open_template_manager(self):
        """F9 단축키: 템플릿 관리자 열기"""
        dialog = TemplateDialog(self.template_dir, self.get_current_state_dict, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_file_path:
            self.load_template_pure_data(dialog.selected_file_path)
