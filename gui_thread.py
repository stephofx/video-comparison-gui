import sys
import os
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from qrangeslider import QRangeSlider
from VideoFrame import VideoFrame, DelayWorker

class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'plant.png')))

        self.setWindowTitle("Video Comparison GUI")
        self.statusBar()
        self.img_list = None
        self.cur_video_id = 0

        self.layout = QGridLayout()
        # Main Widget Init
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)
        self.setGeometry(250, 50, 1920, 1080)

        # Open File Dialog
        openFile = QAction('Open Image Directory', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open Image Directory')
        openFile.triggered.connect(self.fileDialog)

        change_framerate = QAction('Change Framerate...', self)
        change_framerate.setStatusTip('Change Playback Framerate of Video (default: 1 frame/sec)')
        change_framerate.triggered.connect(self.setFrameRate)

        change_skiprate = QAction('Change Skip Rate...', self)
        change_skiprate.setStatusTip('Change Frame Skip Rate in Selected Photos (default: 1)')
        change_skiprate.triggered.connect(self.setSkipRate)

        set_v_1 = QAction('Video 1...', self)
        set_v_1.setStatusTip('Set Video 1 (Top Left Corner) Settings')
        set_v_1.triggered.connect(self.setv1)

        set_v_2 = QAction('Video 2...', self)
        set_v_2.setStatusTip('Set Video 2 (Top Right Corner) Settings')
        set_v_2.triggered.connect(self.setv2)

        set_v_3 = QAction('Video 3...', self)
        set_v_3.setStatusTip('Set Video 3 (Bottom Left Corner) Settings')
        set_v_3.triggered.connect(self.setv3)

        set_v_4 = QAction('Video 4...', self)
        set_v_4.setStatusTip('Set Video 4 (Bottom Right Corner) Settings')
        set_v_4.triggered.connect(self.setv4)

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(openFile)
        edit_menu = menubar.addMenu('&Edit')
        edit_menu.addAction(change_framerate)
        edit_menu.addAction(change_skiprate)
        video_menu = menubar.addMenu('&Video')
        video_menu.addAction(set_v_1)
        video_menu.addAction(set_v_2)
        video_menu.addAction(set_v_3)
        video_menu.addAction(set_v_4)

        # Video Frame Objects
        self.v1 = VideoFrame()
        self.layout.addWidget(self.v1, 0, 0, 1, 2)
        self.v2 = VideoFrame()
        self.layout.addWidget(self.v2, 0, 2, 1, 2)
        self.v3 = VideoFrame()
        self.layout.addWidget(self.v3, 1, 0, 1, 2)
        self.v4 = VideoFrame()
        self.layout.addWidget(self.v4, 1, 2, 1, 2)
        self.video_list = [self.v1, self.v2, self.v3, self.v4]

        ## STREAM 1 LABEL AREA
        #self.label = QLabel('Nothing to show right now.')
        #self.label.setAlignment(Qt.AlignCenter)
        #self.layout.addWidget(self.label)

        self.bottomLayout = QVBoxLayout()

        # GLOBAL PLAY BUTTON
        #self.play = QPushButton("Play")
        #self.play.clicked.connect(self.timerEvent)
        #self.bottomLayout.addWidget(self.play)

        # SLOWDOWN
        self.fr = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'fr.png'))
        self.fr.setIcon(QIcon(icon))
        self.fr.clicked.connect(self.slowdown)
        self.layout.addWidget(self.fr, 2, 0, 1, 1)

        # GLOBAL PLAY BUTTON
        self.play = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'play.png'))
        self.play.setIcon(QIcon(icon))
        self.play.clicked.connect(self.playVideos)
        self.layout.addWidget(self.play, 2, 1, 1, 1)

        # GLOBAL PAUSE BUTTON
        self.pause = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'pause.png'))
        self.pause.setIcon(QIcon(icon))
        self.pause.clicked.connect(self.pauseTimer)
        self.layout.addWidget(self.pause, 2, 2, 1, 1)

        # GLOBAL FAST-FORWARD
        self.ff = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'ff.png'))
        self.ff.setIcon(QIcon(icon))
        self.ff.clicked.connect(self.fastForward)
        self.layout.addWidget(self.ff, 2, 3, 1, 1)


        # GLOBAL SLIDER
        self.slider = QSlider(Qt.Horizontal)
        self.bottomLayout.addWidget(self.slider)
        self.slider.valueChanged.connect(self.showImage)

        # GLOBAL RANGE SLIDER
        self.range_slider = QRangeSlider()
        self.range_slider.setFixedHeight(20)
        self.bottomLayout.addWidget(self.range_slider)
        self.range_slider.endValueChanged.connect(self.boundEnd)
        self.range_slider.startValueChanged.connect(self.boundStart)

        self.layout.addLayout(self.bottomLayout, 3, 0, 1, 4)

        self.timer = QBasicTimer() # FIXME consider something with less lag
        self.startIdx = 0
        self.idx = 0
        self.delay = 1000
        self.skip = 1

        self.threadpool = QThreadPool()

    def fileDialog(self):
        self.img_list, _ = QFileDialog.getOpenFileNames(self,
                                                   'Select one or more files to open',
                                                   '/home', 'Images (*.jpg)')
        self.img_list.sort()
        self.video_list[self.cur_video_id].setImgList(self.img_list)
        self.endIdx = max(self.video_list, key=lambda end: end.size()-1)
        self.endIdx = self.endIdx.size()-1
        self.slider.setRange(0, self.endIdx)
        self.range_slider.setMax(self.endIdx)

    def playVideos(self):
        #v1_thread = DelayWorker(self.v1.startIdx, self.v1.endIdx,
        #                        delay=self.v1.delay, skip=self.v1.skip)
        #v1_thread.signals.idx.connect(self.v1.showImage)
        #v2_thread = DelayWorker(self.v2.startIdx, self.v2.endIdx,
        #                        delay=self.v2.delay, skip=self.v2.skip)
        #v2_thread.signals.idx.connect(self.v2.showImage)
        #v3_thread = DelayWorker(self.v3.startIdx, self.v3.endIdx,
        #                        delay=self.v3.delay, skip=self.v3.skip)
        #v3_thread.signals.idx.connect(self.v3.showImage)
        #v4_thread = DelayWorker(self.v4.startIdx, self.v4.endIdx,
        #                        delay=self.v4.delay, skip=self.v4.skip)
        #v4_thread.signals.idx.connect(self.v4.showImage)
        #self.threadpool.start(v1_thread)
        #self.threadpool.start(v2_thread)
        #self.threadpool.start(v3_thread)
        #self.threadpool.start(v4_thread)
        #self.threadpool.start(v2_thread)
        self.v1.timerEvent()
        self.v2.timerEvent()
        self.v3.timerEvent()
        self.v4.timerEvent()
        #self.slider.setValue(self.idx)
        #self.idx += self.skip

    def showImage(self):
        self.idx = self.slider.value()
        for i in range(len(self.video_list)):
            self.video_list[i].showImage(self.idx)

    def setFrameRate(self):
        delay, _ = QInputDialog.getDouble(self, 'Change Framerate...',
                                         'New Framerate (frames/second)',
                                         1000/self.delay, 1, 100, 1)
        self.delay = 1000.0/delay
        self.video_list[self.cur_video_id].setFrameRate(self.delay)

    def setSkipRate(self):
        self.skip, _ = QInputDialog.getInt(self, 'Change Skip Rate...',
                                         'New Skip Rate', self.skip, 1, 100, 1)
        self.video_list[self.cur_video_id].setSkipRate(self.skip)

    def boundEnd(self):
        self.endIdx = self.range_slider.end()

    def boundStart(self):
        self.startIdx = self.range_slider.start()
        self.idx = self.startIdx

    def setv1(self):
        self.cur_video_id = 0
        self.statusBar().showMessage(f'Selected Video {self.cur_video_id+1}')

    def setv2(self):
        self.cur_video_id = 1
        self.statusBar().showMessage(f'Selected Video {self.cur_video_id+1}')

    def setv3(self):
        self.cur_video_id = 2
        self.statusBar().showMessage(f'Selected Video {self.cur_video_id+1}')

    def setv4(self):
        self.cur_video_id = 3
        self.statusBar().showMessage(f'Selected Video {self.cur_video_id+1}')

    def pauseTimer(self):
        for i in range(len(self.video_list)):
            self.video_list[i].pauseTimer()

    def fastForward(self):
        for i in range(len(self.video_list)):
            self.video_list[i].fastForward()

    def slowdown(self):
        for i in range(len(self.video_list)):
            self.video_list[i].slowdown()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    app.exec_()
