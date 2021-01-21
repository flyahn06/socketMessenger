import socket

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('', 1123))

serversocket.listen()

print("Server started, listening...")

connectionsocket, address = serversocket.accept()

connectionsocket.send("Ping 핑!".encode('utf-8'))

message = connectionsocket.recv(16384)

print(message.decode('utf-8'))
