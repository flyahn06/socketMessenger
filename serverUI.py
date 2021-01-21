from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import sys
import socket
import time

class ClientConnection(QThread):
    address = pyqtSignal(tuple)
    message = pyqtSignal(tuple)

class Server(QThread):
    messageSender = pyqtSignal(tuple)
    generalMessageSender = pyqtSignal(str)

    def __init__(self, clientsocket, addr):
        super().__init__()
        self.clientsocket = clientsocket
        self.addr = addr

    def run(self):
        while True:
            try:
                message = self.clientsocket.recv(16384).decode('utf-8')
            except ConnectionResetError:
                self.generalMessageSender.emit("[!] {}:{}과의 연결이 끊어졌습니다.".format(self.addr[0], self.addr[1]))
                break
            if message:
                self.messageSender.emit((self.addr[0], message))
                print(message)
            time.sleep(0.5)

class CreateSocket(QThread):
    address_sender = pyqtSignal(tuple)
    error_oserror = pyqtSignal()
    message = pyqtSignal(tuple)
    generalMessage = pyqtSignal(str)
    usertableSender = pyqtSignal(list)

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.succeed = True
        self.close = False
        self.clients = []
        self.usertable = []

        try:
            self.serversocket.bind(('', self.port))
        except OSError:
            self.error_oserror.emit()
            self.succeed = False

    def close_socket(self):
        self.close = True
        socket.socket(socket.AF_INET,
                      socket.SOCK_STREAM).connect(('127.0.0.1', self.port))
        self.serversocket.shutdown(socket.SHUT_RDWR)
        self.serversocket.close()

    def run(self):
        if not self.succeed:
            return

        self.serversocket.listen(100)

        while not self.close:
            try:
                clientsocket, address = self.serversocket.accept()
            except OSError:
                break
            self.address_sender.emit(address)

            displayname = clientsocket.recv(16384).decode().replace("DISPLAYNAME", "")
            self.usertable.append((address[0], address[1], displayname))

            usertableForClient = []

            for user in self.usertable:
                temp = " ".join([user[0], str(user[1]), user[2]]).strip()
                usertableForClient.append(temp)

            result = "\n"
            result = result.join(usertableForClient)
            clientsocket.send(result.encode())

            self.usertableSender.emit(self.usertable)

            worker = Server(clientsocket, address)
            worker.messageSender.connect(self.messagesender)
            worker.generalMessageSender.connect(self.generalMessageSender)
            self.clients.append(worker)
            self.clients[self.clients.index(worker)].start()

    @pyqtSlot(tuple)
    def messagesender(self, msg):
        self.message.emit(msg)

    @pyqtSlot(str)
    def generalMessageSender(self, msg):
        self.generalMessage.emit(msg)

class ServerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        self.setObjectName("MainWindow")
        self.resize(700, 500)

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralwidget")

        self.gridLayout_2 = QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")

        self.portedit = QLineEdit(self.centralwidget)
        self.portedit.setObjectName("portedit")
        self.gridLayout.addWidget(self.portedit, 1, 0, 1, 1)

        self.startbutton = QPushButton(self.centralwidget)
        self.startbutton.setObjectName("startbutton")
        self.gridLayout.addWidget(self.startbutton, 1, 1, 1, 1)

        self.stopbutton = QPushButton(self.centralwidget)
        self.stopbutton.setObjectName("stopbutton")
        self.gridLayout.addWidget(self.stopbutton, 1, 2, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.tableView = QTableView(self.centralwidget)
        self.tableView.setObjectName("tableView")
        self.horizontalLayout.addWidget(self.tableView)

        self.logtextbox = QTextBrowser(self.centralwidget)
        self.logtextbox.setObjectName("logtextbox")
        self.horizontalLayout.addWidget(self.logtextbox)

        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 3)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        self.setCentralWidget(self.centralwidget)

        self.retranslateUi()
        self.make_connection()
        self.show()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "소켓 채팅 서버"))
        self.startbutton.setText(_translate("MainWindow", "Start"))
        self.stopbutton.setText(_translate("MainWindow", "Stop"))

        self.startbutton.setEnabled(True)
        self.stopbutton.setEnabled(False)

    def make_connection(self):
        self.startbutton.clicked.connect(self.start)
        self.stopbutton.clicked.connect(self.stop)

    def start(self):
        port = self.portedit.text()

        self.logtextbox.append("[*] 서버를 시작합니다.")
        self.logtextbox.append("[*] 서버 포트: {}".format(port))

        try:
            port = int(port)
        except ValueError:
            self.logtextbox.append("[!] 오류: 서버 포트가 정수형이 아닙니다. 정수형 포트를 입력하여 주십시오.")
            self.portedit.setText("")
            return

        if not 0 <= port <= 65535:
            self.logtextbox.append("[!] 입력된 포트가 너무 큽니다. 포트의 범위는 0-65535여야 합니다.")
            self.portedit.setText("")
            return

        self.serversocket = CreateSocket(port)
        self.serversocket.address_sender.connect(self.new_client)
        self.serversocket.message.connect(self.display)
        self.serversocket.generalMessage.connect(self.generalDisplay)
        self.serversocket.usertableSender.connect(self.usertableDisplay)
        self.serversocket.start()

        self.logtextbox.append("[*] 서버가 정상적으로 포트 {} 에서 시작되었습니다.".format(port))

        self.startbutton.setEnabled(False)
        self.stopbutton.setEnabled(True)

    def stop(self):
        self.serversocket.close_socket()

        self.logtextbox.append("[*] 서버가 정상적으로 종료되었습니다.")

        self.startbutton.setEnabled(True)
        self.stopbutton.setEnabled(False)

    @pyqtSlot(tuple)
    def new_client(self, address: tuple):
        self.logtextbox.append("[+] IP {}, PORT {} 에서 새로운 연결이 들어와 수립되었습니다.".format(address[0], address[1]))

    @pyqtSlot()
    def os_error(self):
        self.logtextbox.append("[!] 포트 {} 는 점유된 포트입니다.".format(self.port))

    @pyqtSlot(tuple)
    def display(self, message):
        self.logtextbox.append("[*] {} 로부터 메시지가 도착했습니다: {}".format(message[0], message[1]))

    @pyqtSlot(str)
    def generalDisplay(self, message):
        self.logtextbox.append(message)

    @pyqtSlot(list)
    def usertableDisplay(self, usertable):
        self.tableView.setRowCount()
        self.tableView.setRowCount(len(usertable))

        self.tableView.setHorizontalHeaderLabels(["IP", "포트", "닉네임"])


app = QApplication(sys.argv)
w = ServerUI()
sys.exit(app.exec_())