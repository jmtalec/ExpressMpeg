import webbrowser, sys
from PyQt6.QtWidgets import QDialog, QFileDialog, QDialogButtonBox, QFileIconProvider, QMessageBox, QWidget, QListWidgetItem, QApplication, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtGui import QIcon, QMouseEvent, QCursor, QColor, QLinearGradient, QBrush
from PyQt6.QtCore import QFileInfo, QEvent, QPointF, Qt, QSize
from PyQt6.uic.load_ui import loadUi

from utils import *
from async_funcs import *

from qframelesswindow import AcrylicWindow, FramelessWindow
from qframelesswindow.titlebar.title_bar_buttons import TitleBarButtonState
from dotwidget import DotWidget

if isWin11:
    # utils for windows snap
    import win32con
    from ctypes.wintypes import MSG

__version__ = "2.10.0"

class AudioItem(QWidget):

    def __init__(self, app, list_item, file_name:str):
        """Infos on songs, output folder, ect..."""
        super().__init__(app)
        
        self.app = app

        self.list_item = list_item
        self.file_name = file_name
    
        self.ext = get_file_type(file_name)
        
        loadUi('./ui/list-item.ui', self)
        
        self.label.setText(self.file_name.replace("/", "\\"))
        self.trashButton.clicked.connect(self.trash)
        self.playButton.clicked.connect(self.folder)
        
        file_icon = icon_provider.icon(QFileInfo(self.file_name))
        self.iconLabel.setPixmap(file_icon.pixmap(20, 20))

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)  # Softness of the shadow
        shadow.setXOffset(0.75)  # Horizontal shadow position
        shadow.setYOffset(0.75)  # Vertical shadow position
        shadow.setColor(QColor(0, 0, 0, 80))  # RGBA Black with transparency
        self.iconLabel.setGraphicsEffect(shadow)
        self.setObjectName("listItem")

        self.converting = False

    def folder(self):
        open_folder(pathlib.Path(self.file_name).parent)
        
    def trash(self):
        row = self.app.listWidget.row(self.list_item)
        self.app.listWidget.takeItem(row)
        self.app.handler.audio_list.remove(self.file_name)
        del self.app.file_widgets[self.file_name]
    
    def set_progress(self, i):
        self.state_label.setText(f"{i}%")
        self.state_label.setStyleSheet("color:#aaaaaa")
        
        palette = self.palette()
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        if i < 99:
            gradient.setColorAt(i/100, QColor(217, 227, 239))
            gradient.setColorAt(i/100+0.001, QColor(0, 0, 0, 0))
            palette.setBrush(self.backgroundRole(), QBrush(gradient))
        else:
            gradient.setColorAt(0.99, QColor(217, 227, 239))
            gradient.setColorAt(1.0, QColor(255, 255, 255, 200))
            palette.setBrush(self.backgroundRole(), QBrush(gradient))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def disable(self):
        self.trashButton.setEnabled(False)
        self.playButton.setEnabled(False)


class ActionItem(QWidget):
    def __init__(self, app, audio_type):
        super().__init__(app)

        self.app = app
        loadUi('./ui/action-item.ui', self)
        self.audio_type = audio_type
        
        audf = audio_formats.copy()
        if audio_type != ".mp4":
            audf.remove(audio_type)
        audf.remove(".mp4")

        self.outCombo.addItems(audf)
        self.outCombo.setCurrentIndex(audf.index(settings["pre_references"][self.audio_type]))
        self.ext_label.setText(f"Transformer les audios <b>{audio_type}</b> en ")
    
    def fetch(self):
        ext = self.outCombo.currentText()
        send_to_output_folder = self.radioButtonOutput.isChecked()
        settings["pre_references"][self.audio_type] = ext
        save_settings(settings)
        self.app.handler.audio_options[self.audio_type] = (ext, send_to_output_folder)
        
class Startup(QDialog):
    def __init__(self, app):
        
        super().__init__(app)
        
        loadUi('./ui/start-dialog.ui', self)
        self.setWindowTitle('Choisir les options audio')

        self.widget_list = []
        self.app = app

        for ext in self.app.handler.audio_types():
            self.add_action(ext)
        
        self.buttonBox.accepted.connect(self.handleAccept)
        self.buttonBox.rejected.connect(self.reject)
    
    def handleAccept(self):
        for widget in self.widget_list:
            widget.fetch()
        self.accept()
    
    def add_action(self, type):
        widget = ActionItem(self.app, type)
        self.widget_list.append(widget)
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.listWidget.addItem(item)
        self.listWidget.setItemWidget(item, widget)


class Settings(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        loadUi("ui/settings.ui", self)
        self.openButton.setIcon(QIcon(icon_provider.icon(QFileIconProvider.IconType.Folder).pixmap(16, 16)))
        self.openButton.clicked.connect(self.open)
        
        self.fileLineEdit.setText(settings["output_folder"].replace('/', os.sep))
        
        expressmpeg_font.setPointSize(17)
        self.titleLabel.setFont(app_font)
        
        self.framerateSlider.setMaximum(len(frame_rates)-1)
        self.framerateSlider.setValue(frame_rates.index(settings["frame_rate"]))
        self.framerateLabel.setNum(settings["frame_rate"])
        self.framerateSlider.valueChanged.connect(lambda x: self.framerateLabel.setNum(frame_rates[x]))


        if settings["frame_rate"] == 44100:
            self.defaultQualityRadioButton.setChecked(True)
            self.sliderFrame.setVisible(False)
        else:
            self.customRadioButton.setChecked(True)
        
        match settings["n_processes"]:
            case 1:
                self.radioButton_1.setChecked(True)
            case 2:
                self.radioButton_2.setChecked(True)
            case 3:
                self.radioButton_3.setChecked(True)
        
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok    ).clicked.disconnect()
        self.buttonBox.button(QDialogButtonBox.StandardButton.Apply ).clicked.connect(self.apply )
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok    ).clicked.connect(self.ok    )
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.cancel)

        
    def open(self):
        folder_path = QFileDialog.getExistingDirectory(self)
        if folder_path:
            self.fileLineEdit.setText(str(pathlib.Path(folder_path)))
    
    def ok(self):
        if self.apply():
            self.accept()
    
    def cancel(self):
        self.reject()

    def apply(self):
        folder_path = self.fileLineEdit.text()
        changes = {}
        if os.path.exists(folder_path):
            changes["output_folder"] = str().join([x if x != "\\" else "/" for x in list(self.fileLineEdit.text())])
            
            if self.radioButton_1.isChecked():
                changes["n_processes"] = 1
            elif self.radioButton_2.isChecked():
                changes["n_processes"] = 2
            else:
                changes["n_processes"] = 3
            
            if self.defaultQualityRadioButton.isChecked():
                changes["frame_rate"] = 44100
            else:
                changes["frame_rate"] = frame_rates[self.framerateSlider.value()]
            
            save_settings(changes)
            return True
        
        else:
            qmb = QMessageBox(QMessageBox.Icon.Critical,
                        "Dossier introuvable",
                        f"Le dossier \"{self.fileLineEdit.text()}\" est introuvable.\nVeuillez vérifier l'orthographe du chemin d'accès au dossier.",
                        parent = self
            )
            qmb.setWindowIcon(appIcon)
            qmb.exec()
            return False

class AcrylicWindowWithSnapLayout(AcrylicWindow):
    """
    Ajoute la fonction de `snap layout` à la fenêtre.
    Voir https://pyqt-frameless-window.readthedocs.io/en/latest/snap-layout.html
    """

    
    def nativeEvent(self, eventType, message):
            
            msg = MSG.from_address(message.__int__())
            if not msg.hWnd:
                return super().nativeEvent(eventType, message)
            if msg.message == win32con.WM_NCHITTEST and self._isResizeEnabled:
                if self._isHoverMaxBtn():
                    self.titleBar.maxBtn.setState(TitleBarButtonState.HOVER)
                    return True, win32con.HTMAXBUTTON
            elif msg.message in [0x2A2, win32con.WM_MOUSELEAVE]:
                self.titleBar.maxBtn.setState(TitleBarButtonState.NORMAL)
            elif msg.message in [win32con.WM_NCLBUTTONDOWN, win32con.WM_NCLBUTTONDBLCLK] and self._isHoverMaxBtn():
                e = QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
                QApplication.sendEvent(self.titleBar.maxBtn, e)
                return True, 0
            elif msg.message in [win32con.WM_NCLBUTTONUP, win32con.WM_NCRBUTTONUP] and self._isHoverMaxBtn():
                e = QMouseEvent(QEvent.Type.MouseButtonRelease, QPointF(), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
                QApplication.sendEvent(self.titleBar.maxBtn, e)
            return super().nativeEvent(eventType, message)

    def _isHoverMaxBtn(self):
        pos = QCursor.pos() - self.geometry().topLeft() - self.titleBar.pos()
        return self.titleBar.childAt(pos) is self.titleBar.maxBtn

class Main(AcrylicWindowWithSnapLayout if isWin11 else FramelessWindow):
    
    def __init__(self) -> None:
        
        super().__init__()
        
        loadUi('./ui/main-window.ui', self)
        
        expressmpeg_font.setPointSize(16)
        self.label_3.setFont(expressmpeg_font)
 
        expressmpeg_font.setPointSize(29)
        self.label.setFont(expressmpeg_font)
        self.titleBar.closeBtn.setStyleSheet("background-color:blue")
        expressmpeg_font.setPointSize(16)
        
        if isWin11:
            self.windowEffect.setMicaEffect(self.winId())
        else:
            self.setStyleSheet("QWidget#Form{background-color:#f0f0f0}")
        
        layout = QHBoxLayout(self.progressFrame)
        
        self.dotWidget = DotWidget(self.progressFrame, 5)
        layout.addWidget(self.dotWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.setWindowIcon(appIcon)
        self.resize(QSize(800, 600))
        self.setWindowTitle('ExpressMpeg')
        
        self.addButton.clicked.connect(self.add_files)
        self.titleBar.closeBtn.clicked.disconnect()
        self.titleBar.closeBtn.clicked.connect(self.close_button)
        
        self.titleBar.maxBtn.setToolTip("Maximiser")
        self.titleBar.minBtn.setToolTip("Minimiser")
        self.titleBar.closeBtn.setToolTip("Fermer")
        
        self.outButton.clicked.connect(lambda x: open_folder(settings["output_folder"]))
        self.settingsButton.clicked.connect(self.open_settings_window)
        self.helpButton.clicked.connect(self.open_about_window)
        self.startButton.clicked.connect(self.start)

        self.file_widgets = dict()

        self.handler = Handler(self)
        

    def open_settings_window(self):
        window = Settings(self)
        window.exec()

    def open_about_window(self):
        window = About(self)
        window.exec()

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key.Key_Delete, Qt.Key.Key_Backspace]:
            if not self.handler.converting:
                selected = self.listWidget.selectedItems()
                for item in selected:
                    item.audio_widget.trash()
            else:
                QApplication.beep()

    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and all(os.path.exists(url.toLocalFile()) for url in event.mimeData().urls()) and not self.handler.close and not self.handler.populating:
            paths = [url.toLocalFile() for url in event.mimeData().urls()]
            if any([get_file_type(path) in audio_formats for path in paths]):
                event.acceptProposedAction()
            elif any([os.path.isdir(path) for path in paths]):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        mime_data = event.mimeData()
        file_paths = []
        code = None
        for url in mime_data.urls():
            
            path = pathlib.Path(url.toLocalFile())
            
            if path.is_file() and path.suffix in audio_formats:
                file_paths.append(str(path))
            
            elif path.is_dir():
                if any(os.path.isdir(path.joinpath(x)) for x in os.listdir(path)):
                    if code is None:
                        qmb = QMessageBox(
                            QMessageBox.Icon.Question,
                            "Options de glisser-déposer",
                            'Souhaitez-vous inclure les fichiers présents dans les sous-dossiers ?',
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            self
                        )
                        qmb.setWindowIcon(appIcon)
                        code = qmb.exec()

                    for foldername, subfolders, filenames in os.walk(path):
                        for filename in filenames:
                            if code == QMessageBox.StandardButton.Yes and get_file_type(filename) in audio_formats:
                                file_paths.append(os.path.join(foldername, filename))
                else:
                    for filename in os.listdir(path):
                        if get_file_type(filename) in audio_formats:
                            file_paths.append(str(path.joinpath(filename)))
        
        if file_paths:
            self.populate(file_paths)
    
    def add_files(self):
        filter = get_description()
        file_paths, _ = QFileDialog.getOpenFileNames(
            parent=self, 
            caption="Ajouter des fichiers audio à convertir", 
            filter=filter
        )
        if file_paths:
            self.populate(file_paths)

    def populate(self, paths:list):
        self.addButton.setDisabled(True)
        self.startButton.setDisabled(True)
        self.setCursor(Qt.CursorShape.BusyCursor)
        
        self.handler.populating = True
        
        np = 0
        for path in paths:
            if path not in self.handler.audio_list:
                item = QListWidgetItem()
                widget = AudioItem(self, item, path)
                self.file_widgets[path] = widget
                item.audio_widget = widget
                item.setSizeHint(widget.sizeHint())
                self.listWidget.addItem(item)
                self.listWidget.setItemWidget(item, widget)
                self.handler.audio_list.append(path)
                if np == 5:
                    QApplication.processEvents()
                    np = 0
                np += 1
        

        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.handler.populating = False
        self.startButton.setEnabled(True)
        self.addButton.setEnabled(True)
    
    def exit(self):
        self.handler.close = True
        sys.exit()

    def close_button(self):
        if self.handler.converting:
            qmb = QMessageBox(QMessageBox.Icon.Question, 
                               "Annuler la conversion ?", 
                               "Êtes-vous certain de vouloir annuler la conversion ?", 
                               QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel, 
                               self
                               )
            qmb.setWindowIcon(appIcon)
            code = qmb.exec()
            if code == QMessageBox.StandardButton.Ok:
                self.hide()
                self.exit()
        else:
            self.hide()
            sys.exit()
    
    def closeEvent(self, _):
        if self.handler.converting:
            self.hide()
            self.exit()
        else:
            self.hide()
            sys.exit()
        
    def start(self):
        audios = self.handler.audio_list
        if audios:
            dialog = Startup(self)
            if dialog.exec():
                self.dotWidget.start()
                self.addButton.setEnabled(False)
                self.startButton.setEnabled(False)
                self.settingsButton.setEnabled(False)
                self.handler.converting = True
                for item in self.file_widgets.values():
                    item.disable()
                loop = asyncio.get_event_loop()
                loop.run_until_complete(asyncio.gather(convert_files(self.handler), update_app(self.handler)))
                self.dotWidget.stop()
                if not self.handler.output_folder_error:
                    qmb = QMessageBox(QMessageBox.Icon.Information,
                                "État de la conversion",
                                "Tous les fichiers audios ont été convertis !",
                                QMessageBox.StandardButton.Ok
                                )
                    qmb.setWindowIcon(appIcon)
                    qmb.exec()
                self.handler.output_folder_error = False
                self.addButton.setEnabled(True)
                self.startButton.setEnabled(True)
                self.settingsButton.setEnabled(True)

class About(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        
        loadUi('ui/about.ui', self)
        self.label_3.setText(__version__)

        self.tabWidget.removeTab(3)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Help).clicked.connect(self.open_url)

    def open_url(self):
        webbrowser.open("https://github.com/jmtalec/ExpressMpeg/tree/main")
