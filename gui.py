import sys
import os
import time
from multiprocessing import Process
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from ffmpy import FFmpeg

from qrangeslider import QRangeSlider
from VideoFrame import VideoFrame

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

        change_calibrate = QAction('Turn Calibration On/Off...', self)
        change_calibrate.setStatusTip('Calibrate auto height detection to plant pot')
        change_calibrate.triggered.connect(self.calibrate)

        export_video = QAction('Export Video...', self)
        export_video.setStatusTip('Export the current video frame with current settings')
        export_video.triggered.connect(self.export)

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(openFile)
        file_menu.addAction(export_video)
        edit_menu = menubar.addMenu('&Edit')
        edit_menu.addAction(change_framerate)
        edit_menu.addAction(change_skiprate)
        video_menu = menubar.addMenu('&Video')
        video_menu.addAction(set_v_1)
        video_menu.addAction(set_v_2)
        video_menu.addAction(set_v_3)
        video_menu.addAction(set_v_4)
        calibrate_menu = menubar.addMenu('&Calibrate')
        calibrate_menu.addAction(change_calibrate)

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
        #self.fr = QPushButton(self)
        #icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'fr.png'))
        #self.fr.setIcon(QIcon(icon))
        #self.fr.clicked.connect(self.slowdown)
        #self.layout.addWidget(self.fr, 2, 0, 1, 1)

        # GLOBAL PLAY BUTTON
        self.play = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'play.png'))
        self.play.setIcon(QIcon(icon))
        self.play.clicked.connect(self.timerEvent)
        self.layout.addWidget(self.play, 2, 0, 1, 1)

        # GLOBAL PAUSE BUTTON
        self.pause = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'pause.png'))
        self.pause.setIcon(QIcon(icon))
        self.pause.clicked.connect(self.pauseTimer)
        self.layout.addWidget(self.pause, 2, 1, 1, 1)

        # GLOBAL FAST-FORWARD
        self.ff = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'ff.png'))
        self.ff.setIcon(QIcon(icon))
        self.ff.clicked.connect(self.fastForward)
        self.layout.addWidget(self.ff, 2, 3, 1, 1)

        # GLOBAL STOP
        self.stop = QPushButton(self)
        icon = QPixmap(os.path.join(os.path.dirname(__file__), 'icons', 'stop.png'))
        self.stop.setIcon(QIcon(icon))
        self.stop.clicked.connect(self.stopTimer)
        self.layout.addWidget(self.stop, 2, 2, 1, 1)

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

    def fileDialog(self):
        self.img_list, _ = QFileDialog.getOpenFileNames(self,
                                                   'Select one or more files to open',
                                                   '/home', 'Images (*.jpg)')
        self.img_list.sort()
        if len(self.img_list) == 0:
            return
        self.video_list[self.cur_video_id].setImgList(self.img_list)
        self.endIdx = max(self.video_list, key=lambda end: end.size()-1)
        self.endIdx = self.endIdx.size()-1
        self.slider.setRange(0, self.endIdx)
        self.range_slider.setMax(self.endIdx)

    def timerEvent(self):
        self.v1.timerEvent()
        self.v2.timerEvent()
        self.v3.timerEvent()
        self.v4.timerEvent()
        p1 = Process(target=self.v1.timerEvent(), args=())
        p2 = Process(target=self.v2.timerEvent(), args=())
        p3 = Process(target=self.v3.timerEvent(), args=())
        p4 = Process(target=self.v4.timerEvent(), args=())
        p1.start()
        p2.start()
        p3.start()
        p4.start()
        p1.join()
        p2.join()
        p3.join()
        p4.join()
        self.slider.setValue(self.idx)
        self.idx += self.skip

    def showImage(self):
        self.idx = self.slider.value()
        for i in range(len(self.video_list)):
            self.video_list[i].showImage(self.idx)

    def setFrameRate(self):
        delay, _ = QInputDialog.getDouble(self, 'Change Output Framerate...',
                                         'New Framerate (frames/second)',
                                         1000/self.delay, 1, 100, 1)
        self.delay = 1000.0/delay
        self.video_list[self.cur_video_id].setFrameRate(self.delay)

    def setSkipRate(self):
        self.skip, _ = QInputDialog.getInt(self, 'Change Skip Rate...',
                                         'New Skip Rate', self.skip, 1, 10000, 1)
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

    def stopTimer(self):
        for i in range(len(self.video_list)):
            self.video_list[i].stopTimer()

    def fastForward(self):
        for i in range(len(self.video_list)):
            self.video_list[i].fastForward()

    def slowdown(self):
        for i in range(len(self.video_list)):
            self.video_list[i].slowdown()

    def calibrate(self):
        self.video_list[self.cur_video_id].setCalibrateMode()

    def export(self):
        with open('imglist.txt', 'w') as file_list:
            for idx in range(self.video_list[self.cur_video_id].startIdx, len(self.video_list[self.cur_video_id].img_list), self.video_list[self.cur_video_id].skip):
                print(f'file \'{self.video_list[self.cur_video_id].img_list[idx]}\'', file=file_list)
        framerate = 1000/self.video_list[self.cur_video_id].delay
        if framerate == 1:
            ff = FFmpeg(inputs={'imglist.txt': f'-f concat -safe 0 -r 1'},
                    outputs={'timelapse.mp4': f'-vf "fps={framerate}" -c:v libx264'})
        else:
            ff = FFmpeg(inputs={'imglist.txt': f'-f concat -safe 0'},
                    outputs={'timelapse.mp4': f'-vf "fps={framerate}" -c:v libx264'})
        print(ff.cmd)
        ff.run()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    app.exec_()
