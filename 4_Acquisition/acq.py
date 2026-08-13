import sys
import mmap
import struct
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication,QMainWindow,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QWidget
import pyqtgraph as pg

SHARED_FILE="/dev/shm/detector_data"
SHARED_SIZE=8

class DetectorViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Detector")
        self.setGeometry(100,100,900,650)
        self.values=[]
        self.open_shared_memory()
        self.setup_ui()
        self.timer=QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(500)

    def open_shared_memory(self):
        try:
            self.fd=open(SHARED_FILE,"r+b")
            self.shm=mmap.mmap(self.fd.fileno(),SHARED_SIZE)
        except Exception as e:
            print("Shared memory error:",e)
            sys.exit(1)

    def setup_ui(self):
        widget=QWidget()
        self.setCentralWidget(widget)
        layout=QVBoxLayout(widget)

        widget.setStyleSheet("""
        QWidget{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #07131F,stop:0.5 #101820,stop:1 #16232F);}
        QLabel{color:#E8F5E9;font-size:18px;font-weight:bold;}
        QPushButton{color:white;border:none;border-radius:18px;font-size:16px;font-weight:bold;padding:12px 28px;}
        """)

        self.plot=pg.PlotWidget()
        self.plot.setBackground("#050B10")
        self.plot.showGrid(x=True,y=True,alpha=0.2)
        self.plot.setLabel("bottom","Sample",color="#80CBC4",size="12pt")
        self.plot.setLabel("left","Detector Count",color="#80CBC4",size="12pt")
        self.plot.getAxis("bottom").setTextPen("#B2DFDB")
        self.plot.getAxis("left").setTextPen("#B2DFDB")
        self.plot.getAxis("bottom").setPen("#527A78")
        self.plot.getAxis("left").setPen("#527A78")
        self.curve=self.plot.plot(pen=pg.mkPen("#00FF88",width=2))
        layout.addWidget(self.plot)

        self.count_label=QLabel("Detector Count: 0")
        self.count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.count_label)

        self.status_label=QLabel("● RUNNING")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color:#00FF88;font-size:16px;font-weight:bold;")
        layout.addWidget(self.status_label)

        controls=QHBoxLayout()

        self.start_btn=QPushButton("▶ Start")
        self.stop_btn=QPushButton("■ Stop")

        self.start_btn.setStyleSheet("""
        QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #00C853,stop:0.5 #00E676,stop:1 #69F0AE);color:#001B0D;border:1px solid #00FF88;}
        QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #00E676,stop:1 #B9F6CA);}
        QPushButton:pressed{background:#00A843;}
        """)

        self.stop_btn.setStyleSheet("""
        QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #FF1744,stop:0.5 #F50057,stop:1 #FF5252);border:1px solid #FF4569;}
        QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #FF5252,stop:1 #FF80AB);}
        QPushButton:pressed{background:#B71C1C;}
        """)

        controls.addStretch()
        controls.addWidget(self.start_btn)
        controls.addWidget(self.stop_btn)
        controls.addStretch()
        layout.addLayout(controls)

        self.start_btn.clicked.connect(self.start_generator)
        self.stop_btn.clicked.connect(self.stop_generator)

    def read_data(self):
        self.shm.seek(0)
        return struct.unpack("ii",self.shm.read(8))

    def write_running(self,value):
        self.shm.seek(4)
        self.shm.write(struct.pack("i",value))
        self.shm.flush()

    def update_data(self):
        try:
            count,running=self.read_data()
            if running:
                self.count_label.setText(f"Detector Count: {count}")
                self.values.append(count)
                if len(self.values)>100:
                    self.values.pop(0)
                self.curve.setData(self.values)
                self.status_label.setText("● RUNNING")
                self.status_label.setStyleSheet("color:#00FF88;font-size:16px;font-weight:bold;")
        except Exception as e:
            print("Read error:",e)

    def start_generator(self):
        self.write_running(1)
        self.status_label.setText("● RUNNING")
        self.status_label.setStyleSheet("color:#00FF88;font-size:16px;font-weight:bold;")

    def stop_generator(self):
        self.write_running(0)
        self.status_label.setText("● STOPPED")
        self.status_label.setStyleSheet("color:#FF5252;font-size:16px;font-weight:bold;")

    def closeEvent(self,event):
        self.timer.stop()
        self.shm.close()
        self.fd.close()
        event.accept()

if __name__=="__main__":
    from PyQt5.QtCore import Qt
    app=QApplication(sys.argv)
    window=DetectorViewer()
    window.show()
    sys.exit(app.exec_())
