import socket
import time
from datetime import datetime
import json
import random

def client_program():
    host = "host.docker.internal"
    port = 5000
    # wait for the server to boot the socket
    waiting_time = 3
    time.sleep(waiting_time)
    
    # create a connection to the server
    client_socket = socket.socket()
    client_socket.connect((host, port))
    client_name = 'crane'

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
    generateLog('connection test', 'send', msg_send)
    json_recv = client_socket.recv(1024).decode()
    post = time.time()
    responseTime = post-pre
    status = responseTimeStatus(responseTime)
    msg_recv = json.loads(json_recv)
    generateLog('connection test', 'recv', str(msg_recv))
    generateLog(status, str(responseTime), '')
  
    generateLog('connection', '', '')

    if msg_recv == 'crane':
        msg_send = request
        status = 'request'

        while True:
            # send a message (request, error or transport confirmation) to the server
            json_send = json.dumps(msg_send)
            pre = time.time()
            client_socket.send(json_send.encode())
            generateLog(status, 'send', str(json_send))

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
                origin = msg_recv['from']
                destination = msg_recv['to']
                id = msg_recv['id']
                y = msg_recv['y']
                x = msg_recv['x']
                direction = msg_recv['direction']

                # set error rate
                random_number = random.randint(1, 20)
                # generate an inbound error: assigned bin already contains a seat
                if random_number <= 1 and origin == 'Inbound_place' and destination == 'Warehouse':
                   # declare an error message
                   msg_send = {
                       'message' : 'Occupied',
                       'id' : id,
                       'y' : y,
                       'x' : x,
                       'direction' : direction,
                   }
                   status = 'bin occupied'
                # generate an outbound error: assigned bin does not contain the desired seat
                elif random_number <= 1 and origin == 'Warehouse' and destination == 'Outbound_place':
                   # declare an error message
                   msg_send = {
                       'message' : 'Empty',
                       'id' : id,
                       'y' : y,
                       'x' : x,
                       'direction' : direction,
                   }
                   status = 'bin empty'
                # declare a transport confirmation message
                else:
                    msg_send = {
                        'message' : 'Moved',
                        'from' : origin,
                        'to' : destination,
                        'id' : id,
                        'y' : y,
                        'x' : x,
                        'direction' : direction,
                    }
                    status = 'transport success'
                msg_send.update( {'timestamp' : currentTime()} )
                waiting_time = 30
            # check if the received message is a no operation message
            elif msg_recv['message'] == 'No operation':
                # declare another request message
                request.update( {'timestamp' : currentTime()} )
                msg_send = request
                status = 'request'
                waiting_time = 10
            # check if received message is a confirmation message
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
    log_file = open("/var/log/crane.log", "a")
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