# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'syringe_pump_init_ui.ui'
#
# Created: Mon Nov 10 15:23:47 2014
#      by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_InitWindow(object):
    def setupUi(self, InitWindow):
        InitWindow.setObjectName("InitWindow")
        InitWindow.resize(480, 160)
        self.verticalLayout = QtWidgets.QVBoxLayout(InitWindow)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textBrowser = QtWidgets.QTextBrowser(InitWindow)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(212, 208, 200))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        self.textBrowser.setPalette(palette)
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout.addWidget(self.textBrowser)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.entertesting_button = QtWidgets.QPushButton(InitWindow)
        self.entertesting_button.setObjectName("entertesting_button")
        self.horizontalLayout.addWidget(self.entertesting_button)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.dontinit_button = QtWidgets.QPushButton(InitWindow)
        self.dontinit_button.setObjectName("dontinit_button")
        self.horizontalLayout.addWidget(self.dontinit_button)
        self.init_button = QtWidgets.QPushButton(InitWindow)
        self.init_button.setObjectName("init_button")
        self.horizontalLayout.addWidget(self.init_button)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(InitWindow)
        QtCore.QMetaObject.connectSlotsByName(InitWindow)

    def retranslateUi(self, InitWindow):
        _translate = QtCore.QCoreApplication.translate
        InitWindow.setWindowTitle(_translate("InitWindow", "Warning"))
        self.textBrowser.setHtml(_translate("InitWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\" bgcolor=\"#000000\">\n"
"<p align=\"center\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600; color:#ff0000;\">WARNING:</span><span style=\" color:#ff0000;\"> To initialize the motor and start the program, the motor must turn a few revolutions.</span></p>\n"
"<p align=\"center\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; color:#ff0000;\"><br /></p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#ffffff;\">If the motor is already running, it has probably already been initialized. If this is the case, please press &quot;Don\'t Initialize&quot;.</span></p></body></html>"))
        self.entertesting_button.setText(_translate("InitWindow", "Testing Mode"))
        self.dontinit_button.setText(_translate("InitWindow", "Don\'t Initialize"))
        self.init_button.setText(_translate("InitWindow", "Initialize"))

