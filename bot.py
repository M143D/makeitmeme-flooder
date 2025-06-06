import requests
import random
import string
import asyncio
import websockets

def generate_random_username(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

def get_random_avatar():
    try:
        with open("avatar.txt", "r") as f:
            avatars = [line.strip() for line in f if line.strip()]
        if avatars:
            return random.choice(avatars)
        else:
            return "113d8b13-6260-4aae-86e9-5eab8dacdfe3"
    except Exception:
        return "113d8b13-6260-4aae-86e9-5eab8dacdfe3"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

HEADERS = {
    "User-Agent": get_random_user_agent(),
    "Origin": "https://makeitmeme.com"
}

def join_matchmaking(code, username):
    url = f"https://gs.makeitmeme.com/matchmake/joinById/{code}"
    payload = {
        "accessToken": None,
        "avatar": get_random_avatar(),
        "clientId": "",
        "clientVersion": "2.0.2",
        "env": "prod",
        "username": username
    }
    try:
        response = requests.post(url, json=payload, headers=HEADERS)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

async def send_keepalive(websocket, username, interval=2):
    while True:
        try:
            await asyncio.sleep(interval)
            keep_alive_message = b'\x0d\xa4\x70\x69\x6e\x67\x80'
            await websocket.send(keep_alive_message)
            print(f"[+] send keep alive request for {username}")
        except Exception:
            break

# solver <3
async def connect_to_websocket(ws_url, username, session_time=10):
    try:
        async with websockets.connect(ws_url, extra_headers=HEADERS) as websocket:
            await websocket.send(b'\x0a')
            keepalive_task = asyncio.create_task(send_keepalive(websocket, username, interval=2))
            start_time = asyncio.get_event_loop().time()
            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= session_time:
                    break
                try:
                    remaining = session_time - elapsed
                    message = await asyncio.wait_for(websocket.recv(), timeout=remaining)
                    if b"seat reservation expired" in message:
                        break
                except asyncio.TimeoutError:
                    break
            keepalive_task.cancel()
    except Exception:
        pass

async def async_session(session_number, code, session_duration):
    username = generate_random_username()
    join_response = await asyncio.to_thread(join_matchmaking, code, username)
    if not join_response:
        return
    print(f"[+] joined {username}")
    room_data = join_response.get("room", {})
    session_id = join_response.get("sessionId")
    process_id = room_data.get("processId")
    room_id = room_data.get("roomId")
    public_address = room_data.get("publicAddress")
    if not (session_id and process_id and room_id and public_address):
        return
    ws_url = f"wss://{public_address}/{process_id}/{room_id}?sessionId={session_id}"
    await connect_to_websocket(ws_url, username, session_time=session_duration)

async def async_main(code, num_sessions, session_duration):
    tasks = [
        async_session(session_number=i + 1, code=code, session_duration=session_duration)
        for i in range(num_sessions)
    ]
    await asyncio.gather(*tasks)

def main():
    code = input("Please enter the matchmaking code: ").strip()
    try:
        num_sessions = int(input("How many concurrent sessions to create? "))
    except ValueError:
        return
    try:
        session_duration = int(input("How many seconds should each session last? "))
    except ValueError:
        session_duration = 10
    asyncio.run(async_main(code, num_sessions, session_duration))

if __name__ == '__main__':
    main()
