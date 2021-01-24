from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import QMessageBox
import sys
import socket
import time

class ConnectUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()
    
    def setupUi(self):
        self.setObjectName("mainWindow")
        self.resize(673, 60)
        
        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        
        self.IPlbl = QLabel(self)
        self.IPlbl.setObjectName("IPlbl")
        self.gridLayout.addWidget(self.IPlbl, 0, 0, 1, 1)
        
        self.NICKlbl = QLabel(self)
        self.NICKlbl.setObjectName("NICKlbl")
        self.gridLayout.addWidget(self.NICKlbl, 0, 2, 1, 1)
        
        self.PORTlbl = QLabel(self)
        self.PORTlbl.setObjectName("PORTlbl")
        self.gridLayout.addWidget(self.PORTlbl, 0, 1, 1, 1)
        
        self.IPInput = QLineEdit(self)
        self.IPInput.setObjectName("IPInput")
        self.gridLayout.addWidget(self.IPInput, 1, 0, 1, 1)
        
        self.PORTInput = QLineEdit(self)
        self.PORTInput.setObjectName("PORTInput")
        self.gridLayout.addWidget(self.PORTInput, 1, 1, 1, 1)
        
        self.NICKInput = QLineEdit(self)
        self.NICKInput.setObjectName("NICKInput")
        self.gridLayout.addWidget(self.NICKInput, 1, 2, 1, 1)
        
        self.horizontalLayout.addLayout(self.gridLayout)
        
        self.connectBtn = QPushButton(self)
        self.connectBtn.setObjectName("connectBtn")
        self.horizontalLayout.addWidget(self.connectBtn)
        
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        
        self.setCentralWidget(self.centralwidget)
        self.retranslateUi()
        self.connectBtn.clicked.connect(self.run)
        self.show()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("mainWindow", "소켓 채팅 클라이언트 - 연결"))
        self.IPlbl.setText(_translate("mainWindow", "IP"))
        self.NICKlbl.setText(_translate("mainWindow", "NICK"))
        self.PORTlbl.setText(_translate("mainWindow", "PORT"))
        self.connectBtn.setText(_translate("mainWindow", "연결"))

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter:
            self.run()

    def run(self):
        ip = self.IPInput.text()
        port = self.PORTInput.text()
        nick = self.NICKInput.text()

        try:
            port = int(port)
        except ValueError:
            QMessageBox.critical(self, '오류!', "포트 번호는 정수여야 합니다.",
                                 QMessageBox.Yes, QMessageBox.Yes)
            return

        if not 0 <= port <= 65535:
            QMessageBox.critical(self, '오류!', "포트 범위가 너무 큽니다.\n포트는 0-65535 사이의 정수여야만 합니다.",
                                 QMessageBox.Yes, QMessageBox.Yes)
            return

        ans = QMessageBox.question(self, '확인', "정보를 확인해주세요. 맞다면 예, 아니면 아니오를 눌러주세요.\nIP: {}\nPORT: {}\nNICK: {}".format(ip, nick, port),
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if ans == QMessageBox.No:
            return

        self.close()
        self.next=ClientUI(ip, port, nick)
        

class ClientSocketGenerator(QThread):
    usertablesender = pyqtSignal(list)
    msgSender = pyqtSignal(str)
    connectionrefusederror = pyqtSignal()
    
    def __init__(self, host, port, nick):
        super().__init__()
        self.host = host
        self.port = port
        self.nick = nick
        self.ready = False
        self.error = False
        # 소켓 객체를 생성합니다.
        # 주소 체계(address family)로 IPv4, 소켓 타입으로 TCP 사용합니다.
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 지정한 HOST와 PORT를 사용하여 서버에 접속합니다.
        try:
            self.client_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            self.error = True
            return

        self.client_socket.send("DISPLAYNAME {}".format(self.nick).encode())
        self.rawusertable = self.client_socket.recv(16384).decode()
        self.usertable = self.interpret(self.rawusertable)

        self.ready = True

    def run(self):
        while True:
            print(self.ready, self.error)
            if self.ready:
                break
            if self.error:
                self.connectionrefusederror.emit()
                return
            time.sleep(0.1)
            
        self.usertablesender.emit(self.usertable)
        
        while True:
            msg = self.client_socket.recv(16384).decode()
            if msg.startswith("sysut"):
                msg = msg.replace("sysut\n", "")
                msg = self.interpret(msg)
                self.usertablesender.emit(msg)
                continue
                
            self.msgSender.emit(msg)

            print(msg)

    def close(self):
        self.client_socket.close()

    def send(self, text):
        self.client_socket.send(text.encode())

    def interpret(self, msg):
        rawusertable = msg.split("\n")
        usertable = []

        for eachuser in rawusertable:
            if eachuser == "\n": continue
            ip = eachuser.split(" ")[0]
            port = eachuser.split(" ")[1]
            nick = eachuser.split(" ")[2]
            usertable.append((ip, port, nick))

        return usertable


class ClientUI(QMainWindow):
    def __init__(self, ip, port, nick):
        super().__init__()
        self.ip = ip
        self.port = port
        self.nick = nick
        self.setupUi()

    def setupUi(self):
        self.setObjectName("MainWindow")
        self.resize(778, 441)
        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralwidget")

        self.gridLayout_2 = QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")

        self.tableWidget = QTableWidget(self.centralwidget)
        self.tableWidget.setObjectName("tableWidget")
        self.gridLayout.addWidget(self.tableWidget, 0, 2, 1, 1)

        self.userinput = QLineEdit(self.centralwidget)
        self.userinput.setObjectName("userinput")
        self.horizontalLayout.addWidget(self.userinput)

        self.sendbutton = QPushButton(self.centralwidget)
        self.sendbutton.setObjectName("sendbutton")
        self.horizontalLayout.addWidget(self.sendbutton)

        self.gridLayout.addLayout(self.horizontalLayout, 3, 1, 1, 2)

        self.chattextbox = QTextBrowser(self.centralwidget)
        self.chattextbox.setObjectName("chattextbox")

        self.gridLayout.addWidget(self.chattextbox, 0, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        self.setCentralWidget(self.centralwidget)

        self.retranslateUi()
        self.show()

        self.sendbutton.clicked.connect(self.send)
        self.worker = ClientSocketGenerator(self.ip, self.port, self.nick)
        self.worker.usertablesender.connect(self.usertableDisplay)
        self.worker.msgSender.connect(self.displayMsg)
        self.worker.connectionrefusederror.connect(self.connectionrefusederrorDisplay)
        self.worker.start()
        

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "소켓 채팅 클라이언트"))
        self.sendbutton.setText(_translate("MainWindow", "전송"))

    def closeEvent(self, *args, **kwargs):
        self.worker.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter:
            self.send()

    def send(self):
        text = self.userinput.text()
        self.userinput.setText("")
        self.worker.send(text)

    @pyqtSlot(list)
    def usertableDisplay(self, usertable):
        print("Got {}".format(usertable))
        column_headers = ('아아피', '포트', '닉네임')
        self.tableWidget.setHorizontalHeaderLabels(column_headers)
        self.tableWidget.setRowCount(len(usertable))
        self.tableWidget.setColumnCount(3)

        for packeddata, index in zip(usertable, range(len(usertable))):
            ip, port, nick = packeddata
            self.tableWidget.setItem(index, 0, QTableWidgetItem(ip))
            self.tableWidget.setItem(index, 1, QTableWidgetItem(str(port)))
            self.tableWidget.setItem(index, 2, QTableWidgetItem(nick))

    @pyqtSlot(str)
    def displayMsg(self, msg):
        self.chattextbox.append(msg)

    @pyqtSlot()
    def connectionrefusederrorDisplay(self):
        self.close()
        ret = QMessageBox.critical(self, '오류!', "연결하지 못했습니다.",
                                 QMessageBox.Yes, QMessageBox.Yes)

app = QApplication(sys.argv)
w = ConnectUI()
sys.exit(app.exec_())
