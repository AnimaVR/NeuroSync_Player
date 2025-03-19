import socket

class EmoteConnect:
    server_address = '127.0.0.1'
    server_port = 7777

    @classmethod
    def send_emote(cls, emote_name: str):
        """
        Sends the provided emote name.
        This function creates a new connection each time, just like the C# implementation.
        """
        # Validate the emote name (ensures no empty or whitespace-only strings)
        if not emote_name.strip():
            print("Emote name is invalid or empty.")
            return

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((cls.server_address, cls.server_port))
              #  print(f"Connected to UnrealEngine emote receiver {cls.server_address}:{cls.server_port}")
                message_bytes = emote_name.strip().encode('utf-8')
                client.sendall(message_bytes)
             #   print(f"Successfully sent emote: {emote_name}")

        except Exception as ex:
            print(f"Error while sending emote: {ex}")


'''
EmoteConnect.send_emote("Wave")

# To send an emote on its own thread (non-blocking):
thread = threading.Thread(target=EmoteConnect.send_emote, args=("Wave",))
thread.start()

'''
