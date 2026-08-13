import sys
import ctypes
import numpy as np
from PyQt5.QtCore import QTimer,Qt
from PyQt5.QtWidgets import QApplication,QMainWindow,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QWidget,QDoubleSpinBox,QTableWidget,QTableWidgetItem,QMessageBox
import pyqtgraph as pg
from scipy.signal import find_peaks

SHM_KEY=0x1234
CHANNELS=1024

class SpectrumData(ctypes.Structure):
    _fields_=[("active",ctypes.c_int),("data",ctypes.c_float*CHANNELS)]

libc=ctypes.CDLL("libc.so.6")
libc.shmget.argtypes=[ctypes.c_int,ctypes.c_size_t,ctypes.c_int]
libc.shmget.restype=ctypes.c_int
libc.shmat.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_int]
libc.shmat.restype=ctypes.c_void_p
libc.shmdt.argtypes=[ctypes.c_void_p]
libc.shmdt.restype=ctypes.c_int

class PeakDetector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.shm_ptr=None
        self.shared=None
        self.peaks=np.array([])
        self.running=True
        self.connect_shared_memory()
        self.setup_ui()
        self.timer=QTimer()
        self.timer.timeout.connect(self.update_spectrum)
        self.timer.start(100)

    def connect_shared_memory(self):
        shmid=libc.shmget(SHM_KEY,ctypes.sizeof(SpectrumData),0o666)
        if shmid<0:
            QMessageBox.critical(self,"Shared Memory Error","Shared memory not found.\n\nStart the C Spectrum Generator first.")
            sys.exit(1)
        self.shm_ptr=libc.shmat(shmid,None,0)
        if self.shm_ptr is None or self.shm_ptr==ctypes.c_void_p(-1).value:
            QMessageBox.critical(self,"Memory Error","Failed to attach to shared memory.")
            sys.exit(1)
        self.shared=ctypes.cast(self.shm_ptr,ctypes.POINTER(SpectrumData))

    def setup_ui(self):
        self.setWindowTitle("Real-Time Spectrum Peak Detection")
        self.setGeometry(100,100,1150,800)

        widget=QWidget()
        self.setCentralWidget(widget)
        layout=QVBoxLayout(widget)

        widget.setStyleSheet("""
        QWidget{
            background:qlineargradient(
                x1:0,y1:0,x2:1,y2:1,
                stop:0 #07131F,
                stop:0.5 #101820,
                stop:1 #16232F
            );
        }

        QLabel{
            color:#E8F5E9;
            font-size:14px;
            font-weight:bold;
        }

        QDoubleSpinBox{
            background:#172A36;
            color:#00FF9C;
            border:1px solid #00E676;
            border-radius:10px;
            padding:7px;
            font-size:14px;
            font-weight:bold;
        }

        QTableWidget{
            background:#0D1922;
            color:#E8F5E9;
            gridline-color:#29404F;
            border:1px solid #29404F;
            border-radius:10px;
            font-size:13px;
        }

        QTableWidget::item:selected{
            background:#00695C;
        }

        QHeaderView::section{
            background:#173447;
            color:#00FF9C;
            padding:8px;
            border:none;
            font-weight:bold;
        }

        QPushButton{
            color:white;
            border:none;
            border-radius:16px;
            font-size:14px;
            font-weight:bold;
            padding:11px 24px;
        }
        """)

        self.plot=pg.PlotWidget()
        self.plot.setBackground("#050B10")
        self.plot.showGrid(x=True,y=True,alpha=0.15)
        self.plot.setLabel("bottom","Channel",color="#80CBC4",size="12pt")
        self.plot.setLabel("left","Counts",color="#80CBC4",size="12pt")
        self.plot.getAxis("bottom").setTextPen("#B2DFDB")
        self.plot.getAxis("left").setTextPen("#B2DFDB")
        self.plot.getAxis("bottom").setPen("#527A78")
        self.plot.getAxis("left").setPen("#527A78")
        self.plot.setXRange(0,CHANNELS)

        self.curve=self.plot.plot(
            pen=pg.mkPen("#00FF88",width=2)
        )

        layout.addWidget(self.plot)

        controls=QHBoxLayout()

        self.status=QLabel("● CONNECTED")
        self.status.setStyleSheet(
            "color:#00FF88;font-size:15px;font-weight:bold;"
        )

        self.threshold_label=QLabel("Noise Threshold:")

        self.threshold=QDoubleSpinBox()
        self.threshold.setRange(0,100000000)
        self.threshold.setValue(20)
        self.threshold.setDecimals(2)
        self.threshold.setSingleStep(5)
        self.threshold.setFixedWidth(120)

        self.start_btn=QPushButton("▶  Start")
        self.stop_btn=QPushButton("■  Stop")

        self.start_btn.setStyleSheet("""
        QPushButton{
            background:qlineargradient(
                x1:0,y1:0,x2:1,y2:1,
                stop:0 #00C853,
                stop:0.5 #00E676,
                stop:1 #69F0AE
            );
            border:1px solid #00FF88;
            color:#001B0D;
        }
        QPushButton:hover{
            background:qlineargradient(
                x1:0,y1:0,x2:1,y2:1,
                stop:0 #00E676,
                stop:0.5 #69F0AE,
                stop:1 #B9F6CA
            );
        }
        QPushButton:pressed{
            background:#00A843;
        }
        """)

        self.stop_btn.setStyleSheet("""
        QPushButton{
            background:qlineargradient(
                x1:0,y1:0,x2:1,y2:1,
                stop:0 #FF1744,
                stop:0.5 #F50057,
                stop:1 #FF5252
            );
            border:1px solid #FF4569;
        }
        QPushButton:hover{
            background:qlineargradient(
                x1:0,y1:0,x2:1,y2:1,
                stop:0 #FF5252,
                stop:0.5 #FF1744,
                stop:1 #FF80AB
            );
        }
        QPushButton:pressed{
            background:#B71C1C;
        }
        """)

        self.detect_btn=QPushButton("⚡ Detect Peaks")
        self.detect_btn.setStyleSheet("""
        QPushButton{
            background:qlineargradient(
                x1:0,y1:0,x2:1,y2:1,
                stop:0 #7B1FA2,
                stop:0.5 #9C27B0,
                stop:1 #E040FB
            );
        }
        QPushButton:hover{
            background:qlineargradient(
                x1:0,y1:0,x2:1,y2:1,
                stop:0 #9C27B0,
                stop:1 #EA80FC
            );
        }
        QPushButton:pressed{
            background:#6A1B9A;
        }
        """)

        self.clear_btn=QPushButton("Clear Peaks")
        self.clear_btn.setStyleSheet("""
        QPushButton{
            background:qlineargradient(
                x1:0,y1:0,x2:1,y2:1,
                stop:0 #455A64,
                stop:1 #78909C
            );
        }
        QPushButton:hover{
            background:#90A4AE;
        }
        QPushButton:pressed{
            background:#37474F;
        }
        """)

        controls.addWidget(self.status)
        controls.addStretch()
        controls.addWidget(self.threshold_label)
        controls.addWidget(self.threshold)
        controls.addWidget(self.detect_btn)
        controls.addWidget(self.clear_btn)
        controls.addWidget(self.start_btn)
        controls.addWidget(self.stop_btn)

        layout.addLayout(controls)

        self.info=QLabel("Waiting for spectrum...")
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setStyleSheet("""
        QLabel{
            color:#80CBC4;
            background:#0B1C27;
            border:1px solid #214353;
            border-radius:10px;
            padding:8px;
        }
        """)
        layout.addWidget(self.info)

        self.table=QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Channel","Peak Height"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.detect_btn.clicked.connect(self.detect_peaks)
        self.clear_btn.clicked.connect(self.clear_peaks)
        self.start_btn.clicked.connect(self.start_detection)
        self.stop_btn.clicked.connect(self.stop_detection)

    def update_spectrum(self):
        if not self.running:return

        try:
            if self.shared.contents.active==1:
                data=np.ctypeslib.as_array(self.shared.contents.data).copy().flatten()

                self.curve.setData(
                    np.arange(CHANNELS),
                    data
                )

                self.detect_peaks(data)

                self.status.setText("● RUNNING")
                self.status.setStyleSheet(
                    "color:#00FF88;font-size:15px;font-weight:bold;"
                )

        except Exception as e:
            self.status.setText("● MEMORY ERROR")
            self.status.setStyleSheet(
                "color:#FF5252;font-size:15px;font-weight:bold;"
            )
            print("Error:",e)

    def detect_peaks(self,data=None):
        if self.shared is None:return

        try:
            if data is None:
                data=np.ctypeslib.as_array(self.shared.contents.data).copy().flatten()

            threshold=self.threshold.value()

            peaks,_=find_peaks(
                data,
                height=threshold,
                distance=5,
                prominence=max(1,threshold*0.1)
            )

            self.peaks=peaks
            self.show_peaks(data)

            self.info.setText(
                f"Detected {len(peaks)} peaks  |  "
                f"Threshold: {threshold:.2f}"
            )

        except Exception as e:
            print("Peak detection error:",e)

    def show_peaks(self,data):
        self.clear_peak_markers()

        self.table.setRowCount(len(self.peaks))

        if len(self.peaks)>0:

            self.peak_scatter=pg.ScatterPlotItem(
                x=self.peaks,
                y=data[self.peaks],
                size=14,
                brush=pg.mkBrush("#FF1744"),
                pen=pg.mkPen("#FFFFFF",width=2)
            )

            self.plot.addItem(self.peak_scatter)

            for row,peak in enumerate(self.peaks):

                self.table.setItem(
                    row,
                    0,
                    QTableWidgetItem(str(peak))
                )

                self.table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        f"{data[peak]:.2f}"
                    )
                )

    def clear_peak_markers(self):
        if hasattr(self,"peak_scatter"):
            self.plot.removeItem(self.peak_scatter)
            del self.peak_scatter

    def clear_peaks(self):
        self.clear_peak_markers()
        self.peaks=np.array([])
        self.table.setRowCount(0)
        self.info.setText("Peak markers cleared.")

    def stop_detection(self):
        self.running=False
        self.timer.stop()
        self.status.setText("● STOPPED")
        self.status.setStyleSheet(
            "color:#FF5252;font-size:15px;font-weight:bold;"
        )
        self.info.setText(
            "Detection stopped. Press Start to resume."
        )

    def start_detection(self):
        if self.running:return
        self.running=True
        self.status.setText("● RUNNING")
        self.status.setStyleSheet(
            "color:#00FF88;font-size:15px;font-weight:bold;"
        )
        self.info.setText("Peak detection resumed.")
        self.timer.start(100)

    def closeEvent(self,event):
        self.timer.stop()

        if self.shm_ptr:
            libc.shmdt(self.shm_ptr)

        event.accept()

if __name__=="__main__":
    app=QApplication(sys.argv)
    window=PeakDetector()
    window.show()
    sys.exit(app.exec_())
