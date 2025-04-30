# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDialog,
    QDialogButtonBox, QSizePolicy, QSpacerItem, QTabWidget,
    QVBoxLayout, QWidget)

class Ui_settingsDialog(object):
    def setupUi(self, settingsDialog):
        if not settingsDialog.objectName():
            settingsDialog.setObjectName(u"settingsDialog")
        settingsDialog.resize(400, 300)
        self.verticalLayout = QVBoxLayout(settingsDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabSettingsPages = QTabWidget(settingsDialog)
        self.tabSettingsPages.setObjectName(u"tabSettingsPages")
        self.tab_General = QWidget()
        self.tab_General.setObjectName(u"tab_General")
        self.verticalLayout_2 = QVBoxLayout(self.tab_General)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.cb_darkMode = QCheckBox(self.tab_General)
        self.cb_darkMode.setObjectName(u"cb_darkMode")

        self.verticalLayout_2.addWidget(self.cb_darkMode)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.tabSettingsPages.addTab(self.tab_General, "")
        self.tab_Prompts = QWidget()
        self.tab_Prompts.setObjectName(u"tab_Prompts")
        self.tabSettingsPages.addTab(self.tab_Prompts, "")

        self.verticalLayout.addWidget(self.tabSettingsPages)

        self.buttonBox = QDialogButtonBox(settingsDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(settingsDialog)
        self.buttonBox.accepted.connect(settingsDialog.accept)
        self.buttonBox.rejected.connect(settingsDialog.reject)

        self.tabSettingsPages.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(settingsDialog)
    # setupUi

    def retranslateUi(self, settingsDialog):
        settingsDialog.setWindowTitle(QCoreApplication.translate("settingsDialog", u"Dialog", None))
        self.cb_darkMode.setText(QCoreApplication.translate("settingsDialog", u"Dark mode", None))
        self.tabSettingsPages.setTabText(self.tabSettingsPages.indexOf(self.tab_General), QCoreApplication.translate("settingsDialog", u"General", None))
        self.tabSettingsPages.setTabText(self.tabSettingsPages.indexOf(self.tab_Prompts), QCoreApplication.translate("settingsDialog", u"Prompts", None))
    # retranslateUi

