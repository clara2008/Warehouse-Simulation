from datetime import datetime
import socket
import _thread
import time
import json
import psycopg2

def server_program():
    host = '0.0.0.0'
    port = 5000

    # boot the socket
    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen(1)

    # create and test the database connection
    db_conn = psycopg2.connect(
        database="postgres", user='postgres', password='docker', host='host.docker.internal', port='5432'
    )
    cursor = db_conn.cursor()
    query_conn_test = "SELECT * FROM transport_units"
    cursor.execute(query_conn_test)
    db_test = cursor.fetchone()
    generateLog('database connection', '', '')

    # task for the assembly HMI
    def hmi_task(threadName, con, addr):
       generateLog('connection', '', threadName)

       while True:
           # receive a message from the HMI
           json_recv = con.recv(1024).decode()
           msg_recv = json.loads(json_recv)
         
           # if no message is received, break
           if not msg_recv:
              break
          
           generateLog(threadName, 'recv', str(msg_recv))
         
           seat_id = msg_recv['id']
         
           # flag the requested seat for outbound in the database table
           myquery = "UPDATE transport_units SET outbound_request = True WHERE id=%s"
           cursor.execute(myquery, (seat_id,))

           # save changes to the database
           db_conn.commit()

           generateLog('outbound request for seat ', str(seat_id), ' set in database.')

           # send a confirmation to the HMI
           msg_send = {
                'message' : 'Seat will be transported to Outbound Place.',
                'id' : msg_recv['id']
           }
           msg_send.update( {'timestamp' : currentTime()} )
           json_send = json.dumps(msg_send)
           con.send(json_send.encode())
           generateLog(threadName, 'send', json_send)

       # close the connection to the HMI
       con.close()
       generateLog('disconnection', '', 'threadName')

    # task for the IDP client
    def idp_task(threadName, con, addr):
       generateLog('connection', '', threadName)

       while True:
           # receive a message from the IDP client
           json_recv = con.recv(1024).decode()
           msg_recv = json.loads(json_recv)

           # if no message is received, break
           if not msg_recv:
              break

           generateLog(threadName, 'recv', str(msg_recv))

           # create new database table record based on the received seat data
           myquery = "INSERT INTO transport_units (id, color, type, weight, height, length, width, current_loc, outbound_request) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
           values = (msg_recv['id'], msg_recv['color'], msg_recv['type'], msg_recv['weight'], msg_recv['height'], msg_recv['length'], msg_recv['width'], msg_recv['current_loc'], msg_recv['outbound_request'])
           cursor.execute(myquery, values)

           # save changes to the database
           db_conn.commit()
           log_str = 'data of seat ' + msg_recv['id'] + ' saved in database.'
           generateLog(log_str, '', '')

           # send a confirmation to the IDP client
           msg_send = {
                'message' : 'ID saved in DB',
                'id' : msg_recv['id'],
           }
           msg_send.update( {'timestamp' : currentTime()} )
           json_send = json.dumps(msg_send)
           con.send(json_send.encode())
           generateLog(threadName, 'send', json_send)

       # close the connection to the IDP client
       con.close()
       generateLog('disconnection', '', 'threadName')

    # task for the conveyor
    def conveyor_task(threadName, con, addr):
       generateLog('connection', '', threadName)

       while True:
           # receive a message from the conveyor
           json_recv = con.recv(1024).decode()
           msg_recv = json.loads(json_recv)

           # if no message is received, break
           if not msg_recv:
               break

           generateLog(threadName, 'recv', str(msg_recv))

           # check if the received message is a request message
           if msg_recv['message'] == 'Request for transport':
               # search database for seats waiting at the identification point that need to be transported to the inbound place
               cursor = db_conn.cursor()
               myquery = "SELECT id FROM transport_units WHERE current_loc = 'IDP'"
               cursor.execute(myquery)
               db_record = cursor.fetchone()

               # declare a 'no operation' message if there are no seats at the identification point
               if not db_record:
                   msg_send = {
                        'message' : 'No operation'
                   }

               # declare a transport order if there is a seat waiting at the identification point
               else:
                   seat_id = db_record[0]
                   msg_send = {
                        'message': 'Move to',
                        'from': 'IDP',
                        'to': 'Inbound_place',
                        'id': seat_id,
                   }
           # if the message is not a request, it is the confirmation of a successful transport
           else:
               seat_id = str(msg_recv['id'])

               # update the datebase record by setting the current location of the seat to 'inbound_place'
               cursor = db_conn.cursor()
               myquery = "UPDATE transport_units SET current_loc = 'Inbound_place' WHERE id=%s"
               cursor.execute(myquery, (seat_id,))

               # save changes to the database
               db_conn.commit()
               log_str = "new location 'inbound place' of seat " + msg_recv['id'] + " saved in database."
               generateLog(log_str, '', '')

               # declare a confirmation message
               msg_send = {
                    'message': 'Acknowledge',
                    'id': seat_id
               }
           # send a message to the conveyor
           msg_send.update( {'timestamp' : currentTime()} )
           json_send = json.dumps(msg_send)
           con.send(json_send.encode())
           generateLog(threadName, 'send', str(json_send))

       # close the connection to the conveyor
       con.close()
       generateLog('disconnection', '', 'threadName')

    # task for the crane
    def crane_task(threadName, con, addr):
        generateLog('connection', '', threadName)

        while True:
            # receive a message from the crane
            json_recv = con.recv(1024).decode()
            msg_recv = json.loads(json_recv)

            # if no message is received, break
            if not msg_recv:
                break

            generateLog(threadName, 'recv', str(msg_recv))

            # check if the received message is a request message
            if msg_recv['message'] == 'Request for transport':
                # search the database for seats waiting for outbound
                cursor = db_conn.cursor()
                query_outbound = "SELECT id, y, x, direction FROM transport_units tu LEFT JOIN warehouse wh ON tu.id = wh.seat_id WHERE current_loc = 'WH' AND outbound_request = true"
                cursor.execute(query_outbound)
                db_record_outbound = cursor.fetchone()

                if db_record_outbound:
                    seat_id = db_record_outbound[0]
                    y = db_record_outbound[1]
                    x = db_record_outbound[2]
                    direction = db_record_outbound[3]
                    # check for the bin of outbound seat
                    if direction:
                        # declare an outbound order
                        msg_send = {
                            'message': 'Move to',
                            'from' : 'Warehouse',
                            'to' : 'Outbound_place',
                            'y' : y,
                            'x' : x,
                            'direction' : direction,
                            'id': seat_id
                        }
                    # if the bin of outbound seat cannot be found, save error to the database and declear a 'no operation' message
                    else:
                        generateLog('unknown location', '', str(seat_id)) 
                        query_flag_tu = "UPDATE transport_units SET current_loc = 'WH bin not found' WHERE id = %s"
                        cursor.execute(query_flag_tu, (seat_id,))
                        db_conn.commit()
                        log_str = "new location 'WH bin not found' of seat " + str(seat_id) + " saved in database."
                        generateLog(log_str, '', '')
                        msg_send = {
                            'message' : 'No operation'
                        }
                # if there is no seat waiting for outbound, check for seats waiting for inbound
                else:
                    # search database for seats waiting for inbound
                    query_inbound = "SELECT id FROM transport_units WHERE current_loc='Inbound_place'"
                    cursor.execute(query_inbound)
                    db_record_inbound = cursor.fetchone()

                    if db_record_inbound:
                        seat_id = db_record_inbound[0]
                        # search database for an empty bin
                        query_inbound_bin = "SELECT y, x, direction FROM warehouse WHERE seat_id IS NULL AND status IS NULL ORDER BY y, x"
                        cursor.execute(query_inbound_bin)
                        db_record_bin = cursor.fetchone()

                        y = db_record_bin[0]
                        x = db_record_bin[1]
                        direction = db_record_bin[2]
                        # declare an inbound order
                        msg_send = {
                            'message' : 'Move to',
                            'from' : 'Inbound_place',
                            'to' : 'Warehouse',
                            'y' : y,
                            'x' : x,
                            'direction' : direction,
                            'id': seat_id
                        }

                    # if there is no seat waiting for inbound, declare a 'no operation' message
                    else:
                        msg_send = {
                            'message': 'No operation'
                        }

            # check if the received message is a transport confirmation
            elif msg_recv['message'] == 'Moved':
                id = str(msg_recv['id'])
                seat_y = msg_recv['y']
                seat_x = msg_recv['x']
                seat_direction = str(msg_recv['direction'])

                cursor = db_conn.cursor()
                # check if the confirmation message concerns an outbound
                if msg_recv['from'] == 'Warehouse' and msg_recv['to'] == 'Outbound_place':
                    # update current location of the seat to 'outbound_place' and flag the bin as empty
                    query_outbound_done = "UPDATE transport_units SET outbound_request = false, current_loc = 'Outbound_place' WHERE id = %s"
                    query_outbound_done_2 = "UPDATE warehouse SET seat_id = NULL WHERE y = %s AND x = %s AND direction = %s"
                    cursor.execute(query_outbound_done, (id,))
                    cursor.execute(query_outbound_done_2, (seat_y, seat_x, seat_direction))
                    log_str = "new location 'outbound place' of seat " + id + " saved in database."
                    log_str_2 = 'bin y: ' + str(seat_y) + ', x: ' + str(seat_x) + ', direction: ' + seat_direction + ' flagged as empty.'
                # check if the confirmation message concerns an inbound
                elif msg_recv['from'] == 'Inbound_place' and msg_recv['to'] == 'Warehouse':
                    # update the current location of the seat to 'warehouse' and flag the bin as occupied
                    query_inbound_done = "UPDATE transport_units SET current_loc = 'WH' WHERE id=%s"
                    query_inbound_done_2 = "UPDATE warehouse SET seat_id = %s WHERE y = %s AND x = %s AND direction = %s"
                    cursor.execute(query_inbound_done, (id,))
                    cursor.execute(query_inbound_done_2, (id, seat_y, seat_x, seat_direction))
                    log_str = "new location 'warehouse' of seat " + str(id) + " saved in database."
                    log_str_2 = 'bin y: ' + str(seat_y) + ', x: ' + str(seat_x) + ', direction: ' + seat_direction + ' flagged as occupied.'

                # save changes to the database
                db_conn.commit()
                generateLog(log_str, '', '')
                generateLog(log_str_2, '', '') ###war auskommentiert??

                # declare a confirmation message
                msg_send = {
                    'message': 'Acknowledge',
                    'id': seat_id
                }

            # check if the received message is an empty error message
            elif msg_recv['message'] == 'Empty':
                generateLog('error', 'recv', str(msg_recv))
                seat_id = str(msg_recv['id'])
                seat_y = msg_recv['y']
                seat_x = msg_recv['x']
                seat_direction = str(msg_recv['direction'])
                # save the error in the database
                cursor = db_conn.cursor()
                query_flag_tu = "UPDATE transport_units SET current_loc = 'WH error empty' WHERE id = %s"
                query_wh_status = "UPDATE warehouse SET status = 'error empty' WHERE seat_id = %s"
                cursor.execute(query_flag_tu, (seat_id,))
                cursor.execute(query_wh_status, (seat_id,))
                # save changes to the databases
                db_conn.commit()
                log_str = "new location 'WH error empty' of seat " + seat_id + " saved in database"  #WH error empty oder nur error empty?
                log_str_2 = "status of bin of seat " + seat_id + " set to 'error empty'."
                generateLog(log_str, '', '')
                generateLog(log_str_2, '', '')

                # declare a confirmation message
                msg_send = {
                    'message': 'Acknowledge',
                    'id': seat_id
                }

            # check if the received message is an occupied error message
            elif msg_recv['message'] == 'Occupied':
                generateLog('error', 'recv', str(msg_recv))
                id = str(msg_recv['id'])
                seat_id = str(msg_recv['id'])
                seat_y = msg_recv['y']
                seat_x = msg_recv['x']
                seat_direction = str(msg_recv['direction'])
                # save the error in the database
                cursor = db_conn.cursor()
                query_wh_status = "UPDATE warehouse SET status = 'error occupied' WHERE y = %s AND x = %s AND direction = %s"
                cursor.execute(query_wh_status, (seat_y, seat_x, seat_direction))
                # save changes to the database
                db_conn.commit()
                log_str = "status of bin y: " + str(seat_y) + ", x: " + str(seat_x) + ", direction: " + seat_direction + " set to 'error occupied'."
                generateLog(log_str, '', '')
                # search the database for another empty bin
                query_alt_bin = "SELECT y, x, direction FROM warehouse WHERE seat_id IS NULL AND status IS NULL ORDER BY y, x"
                cursor.execute(query_alt_bin)
                db_record_bin = cursor.fetchone()
                y = db_record_bin[0]
                x = db_record_bin[1]
                direction = db_record_bin[2]
                # declare a transport message with new bin coordinates
                msg_send = {
                    'message' : 'Move to',
                    'from' : 'Inbound_place',
                    'to' : 'Warehouse',
                    'y' : y,
                    'x' : x,
                    'direction' : direction,
                    'id': id
                }
            # send a message to the crane
            msg_send.update( {'timestamp' : currentTime()} )
            json_send = json.dumps(msg_send)
            con.send(json_send.encode())
            generateLog(threadName, 'send', str(json_send))

        # close the connection to the crane
        con.close()
        generateLog('disconnection', '', 'threadName')


    while True:
        # accept a new socket connection
        conn, address = server_socket.accept()
        # test the connection
        json_recv = conn.recv(1024).decode()
        msg_recv = json.loads(json_recv)
        generateLog('connection test', 'recv', str(msg_recv))
        msg_send = str(msg_recv)
        json_send = json.dumps(msg_send)
        conn.send(json_send.encode())
        generateLog('connection test', 'send', str(msg_recv))
        # create a new thread
        if msg_recv == 'idp_client':
            _thread.start_new_thread(idp_task, ('idp_client', conn, address) )
        elif msg_recv == 'conveyor':
            _thread.start_new_thread(conveyor_task, ('conveyor', conn, address) )
        elif msg_recv == 'crane':
            _thread.start_new_thread(crane_task, ('crane', conn, address) )
        elif msg_recv == 'hmi':
            _thread.start_new_thread(hmi_task, ('hmi', conn, address))

# get the current timestamp
def currentTime():
    return str(datetime.now())

# generate log entries
def generateLog(status, action, json_str):
    log = '\n' + datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ' ' + status + ' ' + action + ' ' + json_str
    log_file = open("/var/log/server.log", "a")
    log_file.write(log)
    log_file.close()

if __name__ == '__main__':
    server_program()
