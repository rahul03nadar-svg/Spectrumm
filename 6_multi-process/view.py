import ctypes
import sys
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
import pyqtgraph as pg

SHM_KEY = 0x5678
CHANNELS = 1024

class SpectrumData(ctypes.Structure):
    _fields_ = [("active", ctypes.c_int), ("data", ctypes.c_float * CHANNELS)]

libc = ctypes.CDLL("libc.so.6")
libc.shmget.argtypes = [ctypes.c_int, ctypes.c_size_t, ctypes.c_int]
libc.shmget.restype = ctypes.c_int
libc.shmat.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
libc.shmat.restype = ctypes.c_void_p
libc.shmdt.argtypes = [ctypes.c_void_p]
libc.shmdt.restype = ctypes.c_int

class SpectrumViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.shm_ptr = None
        self.shared = None
        self.connect_shared_memory()
        self.setup_ui()
        self.setup_timer()

    def connect_shared_memory(self):
        shmid = libc.shmget(SHM_KEY, ctypes.sizeof(SpectrumData), 0o666)
        if shmid < 0:
            print("Error: Processed shared memory not found.")
            print("Start generator and processor first.")
            sys.exit(1)
        self.shm_ptr = libc.shmat(shmid, None, 0)
        if self.shm_ptr is None or self.shm_ptr == ctypes.c_void_p(-1).value:
            print("Error: Failed to attach shared memory.")
            sys.exit(1)
        self.shared = ctypes.cast(self.shm_ptr, ctypes.POINTER(SpectrumData))

    def setup_ui(self):
        self.setWindowTitle("Real-Time Processed Spectrum")
        self.setGeometry(100, 100, 1000, 650)
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)
        widget.setStyleSheet("""
        QWidget {
            background-color: #101820;
        }
        QLabel {
            color: white;
            font-size: 15px;
            font-weight: bold;
        }
        """)
        self.plot = pg.PlotWidget()
        self.plot.setBackground("black")
        self.plot.setLabel("bottom", "Channel", color="white", size="12pt")
        self.plot.setLabel("left", "Counts", color="white", size="12pt")
        self.plot.getAxis("bottom").setTextPen("white")
        self.plot.getAxis("left").setTextPen("white")
        self.plot.getAxis("bottom").setPen("white")
        self.plot.getAxis("left").setPen("white")
        self.plot.setXRange(0, CHANNELS)
        self.curve = self.plot.plot(pen=pg.mkPen("lime", width=1.5))
        layout.addWidget(self.plot)
        controls = QHBoxLayout()
        self.status = QLabel("Processor: Waiting...")
        controls.addWidget(self.status)
        controls.addStretch()
        self.stop_button = QPushButton("Stop Viewer")
        self.stop_button.setStyleSheet("""
        QPushButton {
            background: qlineargradient(
                x1:0, y1:0,
                x2:1, y2:1,
                stop:0 #FF1414,
                stop:0.5 #E00028,
                stop:1 #FF6478
            );
            color: white;
            border: none;
            border-radius: 18px;
            font-size: 15px;
            font-weight: bold;
            padding: 10px 25px;
        }
        QPushButton:hover {
            background: qlineargradient(
                x1:0, y1:0,
                x2:1, y2:1,
                stop:0 #FF5252,
                stop:1 #FF1744
            );
        }
        QPushButton:pressed {
            background: #B71C1C;
        }
        """)
        self.stop_button.clicked.connect(self.close)
        controls.addWidget(self.stop_button)
        layout.addLayout(controls)

    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_spectrum)
        self.timer.start(16)

    def update_spectrum(self):
        try:
            if self.shared.contents.active == 1:
                data = list(self.shared.contents.data)
                self.curve.setData(data)
                self.status.setText("Processor: Running")
        except Exception as e:
            self.status.setText("Processor: Error")
            print("Viewer error:", e)

    def closeEvent(self, event):
        self.timer.stop()
        if self.shm_ptr: libc.shmdt(self.shm_ptr)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpectrumViewer()
    window.show()
    sys.exit(app.exec_())
