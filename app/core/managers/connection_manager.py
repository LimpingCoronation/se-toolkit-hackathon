from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    _connection: dict[int, WebSocket] = {}

    def connect(self, id: int, socket: WebSocket):
        self._connection[id] = socket
    
    def disconnect(self, id: int):
        if self._connection.get(id) is not None:
            del self._connection[id]
    
    def get(self, id: int):
        return self._connection.get(id)
    
    async def send_message(self, id: int, message: dict[Any, Any]):
        connection = self.get(id)
        if connection is not None:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(e)
