import sys
from PyQt6.QtCore import QTimer

from PyQt6.QtGui import (
    QColor,
    QPainter,
    QBrush,
    QPen
)

from PyQt6.QtWidgets import QWidget

from enum import Enum

BLUE = QColor(20, 20, 250, 255)
TRANSPARENT = QColor(0, 0, 0, 0)

class _Dot:
    class State(Enum):
        _0 = 3
        _1_6 = 2
        _2_6 = 1
        _3_6 = 1
        _4_6 = 2
        _5_6 = 3
        stop = 0

class Dot(_Dot):
    
    def __init__(self, x):
        self.y = 0
        self.x = x
        self.color = TRANSPARENT
        self.size = 3
    
    def update(self, state:_Dot.State):
        self.x += state.value
        if self.x == 0:
            self.color = TRANSPARENT
        else:
            self.color = BLUE


def dist(dot_a:Dot, dot_b:Dot):
    return abs(dot_a.x-dot_b.x)

class DotWidget(QWidget):
    def __init__(self, parent: QWidget=None, n:int=5, distance:int=25):
        super().__init__(parent)
        # Création de la matrice des états de chaque points
        self.mat_dots = [0 for x in range(0, n)]
        
        self.distance = distance

        # Création de chaque points
        self.dots:list[Dot] = [Dot(0) for x in range(0, n)]
        self.update_matrix()
        self.setMinimumHeight(3)
        # Création d'un updater et d'un timer
        self.animation = QTimer(self)
        self.animation.timeout.connect(self.move_dot)
        self.starting = False
        self.n = n
        
    def start(self, msec:int = 10):
        self.animation.start(msec)
    
    def pause(self):
        for dot in self.dots: dot.color = QColor(20, 20, 250, 255)
        self.animation.stop()
    
    def stop(self):
        for dot in self.dots: dot.color = QColor(0, 0, 0, 0)
        self.update()
        self.dots:list[Dot] = [Dot(0) for x in range(0, self.n)]
        self.animation.stop()
        self.update_matrix()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen()
        pen.setColor(TRANSPARENT)
        painter.setPen(pen)

        for dot in self.dots:
            painter.setBrush(QBrush(dot.color))
            painter.drawEllipse(dot.x, dot.y, dot.size, dot.size)

    def move_dot(self):
        self.update_matrix()
        for pos, dot in enumerate(self.dots):
            dot.update(self.mat_dots[pos])
        self.update()
    
    def update_matrix(self):
        self.length = self.size().width()
        position = [dot.x for dot in self.dots]
        _1_6 = self.length*1/6
        _2_6 = self.length*2/6
        _3_6 = self.length*3/6
        _4_6 = self.length*4/6
        _5_6 = self.length*5/6
        for pos, dot_x in enumerate(position):
            if dot_x <= _1_6 and dot_x > 0:
                self.mat_dots[pos] = Dot.State._0
            elif dot_x > _1_6 and dot_x <= _2_6:
                self.mat_dots[pos] = Dot.State._1_6
            elif dot_x > _2_6 and dot_x <= _3_6:
                self.mat_dots[pos] = Dot.State._2_6
            elif dot_x > _3_6 and dot_x <= _4_6:
                self.mat_dots[pos] = Dot.State._3_6
            elif dot_x > _4_6 and dot_x <= _5_6:
                self.mat_dots[pos] = Dot.State._4_6
            elif dot_x > _5_6 and dot_x <= self.length:
                self.mat_dots[pos] = Dot.State._5_6
            else:
                if all([dot == Dot.State.stop for dot in self.mat_dots]) and not self.starting:
                    self.starting = True
                if not any([dot == Dot.State.stop for dot in self.mat_dots]):
                    self.starting = False
                if self.starting:
                    try:
                        if dist(self.dots[pos], self.dots[pos+1]) >= self.distance:
                            self.mat_dots[pos] = Dot.State._0
                    except IndexError:
                        self.mat_dots[pos] = Dot.State._0

                else:
                    self.mat_dots[pos] = Dot.State.stop
                    self.dots[pos].x = 0

                    

if __name__ == "__main__":

    from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QApplication
    
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Dot Animation")
            self.setGeometry(100, 100, 800, 200)
            central_widget = QWidget(self)
            layout = QVBoxLayout(central_widget)
            self.setCentralWidget(central_widget)
            self.dot_widget = DotWidget(central_widget, 5)
            self.button = QPushButton(central_widget, text="Start")
            self.button.clicked.connect(self.on_click)
            layout.addWidget(self.dot_widget)
            layout.addWidget(self.button)
            self.running = False

        def on_click(self):
            if self.running:
                self.dot_widget.stop()
                self.button.setText("Start")
                self.running = False
            else:
                self.dot_widget.start()
                self.button.setText("Stop")
                self.running = True
                
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
