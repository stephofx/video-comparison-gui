import sys
import os
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from qrangeslider import QRangeSlider

class WorkerSignals(QObject):
    idx = pyqtSignal(int)


class DelayWorker(QRunnable):

    def __init__(self, *args, **kwargs):
        super(DelayWorker, self).__init__()
        self.startIdx = args[0]
        self.endIdx = args[1]
        self.stop = False
        self.kwargs = kwargs
        self.signals = WorkerSignals()


    @pyqtSlot()
    def run(self):
        for idx in range(self.startIdx, self.endIdx+1, self.kwargs['skip']):
            if self.stop:
                break
            self.signals.idx.emit(idx)
            time.sleep(self.kwargs['delay']/1000)


class VideoFrame(QWidget):

    def __init__(self, *args, **kwargs):
        super(VideoFrame, self).__init__(*args, **kwargs)
        self.layout = QVBoxLayout()
        self.img_list = []

        # VIDEO LABEL AREA
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
        self.ff.setGeometry(480, 370, 50, 30)
        self.ff.clicked.connect(self.fastForward)
        self.layout.addWidget(self.ff)

        # SLOWDOWN
        self.fr = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'fr.png'))
        self.fr.setIcon(QIcon(icon))
        self.fr.setGeometry(240, 370, 50, 30)
        self.fr.clicked.connect(self.slowdown)
        self.layout.addWidget(self.fr)

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
        self.endIdx = 0
        self.idx = 0
        self.delay = 1000
        self.skip = 1

        self.threadpool = QThreadPool()
        self.thread = None

    def size(self):
        return len(self.img_list)

    def boundEnd(self):
        self.endIdx = self.range_slider.end()

    def boundStart(self):
        self.startIdx = self.range_slider.start()
        self.idx = self.startIdx

    def setSkipRate(self, skip_rate):
        self.skip = skip_rate
        if self.thread is not None:
            self.thread.kwargs['skip'] = self.delay/1000

    def setFrameRate(self, delay):
        self.delay = delay
        if self.thread is not None:
            self.thread.kwargs['delay'] = self.delay/1000

    def setImgList(self, img_list):
        self.img_list = img_list
        self.endIdx = len(self.img_list)-1
        self.slider.setRange(0, len(self.img_list)-1)
        self.range_slider.setMax(len(self.img_list)-1)
        pixmap = QPixmap(self.img_list[self.idx]).scaled(600, 800, Qt.KeepAspectRatio, Qt.FastTransformation)
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

    def timerEvent(self):
        self.thread = DelayWorker(self.startIdx, self.endIdx,
                                delay=self.delay, skip=self.skip)
        self.thread.signals.idx.connect(self.showImage)
        self.threadpool.start(self.thread)
        # if len(self.img_list) == 0:
        #     return
        # if self.idx > self.endIdx:
        #     self.timer.stop()
        #     self.idx = self.startIdx
        #     return
        # self.timer.start(self.delay, self)
        # pixmap = QPixmap(self.img_list[self.idx]).scaled(600, 800, Qt.KeepAspectRatio, Qt.FastTransformation)
        # self.label.setPixmap(pixmap)
        # self.slider.setValue(self.idx)
        # self.idx += self.skip

    def pauseTimer(self):
        self.thread.stop = True
        self.startIdx = self.idx

    def fastForward(self):
        if len(self.img_list) == 0:
            return
        self.thread.kwargs['delay'] /= 2

    def slowdown(self):
        if len(self.img_list) == 0:
            return
        self.thread.kwargs['delay'] *= 2
