# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'syringe_pump_init_ui.ui'
#
# Created: Thu Aug 14 17:05:40 2014
#      by: PyQt5 UI code generator 5.2.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_InitWindow(object):
    def setupUi(self, InitWindow):
        InitWindow.setObjectName("InitWindow")
        InitWindow.resize(494, 198)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(InitWindow.sizePolicy().hasHeightForWidth())
        InitWindow.setSizePolicy(sizePolicy)
        self.textBrowser = QtWidgets.QTextBrowser(InitWindow)
        self.textBrowser.setGeometry(QtCore.QRect(5, 11, 481, 151))
        self.textBrowser.setObjectName("textBrowser")
        self.init_button = QtWidgets.QPushButton(InitWindow)
        self.init_button.setGeometry(QtCore.QRect(410, 170, 75, 23))
        self.init_button.setObjectName("init_button")
        self.dontinit_button = QtWidgets.QPushButton(InitWindow)
        self.dontinit_button.setGeometry(QtCore.QRect(330, 170, 75, 23))
        self.dontinit_button.setObjectName("dontinit_button")
        self.entertesting_button = QtWidgets.QPushButton(InitWindow)
        self.entertesting_button.setGeometry(QtCore.QRect(10, 170, 101, 21))
        self.entertesting_button.setObjectName("entertesting_button")

        self.retranslateUi(InitWindow)
        QtCore.QMetaObject.connectSlotsByName(InitWindow)

    def retranslateUi(self, InitWindow):
        _translate = QtCore.QCoreApplication.translate
        InitWindow.setWindowTitle(_translate("InitWindow", "Init"))
        self.textBrowser.setHtml(_translate("InitWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\" bgcolor=\"#000000\">\n"
"<p align=\"center\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p align=\"center\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#ff0000;\"><br /></p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; font-weight:600; color:#ff0000;\">WARNING</span><span style=\" font-size:8pt; color:#ff0000;\">: To initialize the motor and start the program, the motor must turn a few revolutions. </span></p>\n"
"<p align=\"center\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; color:#ffffff;\">Please modify your setup such that this course of action will not irreversibly annhilate everything you ever worked on.</span></p>\n"
"<p align=\"center\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; color:#ffffff;\"><br /></p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; color:#ffffff;\">However, if the motor is already running, it has probably already been initialized. If this is the case, please press &quot;Don\'t initialize&quot;.</span></p></body></html>"))
        self.init_button.setText(_translate("InitWindow", "Initialize"))
        self.dontinit_button.setText(_translate("InitWindow", "Don\'t initialize"))
        self.entertesting_button.setText(_translate("InitWindow", "Enter testing mode"))

