import socket
import time
import json
from datetime import datetime


def client_program():
    host = "host.docker.internal"
    port = 5000
    # wait for the server to boot the socket
    waiting_time = 2
    time.sleep(waiting_time)

    # create a connection to the server
    client_socket = socket.socket()
    client_socket.connect((host, port))
    client_name = 'conveyor'

    # declare a request message
    request = {
        'message': 'Request for transport'
    }
    request.update( {'timestamp' : currentTime()} )

    # test the connection
    msg_send = client_name
    json_send = json.dumps(msg_send)
    pre = time.time()
    client_socket.send(json_send.encode())
    generateLog('connection test', 'send', client_name)
    json_recv = client_socket.recv(1024).decode()
    post = time.time()
    responseTime = post-pre
    status = responseTimeStatus(responseTime)
    msg_recv = json.loads(json_recv)
    generateLog('connection test', 'recv', str(msg_recv))
    generateLog(status, str(responseTime), '')

    generateLog('connection', '', '')

    if msg_recv == 'conveyor':
        msg_send = request
        status = 'request'

        while True:
            # send a message (request or transport confirmation) to the server
            pre = time.time()
            json_send = json.dumps(msg_send)
            client_socket.send(json_send.encode())
            generateLog(status, 'send', str(msg_send))

            # receive a message from the server
            json_recv = client_socket.recv(1024).decode()
            post = time.time()
            responseTime = post-pre
            status = responseTimeStatus(responseTime)
            msg_recv = json.loads(json_recv)
            generateLog('response', 'recv', str(msg_recv))
            generateLog(status, str(responseTime), '')

            # check if the received message is a transport order
            if msg_recv['message'] == 'Move to':
                # declare a transport confirmation message
                id = msg_recv['id']
                destination = msg_recv['to']
                msg_send = {
                    'message' : 'Moved',
                    'id' : id,
                    'to' : destination
                }
                msg_send.update( {'timestamp' : currentTime()} )
                status = 'transport success'
                waiting_time = 60
            # check if the received message is a no operation message
            elif msg_recv['message'] == 'No operation':
                # declare another request message
                request.update( {'timestamp' : currentTime()} )
                msg_send = request
                status = 'request'
                waiting_time = 10
            # check if the received message is a confirmation message
            elif msg_recv['message'] == 'Acknowledge':
                # declare another request message
                request.update( {'timestamp' : currentTime()} )
                msg_send = request
                status = 'request'
                waiting_time = 0
            # wait before sending a message to the server
            time.sleep(waiting_time)

    # close the connection to the server
    client_socket.close()
    generateLog('disconnection', '', '')

# get the current timestamp
def currentTime():
    return str(datetime.now())

# generate log entries
def generateLog(status, action, json_str):
    log = '\n' + datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ' ' + status + ' ' + action + ' ' + json_str
    log_file = open("/var/log/conveyor.log", "a")
    log_file.write(log)
    log_file.close()

# define the response time status depending on whether the response time is less or more than one second
def responseTimeStatus(responseTime):
    if responseTime <= 1:
        status = 'response time ok'
    elif responseTime > 1:
        status = 'slow response'
    return status

if __name__ == '__main__':
    client_program()
