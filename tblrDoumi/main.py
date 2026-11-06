import sys, os
import json
from PySide6.QtWidgets import (QApplication, QMessageBox)
from PySide6.QtGui import QIcon

from tblrDoumi import __version__ as VERSION
from tblrDoumi.TblrGenerator import TblrGenerator
from tblrDoumi.i18n import tr

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # OS 기본 대신 Fusion 스타일 사용

    icon_path = resource_path("tblrdoumi.ico")
    app.setWindowIcon(QIcon(icon_path))

    window = TblrGenerator()
    window.show()

    # 인자로 파일이 넘어온 경우 처리
    if len(sys.argv) > 1 and sys.argv[1].endswith(".tblr"):
        filename = sys.argv[1]
        try:
            window.load_table(filename)
        except FileNotFoundError:
            QMessageBox.critical(window, tr("msg.file_error.title"), tr("msg.file_error.not_found", filename=filename))
        except json.JSONDecodeError:
            QMessageBox.critical(window, tr("msg.file_error.title"), tr("msg.file_error.invalid_format", filename=filename))
        except Exception as e:
            QMessageBox.critical(window, tr("msg.error.title"), tr("msg.file_error.open_failed", filename=filename, err=str(e)))

    sys.exit(app.exec())