from datetime import datetime
import socket
import time
import json
import random


def client_program():
    host = "host.docker.internal"
    port = 5000
    # wait for the server to boot the socket
    waiting_time = 1
    time.sleep(waiting_time)
  
    # create a connection to the server
    client_socket = socket.socket()
    client_socket.connect((host, port))
    client_name = 'idp_client'

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

    # declare the seat ID variable
    id = 1

    if msg_recv == 'idp_client':
        while True:
            # create a seat ID
            id_str = str(id).zfill(5)
          
            # generate a new seat dataset and send it to the server
            seatData = generateSeatData(id_str)
            seatData.update( {'timestamp' : currentTime()} )
            msg_send = seatData
            json_send = json.dumps(msg_send)
            pre = time.time()
            client_socket.send(json_send.encode())
            generateLog('seat arrival', 'send', json_send)
          
            # receive a confirmation from the server
            json_recv = client_socket.recv(1024).decode()
            post = time.time()
            responseTime = post-pre
            status = responseTimeStatus(responseTime)
            msg_recv = json.loads(json_recv)   
            generateLog('response', 'recv', str(msg_recv))
            generateLog(status, str(responseTime), '')

            id += 1
            # wait 90 seconds before generating the next seat dataset
            time.sleep(90)

    # close the connection to the server
    client_socket.close()
    generateLog('disconnection', '', '')

# generate a seat dataset
def generateSeatData(id_str):
    colors = ['black', 'brown', 'beige']
    types = ['front', 'back']
    weights = [25000, 27000]
    heights = [1000, 1050, 1100]
    lengths = [550, 600]
    widths = [500, 550]

    seatData = {
        'id': id_str,
        'color': random.choice(colors),
        'type': random.choice(types),
        'weight': random.choice(weights),
        'height': random.choice(heights),
        'length': random.choice(lengths),
        'width': random.choice(widths),
        'current_loc': 'IDP',
        'outbound_request' : 'false'
    }
    return seatData

# get the current timestamp
def currentTime():
    return str(datetime.now())[:-7]

# generate log entries
def generateLog(status, action, json_str):
    log = '\n' + datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ' ' + status + ' ' + action + ' ' + json_str
    log_file = open("/var/log/client.log", "a")
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
