from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtCore import Qt

class TableBorderDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hline_data = {}
        self.vline_data = {}

    def set_border_data(self, hlines, vlines):
        self.hline_data = hlines
        self.vline_data = vlines
        if self.parent():
            self.parent().viewport().update()

    def paint(self, painter, option, index):
        # 1. 기본 배경 및 텍스트 렌더링
        super().paint(painter, option, index)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        rect = option.rect
        table = self.parent()
        
        # 실제 행/열 인덱스 (1-based)
        row = index.row() + 1
        col = index.column() + 1
        
        # [중요] 병합 정보 가져오기
        row_span = table.rowSpan(index.row(), index.column()) if table else 1
        col_span = table.columnSpan(index.row(), index.column()) if table else 1
        
        # 병합된 영역의 마지막 행/열 번호 계산
        last_row_in_span = row + row_span - 1
        last_col_in_span = col + col_span - 1

        total_rows = table.rowCount() if table else index.model().rowCount()
        total_cols = table.columnCount() if table else index.model().columnCount()

        # --- 기본 그리드 (연한 회색) ---
        default_grid_pen = QPen(QColor("#DCDCDC"), 1, Qt.PenStyle.SolidLine)
        default_grid_pen.setCosmetic(True)
        painter.setPen(default_grid_pen)
        
        # 병합된 rect 기준으로 오른쪽과 아래쪽 기본선 그리기
        painter.drawLine(rect.right(), rect.top(), rect.right(), rect.bottom())
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        # --- 커스텀 HLine (위쪽 테두리) ---
        # 병합된 셀의 가장 윗줄(row) 기준
        if row in self.hline_data:
            col_data = self.hline_data[row]
            if "-" in col_data or col in col_data:
                pen = col_data.get("-" if "-" in col_data else col)
                if pen:
                    w = max(1, round(pen.widthF()))
                    pen.setWidth(w)
                    painter.setPen(pen)
                    painter.drawLine(rect.left(), rect.top(), rect.right(), rect.top())

        # --- 커스텀 HLine (병합된 셀의 맨 아래쪽 테두리) ---
        # 핵심: row + 1이 아니라 last_row_in_span + 1을 체크
        target_bottom_idx = last_row_in_span + 1
        if target_bottom_idx in self.hline_data:
            col_data = self.hline_data[target_bottom_idx]
            if "-" in col_data or col in col_data:
                pen = col_data.get("-" if "-" in col_data else col)
                if pen:
                    w = max(1, round(pen.widthF()))
                    pen.setWidth(w)
                    painter.setPen(pen)
                    # 실제 rect.bottom() 위치에 그림
                    y = rect.bottom() if last_row_in_span < total_rows else rect.bottom() - (w - 1)
                    painter.drawLine(rect.left(), y, rect.right(), y)

        # --- 커스텀 VLine (왼쪽 테두리) ---
        if col in self.vline_data:
            row_data = self.vline_data[col]
            if "-" in row_data or row in row_data:
                pen = row_data.get("-" if "-" in row_data else row)
                if pen:
                    w = max(1, round(pen.widthF()))
                    pen.setWidth(w)
                    painter.setPen(pen)
                    painter.drawLine(rect.left(), rect.top(), rect.left(), rect.bottom())

        # --- 커스텀 VLine (병합된 셀의 맨 오른쪽 테두리) ---
        # 핵심: col + 1이 아니라 last_col_in_span + 1을 체크
        target_right_idx = last_col_in_span + 1
        if target_right_idx in self.vline_data:
            row_data = self.vline_data[target_right_idx]
            if "-" in row_data or row in row_data:
                pen = row_data.get("-" if "-" in row_data else row)
                if pen:
                    w = max(1, round(pen.widthF()))
                    pen.setWidth(w)
                    painter.setPen(pen)
                    x = rect.right() if last_col_in_span < total_cols else rect.right() - (w - 1)
                    painter.drawLine(x, rect.top(), x, rect.bottom())

        # --- 뱃지 (파란 점) ---
        if index.data(Qt.ItemDataRole.UserRole + 1):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#4285F4"))
            radius = 3
            margin = 5
            painter.drawEllipse(rect.right() - (radius * 2) - margin, rect.top() + margin, radius * 2, radius * 2)

        painter.restore()
        