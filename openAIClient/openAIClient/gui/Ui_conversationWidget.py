# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'conversationWidget.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QHBoxLayout,
    QLabel, QListView, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QTextBrowser,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_conversationForm(object):
    def setupUi(self, conversationForm):
        if not conversationForm.objectName():
            conversationForm.setObjectName(u"conversationForm")
        conversationForm.resize(452, 318)
        self.verticalLayout_3 = QVBoxLayout(conversationForm)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.conversationLayout = QVBoxLayout()
        self.conversationLayout.setObjectName(u"conversationLayout")
        self.conversationLabel = QLabel(conversationForm)
        self.conversationLabel.setObjectName(u"conversationLabel")

        self.conversationLayout.addWidget(self.conversationLabel)

        self.conversationDisplay = QTextBrowser(conversationForm)
        self.conversationDisplay.setObjectName(u"conversationDisplay")

        self.conversationLayout.addWidget(self.conversationDisplay)


        self.verticalLayout_3.addLayout(self.conversationLayout)

        self.busyIndicator = QLabel(conversationForm)
        self.busyIndicator.setObjectName(u"busyIndicator")
        self.busyIndicator.setVisible(True)
        self.busyIndicator.setStyleSheet(u"color: blue; font-weight: bold;")
        self.busyIndicator.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.busyIndicator)

        self.fileLayout = QHBoxLayout()
        self.fileLayout.setObjectName(u"fileLayout")
        self.attachedFilesList = QListWidget(conversationForm)
        self.attachedFilesList.setObjectName(u"attachedFilesList")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.attachedFilesList.sizePolicy().hasHeightForWidth())
        self.attachedFilesList.setSizePolicy(sizePolicy)
        self.attachedFilesList.setMinimumSize(QSize(0, 40))
        self.attachedFilesList.setMaximumSize(QSize(16777215, 80))
        self.attachedFilesList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.attachedFilesList.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.attachedFilesList.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.attachedFilesList.setFlow(QListView.LeftToRight)
        self.attachedFilesList.setProperty(u"isWrapping", True)
        self.attachedFilesList.setResizeMode(QListView.Adjust)

        self.fileLayout.addWidget(self.attachedFilesList)

        self.fileButtonsLayout = QVBoxLayout()
        self.fileButtonsLayout.setObjectName(u"fileButtonsLayout")
        self.attachDirectoryButton = QPushButton(conversationForm)
        self.attachDirectoryButton.setObjectName(u"attachDirectoryButton")
        self.attachDirectoryButton.setMinimumSize(QSize(100, 18))
        self.attachDirectoryButton.setStyleSheet(u"text-align: left; padding-left: 10px")
        self.attachDirectoryButton.setIconSize(QSize(16, 16))

        self.fileButtonsLayout.addWidget(self.attachDirectoryButton)

        self.attachButton = QPushButton(conversationForm)
        self.attachButton.setObjectName(u"attachButton")
        self.attachButton.setMinimumSize(QSize(100, 18))
        self.attachButton.setStyleSheet(u"text-align: left; padding-left: 10px")
        self.attachButton.setIconSize(QSize(16, 16))

        self.fileButtonsLayout.addWidget(self.attachButton)

        self.verticalSpacer_3 = QSpacerItem(12, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.fileButtonsLayout.addItem(self.verticalSpacer_3)


        self.fileLayout.addLayout(self.fileButtonsLayout)


        self.verticalLayout_3.addLayout(self.fileLayout)

        self.messageLayout = QHBoxLayout()
        self.messageLayout.setObjectName(u"messageLayout")
        self.userInput = QTextEdit(conversationForm)
        self.userInput.setObjectName(u"userInput")
        sizePolicy.setHeightForWidth(self.userInput.sizePolicy().hasHeightForWidth())
        self.userInput.setSizePolicy(sizePolicy)
        self.userInput.setMinimumSize(QSize(0, 40))
        self.userInput.setMaximumSize(QSize(16777215, 80))
        self.userInput.setFrameShape(QFrame.Box)

        self.messageLayout.addWidget(self.userInput)

        self.sendButtonLayout = QVBoxLayout()
        self.sendButtonLayout.setObjectName(u"sendButtonLayout")
        self.sendButton = QPushButton(conversationForm)
        self.sendButton.setObjectName(u"sendButton")
        self.sendButton.setMinimumSize(QSize(100, 18))
        self.sendButton.setStyleSheet(u"text-align: left; padding-left: 10px")
        self.sendButton.setIconSize(QSize(16, 16))

        self.sendButtonLayout.addWidget(self.sendButton)

        self.verticalSpacer_4 = QSpacerItem(13, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.sendButtonLayout.addItem(self.verticalSpacer_4)


        self.messageLayout.addLayout(self.sendButtonLayout)


        self.verticalLayout_3.addLayout(self.messageLayout)

        self.verticalLayout_3.setStretch(0, 1)

        self.retranslateUi(conversationForm)

        QMetaObject.connectSlotsByName(conversationForm)
    # setupUi

    def retranslateUi(self, conversationForm):
        conversationForm.setWindowTitle(QCoreApplication.translate("conversationForm", u"Form", None))
        self.conversationLabel.setText(QCoreApplication.translate("conversationForm", u"Conversation:", None))
        self.busyIndicator.setText(QCoreApplication.translate("conversationForm", u"<html><img src=\"assets/ai-spark.png\" width=\"16\" height=\"16\"><span style=\"line-height:16px;\"> Thinking... </span></html>", None))
        self.attachDirectoryButton.setText(QCoreApplication.translate("conversationForm", u"Attach Directory", None))
        self.attachButton.setText(QCoreApplication.translate("conversationForm", u"Attach Files", None))
        self.userInput.setPlaceholderText(QCoreApplication.translate("conversationForm", u"Type your message here...", None))
        self.sendButton.setText(QCoreApplication.translate("conversationForm", u"Send", None))
    # retranslateUi

