import sys
import csv
import numpy as np
from PyQt5.QtWidgets import QApplication,QMainWindow,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QFileDialog,QWidget,QMessageBox
from PyQt5.QtCore import Qt
import pyqtgraph as pg
from scipy.optimize import curve_fit

def gaussian(x,amplitude,mean,stddev):
    return amplitude*np.exp(-(x-mean)**2/(2*stddev**2))

class GaussianFitting(QMainWindow):
    def __init__(self):
        super().__init__()
        self.x=np.array([])
        self.y=np.array([])
        self.fit_curve=None
        self.region=None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Gaussian Peak Fitting")
        self.setGeometry(100,100,1100,750)
        widget=QWidget()
        self.setCentralWidget(widget)
        layout=QVBoxLayout(widget)
        widget.setStyleSheet("""
        QWidget{background-color:#101820;}
        QLabel{color:white;font-size:14px;font-weight:bold;}
        QPushButton{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1976D2,stop:1 #00B0FF);
            color:white;border:none;border-radius:15px;
            font-size:14px;font-weight:bold;padding:10px 20px;
        }
        QPushButton:hover{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #2196F3,stop:1 #40C4FF);
        }
        QPushButton:pressed{background:#0D47A1;}
        """)
        self.plot=pg.PlotWidget()
        self.plot.setBackground("black")
        self.plot.setLabel("bottom","Channel",color="white",size="12pt")
        self.plot.setLabel("left","Counts",color="white",size="12pt")
        self.plot.getAxis("bottom").setTextPen("white")
        self.plot.getAxis("left").setTextPen("white")
        self.plot.getAxis("bottom").setPen("white")
        self.plot.getAxis("left").setPen("white")
        self.curve=self.plot.plot(pen=pg.mkPen("lime",width=1.5))
        layout.addWidget(self.plot)
        controls=QHBoxLayout()
        self.load_btn=QPushButton("Load Spectrum")
        self.fit_btn=QPushButton("Fit Gaussian")
        self.clear_btn=QPushButton("Clear Fit")
        self.save_btn=QPushButton("Save Parameters")
        controls.addWidget(self.load_btn)
        controls.addWidget(self.fit_btn)
        controls.addWidget(self.clear_btn)
        controls.addWidget(self.save_btn)
        layout.addLayout(controls)
        self.info=QLabel("Load a spectrum and select a fitting region.")
        self.info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info)
        self.residual_plot=pg.PlotWidget()
        self.residual_plot.setBackground("black")
        self.residual_plot.setLabel("bottom","Channel",color="white",size="12pt")
        self.residual_plot.setLabel("left","Residual",color="white",size="12pt")
        self.residual_plot.getAxis("bottom").setTextPen("white")
        self.residual_plot.getAxis("left").setTextPen("white")
        self.residual_plot.getAxis("bottom").setPen("white")
        self.residual_plot.getAxis("left").setPen("white")
        layout.addWidget(self.residual_plot)
        self.load_btn.clicked.connect(self.load_file)
        self.fit_btn.clicked.connect(self.fit_gaussian)
        self.clear_btn.clicked.connect(self.clear_fit)
        self.save_btn.clicked.connect(self.save_parameters)
        self.plot.scene().sigMouseClicked.connect(self.mouse_click)

    def load_file(self):
        filename,_=QFileDialog.getOpenFileName(self,"Open Spectrum","","Data Files (*.txt *.csv)")
        if not filename:return
        try:
            data=np.loadtxt(filename,delimiter=",")
            if data.ndim==1:
                self.y=data
                self.x=np.arange(len(self.y))
            else:
                self.x=data[:,0]
                self.y=data[:,1]
            self.curve.setData(self.x,self.y)
            self.info.setText("Spectrum loaded. Click two points on the graph to select fitting region.")
            self.clear_fit()
        except Exception as e:
            QMessageBox.critical(self,"Error",f"Could not load file:\n{e}")

    def mouse_click(self,event):
        if event.button()!=Qt.LeftButton or len(self.x)==0:return
        position=self.plot.plotItem.vb.mapSceneToView(event.scenePos())
        x_value=position.x()
        if self.region is None:
            self.region=[x_value,None]
            self.info.setText(f"Start selected: {x_value:.2f}. Select the second point.")
        else:
            self.region[1]=x_value
            self.info.setText(f"Region selected: {min(self.region):.2f} to {max(self.region):.2f}. Click Fit Gaussian.")
        if self.region[0] is not None and self.region[1] is not None:
            if hasattr(self,"selection"):
                self.plot.removeItem(self.selection)
            self.selection=pg.LinearRegionItem(sorted(self.region))
            self.selection.setBrush(pg.mkBrush(0,150,255,50))
            self.plot.addItem(self.selection)

    def fit_gaussian(self):
        if len(self.x)==0:
            QMessageBox.warning(self,"Warning","Load a spectrum first.")
            return
        if self.region is None or self.region[1] is None:
            QMessageBox.warning(self,"Warning","Select a fitting region first.")
            return
        low,high=sorted(self.region)
        mask=(self.x>=low)&(self.x<=high)
        xfit=self.x[mask]
        yfit=self.y[mask]
        if len(xfit)<5:
            QMessageBox.warning(self,"Warning","Selected region contains insufficient data.")
            return
        amplitude=float(np.max(yfit))
        mean=float(xfit[np.argmax(yfit)])
        stddev=float((high-low)/4)
        try:
            params,_=curve_fit(gaussian,xfit,yfit,p0=[amplitude,mean,stddev],maxfev=10000)
            amplitude,mean,stddev=params
            stddev=abs(stddev)
            fitted=gaussian(xfit,amplitude,mean,stddev)
            residual=yfit-fitted
            ss_res=np.sum(residual**2)
            ss_tot=np.sum((yfit-np.mean(yfit))**2)
            r2=1-(ss_res/ss_tot) if ss_tot!=0 else 0
            fwhm=2.355*stddev
            if self.fit_curve:
                self.plot.removeItem(self.fit_curve)
            self.fit_curve=pg.PlotDataItem(xfit,fitted,pen=pg.mkPen("red",width=3))
            self.plot.addItem(self.fit_curve)
            self.residual_plot.clear()
            self.residual_plot.plot(xfit,residual,pen=pg.mkPen("yellow",width=1.5))
            self.info.setText(f"A = {amplitude:.4f}    μ = {mean:.4f}    σ = {stddev:.4f}    FWHM = {fwhm:.4f}    R² = {r2:.5f}")
            self.parameters={"Amplitude":amplitude,"Centroid":mean,"StdDev":stddev,"FWHM":fwhm,"R2":r2}
        except Exception as e:
            QMessageBox.critical(self,"Fit Error",f"Gaussian fitting failed:\n{e}")

    def clear_fit(self):
        self.region=None
        if self.fit_curve:
            self.plot.removeItem(self.fit_curve)
            self.fit_curve=None
        if hasattr(self,"selection"):
            self.plot.removeItem(self.selection)
            del self.selection
        self.residual_plot.clear()
        if len(self.x)>0:
            self.info.setText("Spectrum loaded. Select a fitting region.")
        else:
            self.info.setText("Load a spectrum and select a fitting region.")

    def save_parameters(self):
        if not hasattr(self,"parameters"):
            QMessageBox.warning(self,"Warning","Fit the spectrum first.")
            return
        filename,_=QFileDialog.getSaveFileName(self,"Save Parameters","","Text Files (*.txt)")
        if not filename:return
        try:
            with open(filename,"w") as file:
                file.write("Gaussian Peak Fitting Results\n")
                file.write("--------------------------------\n")
                for name,value in self.parameters.items():
                    file.write(f"{name}: {value:.6f}\n")
            QMessageBox.information(self,"Saved","Fitting parameters saved successfully.")
        except Exception as e:
            QMessageBox.critical(self,"Error",f"Could not save file:\n{e}")

if __name__=="__main__":
    app=QApplication(sys.argv)
    window=GaussianFitting()
    window.show()
    sys.exit(app.exec_())
