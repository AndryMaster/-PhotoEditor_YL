# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'QT Forms\crop.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 623)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.put_image = QtWidgets.QLabel(self.centralwidget)
        self.put_image.setGeometry(QtCore.QRect(0, 0, 800, 600))
        self.put_image.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.put_image.setText("")
        self.put_image.setAlignment(QtCore.Qt.AlignCenter)
        self.put_image.setIndent(0)
        self.put_image.setObjectName("put_image")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 23))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.menubar.setFont(font)
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Abobe Photoshop - Обрезка изображения"))
