import json
from channels.generic.websocket import AsyncWebsocketConsumer


class JobRelayConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.job_id = str(self.scope["url_route"]["kwargs"]["job_id"])
        self.group_name = f"job-{self.job_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # Optional: handle incoming messages (like ping, debug)
        pass

    async def job_log_event(self, event):
        await self.send(
            text_data=json.dumps({"type": "log", "message": event["message"]})
        )
