import socket
import ssl
import base64

# Configuration for the real SMTP server (Gmail)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'testemailnetworks123@gmail.com'
SMTP_PASSWORD = 'brcc einz quoc lvyi'

# SMTP Command Handlers
def handle_helo_command(domain):
    return f"250 Hello {domain}, pleased to meet you\r\n"

def handle_mail_command(sender):
    global current_sender
    current_sender = sender
    return f"250 {sender} ... Sender OK\r\n"

def handle_rcpt_command(recipient):
    global current_recipient
    current_recipient = recipient
    return f"250 {recipient} ... Recipient OK\r\n"

def handle_data_command(data):
    try:
        smtp_socket = socket.create_connection((SMTP_SERVER, SMTP_PORT))
        
        # Send EHLO and STARTTLS commands
        smtp_socket.sendall(b'HELO smtp.gmail.com\r\n')
        if not smtp_socket.recv(1024).startswith(b'220'):
            raise Exception("EHLO command failed")
        
        smtp_socket.sendall(b'STARTTLS\r\n')
        print(smtp_socket.recv(1024).decode('utf-8').strip())
        if not smtp_socket.recv(1024).startswith(b'220'):
            raise Exception("STARTTLS command failed")
        
        # Upgrade to SSL/TLS connection
        context = ssl.create_default_context()
        smtp_socket = context.wrap_socket(smtp_socket, server_hostname=SMTP_SERVER)
        
        smtp_socket.sendall(b'EHLO localhost\r\n')
        if not smtp_socket.recv(1024).startswith(b'250'):
            raise Exception("EHLO after STARTTLS command failed")

        # Authenticate
        smtp_socket.sendall(b'AUTH LOGIN\r\n')
        if not smtp_socket.recv(1024).startswith(b'334'):
            raise Exception("AUTH LOGIN command failed")
        
        smtp_socket.sendall(base64.b64encode(SMTP_USERNAME.encode()) + b'\r\n')
        if not smtp_socket.recv(1024).startswith(b'334'):
            raise Exception("Username not accepted")
        
        smtp_socket.sendall(base64.b64encode(SMTP_PASSWORD.encode()) + b'\r\n')
        if not smtp_socket.recv(1024).startswith(b'235'):
            raise Exception("Password not accepted")

        # Send email
        smtp_socket.sendall(f'MAIL FROM:{current_sender}\r\n'.encode('utf-8'))
        if not smtp_socket.recv(1024).startswith(b'250'):
            raise Exception("MAIL FROM command failed")
        
        smtp_socket.sendall(f'RCPT TO:{current_recipient}\r\n'.encode())
        if not smtp_socket.recv(1024).startswith(b'250'):
            raise Exception("RCPT TO command failed")
        
        # print(data)
        smtp_socket.sendall(b'DATA\r\n')
        if not smtp_socket.recv(1024).startswith(b'354'):
            raise Exception("DATA command failed")
        
        smtp_socket.sendall(data.encode() + b'\r\n.\r\n')
        response = smtp_socket.recv(1024)
        print(response)
        if not response.startswith(b'250'):
            raise Exception("Sending data failed")
        
        smtp_socket.sendall(b'QUIT\r\n')
        smtp_socket.close()
        return response
    except Exception as e:
        print(f"Error sending email: {e}")
        return b"-ERR Failed to send message\r\n"

def handle_client(client_socket):
    client_socket.sendall(b"220 SMTP server ready\r\n")
    while True:
        try:
            data = client_socket.recv(1024).decode('iso-8859-1').strip()
            if not data:
                break
            print(data)
            if data.upper().startswith("HELO"):
                domain = data[5:]
                response = handle_helo_command(domain)
            elif data.upper().startswith("MAIL FROM"):
                sender = data[10:]
                response = handle_mail_command(sender)
            elif data.upper().startswith("RCPT TO"):
                recipient = data[8:]
                response = handle_rcpt_command(recipient)
            elif data.upper() == "DATA":
                client_socket.sendall(b"354 End data with <CR><LF>.<CR><LF>\r\n")
                data = ""
                while True:
                    line = client_socket.recv(1024).decode('iso-8859-1').strip()
                    if line == ".":
                        break
                    data += line + "\r\n"
                response = handle_data_command(data)
            elif data.upper() == "QUIT":
                client_socket.sendall(b"221 Goodbye\r\n")
                break
            else:
                response = "502 Command not implemented\r\n"
            if isinstance(response, str):
                response = response.encode('utf-8')
            client_socket.sendall(response)
        except BrokenPipeError:
            print("Client disconnected unexpectedly.")
            break

def run_smtp_server(host='0.0.0.0', port=55556):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"SMTP server listening on {host}:{port}")
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        handle_client(client_socket)

if __name__ == "__main__":
    run_smtp_server()
