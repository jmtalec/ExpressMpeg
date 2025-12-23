from PyQt6.QtCore import Qt, QTranslator, QLibraryInfo
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap

import sys

app = QApplication(sys.argv)

if __name__ == "__main__":
    splash_pix = QPixmap(r'.\\ui\\splash.png')
    splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    splash.setCursor(Qt.CursorShape.BlankCursor)
     
import ui
from utils import app_font
from windows import Main


if __name__ == "__main__":
    translator = QTranslator()
    
    if translator.load("qtbase_fr_FR", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(translator)

    app.setStyle('windowsvista')
    app_font.setPointSize(9)
    app.setFont(app_font)
    
    mw = Main()

    splash.close()
    splash.destroy()
    
    mw.show()
    app.exec()
