from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt
import sys
import socket
import time

class ClientSocketGenerator(QThread):
    def __init__(self, host, port, nick):
        super().__init__()
        self.host = host
        self.port = port
        self.nick = nick
        # 소켓 객체를 생성합니다.
        # 주소 체계(address family)로 IPv4, 소켓 타입으로 TCP 사용합니다.
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 지정한 HOST와 PORT를 사용하여 서버에 접속합니다.
        self.client_socket.connect((self.host, self.port))

        self.client_socket.send("DISPLAYNAME {}".format(self.nick).encode())
        self.rawusertable = self.client_socket.recv(16384).decode()
        print(self.rawusertable)

        self.rawusertable = self.rawusertable.split("\n")
        self.usertable = []

        for eachuser in self.rawusertable:
            if eachuser == "\n": continue
            ip = eachuser.split(" ")[0]
            port = eachuser.split(" ")[1]
            nick = eachuser.split(" ")[2]

            self.usertable.append((ip, port, nick))

    def run(self):
        pass

    def close(self):
        self.client_socket.close()

    def send(self, text):
        self.client_socket.send(text.encode())


class ClientUI(QMainWindow):
    def __init__(self):
        super().__init__()
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

        self.usertable = QTableView(self.centralwidget)
        self.usertable.setObjectName("usertable")
        self.gridLayout.addWidget(self.usertable, 0, 2, 1, 1)

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
        self.sendbutton.clicked.connect(self.send)
        self.worker = ClientSocketGenerator("127.0.0.1", 1111, "DeVar")
        self.worker.start()
        self.show()

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

app = QApplication(sys.argv)
w = ClientUI()
sys.exit(app.exec_())