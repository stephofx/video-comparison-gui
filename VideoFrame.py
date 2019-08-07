import sys
import os
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from qrangeslider import QRangeSlider
from backprojection import alpha_beta, lp_projection_calibration, lp_projection


class VideoFrame(QWidget):

    def __init__(self, *args, **kwargs):
        super(VideoFrame, self).__init__(*args, **kwargs)
        self.layout = QVBoxLayout()
        self.img_list = []

        # STREAM 1 LABEL AREA
        self.label = QLabel('Nothing to show right now.', self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(30, 20, 750, 360)
        self.layout.addWidget(self.label)

        # PLAY BUTTON
        self.play = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'play.png'))
        self.play.setIcon(QIcon(icon))
        self.play.setGeometry(320, 370, 50, 30)
        self.play.clicked.connect(self.timerEvent)
        self.layout.addWidget(self.play)

        # PAUSE BUTTON
        self.pause = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'pause.png'))
        self.pause.setIcon(QIcon(icon))
        self.pause.setGeometry(400, 370, 50, 30)
        self.pause.clicked.connect(self.pauseTimer)
        self.layout.addWidget(self.pause)

        # FAST-FORWARD
        self.ff = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'ff.png'))
        self.ff.setIcon(QIcon(icon))
        self.ff.setGeometry(560, 370, 50, 30)
        self.ff.clicked.connect(self.fastForward)
        self.layout.addWidget(self.ff)

        # SLOWDOWN
        self.fr = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'fr.png'))
        self.fr.setIcon(QIcon(icon))
        self.fr.setGeometry(240, 370, 50, 30)
        self.fr.clicked.connect(self.slowdown)
        self.layout.addWidget(self.fr)

        self.stop = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'stop.png'))
        self.stop.setIcon(QIcon(icon))
        self.stop.setGeometry(480, 370, 50, 30)
        self.stop.clicked.connect(self.stopTimer)
        self.layout.addWidget(self.stop)

        # SLIDER 1
        self.slider = QSlider(Qt.Horizontal, self)
        self.layout.addWidget(self.slider)
        self.slider.setGeometry(10, 400, 825, 20)
        self.slider.valueChanged.connect(self.showImage)

        # RANGE SLIDER
        self.range_slider = QRangeSlider(self)
        self.range_slider.setFixedHeight(30)
        self.range_slider.setFixedWidth(825)
        self.range_slider.move(10, 420)
        self.range_slider.endValueChanged.connect(self.boundEnd)
        self.range_slider.startValueChanged.connect(self.boundStart)

        self.timer = QBasicTimer() # FIXME consider something with less lag
        self.startIdx = 0
        self.idx = 0
        self.delay = 1000
        self.skip = 1

        self.calibrate_mode = False
        self.alpha = None
        self.beta = None
        self.t = None
        self.z = None

    def size(self):
        return len(self.img_list)

    def mousePressEvent(self, event):
        print('Calibration: ' + str(self.calibrate_mode))
        if self.calibrate_mode is True:
            c_x, c_y = (event.x(), event.y())
            self.alpha, self.beta = alpha_beta(c_x, c_y)
            self.t = lp_projection_calibration(self.alpha, self.beta)
        elif self.t is not None:
            c_x, c_y = (event.x(), event.y())
            self.alpha, self.beta = alpha_beta(c_x, c_y)
            self.z = lp_projection(self.alpha, self.beta, self.t)
            print('Height (inches): ' + str(self.z))

    def setCalibrateMode(self):
        self.calibrate_mode = not self.calibrate_mode

    def boundEnd(self):
        self.endIdx = self.range_slider.end()

    def boundStart(self):
        self.startIdx = self.range_slider.start()
        self.idx = self.startIdx

    def setSkipRate(self, skip_rate):
        self.skip = skip_rate

    def setFrameRate(self, delay):
        self.delay = delay

    def setImgList(self, img_list):
        self.img_list = img_list
        self.endIdx = len(self.img_list)-1
        self.slider.setRange(0, len(self.img_list)-1)
        self.range_slider.setMax(len(self.img_list)-1)
        pixmap = QPixmap(self.img_list[self.idx]).scaled(600, 800, Qt.KeepAspectRatio, Qt.FastTransformation)
        #self.pixmap_list = [QPixmap(self.img_list[i]).scaled(600, 800, Qt.KeepAspectRatio, Qt.FastTransformation) for i in range(0, len(self.img_list))]
        self.label.setPixmap(pixmap)

    def showImage(self):
        if len(self.img_list) == 0:
            return
        self.idx = self.slider.value()
        pixmap = QPixmap(self.img_list[self.idx]).scaled(600, 800, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.label.setPixmap(pixmap)

    def showImage(self, idx):
        if len(self.img_list) == 0 or idx > len(self.img_list)-1:
            return
        self.idx = idx
        self.slider.setValue(idx)
        pixmap = QPixmap(self.img_list[idx]).scaled(600, 800, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.label.setPixmap(pixmap)

    def timerEvent(self, e=None):
        if len(self.img_list) == 0:
            return
        if self.idx > self.endIdx:
            self.timer.stop()
            self.idx = self.startIdx
            return
        self.timer.start(self.delay, self)
        self.showImage(self.idx)
        #self.label.setPixmap(self.pixmap_list[self.idx])
        self.slider.setValue(self.idx)
        self.idx += self.skip

    def pauseTimer(self):
        self.timer.stop()

    def stopTimer(self):
        self.timer.stop()
        self.startIdx = self.range_slider.start()
        self.idx = self.startIdx

    def fastForward(self):
        if len(self.img_list) == 0:
            return
        self.delay /= 2

    def slowdown(self):
        if len(self.img_list) == 0:
            return
        self.delay *= 2

