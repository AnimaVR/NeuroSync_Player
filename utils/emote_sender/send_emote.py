import socket
import threading

class EmoteConnect:
    # Define server address and port (similar to C# constants)
    server_address = '127.0.0.1'
    server_port = 7777

    # This will hold our persistent connection socket
    _socket = None

    # A lock to ensure that connection setup and sending is thread-safe
    _lock = threading.Lock()

    @classmethod
    def connect(cls):
        """
        Establish a persistent TCP connection to the server.
        Called on load or when a reconnection is needed.
        """
        try:
            # Create a new socket using IPv4 and TCP (similar to TcpClient in C#)
            cls._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cls._socket.connect((cls.server_address, cls.server_port))
            print(f"Connected to UnrealEngine emote receiver {cls.server_address}:{cls.server_port}")
        except Exception as ex:
            print(f"Error while connecting to server: {ex}")
            cls._socket = None

    @classmethod
    def send_emote(cls, emote_name: str):
        """
        Sends the provided emote name using the persistent connection.
        If the connection is not established or fails, it will reconnect.
        """
        # Validate the emote name (ensures no empty or whitespace-only strings)
        if not emote_name.strip():
            print("Emote name is invalid or empty.")
            return

        with cls._lock:
            # If there is no active connection, attempt to connect.
            if cls._socket is None:
                cls.connect()

            if cls._socket is None:
                print("Failed to connect to the server, cannot send emote.")
                return

            try:
                # Convert the emote name to bytes (UTF-8 encoded) after trimming whitespace.
                message_bytes = emote_name.strip().encode('utf-8')
                # Send the emote (blocking call)
                cls._socket.sendall(message_bytes)
                print(f"Successfully sent emote: {emote_name}")
            except Exception as ex:
                print(f"Error while sending emote: {ex}")
                # On error, close the connection to force a reconnection on the next attempt.
                try:
                    cls._socket.close()
                except Exception:
                    pass
                cls._socket = None


'''
EmoteConnect.send_emote("Wave")

# To send an emote on its own thread (non-blocking):
thread = threading.Thread(target=EmoteConnect.send_emote, args=("Wave",))
thread.start()

'''
