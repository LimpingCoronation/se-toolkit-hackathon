import json

import redis.asyncio as redis

from .connection_manager import ConnectionManager


class RedisManager:
    def __init__(self, client: redis.Redis, connection_manager: ConnectionManager):
        self._client = client
        self._connection_manager = connection_manager
        self._pubsub = client.pubsub()
    
    async def subscribe(self, channel_id: str):
        await self._pubsub.subscribe(channel_id)
    
    async def send_message(self, channel_id: str, data: str):
        await self._client.publish(channel=channel_id, message=data)

    async def listener(self):
        print("Listening is launched!")

        async for msg in self._pubsub.listen():
            if msg['type'] == 'message':
                data = json.loads(msg['data'])
                print(data)
                if data['type'] == "update":
                    user_id = data.get('user_id')
                    service_id = data.get('service_id')
                    status = data.get('status')
                    await self._connection_manager.send_message(
                        int(user_id), 
                        message=f"{service_id}:{status}")
