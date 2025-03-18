import asyncio

class EmoteConnect:
    # Define server address and port (similar to C# constants)
    server_address = '127.0.0.1'
    server_port = 7777

    # These will hold our persistent connection reader and writer
    _reader = None
    _writer = None

    # A lock to ensure that connection setup is thread-safe
    _connection_lock = asyncio.Lock()

    @classmethod
    async def connect(cls):
        """
        Establish a persistent TCP connection to the server.
        Called on load or when a reconnection is needed.
        """
        try:
            # Open a TCP connection (like TcpClient in C#)
            cls._reader, cls._writer = await asyncio.open_connection(
                cls.server_address, cls.server_port
            )
            print(f"Connected to UnrealEngine emote receiver {cls.server_address}:{cls.server_port}")
        except Exception as ex:
            print(f"Error while connecting to server: {ex}")
            cls._reader, cls._writer = None, None

    @classmethod
    async def send_emote(cls, emote_name: str):
        """
        Sends the provided emote name using the persistent connection.
        If the connection is not established or fails, it will reconnect.
        """
        # Validate the emote name (ensures no empty or whitespace-only strings)
        if not emote_name.strip():
            print("Emote name is invalid or empty.")
            return

        # Lock to prevent concurrent connection attempts or writes.
        async with cls._connection_lock:
            # Check if we have an active connection, otherwise attempt to connect.
            if cls._writer is None or cls._writer.is_closing():
                await cls.connect()

            if cls._writer is None:
                print("Failed to connect to the server, cannot send emote.")
                return

            try:
                # Convert the emote to bytes, trimming any extra spaces.
                message_bytes = emote_name.strip().encode('utf-8')
                cls._writer.write(message_bytes)
                await cls._writer.drain()  # Ensure the message is sent
                print(f"Successfully sent emote: {emote_name}")
            except Exception as ex:
                print(f"Error while sending emote: {ex}")
                # On error, close the connection to force a reconnection on the next attempt.
                if cls._writer:
                    cls._writer.close()
                    try:
                        await cls._writer.wait_closed()
                    except Exception:
                        pass
                cls._writer = None

# Example usage:
# To run this example, ensure you have an active asyncio event loop.
# You can test the send_emote functionality as follows:

if __name__ == "__main__":
    async def main():
        # Example: Send a single emote "Wave" using the persistent connection.
        await EmoteConnect.send_emote("Wave")
    
    asyncio.run(main())
