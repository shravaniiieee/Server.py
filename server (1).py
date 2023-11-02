import socket
import threading
import os

# Configuration
HOST = '0.0.0.0'
PORT = 6555
LISTENER_LIMIT = 5
received_files_directory = 'received_files'

if not os.path.exists(received_files_directory):
    os.makedirs(received_files_directory)

active_clients = {}

# Function to listen for upcoming messages from a client
def listen_for_messages(client, username):
    while True:
        try:
            message = client.recv(2048).decode('utf-8')
            if message:
                final_msg = f"{username}~{message}"
                send_messages_to_all(final_msg)
            else:
                remove_client(username)
        except ConnectionResetError:
            remove_client(username)

# Function to send message to a single client
def send_message_to_client(client, message):
    client.sendall(message.encode())

# Function to send any new message to all the clients that
# are currently connected to this server
def send_messages_to_all(message):
    for user, user_data in active_clients.items():
        client, _ = user_data
        send_message_to_client(client, message)

# Function to handle client
def client_handler(client):
    while True:
        try:
            credentials = client.recv(2048).decode('utf-8')
            if credentials:
                username, password = credentials.split('~')
                print(username)
                print(password)
                if authenticate_user(username, password):
                    active_clients[username] = (client, '')
                    prompt_message = "SERVER~" + f"{username} added to the chat"
                    send_messages_to_all(prompt_message)
                    send_existing_users(client)
                    client.send("SERVER~Authentication successful".encode())  # Send success response
                    break
                else:
                    client.send("SERVER~Authentication failed".encode())  # Send failure response
                    return
        except ConnectionResetError:
            return

# Function to handle file transfers from clients
def handle_file_transfer(client, username):
    try:
        filename = client.recv(1024).decode('utf-8')
        if not filename:
            return

        with open(os.path.join(received_files_directory, filename), 'wb') as file:
            while True:
                file_data = client.recv(1024)
                if file_data == b"END_OF_FILE":
                    break
                file.write(file_data)

        client.send(b"File received successfully.")
        send_message_to_client(client, "SERVER~File received successfully.")
    except Exception as e:
        print(f"Error during file transfer: {e}")

# Function to remove a client
def remove_client(username):
    if username in active_clients:
        del active_clients[username]
        prompt_message = "SERVER~" + f"{username} left the chat"
        send_messages_to_all(prompt_message)

# Function to send a list of existing users to a client
def send_existing_users(client):
    user_list = "SERVER~Existing Users: " + ', '.join(active_clients.keys())
    send_message_to_client(client, user_list)

# Function to authenticate a user
def authenticate_user(username, password):
    if username in user_credentials:
        if password == user_credentials[username]:
            return True
    return False

# Main function
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        print(f"Running the server on {HOST}:{PORT}")
    except Exception as e:
        print(f"Unable to bind to host {HOST} and port {PORT}: {e}")
        return

    server.listen(LISTENER_LIMIT)

    while True:
        client, address = server.accept()
        print(f"Successfully connected to client {address[0]}:{address[1]}")
        threading.Thread(target=client_handler, args=(client,)).start()
        threading.Thread(target=handle_file_transfer, args=(client, 'Server')).start()

if __name__ == '__main__':
    main()
