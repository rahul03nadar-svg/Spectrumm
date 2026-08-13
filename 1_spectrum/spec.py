import os
os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"

import sys
import time
import ctypes
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget
from PyQt5.QtCore import QTimer
import pyqtgraph as pg

libc = ctypes.CDLL('libc.so.6')
libc.shmget.argtypes = [ctypes.c_int, ctypes.c_size_t, ctypes.c_int]
libc.shmget.restype = ctypes.c_int

libc.shmat.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
libc.shmat.restype = ctypes.c_void_p  

libc.shmdt.argtypes = [ctypes.c_void_p]
libc.shmdt.restype = ctypes.c_int

SHM_KEY = 0x1234
CHANNELS = 1024
SHM_SIZE = 4 + (CHANNELS * 4) 

class SpectrumVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Spectrum Visualizer")
        self.setGeometry(100, 100, 800, 600)

        self.shmid = libc.shmget(SHM_KEY, SHM_SIZE, 0o666)
        if self.shmid < 0:
            print("Error: Cannot find Shared Memory")
            sys.exit(1)
            
        self.shm_ptr = libc.shmat(self.shmid, None, 0)
        if self.shm_ptr == -1 or self.shm_ptr is None:
            print("Error: Failed to attach to shared memory.")
            sys.exit(1)
        
        self.last_time = time.time()
        self.frame_count = 0

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)
        self.main_widget.setStyleSheet("""
    QWidget {
        background-color: #101820;
    }
""")
        
     
        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setBackground('k')
        self.plot_graph.setLabel('bottom','Channel', color='white', size='12pt')
        self.plot_graph.setLabel('left','Counts', color='white', size='12pt')
        self.plot_graph.getAxis('bottom').setTextPen('white')
        self.plot_graph.getAxis('left').setTextPen('white')
        self.plot_graph.getAxis('bottom').setPen('white')
        self.plot_graph.getAxis('left').setPen('white')
        self.plot_graph.setYRange(0, 160)
        self.plot_graph.setXRange(0, CHANNELS)
        self.curve = self.plot_graph.plot(pen=pg.mkPen('g', width=1.0))
        self.layout.addWidget(self.plot_graph)
        self.plot_graph.setBackground('k')

        self.control_layout = QHBoxLayout()
        self.fps_label = QLabel("Update Rate: 0 FPS")
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        
        self.start_btn.setStyleSheet("""
    QPushButton {
       background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
    stop:0 rgba(0, 255, 100, 190),
    stop:0.5 rgba(0, 220, 80, 150),
    stop:1 rgba(100, 255, 170, 190)
    );
    color:white;
    border:none;
    border-radius:18px;
    font-size:16px;
    font-weight:bold;
    padding:12px;
    }

    QPushButton:hover {
        background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #00E676,
        stop:1 #76FF03
    );
    }

    QPushButton:pressed {
        background:#00A843;
    }
""")
        self.stop_btn.setStyleSheet("""
    QPushButton {
      
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
    stop:0 rgba(255, 20, 60, 190),
    stop:0.5 rgba(220, 0, 40, 150),
    stop:1 rgba(255, 100, 120, 190)
    );
    color:white;
    border:none;
    border-radius:18px;
    font-size:16px;
    font-weight:bold;
    padding:12px;
    }

    QPushButton:hover {
        background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #FF5252,
        stop:1 #FF1744
    );
    }

    QPushButton:pressed {
        background:#B71C1C;
    }
""")
        

        self.control_layout.addWidget(self.fps_label)
        self.control_layout.addWidget(self.start_btn)
        self.control_layout.addWidget(self.stop_btn)
        self.layout.addLayout(self.control_layout)

        self.start_btn.clicked.connect(self.start_generator)
        self.stop_btn.clicked.connect(self.stop_generator)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_spectrum)
        self.timer.start(1000)

    def update_spectrum(self):
        try:

            is_active = ctypes.cast(ctypes.c_void_p(self.shm_ptr), ctypes.POINTER(ctypes.c_int)).contents.value
            
            if is_active == 1:

                data_ptr = ctypes.cast(ctypes.c_void_p(self.shm_ptr + 4), ctypes.POINTER(ctypes.c_float * CHANNELS))
                self.curve.setData(list(data_ptr.contents))

            self.frame_count += 1
            now = time.time()
            elapsed = now - self.last_time
            if elapsed >= 1.0:
                self.fps_label.setText(f"Update Rate: {int(self.frame_count / elapsed)} FPS")
                self.frame_count = 0
                self.last_time = now
        except Exception as e:
            print(f"Error reading memory: {e}")

    def start_generator(self):
        ctypes.cast(ctypes.c_void_p(self.shm_ptr), ctypes.POINTER(ctypes.c_int)).contents.value = 1

    def stop_generator(self):
        ctypes.cast(ctypes.c_void_p(self.shm_ptr), ctypes.POINTER(ctypes.c_int)).contents.value = 0

    def closeEvent(self, event):
        libc.shmdt(ctypes.c_void_p(self.shm_ptr))
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpectrumVisualizer()
    window.show()
    sys.exit(app.exec_())

