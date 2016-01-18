#!python2
# -*- coding:utf-8 -*-
import sys
import os
import time
import pickle
import requests # pip install requests
from PyQt4.QtCore import *
from PyQt4.QtGui import *

BUTTON_HEIGHT = 30
ISOTIMEFORMAT = '%Y-%m-%d %X'

class HttpItem():
    def __init__(self):
        self.time = ''
        self.url = ''
        self.proxy = ()
        self.proxyDict = {}
        self.requestHeader = ''
        self.requestHeaderDict = {}
        self.requestData = ''
        self.realUrl = ''
        self.responseHeader = ''
        self.responseHeaderDict = {}
        self.responseData = ''
        self.responseCode = ''
        self.exception = None
        self.timeout = 60

class Util():
    @staticmethod
    def headerToDict(header, headerDict = None):
        headers = header.split('\n')
        if not headerDict:
            headerDict = {}
        for it in headers:
            item = it.split(':')
            if len(item) == 2:
                headerDict[item[0].strip()] = item[1].strip()
        return headerDict

    @staticmethod
    def dictToHeader(headerDict):
        header = ''
        for key in headerDict:
            header += "%s: %s\r\n" % (key, headerDict[key])
        return header

class HttpThread(QThread):
    Trigger = pyqtSignal(list)

    def __init__(self, parent=None):
        super(HttpThread, self).__init__(parent)

    def setup(self, http):
        self.http = http

    def run(self):
        print 'http thread begin to tun'
        try:
            # get raw data if stream is True
            if self.http.requestData:
                response = requests.post(self.http.url, data=self.http.requestData, headers=self.http.requestHeaderDict, proxies=self.http.proxyDict, timeout=self.http.timeout, stream=False)
            else:
                response = requests.get(self.http.url, headers=self.http.requestHeaderDict, proxies=self.http.proxyDict, timeout=self.http.timeout, stream=False)
            header = ''
            for key in response.request.headers:
                if key not in self.http.requestHeader:
                    header += '%s: %s\r\n' % (key, response.request.headers[key])
            self.http.requestHeader = header + self.http.requestHeader
            self.http.realUrl = response.url
            self.http.responseHeaderDict = response.headers
            self.http.responseHeader = Util.dictToHeader(response.headers)
            self.http.responseData = response.text
            self.http.responseCode = response.status_code
        except requests.exceptions.RequestException, e:
            self.http.exception = e
        self.Trigger.emit([self.http])
        print 'http thread exit'

class CodeDlg(QDialog):
    def __init__(self, parent=None):
        super(CodeDlg, self).__init__(parent)
        self.setWindowFlags(Qt.Dialog|Qt.WindowMinMaxButtonsHint)
        self.setWindowTitle("Code Dlg")
        # self.setAttribute(Qt.WA_DeleteOnClose)
        self.resize(600, 400)
        vLayout = QVBoxLayout()
        self.setLayout(vLayout)

        hLayout = QHBoxLayout()
        button = QPushButton('e&val')
        button.setFixedHeight(BUTTON_HEIGHT)
        button.clicked.connect(self.clicked)
        hLayout.addWidget(button)

        button = QPushButton('e&xec')
        button.setFixedHeight(BUTTON_HEIGHT)
        button.clicked.connect(self.clicked)
        hLayout.addWidget(button)
        vLayout.addLayout(hLayout)

        self.inputEdit = QTextEdit('self.mainDlg.windowTitle()')
        vLayout.addWidget(self.inputEdit, 1)
        self.outputEdit = QTextEdit()
        vLayout.addWidget(self.outputEdit, 2)

    def clicked(self):
        button = self.sender()
        if not (button and isinstance(button, QPushButton)):
            return
        self.scrollToEnd()
        try:
            text = unicode(self.inputEdit.toPlainText())
            print type(text), text
            if button.text() == 'e&val':
                ret = eval(text)
                self.outputEdit.append('<font color=green>%s</font>' % text)
                self.outputEdit.append('%s\n' % ret)
            else:
                exec(text)
        except:
            self.outputEdit.append('<font color=red>%s</font> is invalid!' % text)
            self.outputEdit.append('')
        self.scrollToEnd()

    def scrollToEnd(self):
        currentCursor = self.outputEdit.textCursor()
        currentCursor.movePosition(QTextCursor.End)
        self.outputEdit.setTextCursor(currentCursor)

class MainDlg(QDialog):
    def __init__(self, parent=None):
        super(MainDlg, self).__init__(parent)
        self.initUI()
        self.codeDlg = None
        self.httpItems = []
        self.historyIndex = -1
        self.dir = os.path.dirname(__file__)
        self.configPath = os.path.join(self.dir, 'config.dat')
        self.finished.connect(self.dlgFinished)
        if os.path.exists(self.configPath):
            self.httpItems = pickle.load(open(self.configPath, 'rb'))
            if len(self.httpItems):
                self.historyIndex = 0
                for it in self.httpItems:
                    self.historyComboBox.addItem(it.time + ' ' + it.url)
                self.historyComboBox.addItem('Clear history')
                self.setUIByHttpItem(self.httpItems[0])

    def initUI(self):
        self.setWindowFlags(Qt.Dialog|Qt.WindowMinMaxButtonsHint)
        self.setWindowTitle("Http Requester")
        self.resize(1000, 600)
        self.gridLayout = QGridLayout()
        self.setLayout(self.gridLayout)

        hLayout = QHBoxLayout()
        historyLabel = QLabel('History:')
        hLayout.addWidget(historyLabel)
        self.historyComboBox = QComboBox()
        self.historyComboBox.currentIndexChanged.connect(self.historySelectionChanged)
        hLayout.addWidget(self.historyComboBox, 1)
        timeoutLabel = QLabel('Timeout:')
        hLayout.addWidget(timeoutLabel)
        self.timeoutEdit = QLineEdit('10')
        self.timeoutEdit.setValidator(QIntValidator(1, 1000, self))
        self.timeoutEdit.setMaximumWidth(60)
        hLayout.addWidget(self.timeoutEdit)
        proxyLabel = QLabel('Proxy:')
        hLayout.addWidget(proxyLabel)
        self.proxyComboBox = QComboBox()
        self.proxyComboBox.addItem('http')
        self.proxyComboBox.addItem('https')
        hLayout.addWidget(self.proxyComboBox)
        self.proxyEdit = QLineEdit()
        hLayout.addWidget(self.proxyEdit)
        row = 0
        self.gridLayout.addLayout(hLayout, row, 0, 1, 2)

        hLayout = QHBoxLayout()
        urlLabel = QLabel('URL:')
        hLayout.addWidget(urlLabel)
        self.urlEdit = QLineEdit()
        self.urlEdit.setFixedHeight(BUTTON_HEIGHT-2)
        hLayout.addWidget(self.urlEdit)
        timeLabel = QLabel('Time:')
        hLayout.addWidget(timeLabel)
        self.timeEdit = QLineEdit('0')
        self.timeEdit.setFixedHeight(BUTTON_HEIGHT-2)
        self.timeEdit.setMaximumWidth(50)
        hLayout.addWidget(self.timeEdit)
        self.requestBtn = QPushButton('&Request')
        self.requestBtn.setFixedHeight(BUTTON_HEIGHT)
        self.requestBtn.clicked.connect(self.request)
        hLayout.addWidget(self.requestBtn)
        codeBtn = QPushButton('Run &Code')
        codeBtn.setFixedHeight(BUTTON_HEIGHT)
        codeBtn.clicked.connect(self.openCodeDlg)
        hLayout.addWidget(codeBtn)
        row += 1
        self.gridLayout.addLayout(hLayout, row, 0, 1, 2)

        vLayout = QVBoxLayout()
        requestHeaderLabel = QLabel('Request Header:')
        vLayout.addWidget(requestHeaderLabel)
        self.requestHeaderEdit = QTextEdit()
        self.requestHeaderEdit.setAcceptRichText(False)
        vLayout.addWidget(self.requestHeaderEdit)
        row += 1
        self.gridLayout.addLayout(vLayout, row, 0)
        self.gridLayout.setRowStretch(row, 1)

        vLayout = QVBoxLayout()
        responseHeaderLabel = QLabel('Response Header:')
        vLayout.addWidget(responseHeaderLabel)
        self.responseHeaderEdit = QTextEdit()
        self.responseHeaderEdit.setAcceptRichText(False)
        vLayout.addWidget(self.responseHeaderEdit)
        self.gridLayout.addLayout(vLayout, row, 1)
        self.gridLayout.setRowMinimumHeight(row, 100)

        vLayout = QVBoxLayout()
        requestDataLabel = QLabel('Request Data:')
        vLayout.addWidget(requestDataLabel)
        self.requestDataEdit = QTextEdit()
        self.requestDataEdit.setAcceptRichText(False)
        vLayout.addWidget(self.requestDataEdit)
        row += 1
        self.gridLayout.addLayout(vLayout, row, 0)
        self.gridLayout.setRowStretch(row, 3)

        vLayout = QVBoxLayout()
        responseDataLabel = QLabel('Response Data:')
        vLayout.addWidget(responseDataLabel)
        self.responseDataEdit = QTextEdit()
        self.responseDataEdit.setAcceptRichText(False)
        vLayout.addWidget(self.responseDataEdit)
        self.gridLayout.addLayout(vLayout, row, 1)

    def request(self):
        httpItem = HttpItem()
        httpItem.url = unicode(self.urlEdit.text()).strip()
        if not httpItem.url:
            return

        self.httpItem = httpItem

        httpItem.time = time.strftime(ISOTIMEFORMAT, time.localtime())
        timeout = unicode(self.timeoutEdit.text()).strip()
        httpItem.timeout = int(timeout)
        proxy = unicode(self.proxyEdit.text()).strip()
        if proxy:
            proxyType = unicode(self.proxyComboBox.currentText())
            httpItem.proxy = (proxyType, proxy)
            if not proxy.startswith('http'):
                proxy = '%s://%s' % (proxyType, proxy)
            httpItem.proxyDict[proxyType] = proxy

        httpItem.requestHeader = unicode(self.requestHeaderEdit.toPlainText())
        Util.headerToDict(httpItem.requestHeader, httpItem.requestHeaderDict)
        httpItem.requestData = unicode(self.requestDataEdit.toPlainText()).strip()

        self.responseHeaderEdit.clear()
        self.responseDataEdit.clear()
        self.enableUI(False)

        self.httpThread = HttpThread()
        self.httpThread.Trigger.connect(self.httpFinished)
        self.httpThread.setup(self.httpItem)
        self.httpThread.start()

        self.startTime = time.clock()
        self.timeEdit.setText('0')

    def httpFinished(self, http):
        http = http[0]
        if http is not self.httpItem:
            return
        httpTime = time.clock() - self.startTime
        self.timeEdit.setText('%.3f' % httpTime)
        self.enableUI(True)
        if http.exception:
            QMessageBox.warning(self, 'RequestException', str(http.exception))
        self.requestHeaderEdit.setPlainText(http.requestHeader)
        self.responseHeaderEdit.setPlainText(http.responseHeader)
        self.responseDataEdit.setPlainText(http.responseData)
        self.httpItems.append(http)
        if 0 == self.historyComboBox.count():
            self.historyIndex = 0
            self.historyComboBox.addItem(http.time + ' ' + http.url)
            self.historyComboBox.addItem('Clear history')
        else:
            self.historyIndex = self.historyComboBox.count()-1
            self.historyComboBox.insertItem(self.historyIndex, http.time + ' ' + http.url)
            self.historyComboBox.setCurrentIndex(self.historyIndex)

    def enableUI(self, enabled):
        self.historyComboBox.setEnabled(enabled)
        self.requestBtn.setEnabled(enabled)
        self.requestBtn.setText('&Request' if enabled else '&Requesting')

    def historySelectionChanged(self, index):
        if index == self.historyIndex:
            return
        self.historyIndex = index
        if index >= 0:
            if index != self.historyComboBox.count() - 1:
                self.setUIByHttpItem(self.httpItems[index])
            else:
                if QMessageBox.Yes == QMessageBox.warning(self, 'Delete?', 'Do you want to delete the history?', QMessageBox.Yes|QMessageBox.No):
                    self.historyComboBox.clear()
                    self.httpItems = []

    def setUIByHttpItem(self, http):
        self.httpItem = http
        self.timeoutEdit.setText(str(http.timeout))
        if http.proxy:
            self.proxyComboBox.setCurrentIndex(self.proxyComboBox.findText(http.proxy[0]))
            self.proxyEdit.setText(http.proxy[1])
        else:
            self.proxyEdit.clear()
        self.urlEdit.setText(http.url)
        self.timeEdit.setText('0')
        self.requestHeaderEdit.setPlainText(http.requestHeader)
        self.requestDataEdit.setPlainText(http.requestData)
        self.responseHeaderEdit.setPlainText(http.responseHeader)
        self.responseDataEdit.setPlainText(http.responseData)

    def openCodeDlg(self):
        if not self.codeDlg:
            self.codeDlg = CodeDlg(self)
            self.codeDlg.mainDlg = self
        self.codeDlg.show()
        # need raise_ and activateWindow if codeDlg is already shown, otherwise codeDlg won't active
        self.codeDlg.raise_()
        self.codeDlg.activateWindow()

    def dlgFinished(self, ret):
        pickle.dump(self.httpItems, open(self.configPath, 'wb'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dlg = MainDlg()
    dlg.show()
    app.exec_()