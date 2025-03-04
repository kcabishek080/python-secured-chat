import ssl
import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSlot, Qt, QMetaObject, Q_ARG
from client_gui import ChatClientGUI
from client_crypto import CryptoManager
from login_gui import LoginSignupGUI
from db import create_table


class ChatClient:
    def __init__(self, gui, crypto_manager, username):
        self.gui = gui
        self.crypto_manager = crypto_manager
        self.username = username
        self.sock = None
        self.connected = False
        self.public_key_timer = None
        self.gui.disconnectButton.setEnabled(False)

        # Update window title to include username
        self.gui.setWindowTitle(f"Secure Chat - {username}")

        self.lock = threading.Lock()  # Synchronize access to the socket

        self.gui.connectButton.clicked.connect(self.connect_to_server)
        self.gui.disconnectButton.clicked.connect(self.disconnect_from_server)
        self.gui.sendButton.clicked.connect(self.send_message)

        # Connect the Enter key press to sending the message
        self.gui.messageInput.returnPressed.connect(self.send_message)  

        self.connect_button_order()

    def connect_to_server(self):
        host = self.gui.serverIpInput.text()
        port = self.gui.serverPortInput.text()

        if not host or not port:
            self.append_message("Please enter a valid IP and port.")
            return

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
# Uncomment here for SSL/TLS certificate---------------------
        
        # Wrap the socket with SSL/TLS
        # context = ssl.create_default_context()
        # context.verify_mode = ssl.CERT_REQUIRED
        # context.check_hostname = True 
        # context.load_verify_locations('path/to/fullchain.pem')

        # self.sock = context.wrap_socket(self.sock, server_hostname=host)

# ------------------------------------------------------------
        try:
            self.sock.connect((host, int(port)))
            self.connected = True
            self.append_message(f"Connected to server as {self.username}...")
            self.append_message("Waiting for your friend's connection...")
            self.gui.update_connection_status("Connecting")
            self.disconnect_button_order()

            threading.Thread(target=self.listen_for_messages, daemon=True).start()
        except Exception as e:
            self.append_message(f"Failed to connect to server: {e}")
            self.gui.update_connection_status("Disconnected")
            self.gui.disconnectButton.setEnabled(False)

    def disconnect_from_server(self):
        self.close_connection()
        self.connect_button_order()
        self.gui.update_connection_status("Disconnected")

    def listen_for_messages(self):
        try:
            while self.connected:
                message = self.sock.recv(4096).decode('utf-8')
                if not message:
                    continue

                if message.startswith("REQUEST_PUBLIC_KEY"):
                    self.send_public_key()
                elif message.startswith("PEER_PUBLIC_KEY"):
                    self.receive_peer_public_key(message)
                elif message.startswith("DISCONNECT"):
                    self.append_message("Disconnected from server.")
                    self.connected = False
                    self.connect_button_order()
                    self.gui.update_connection_status("Disconnected")
                else:
                    self.receive_message(message)
        except socket.error as e:
            if self.connected:
                self.append_message(f"Socket error: {e}")
                self.close_connection()
                self.connect_button_order()
                self.gui.update_connection_status("Disconnected")
        except Exception as e:
            if self.connected:
                self.append_message(f"Disconnected from server: {e}")
                self.close_connection()
                self.connect_button_order()
                self.gui.update_connection_status("Disconnected")

    def send_public_key(self):
        public_key = self.crypto_manager.get_public_key().decode('utf-8')
        self.sock.sendall(f"PUBLIC_KEY:{public_key}".encode('utf-8'))
        self.start_public_key_timer()

    def start_public_key_timer(self):
        if self.public_key_timer:
            self.public_key_timer.cancel()
        self.public_key_timer = threading.Timer(60.0, self.handle_public_key_timeout)
        self.public_key_timer.start()

    def handle_public_key_timeout(self):
        self.append_message("Public key exchange timed out. Disconnecting...")
        self.close_connection()
        self.connect_button_order()
        self.gui.update_connection_status("Disconnected")

    def receive_peer_public_key(self, message):
        if self.public_key_timer:
            self.public_key_timer.cancel()
        peer_public_key = message.split(":", 1)[1]
        self.crypto_manager.set_peer_public_key(peer_public_key)
        self.append_message("Your friend is now connected.")
        self.gui.update_connection_status("Connected")

        self.disconnect_button_order()

    def send_message(self):
        message = self.gui.messageInput.text()
        if message and self.crypto_manager.peer_public_key:
            encrypted_message = self.crypto_manager.encrypt_message(message)
            try:
                self.sock.sendall(encrypted_message.encode('utf-8'))
                self.gui.messageInput.clear()
                self.append_message(f"You: {message}")
            except Exception as e:
                self.append_message(f"Failed to send message: {e}")
                self.close_connection()
                self.connect_button_order()
                self.gui.update_connection_status("Disconnected")
        else:
            self.append_message("No peer public key set or empty message.")

    def receive_message(self, message):
        try:
            decrypted_message = self.crypto_manager.decrypt_message(message)
            if decrypted_message:  # Check if decrypted message is valid
                self.append_message(f"Peer: {decrypted_message}")
        except Exception as e:
            self.append_message(f"Failed to decrypt message: {e}")

    def close_connection(self):
        with self.lock:
            if self.connected:
                self.connected = False
                try:
                    self.sock.sendall("DISCONNECT".encode('utf-8'))
                except socket.error:
                    pass  # Ignore errors while sending disconnect
                finally:
                    try:
                        self.sock.close()
                    except socket.error:
                        pass  # Ignore errors while closing the socket
                self.append_message("Connection closed.")
        return  # Ensure no further processing

    def append_message(self, message):
        QMetaObject.invokeMethod(self.gui, "append_message", Qt.QueuedConnection, Q_ARG(str, message))

    def connect_button_order(self):
        self.gui.disconnectButton.setEnabled(False)
        self.gui.connectButton.setEnabled(True)
    
    def disconnect_button_order(self):
        self.gui.disconnectButton.setEnabled(True)
        self.gui.connectButton.setEnabled(False)


def main():
    # Create application
    app = QApplication(sys.argv)
    
    # Initialize database
    create_table()
    
    # Create login window
    login_window = LoginSignupGUI()
    
    # Function to handle successful login
    def on_login_successful(username):
        login_window.hide()
        
        # Create the chat GUI and client
        chat_gui = ChatClientGUI()
        crypto_manager = CryptoManager()
        client = ChatClient(chat_gui, crypto_manager, username)
        
        # Handle closing the window
        chat_gui.closeEvent = lambda event: (client.close_connection(), event.accept())
        
        chat_gui.show()
    
    # Connect the login_successful signal to our handler
    login_window.login_successful.connect(on_login_successful)
    
    # Show login window
    login_window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()