import socket
import ssl
import threading
import time

# Configuration for the real POP3 server (Gmail)
POP3_SERVER = 'pop.gmail.com'
POP3_PORT = 995
GMAIL_USERNAME = 'testemailnetworks123@gmail.com'
GMAIL_PASSWORD = 'brcc einz quoc lvyi'

# Define the capabilities your server supports
capabilities = [
    "USER",
    "TOP",
    "UIDL",
    "RESP-CODES",
    "PIPELINING",
    "EXPIRE 60",
    "LOGIN-DELAY 180",
    "IMPLEMENTATION Custom POP3 Server"
]

# Example user data
users = {
    "kamo": {
        "password": "qwertyuiop"
    }
}

server_ssl_socket = None

def handle_capa_command():
    response = "+OK Capability list follows\r\n"
    for capability in capabilities:
        response += f"{capability}\r\n"
    response += ".\r\n"
    return response

def handle_user_command(user):
    global current_user
    if user in users:
        current_user = user
        return "+OK User accepted\r\n"
    else:
        return "-ERR No such user\r\n"

def handle_pass_command(password):
    global current_user
    if current_user and users[current_user]["password"] == password:
        return "+OK Mailbox locked and ready\r\n"
    else:
        return "-ERR Invalid password\r\n"
    
def handle_stat_command():
    # Send STAT command to the real POP3 server
    time.sleep(3)
    server_ssl_socket.sendall(b'STAT\r\n')
    response = server_ssl_socket.recv(4096)
    # print("Response to STAT command from server:", response.decode('utf-8'))
    return response

def handle_list_command():
    # Send LIST command to the real POP3 server
    server_ssl_socket.sendall(b'LIST\r\n')
    response = b""
    while True:
        part = server_ssl_socket.recv(4096)
        response += part
        if b"\r\n.\r\n" in part:
            break
    # print("Response to LIST command from server:", response.decode('utf-8'))
    return response

def handle_dele_command(email_id):
    # Send DELE command to the real POP3 server
    server_ssl_socket.sendall(f'DELE {email_id}\r\n'.encode())
    response = server_ssl_socket.recv(4096)
    print(f"Response to DELE command for email ID {email_id} from server:", response.decode('utf-8'))
    return response

def handle_retr_command(email_id):
    try:
        # Send RETR command to the real POP3 server
        server_ssl_socket.sendall(f'RETR {email_id}\r\n'.encode())
        response = b""
        
        while True:
            chunk = server_ssl_socket.recv(1024)
            response += chunk
            if not chunk:
                break
            response += chunk
            # Check if the end-of-message indicator is in the response
            if b"\r\n.\r\n" in response:
                break
        return response
    except Exception as e:
        print(f"Error handling RETR command for email ID {email_id}: {e}")
        return b"-ERR Failed to retrieve message\r\n"

def handle_uidl_command(email_id=None):
    if email_id:
        # Send UIDL command with a specific message number to the real POP3 server
        server_ssl_socket.sendall(f'UIDL {email_id}\r\n'.encode())
    else:
        # Send UIDL command to the real POP3 server
        server_ssl_socket.sendall(b'UIDL\r\n')
    
    response = b""
    while True:
        part = server_ssl_socket.recv(4096)
        response += part
        if b"\r\n.\r\n" in part:
            break
    print(f"Response to UIDL command from server:", response.decode('utf-8'))
    return response
    
def handle_client(client_socket):
    # Connect to the real POP3 server with SSL
    context = ssl.create_default_context()
    server_socket = socket.create_connection((POP3_SERVER, POP3_PORT))
    global server_ssl_socket
    server_ssl_socket = context.wrap_socket(server_socket, server_hostname=POP3_SERVER)

    # Login to Gmail using the provided credentials
    server_ssl_socket.sendall(f'USER {GMAIL_USERNAME}\r\n'.encode())
    server_ssl_socket.recv(4096)  # Read the response to the USER command

    server_ssl_socket.sendall(f'PASS {GMAIL_PASSWORD}\r\n'.encode())
    GMAIL_Response = server_ssl_socket.recv(4096).decode('utf-8').strip().upper()  # Read the response to the PASS command
    print (GMAIL_Response)

    # Wait for the "+OK Welcome" message from the Google POP3 server
    welcome_message = server_ssl_socket.recv(4096)
    print("Welcome message from server:", welcome_message.decode('utf-8'))

    client_socket.sendall(b"+OK POP3 server ready\r\n")
    while True:
        try:
            data = client_socket.recv(1024).decode('iso-8859-1').strip()
            if not data:
                break
            print(data)
            if data.upper().startswith("USER"):
                user = data[5:]
                response = handle_user_command(user)
            elif data.upper().startswith("PASS"):
                password = data[5:]
                response = handle_pass_command(password)
            elif data.upper() == "STAT":
                response = handle_stat_command()
            elif data.upper() == "LIST":
                response = handle_list_command()
            elif data.upper().startswith("RETR"):
                message_number = data[5:]
                response = handle_retr_command(message_number)
            elif data.upper().startswith("DELE"):
                message_number = data[5:]
                response = handle_dele_command(message_number)
            elif data.upper() == "CAPA":
                response = handle_capa_command()
            elif data.upper().startswith("UIDL"):
                    parts = data.split()
                    if len(parts) > 1:
                        email_id = parts[1]
                        response = handle_uidl_command(email_id)
                    else:
                        response = handle_uidl_command()
            elif data.upper() == "QUIT":
                client_socket.sendall(b"+OK Goodbye\r\n")
                break
            else:
                response = "-ERR Unknown command\r\n"
            if isinstance(response, str):
                response = response.encode('utf-8')
            client_socket.sendall(response)
        except BrokenPipeError:
            print("Client disconnected unexpectedly.")
            break
        
        

def run_server(host='0.0.0.0', port=55555):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow port reuse
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"POP3 server listening on {host}:{port}")
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        handle_client(client_socket)
if __name__ == "__main__":
    run_server()    

