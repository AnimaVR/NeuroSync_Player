# This software is licensed under a **dual-license model**
# For individuals and businesses earning **under $1M per year**, this software is licensed under the **MIT License**
# Businesses or organizations with **annual revenue of $1,000,000 or more** must obtain permission to use this software commercially.

import socket
from config import EMOTE_SERVER_ADDRESS, EMOTE_SERVER_PORT

class EmoteConnect:
    # Use configuration values from config.py
    server_address = EMOTE_SERVER_ADDRESS
    server_port = EMOTE_SERVER_PORT

    @classmethod
    def send_emote(cls, emote_name: str):
        """
        Sends the provided emote name.
        This function creates a new connection each time, similar to the C# implementation.
        """
        # Validate the emote name (ensures no empty or whitespace-only strings)
        if not emote_name.strip():
            print("Emote name is invalid or empty.")
            return

        try:
            # Create a new socket for each connection (mirroring the C# TcpClient behavior)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((cls.server_address, cls.server_port))
                # Convert the emote name to bytes (UTF-8 encoded) after trimming whitespace
                message_bytes = emote_name.strip().encode('utf-8')
                # Send the emote (using sendall to ensure all data is sent)
                client.sendall(message_bytes)
        except Exception as ex:
            print(f"Error while sending emote: {ex}")



'''
EmoteConnect.send_emote("Wave")

# To send an emote on its own thread (non-blocking):
thread = threading.Thread(target=EmoteConnect.send_emote, args=("Wave",))
thread.start()

'''
