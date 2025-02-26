# server_ws.py
import asyncio
import random
import websockets

# A small word list
WORDS = ["apple", "banana", "cat", "dog", "python", "rocket", "house", "keyboard"]

secret_word = random.choice(WORDS)
print(f"[SERVER] Secret word: {secret_word}")

connected_clients = set()

async def handler(websocket):
    """
    Handle each new WebSocket connection.
    """
    # Send the secret word (in real Pictionary, only the 'drawer' sees this)
    await websocket.send(f"SECRET_WORD:{secret_word}")
    
    connected_clients.add(websocket)
    print("[SERVER] A client connected.")
    
    try:
        while True:
            
            # Wait for a message from this client
            message = await websocket.recv()

            # If it's a DRAW message, broadcast it to everyone else
            if message.startswith("DRAW:"):
                for client in connected_clients:
                    if client != websocket:
                        await client.send(message)

            # If it's a GUESS message, respond with RESULT
            elif message.startswith("GUESS:"):
                guess_word = message.split(":", 1)[1].strip().lower()
                if guess_word == secret_word:
                    await websocket.send("RESULT:CORRECT")
                else:
                    await websocket.send("RESULT:WRONG")

            else:
                # Unknown message type; ignore or handle differently
                pass

    except websockets.ConnectionClosed:
        print("[SERVER] A client disconnected.")
    finally:
        connected_clients.remove(websocket)

async def main():
    print("[SERVER] Starting WebSocket server on port 12000...")
    async with websockets.serve(handler, "0.0.0.0", 12000):
        print("[SERVER] WebSocket server listening at ws://0.0.0.0:12000")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
