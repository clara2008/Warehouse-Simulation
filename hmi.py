import tkinter as tk
import psycopg2
from tkinter import ttk
import sv_ttk
import socket
import time
import json
from datetime import datetime

def client_program():
	host = "host.docker.internal"
	port = 5000
	# wait for the server to boot the socket
	waiting_time = 4
	time.sleep(waiting_time)

	# create a connection to the server
	client_socket = socket.socket()
	client_socket.connect((host, port))
	client_name = 'hmi'

	 # test the connection
	msg_send = client_name
	json_send = json.dumps(msg_send)
	client_socket.send(json_send.encode())
	json_recv = client_socket.recv(1024).decode()
	msg_recv = json.loads(json_recv)

	#create the HMI
	createHMI(client_socket)

def createHMI(client_socket):
	# create the window
	root = tk.Tk()
	# set title and size
	root.title("Warehouse Data")
	root.geometry("1000x400")

	# set dark mode, source: https://github.com/rdbende/Sun-Valley-ttk-theme (Retrieved April 09, 2024)
	sv_ttk.set_theme("dark")
	set_style()
	root.after(0, set_style)
	update(root)

	# create a field for entering seat IDs for outbound requests
	entry_label = ttk.Label(root, text = "Enter Seat ID for Outbound:", font=('Calibri', 14))
	entry_label.pack()
	entry_label.place(x=5, y=290)
	entry = ttk.Entry(root, font=("Calibri", 14), width= 10)
	entry.pack()
	entry.place(x=240, y=280)

	# create the send button
	send_button = ttk.Button(root, text="Send", command=lambda: process_entry(entry, root, client_socket), style="TButton")
	send_button.pack()
	send_button.place(x=362, y=280)

	# create the button for updating the table
	update_button = ttk.Button(root, text="Update", command=lambda: update(root), style="TButton")
	update_button.pack()
	update_button.place(x=900, y=280)

	root.mainloop()

# process the entered seat ID
def process_entry(entry, root, client_socket):
    # get the input from the entry field
	input_text = entry.get()
	# create an outbound request
	outbound_request = {
		'message': 'Request for Outbound',
		'id' : input_text
	}
	outbound_request.update( {'timestamp' : currentTime()} )

	# clear the entry field
	entry.delete(0, tk.END)
	try:
		# check if the entered seat ID is in the correct format (five-digit number)
		if 1 <= int(input_text) <= 99999:
			msg_send = outbound_request
			json_send = json.dumps(msg_send)

            # send an outbound request to the server
			client_socket.send(json_send.encode())

			# receive a message from the server
			json_recv = client_socket.recv(1024).decode()
			msg_recv = json.loads(json_recv)

			if msg_recv['message'] == 'Seat will be transported to Outbound Place.':
				# display a label to confirm that the outbound request has been received
				confirmation_label = ttk.Label(root, text = 'Seat ' + msg_recv['id'] + ' will be transported to Outbound Place.', font=('Calibri', 14), foreground='#2dc722')
				confirmation_label.pack()
				confirmation_label.place(x=5, y=330)
				root.after(5000, lambda: destroy_label(confirmation_label))

		else:
			# if the entered number is not in the correct range, display a prompt to enter a correct seat ID
			error_label = ttk.Label(root, text = 'Please enter a correct Seat ID.', font=('Calibri', 14), foreground='#e82323')
			error_label.pack()
			error_label.place(x=5, y=330)
			root.after(5000, lambda: destroy_label(error_label))

	# if the entered text is not a number, display a prompt to enter a correct seat ID
	except ValueError:
		error_label = ttk.Label(root, text = 'Please enter a correct Seat ID.', font=('Calibri', 14), foreground='#e82323')
		error_label.pack()
		error_label.place(x=5, y=330)
		root.after(5000, lambda: destroy_label(error_label))

# allow to sort the columns for x and y coordinates
def sort_column(tree, col, reverse):
    data = [(tree.set(child, col), child) for child in tree.get_children('')]
    data.sort(reverse=reverse)
    for index, (_, child) in enumerate(data):
        tree.move(child, '', index)
    tree.heading(col, command=lambda: sort_column(tree, col, not reverse))


# update the displayed table
def update(root):
	# create a database connection
	db_conn = psycopg2.connect(
	database="postgres", user='postgres', password='docker', host='host.docker.internal', port='5432'
	)
	cursor = db_conn.cursor()

	# fetch all records from the warehouse table
	query = "SELECT x, y, direction, seat_id, status FROM warehouse ORDER BY x, y, direction"
	cursor.execute(query)
	records = cursor.fetchall()

	# remove the existing treeview widget
	for child in root.winfo_children():
	    if isinstance(child, ttk.Treeview):
	        child.destroy()

	# create a new treeview widget with the updated style
	tree = ttk.Treeview(root, style='Custom.Treeview')
	tree["columns"] = ("x", "y", "Direction", "Seat ID", "Status")
	tree["show"] = "headings"

	# add column names
	tree.heading("x", text="X", command=lambda: sort_column(tree, "x", False))
	tree.heading("y", text="Y", command=lambda: sort_column(tree, "y", False))
	tree.heading("Direction", text="Direction")
	tree.heading("Seat ID", text="Seat ID")
	tree.heading("Status", text="Status")

	# add records to the treeview
	for rec in records:
		# replace 'None' values
		rec_with_spaces = [item if item is not None else '-' for item in rec]
		tree.insert("", "end", values=rec_with_spaces)
	tree.pack()

	# close the connection to the database
	db_conn.close()

# remove the outbound confirmation label
def destroy_label(label):
	label.destroy()

# get the current timestamp
def currentTime():
    return str(datetime.now())

# set the style of the HMI components
def set_style():
	style = ttk.Style()
	style.configure("TButton", padding=4, font=("Calibri", 14, 'bold'), foreground='#7ad8fa')
	style.configure("Treeview.Heading",	background="#282828", foreground="#7ad8fa",	font=("Calibri", 16, "bold"))
	style.configure("Custom.Treeview", font=("Calibri", 13))

if __name__ == '__main__':
	client_program()
