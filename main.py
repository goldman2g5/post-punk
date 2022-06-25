#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/8/19 13:38
# @Author  : CoderCharm
# @File    : main.py
# @Software: PyCharm
# @Github  : github/CoderCharm
# @Email   : wg_python@163.com
# @Desc    :
"""

https://stackoverflow.com/questions/15219858/how-to-store-a-complex-object-in-redis-using-redis-py

obj = ExampleObject()
pickled_object = pickle.dumps(obj)
r.set('some_key', pickled_object)
unpacked_object = pickle.loads(r.get('some_key'))
obj == unpacked_object



typing.Dict[key_type, value_type]

"""
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from time import monotonic as now
from fastapi import FastAPI
import sqlite3 as sl
from pydantic import BaseModel

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        # Sonline активированные ссылки
        self.active_connections: List[Dict[str, WebSocket]] = []

    async def connect(self, user: str, ws: WebSocket):
        # Связь
        await ws.accept()
        self.active_connections.append({"user": user, "ws": ws})

    def disconnect(self, user: str, ws: WebSocket):
        # Удалите объект WS во время удаления
        self.active_connections.remove({"user": user, "ws": ws})

    @staticmethod
    async def send_personal_message(message: dict, ws: WebSocket):
        # Отправить личное сообщение
        await ws.send_json(message)

    async def send_other_message(self, message: dict, user: str):
        # Отправить личное сообщение
        for connection in self.active_connections:
            if connection["user"] == user:
                await connection['ws'].send_json(message)

    async def broadcast(self, data: dict):
        #   сообщение
        for connection in self.active_connections:
            await connection['ws'].send_json(data)


manager = ConnectionManager()
pingpong = {}
pingpong["user1"] = now()
pingpong["user2"] = now()
pingpong["user3"] = now()

database = 'notifications.db'


def suka_convert(sql_result):
    result = []
    for i in sql_result:
        result.append({"id": i[0], "type": i[1], "title": i[2], "content": i[3], "lastSentAt": i[4]})
    return result


class Data_Create(BaseModel):
    id: int
    type: str
    title: str
    content: str


class Data_Edit(BaseModel):
    type: str
    title: str
    content: str


con = sl.connect(database)
with con:
    con.execute(
        " CREATE TABLE IF NOT EXISTS notifications_db (id integer, type varchar, title varchar, content varchar, lastSentAt datetime); ")
    con.execute(
        "INSERT INTO notifications_db (id, type, title, content, lastSentAt) values(0, 'SUCCESS', 'pipisya', 'postpunk', '2022-06-25 01:26:03.671048');")
con.close()

app = FastAPI()


@app.get("/api/notifications")
async def get():
    con = sl.connect(database)
    with con: data = con.execute("SELECT * FROM notifications_db;").fetchall()
    con.close()
    return suka_convert(data)


@app.post("/api/notifications")
async def post_create(recieved: Data_Create):
    recieved_data = list(dict(recieved).values())
    con = sl.connect(database)
    with con:
        data = con.execute("SELECT * FROM notifications_db;").fetchall()

    for i in data:
        if i[0] == recieved_data[0]:
            con.close()
            return 'Уведомление с таким id уже существует'
    with con:
        con.execute(
            f'insert into notifications_db (id, type, title, content) values ({recieved_data[0]}, "{recieved_data[1]}", "{recieved_data[2]}", "{recieved_data[3]}");')
    con.close()
    return 'Уведомление успешно создано'


@app.put("/api/notifications/{notification_id}")
async def put_edit(notification_id: int, recieved: Data_Edit):
    recieved_data = list(dict(recieved).values())
    con = sl.connect(database)
    with con:
        data = con.execute("SELECT * FROM notifications_db;").fetchall()

    for i in data:
        if i[0] == notification_id:
            with con: con.execute(
                f'update notifications_db set type = "{recieved_data[0] if i[1] != recieved_data[0] else i[1]}", title = "{recieved_data[1] if i[2] != recieved_data[1] else i[2]}", content = "{recieved_data[2] if i[3] != recieved_data[2] else i[3]}" where id = {notification_id};')
            con.close()
            return 'Уведомление успешно изменено'
    con.close()
    return 'Уведомления с данным id не существует'


@app.delete("/api/notifications/{notification_id}")
async def delete_notification(notification_id: int):
    con = sl.connect(database)
    with con:
        data = con.execute("SELECT * FROM notifications_db;").fetchall()

    for i in data:
        if i[0] == notification_id:
            with con: con.execute(f'delete from notifications_db where id = {notification_id}')
            con.close()
            return 'Уведомление успешно удалено'
    con.close()
    return 'Уведомления с данным id не существует'


@app.get("/api/notifications/{notification_id}/send", response_class=HTMLResponse)
async def send_notification(notification_id: int):
    con = sl.connect(database)
    with con:
        data = con.execute(f'SELECT * FROM notifications_db WHERE id = {notification_id};').fetchall()
        data = suka_convert(data)

    con.close()
    print(data[0]["content"])
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Чат 3</title>
</head>
<body>

<script>
    let ws = new WebSocket("ws://127.0.0.1:8010/ws/server");
    ws.onopen = function () {{
        let message = {{message: "{data[0]["content"]}", user: "server"}}
        let messageJson = JSON.stringify(message);
        ws.send(messageJson);
    }}
</script>
</body>
</html>
"""
    return HTMLResponse(content=html_content, status_code=200)



@app.websocket("/ws/{user}")
async def websocket_endpoint(ws: WebSocket, user: str):
    await manager.connect(user, ws)

    await manager.broadcast({"user": user, "message": "Вошел в чат"})

    try:
        while True:
            # if now() - pingpong["user1"] > 1:
            #     await manager.broadcast({"user": user, "message": "ping"})
            data = await ws.receive_json()
            print(data, type(data))
            # if data['message'] == "pong" and data.get('user') == user:
            #     pingpong['user1'] = now()
            send_user = data.get("send_user")
            if send_user:
                await manager.send_personal_message(data, ws)
                await manager.send_other_message(data, send_user)
            else:
                await manager.broadcast({"user": user, "message": data['message']})

    except WebSocketDisconnect:
        manager.disconnect(user, ws)
        await manager.broadcast({"user": user, "message": "Покинуть"})


if __name__ == "__main__":
    import uvicorn

    # Официальная рекомендация состоит в том, чтобы запустить UVICORN Главная: App --host = 127.0.0.1 --port = 8010 - Breload
    uvicorn.run(app='main:app', host="127.0.0.1", port=8010, reload=True, debug=True, ws_ping_interval=1000,
                ws_ping_timeout=3000)
