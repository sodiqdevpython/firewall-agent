# components/ConnectServer.py
import asyncio
import websockets

class ConnectServer:
    def __init__(self, bios_uuid: str, server_url="ws://localhost:8000/ws/device/"):
        self.bios_uuid = bios_uuid
        self.server_url = f"{server_url}{bios_uuid}/"
        self.reconnect_interval = 5

    async def run(self):
        while True:
            try:
                print(f"🔗 Connecting to server for device {self.bios_uuid}...")
                websocket = await websockets.connect(self.server_url)
                print(f"✅ Connected - Device ONLINE")

                while True:
                    await asyncio.sleep(10)
            except Exception as e:
                print(f"⚠️ Unexpected error: {e}. Retrying in {self.reconnect_interval} seconds...")
