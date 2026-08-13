import os
os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"

import sys
import time
import ctypes
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg

# Connect to Linux
libc = ctypes.CDLL('libc.so.6')

# ARM64 
libc.shmget.argtypes = [ctypes.c_int, ctypes.c_size_t, ctypes.c_int]
libc.shmget.restype = ctypes.c_int
libc.shmat.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
libc.shmat.restype = ctypes.c_void_p
libc.shmdt.argtypes = [ctypes.c_void_p]
libc.shmdt.restype = ctypes.c_int

SHM_KEY = 0x1234
CHANNELS = 1024
SHM_SIZE = 4 + (CHANNELS * 4)

class CustomHoverButton(QPushButton):
    def __init__(self, text, base_color="#2c3e50", hover_color="#34495e"):
        super().__init__(text)
        self.base_color = base_color
        self.hover_color = hover_color
        self.set_custom_style(self.base_color)
        self.setCursor(Qt.PointingHandCursor)

    def set_custom_style(self, bg_color):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: #ffffff;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #1a252f;
            }}
        """)

    def enterEvent(self, event):
        self.set_custom_style(self.hover_color)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.set_custom_style(self.base_color)
        super().leaveEvent(event)


class AdvancedSpectrumPlayerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spectrum file player")
        self.setGeometry(100, 100, 950, 650)
        self.setStyleSheet("QMainWindow { background-color: #121212; }")

        self.shmid = libc.shmget(SHM_KEY, SHM_SIZE, 0o666)
        if self.shmid < 0:
            print("Error: Shared Memory block not ready. Start the C file player first!")
            sys.exit(1)
            
        self.shm_ptr = libc.shmat(self.shmid, None, 0)
        
        self.current_data = [0.0] * CHANNELS

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        self.hud_label = QLabel("Hover over the spectrum to view precise metrics [Channel, Amplitude]")
        self.hud_label.setStyleSheet("color: #e0e0e0; font-size: 13px; font-weight: bold; padding: 4px; background-color: #1e1e1e; border-radius: 4px;")
        self.layout.addWidget(self.hud_label)

        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setBackground('#111111')
        self.plot_graph.setYRange(0, 1900) 
        self.plot_graph.setXRange(0, CHANNELS)
        self.plot_graph.showGrid(x=True, y=True, alpha=0.2)
        
        self.curve = self.plot_graph.plot(pen=pg.mkPen('#2ecc71', width=2))
        self.peak_scatter = self.plot_graph.plot(pen=None, symbol='o', symbolSize=8, symbolBrush='#e74c3c')
        
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#95a5a6', width=1, style=Qt.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('#95a5a6', width=1, style=Qt.DashLine))
        self.plot_graph.addItem(self.v_line, ignoreBounds=True)
        self.plot_graph.addItem(self.h_line, ignoreBounds=True)
        
        self.layout.addWidget(self.plot_graph)
        self.plot_graph.scene().sigMouseMoved.connect(self.mouse_hover_tracking)

        self.control_layout = QHBoxLayout()
        self.status_label = QLabel("STATUS: STREAMING")
        self.status_label.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 14px; padding-right: 15px;")
        
        self.play_btn = CustomHoverButton("Play", base_color="#27ae60", hover_color="#2ece71")
        self.pause_btn = CustomHoverButton("Pause", base_color="#c0392b", hover_color="#e74c3c")
        self.restart_btn = CustomHoverButton("Restart", base_color="#2980b9", hover_color="#3498db")
        
        self.control_layout.addWidget(self.status_label)
        self.control_layout.addWidget(self.play_btn)
        self.control_layout.addWidget(self.pause_btn)
        self.control_layout.addWidget(self.restart_btn)
        self.layout.addLayout(self.control_layout)

        self.play_btn.clicked.connect(self.play_stream)
        self.pause_btn.clicked.connect(self.pause_stream)
        self.restart_btn.clicked.connect(self.restart_stream)

        self.timer = QTimer()
        self.timer.timeout.connect(self.read_shared_memory)
        self.timer.start(50)

    def read_shared_memory(self):
        try:
            data_ptr = ctypes.cast(ctypes.c_void_p(self.shm_ptr + 4), ctypes.POINTER(ctypes.c_float * CHANNELS))
            self.current_data = list(data_ptr.contents)
            
            self.curve.setData(self.current_data)

            peaks_x = []
            peaks_y = []
            for i in range(1, CHANNELS - 1):
                if self.current_data[i] > self.current_data[i-1] and self.current_data[i] > self.current_data[i+1]:
                    if self.current_data[i] > 100: # Ignore base floor noise spikes
                        peaks_x.append(i)
                        peaks_y.append(self.current_data[i])

            self.peak_scatter.setData(peaks_x, peaks_y)

        except Exception as e:
            print(f"Read error: {e}")

    def mouse_hover_tracking(self, pos):
        if self.plot_graph.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_graph.plotItem.vb.mapSceneToView(pos)
            index = int(mouse_point.x())
            
            if 0 <= index < len(self.current_data):
                amplitude_val = self.current_data[index]
                
                self.v_line.setPos(mouse_point.x())
                self.h_line.setPos(amplitude_val)
                
                self.hud_label.setText(f"🎯 CURRENT VALUE -> Channel Index: {index} | Signal Amplitude: {amplitude_val:.2f}")

    def play_stream(self):
        ctypes.cast(ctypes.c_void_p(self.shm_ptr), ctypes.POINTER(ctypes.c_int)).contents.value = 1
        self.status_label.setText("STATUS: STREAMING")
        self.status_label.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 14px;")

    def pause_stream(self):
        ctypes.cast(ctypes.c_void_p(self.shm_ptr), ctypes.POINTER(ctypes.c_int)).contents.value = 0
        self.status_label.setText("STATUS: PAUSED")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 14px;")

    def restart_stream(self):
        ctypes.cast(ctypes.c_void_p(self.shm_ptr), ctypes.POINTER(ctypes.c_int)).contents.value = 2
        self.status_label.setText("STATUS: RESTARTED")
        self.status_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 14px;")

    def closeEvent(self, event):
        libc.shmdt(ctypes.c_void_p(self.shm_ptr))
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvancedSpectrumPlayerGUI()
    window.show()
    sys.exit(app.exec_())

