import asyncio
import os
import json

import redis.asyncio as redis
import aiohttp
from dotenv import load_dotenv

load_dotenv()

jobs: dict[str, str] = {}

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
pubsub = redis_client.pubsub()


def update_event(user_id: str, service_id: str, status: int) -> dict:
    return {
        "type": "update",
        "status": status,
        "user_id": user_id,
        "service_id": service_id
    }


async def listen():
    await pubsub.subscribe("main")

    async for msg in pubsub.listen():
        print(msg)
        if msg['type'] == 'message':
            data = json.loads(msg['data'])
            if data['type'] == "start_translation":
                key = str(data['user_id']) + ":" + str(data["service_id"])
                jobs[key] = data['url']
            if data['type'] == "stop_translation":
                key = str(data['user_id']) + ":" + str(data["service_id"])
                if jobs.get(key) is not None:
                    del jobs[key]


async def check_api():
    timeout = aiohttp.ClientTimeout(total=0.5)

    while True:
        await asyncio.sleep(10)
        for key, value in jobs.items():
            split_key = key.split(':')
            user_id = split_key[0]
            service_id = split_key[1]

            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    async with session.get(value) as response:
                        if response.status == 500:
                            await redis_client.publish("main", json.dumps(update_event(user_id, service_id, 0)))
                        else:
                            await redis_client.publish("main", json.dumps(update_event(user_id, service_id, 1)))
                except asyncio.TimeoutError:
                    await redis_client.publish("main", json.dumps(update_event(user_id, service_id, 0)))
                except:
                    await redis_client.publish("main", json.dumps(update_event(user_id, service_id, 0)))


async def main():
    await asyncio.gather(listen(), check_api())


if __name__ == '__main__':
    print("Worker is launched!")
    asyncio.run(main())
