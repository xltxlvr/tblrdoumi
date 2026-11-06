
import re
from PySide6.QtWidgets import (QApplication, 
                               QPushButton,
                               QMenu, QDialog, QGridLayout)
from PySide6.QtCore import Signal

from tblrDoumi.i18n import tr

class ColorButton(QPushButton):
    def __init__(self, name, rgb, cmyk, parent=None):
        super().__init__(name, parent)
        self.name = name
        self.rgb = rgb
        self.cmyk = cmyk

        try:
            level = int("".join(filter(str.isdigit, name)))
        except ValueError:
            level = 5

        # 색상 이름만 추출 (숫자 제거)
        base_name = re.sub(r"\d+", "", name).lower()

        if level <= 5:
            if base_name == "white":
                text_color = "black"
            else:
                text_color = "white"
        else:
            text_color = "black"

        self.setStyleSheet(
            f"background-color: rgb({rgb[0]},{rgb[1]},{rgb[2]}); "
            f"color: {text_color}; border-radius: 4px; "
            f"text-align: left; padding-left: 6px;"
        )

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        name_action = menu.addAction(tr("colorpalette.copy_name"))
        rgb_action = menu.addAction(tr("colorpalette.copy_rgb"))
        cmyk_action = menu.addAction(tr("colorpalette.copy_cmyk"))

        action = menu.exec(event.globalPos())
        if action == name_action:
            QApplication.clipboard().setText(self.name)
            self.window().status_bar.showMessage(f"{self.name}", 2000)
        elif action == rgb_action:
            QApplication.clipboard().setText(str(self.rgb))
            self.window().status_bar.showMessage(f"{self.name} RGB {self.rgb}", 2000)
        elif action == cmyk_action:
            QApplication.clipboard().setText(str(self.cmyk))
            self.window().status_bar.showMessage(f"{self.name} CMYK {self.cmyk}", 2000)

class ColorPalette(QDialog):

    # nine colors dictionary: Gemini-generated, Copilot corrected.
    ninecolors = {
        "gray1": {"rgb": (36, 36, 36), "cmyk": (0.0, 0.0, 0.0, 0.86), "gray": 0.14},
        "gray2": {"rgb": (59, 59, 59), "cmyk": (0.0, 0.0, 0.0, 0.77), "gray": 0.23},
        "gray3": {"rgb": (77, 77, 77), "cmyk": (0.0, 0.0, 0.0, 0.70), "gray": 0.30},
        "gray4": {"rgb": (97, 97, 97), "cmyk": (0.0, 0.0, 0.0, 0.62), "gray": 0.38},
        "gray5": {"rgb": (117, 117, 117), "cmyk": (0.0, 0.0, 0.0, 0.54), "gray": 0.46},
        "gray6": {"rgb": (140, 140, 140), "cmyk": (0.0, 0.0, 0.0, 0.45), "gray": 0.55},
        "gray7": {"rgb": (163, 163, 163), "cmyk": (0.0, 0.0, 0.0, 0.36), "gray": 0.64},
        "gray8": {"rgb": (191, 191, 191), "cmyk": (0.0, 0.0, 0.0, 0.25), "gray": 0.75},
        "gray9": {"rgb": (222, 222, 222), "cmyk": (0.0, 0.0, 0.0, 0.13), "gray": 0.87},
        "red1": {"rgb": (76, 8, 8), "cmyk": (0.0, 0.89, 0.89, 0.7), "hsb": (0.0, 0.89, 0.3)},
        "red2": {"rgb": (117, 13, 13), "cmyk": (0.0, 0.89, 0.89, 0.54), "hsb": (0.0, 0.89, 0.46)},
        "red3": {"rgb": (156, 17, 17), "cmyk": (0.0, 0.89, 0.89, 0.39), "hsb": (0.0, 0.89, 0.61)},
        "red4": {"rgb": (194, 21, 21), "cmyk": (0.0, 0.89, 0.89, 0.24), "hsb": (0.0, 0.89, 0.76)},
        "red5": {"rgb": (230, 30, 30), "cmyk": (0.0, 0.87, 0.87, 0.1), "hsb": (0.0, 0.87, 0.9)},
        "red6": {"rgb": (237, 90, 90), "cmyk": (0.0, 0.62, 0.62, 0.07), "hsb": (0.0, 0.62, 0.93)},
        "red7": {"rgb": (242, 133, 133), "cmyk": (0.0, 0.45, 0.45, 0.05), "hsb": (0.0, 0.45, 0.95)},
        "red8": {"rgb": (245, 171, 171), "cmyk": (0.0, 0.3, 0.3, 0.04), "hsb": (0.0, 0.3, 0.96)},
        "red9": {"rgb": (250, 212, 212), "cmyk": (0.0, 0.15, 0.15, 0.02), "hsb": (0.0, 0.15, 0.98)},
        "brown1": {"rgb": (56, 31, 6), "cmyk": (0.0, 0.45, 0.89, 0.78), "hsb": (30.0, 0.89, 0.22)},
        "brown2": {"rgb": (87, 48, 10), "cmyk": (0.0, 0.45, 0.89, 0.66), "hsb": (30.0, 0.89, 0.34)},
        "brown3": {"rgb": (117, 65, 13), "cmyk": (0.0, 0.45, 0.89, 0.54), "hsb": (30.0, 0.89, 0.46)},
        "brown4": {"rgb": (145, 81, 16), "cmyk": (0.0, 0.45, 0.89, 0.43), "hsb": (30.0, 0.89, 0.57)},
        "brown5": {"rgb": (176, 98, 19), "cmyk": (0.0, 0.45, 0.89, 0.31), "hsb": (30.0, 0.89, 0.69)},
        "brown6": {"rgb": (209, 116, 23), "cmyk": (0.0, 0.45, 0.89, 0.18), "hsb": (30.0, 0.89, 0.82)},
        "brown7": {"rgb": (232, 143, 53), "cmyk": (0.0, 0.39, 0.77, 0.09), "hsb": (30.0, 0.77, 0.91)},
        "brown8": {"rgb": (240, 179, 117), "cmyk": (0.0, 0.26, 0.51, 0.06), "hsb": (30.0, 0.51, 0.94)},
        "brown9": {"rgb": (247, 216, 186), "cmyk": (0.0, 0.12, 0.25, 0.03), "hsb": (30.0, 0.25, 0.97)},
        "yellow1": {"rgb": (38, 38, 4), "cmyk": (0.0, 0.0, 0.89, 0.85), "hsb": (60.0, 0.89, 0.15)},
        "yellow2": {"rgb": (59, 59, 6), "cmyk": (0.0, 0.0, 0.89, 0.77), "hsb": (60.0, 0.89, 0.23)},
        "yellow3": {"rgb": (79, 79, 9), "cmyk": (0.0, 0.0, 0.89, 0.69), "hsb": (60.0, 0.89, 0.31)},
        "yellow4": {"rgb": (99, 99, 11), "cmyk": (0.0, 0.0, 0.89, 0.61), "hsb": (60.0, 0.89, 0.39)},
        "yellow5": {"rgb": (122, 122, 13), "cmyk": (0.0, 0.0, 0.89, 0.52), "hsb": (60.0, 0.89, 0.48)},
        "yellow6": {"rgb": (145, 145, 16), "cmyk": (0.0, 0.0, 0.89, 0.43), "hsb": (60.0, 0.89, 0.57)},
        "yellow7": {"rgb": (168, 168, 19), "cmyk": (0.0, 0.0, 0.89, 0.34), "hsb": (60.0, 0.89, 0.66)},
        "yellow8": {"rgb": (196, 196, 22), "cmyk": (0.0, 0.0, 0.89, 0.23), "hsb": (60.0, 0.89, 0.77)},
        "yellow9": {"rgb": (230, 230, 25), "cmyk": (0.0, 0.0, 0.89, 0.1), "hsb": (60.0, 0.89, 0.9)},
        "olive1": {"rgb": (23, 41, 4), "cmyk": (0.45, 0.0, 0.89, 0.84), "hsb": (90.0, 0.89, 0.16)},
        "olive2": {"rgb": (37, 66, 7), "cmyk": (0.45, 0.0, 0.89, 0.74), "hsb": (90.0, 0.89, 0.26)},
        "olive3": {"rgb": (48, 87, 10), "cmyk": (0.45, 0.0, 0.89, 0.66), "hsb": (90.0, 0.89, 0.34)},
        "olive4": {"rgb": (61, 110, 12), "cmyk": (0.44, 0.0, 0.89, 0.57), "hsb": (90.0, 0.89, 0.43)},
        "olive5": {"rgb": (74, 133, 15), "cmyk": (0.45, 0.0, 0.89, 0.48), "hsb": (90.0, 0.89, 0.52)},
        "olive6": {"rgb": (86, 156, 17), "cmyk": (0.45, 0.0, 0.89, 0.39), "hsb": (90.0, 0.89, 0.61)},
        "olive7": {"rgb": (102, 184, 20), "cmyk": (0.45, 0.0, 0.89, 0.28), "hsb": (90.0, 0.89, 0.72)},
        "olive8": {"rgb": (119, 214, 24), "cmyk": (0.45, 0.0, 0.89, 0.16), "hsb": (90.0, 0.89, 0.84)},
        "olive9": {"rgb": (177, 240, 115), "cmyk": (0.26, 0.0, 0.52, 0.06), "hsb": (90.0, 0.52, 0.94)},
        "green1": {"rgb": (5, 43, 5), "cmyk": (0.89, 0.0, 0.89, 0.83), "hsb": (120.0, 0.89, 0.17)},
        "green2": {"rgb": (8, 69, 8), "cmyk": (0.89, 0.0, 0.89, 0.73), "hsb": (120.0, 0.89, 0.27)},
        "green3": {"rgb": (10, 89, 10), "cmyk": (0.89, 0.0, 0.89, 0.65), "hsb": (120.0, 0.89, 0.35)},
        "green4": {"rgb": (12, 112, 12), "cmyk": (0.89, 0.0, 0.89, 0.56), "hsb": (120.0, 0.89, 0.44)},
        "green5": {"rgb": (15, 138, 15), "cmyk": (0.89, 0.0, 0.89, 0.46), "hsb": (120.0, 0.89, 0.54)},
        "green6": {"rgb": (18, 163, 18), "cmyk": (0.89, 0.0, 0.89, 0.36), "hsb": (120.0, 0.89, 0.64)},
        "green7": {"rgb": (21, 191, 21), "cmyk": (0.89, 0.0, 0.89, 0.25), "hsb": (120.0, 0.89, 0.75)},
        "green8": {"rgb": (24, 222, 24), "cmyk": (0.89, 0.0, 0.89, 0.13), "hsb": (120.0, 0.89, 0.87)},
        "green9": {"rgb": (148, 242, 148), "cmyk": (0.39, 0.0, 0.39, 0.05), "hsb": (120.0, 0.39, 0.95)},
        "teal1": {"rgb": (5, 43, 24), "cmyk": (0.89, 0.0, 0.45, 0.83), "hsb": (150.0, 0.89, 0.17)},
        "teal2": {"rgb": (7, 66, 37), "cmyk": (0.89, 0.0, 0.45, 0.74), "hsb": (150.0, 0.89, 0.26)},
        "teal3": {"rgb": (10, 89, 50), "cmyk": (0.89, 0.0, 0.44, 0.65), "hsb": (150.0, 0.89, 0.35)},
        "teal4": {"rgb": (12, 112, 62), "cmyk": (0.89, 0.0, 0.45, 0.56), "hsb": (150.0, 0.89, 0.44)},
        "teal5": {"rgb": (15, 135, 75), "cmyk": (0.89, 0.0, 0.45, 0.47), "hsb": (150.0, 0.89, 0.53)},
        "teal6": {"rgb": (18, 161, 89), "cmyk": (0.89, 0.0, 0.44, 0.37), "hsb": (150.0, 0.89, 0.63)},
        "teal7": {"rgb": (21, 189, 105), "cmyk": (0.89, 0.0, 0.45, 0.26), "hsb": (150.0, 0.89, 0.74)},
        "teal8": {"rgb": (24, 219, 122), "cmyk": (0.89, 0.0, 0.45, 0.14), "hsb": (150.0, 0.89, 0.86)},
        "teal9": {"rgb": (138, 242, 190), "cmyk": (0.43, 0.0, 0.21, 0.05), "hsb": (150.0, 0.43, 0.95)},
        "cyan1": {"rgb": (4, 41, 41), "cmyk": (0.89, 0.0, 0.0, 0.84), "hsb": (180.0, 0.89, 0.16)},
        "cyan2": {"rgb": (7, 64, 64), "cmyk": (0.89, 0.0, 0.0, 0.75), "hsb": (180.0, 0.89, 0.25)},
        "cyan3": {"rgb": (10, 87, 87), "cmyk": (0.89, 0.0, 0.0, 0.66), "hsb": (180.0, 0.89, 0.34)},
        "cyan4": {"rgb": (12, 107, 107), "cmyk": (0.89, 0.0, 0.0, 0.58), "hsb": (180.0, 0.89, 0.42)},
        "cyan5": {"rgb": (14, 130, 130), "cmyk": (0.89, 0.0, 0.0, 0.49), "hsb": (180.0, 0.89, 0.51)},
        "cyan6": {"rgb": (17, 156, 156), "cmyk": (0.89, 0.0, 0.0, 0.39), "hsb": (180.0, 0.89, 0.61)},
        "cyan7": {"rgb": (20, 181, 181), "cmyk": (0.89, 0.0, 0.0, 0.29), "hsb": (180.0, 0.89, 0.71)},
        "cyan8": {"rgb": (23, 212, 212), "cmyk": (0.89, 0.0, 0.0, 0.17), "hsb": (180.0, 0.89, 0.83)},
        "cyan9": {"rgb": (120, 240, 240), "cmyk": (0.5, 0.0, 0.0, 0.06), "hsb": (180.0, 0.5, 0.94)},
        "azure1": {"rgb": (7, 37, 66), "cmyk": (0.89, 0.45, 0.0, 0.74), "hsb": (210.0, 0.89, 0.26)},
        "azure2": {"rgb": (12, 58, 105), "cmyk": (0.89, 0.45, 0.0, 0.59), "hsb": (210.0, 0.89, 0.41)},
        "azure3": {"rgb": (15, 78, 140), "cmyk": (0.89, 0.45, 0.0, 0.45), "hsb": (210.0, 0.89, 0.55)},
        "azure4": {"rgb": (19, 98, 176), "cmyk": (0.89, 0.45, 0.0, 0.31), "hsb": (210.0, 0.89, 0.69)},
        "azure5": {"rgb": (23, 117, 212), "cmyk": (0.89, 0.44, 0.0, 0.17), "hsb": (210.0, 0.89, 0.83)},
        "azure6": {"rgb": (53, 143, 232), "cmyk": (0.77, 0.39, 0.0, 0.09), "hsb": (210.0, 0.77, 0.91)},
        "azure7": {"rgb": (100, 168, 237), "cmyk": (0.58, 0.29, 0.0, 0.07), "hsb": (210.0, 0.58, 0.93)},
        "azure8": {"rgb": (148, 195, 242), "cmyk": (0.39, 0.2, 0.0, 0.05), "hsb": (210.0, 0.39, 0.95)},
        "azure9": {"rgb": (200, 225, 250), "cmyk": (0.2, 0.1, 0.0, 0.02), "hsb": (210.0, 0.2, 0.98)},
        "blue1": {"rgb": (13, 13, 122), "cmyk": (0.89, 0.89, 0.0, 0.52), "hsb": (240.0, 0.89, 0.48)},
        "blue2": {"rgb": (20, 20, 186), "cmyk": (0.89, 0.89, 0.0, 0.27), "hsb": (240.0, 0.89, 0.73)},
        "blue3": {"rgb": (37, 37, 230), "cmyk": (0.84, 0.84, 0.0, 0.1), "hsb": (240.0, 0.84, 0.9)},
        "blue4": {"rgb": (70, 70, 235), "cmyk": (0.7, 0.7, 0.0, 0.08), "hsb": (240.0, 0.7, 0.92)},
        "blue5": {"rgb": (100, 100, 237), "cmyk": (0.58, 0.58, 0.0, 0.07), "hsb": (240.0, 0.58, 0.93)},
        "blue6": {"rgb": (127, 127, 240), "cmyk": (0.47, 0.47, 0.0, 0.06), "hsb": (240.0, 0.47, 0.94)},
        "blue7": {"rgb": (157, 157, 245), "cmyk": (0.36, 0.36, 0.0, 0.04), "hsb": (240.0, 0.36, 0.96)},
        "blue8": {"rgb": (186, 186, 247), "cmyk": (0.25, 0.25, 0.0, 0.03), "hsb": (240.0, 0.25, 0.97)},
        "blue9": {"rgb": (217, 217, 250), "cmyk": (0.13, 0.13, 0.0, 0.02), "hsb": (240.0, 0.13, 0.98)},
        "violet1": {"rgb": (52, 10, 94), "cmyk": (0.45, 0.89, 0.0, 0.63), "hsb": (270.0, 0.89, 0.37)},
        "violet2": {"rgb": (81, 16, 145), "cmyk": (0.45, 0.89, 0.0, 0.43), "hsb": (270.0, 0.89, 0.57)},
        "violet3": {"rgb": (106, 21, 191), "cmyk": (0.45, 0.89, 0.0, 0.25), "hsb": (270.0, 0.89, 0.75)},
        "violet4": {"rgb": (132, 34, 230), "cmyk": (0.43, 0.85, 0.0, 0.1), "hsb": (270.0, 0.85, 0.9)},
        "violet5": {"rgb": (155, 75, 235), "cmyk": (0.34, 0.68, 0.0, 0.08), "hsb": (270.0, 0.68, 0.92)},
        "violet6": {"rgb": (175, 110, 240), "cmyk": (0.27, 0.54, 0.0, 0.06), "hsb": (270.0, 0.54, 0.94)},
        "violet7": {"rgb": (193, 143, 242), "cmyk": (0.2, 0.41, 0.0, 0.05), "hsb": (270.0, 0.41, 0.95)},
        "violet8": {"rgb": (213, 178, 247), "cmyk": (0.14, 0.28, 0.0, 0.03), "hsb": (270.0, 0.28, 0.97)},
        "violet9": {"rgb": (232, 215, 250), "cmyk": (0.07, 0.14, 0.0, 0.02), "hsb": (270.0, 0.14, 0.98)},
        "magenta1": {"rgb": (66, 7, 66), "cmyk": (0.0, 0.89, 0.0, 0.74), "hsb": (300.0, 0.89, 0.26)},
        "magenta2": {"rgb": (105, 12, 105), "cmyk": (0.0, 0.89, 0.0, 0.59), "hsb": (300.0, 0.89, 0.41)},
        "magenta3": {"rgb": (138, 15, 138), "cmyk": (0.0, 0.89, 0.0, 0.46), "hsb": (300.0, 0.89, 0.54)},
        "magenta4": {"rgb": (171, 19, 171), "cmyk": (0.0, 0.89, 0.0, 0.33), "hsb": (300.0, 0.89, 0.67)},
        "magenta5": {"rgb": (204, 22, 204), "cmyk": (0.0, 0.89, 0.0, 0.2), "hsb": (300.0, 0.89, 0.8)},
        "magenta6": {"rgb": (232, 56, 232), "cmyk": (0.0, 0.76, 0.0, 0.09), "hsb": (300.0, 0.76, 0.91)},
        "magenta7": {"rgb": (240, 115, 240), "cmyk": (0.0, 0.52, 0.0, 0.06), "hsb": (300.0, 0.52, 0.94)},
        "magenta8": {"rgb": (245, 164, 245), "cmyk": (0.0, 0.33, 0.0, 0.04), "hsb": (300.0, 0.33, 0.96)},
        "magenta9": {"rgb": (250, 207, 250), "cmyk": (0.0, 0.17, 0.0, 0.02), "hsb": (300.0, 0.17, 0.98)},
        "purple1": {"rgb": (74, 8, 41), "cmyk": (0.0, 0.89, 0.45, 0.71), "hsb": (330.0, 0.89, 0.29)},
        "purple2": {"rgb": (115, 13, 64), "cmyk": (0.0, 0.89, 0.45, 0.55), "hsb": (330.0, 0.89, 0.45)},
        "purple3": {"rgb": (150, 17, 83), "cmyk": (0.0, 0.89, 0.44, 0.41), "hsb": (330.0, 0.89, 0.59)},
        "purple4": {"rgb": (186, 20, 103), "cmyk": (0.0, 0.89, 0.45, 0.27), "hsb": (330.0, 0.89, 0.73)},
        "purple5": {"rgb": (224, 25, 125), "cmyk": (0.0, 0.89, 0.45, 0.12), "hsb": (330.0, 0.89, 0.88)},
        "purple6": {"rgb": (235, 80, 157), "cmyk": (0.0, 0.66, 0.33, 0.08), "hsb": (330.0, 0.66, 0.92)},
        "purple7": {"rgb": (240, 127, 183), "cmyk": (0.0, 0.47, 0.23, 0.06), "hsb": (330.0, 0.47, 0.94)},
        "purple8": {"rgb": (245, 169, 207), "cmyk": (0.0, 0.31, 0.16, 0.04), "hsb": (330.0, 0.31, 0.96)},
        "purple9": {"rgb": (250, 210, 230), "cmyk": (0.0, 0.16, 0.08, 0.02), "hsb": (330.0, 0.16, 0.98)},
        "black": {"rgb": (0,0,0), "cmyk": (0.0,0.0,0.0,1.0), "hsb": (0,0,0)},
        "white": {"rgb": (255,255,255), "cmyk": (0,0,0,0), "hsb": (0,1,1)},
    }

    hues = [
        "gray", "red", "brown", "yellow", "olive",
        "green", "teal", "cyan", "azure", "blue",
        "violet", "magenta", "purple",
    ]


    color_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("colorpalette.window_title"))

        layout = QGridLayout(self)
        for row, hue in enumerate(self.hues):
            for col in range(9):
                name = f"{hue}{col+1}"
                if name in self.ninecolors:
                    rgb = self.ninecolors[name]["rgb"]
                    cmyk = self.ninecolors[name]["cmyk"]
                    btn = ColorButton(name, rgb, cmyk)
                    btn.clicked.connect(lambda _, n=name: self.select_and_close(n))
                    layout.addWidget(btn, row, col)

        # 마지막 행(14행)에 white, black 버튼 추가
        row = len(self.hues)  # 즉 13행 다음 → 14행
        for col, name in enumerate(["white", "black"]):
            if name in self.ninecolors:
                rgb = self.ninecolors[name]["rgb"]
                cmyk = self.ninecolors[name]["cmyk"]
                btn = ColorButton(name, rgb, cmyk)
                btn.clicked.connect(lambda _, n=name: self.select_and_close(n))
                layout.addWidget(btn, row, col)

    def select_and_close(self, name: str):
        # 시그널로 선택된 색상 전달
        self.color_selected.emit(name)
        # 다이얼로그 닫기
        self.accept()
