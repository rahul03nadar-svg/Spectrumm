import os
import struct
import sys
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
import pyqtgraph as pg

CHANNELS = 1024
INPUT_FILE = "../data/spectrum.bin"
FRAME_SIZE = 4 + 8 + CHANNELS * 4

class SpectrumReplay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file = None
        self.current_frame = 0
        self.total_frames = 0
        self.setWindowTitle("Spectrum Data Replay")
        self.setGeometry(100, 100, 1000, 650)
        self.setup_ui()
        self.load_file()
        self.timer = QTimer()
        self.timer.timeout.connect(self.display_frame)
        self.timer.setInterval(16)

    def setup_ui(self):
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
        self.frame_label = QLabel("Frame: 0 / 0")
        self.play = QPushButton("▶ Play")
        self.pause = QPushButton("⏸ Pause")
        self.restart = QPushButton("↻ Restart")
        controls.addWidget(self.frame_label)
        controls.addStretch()
        controls.addWidget(self.play)
        controls.addWidget(self.pause)
        controls.addWidget(self.restart)
        layout.addLayout(controls)
        self.style_buttons()
        self.play.clicked.connect(self.play_replay)
        self.pause.clicked.connect(self.pause_replay)
        self.restart.clicked.connect(self.restart_replay)

    def style_buttons(self):
        self.play.setStyleSheet("""
        QPushButton {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #00A83B, stop:0.5 #00D95F, stop:1 #39FF88
            );
            color: white;
            border: 2px solid #00FF66;
            border-radius: 18px;
            font-size: 15px;
            font-weight: bold;
            padding: 10px 25px;
        }
        QPushButton:hover {
            background: #00FF75;
        }
        QPushButton:pressed {
            background: #008F3A;
        }
        """)
        self.pause.setStyleSheet("""
        QPushButton {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #FF8F00, stop:1 #FFC107
            );
            color: white;
            border: none;
            border-radius: 18px;
            font-size: 15px;
            font-weight: bold;
            padding: 10px 25px;
        }
        QPushButton:hover {
            background: #FFB300;
        }
        """)
        self.restart.setStyleSheet("""
        QPushButton {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #1976D2, stop:1 #00B0FF
            );
            color: white;
            border: none;
            border-radius: 18px;
            font-size: 15px;
            font-weight: bold;
            padding: 10px 25px;
        }
        QPushButton:hover {
            background: #29B6F6;
        }
        """)

    def load_file(self):
        if not os.path.exists(INPUT_FILE):
            print(f"Error: {INPUT_FILE} not found.")
            return
        self.file = open(INPUT_FILE, "rb")
        size = os.path.getsize(INPUT_FILE)
        self.total_frames = size // FRAME_SIZE
        print(f"Loaded {self.total_frames} spectra.")
        self.frame_label.setText(f"Frame: 0 / {self.total_frames}")

    def read_frame(self):
        if self.file is None or self.current_frame >= self.total_frames:
            return None
        self.file.seek(self.current_frame * FRAME_SIZE)
        data = self.file.read(FRAME_SIZE)
        if len(data) != FRAME_SIZE:
            return None
        frame = struct.unpack("I", data[:4])[0]
        timestamp = struct.unpack("d", data[4:12])[0]
        spectrum = struct.unpack(f"{CHANNELS}f", data[12:])
        return frame, timestamp, spectrum

    def display_frame(self):
        result = self.read_frame()
        if result is None:
            self.pause_replay()
            return
        frame, timestamp, spectrum = result
        self.curve.setData(spectrum)
        self.frame_label.setText(f"Frame: {frame + 1} / {self.total_frames}")
        self.current_frame += 1

    def play_replay(self):
        if self.total_frames:
            self.timer.start()

    def pause_replay(self):
        self.timer.stop()

    def restart_replay(self):
        self.timer.stop()
        self.current_frame = 0
        self.curve.clear()
        self.frame_label.setText(f"Frame: 0 / {self.total_frames}")

    def closeEvent(self, event):
        self.timer.stop()
        if self.file:
            self.file.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpectrumReplay()
    window.show()
    sys.exit(app.exec_())
