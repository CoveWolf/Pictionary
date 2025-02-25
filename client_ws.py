# client_ws.py
#
# This is your Pygame client that connects via WebSockets (ws://).
# It can run as a normal Python script, *or* be compiled to WebAssembly
# with PyGBAG for in-browser play.

import pygame
import sys
import asyncio
import websockets

# Where to connect
SERVER_URI = "ws://localhost:1200"  # Adjust if server is on another machine/port

# Pygame setup
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pictionary Client - WebSockets")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
font = pygame.font.SysFont(None, 24)

class PictionaryClient:
    def __init__(self):
        self.running = True
        self.clock.tick(60)
        screen.fill(WHITE)
        self.secret_word = None
        self.guess_result = None
        
        self.drawing = False
        self.last_pos = None
        self.chat_input = ""
        
        pygame.display.flip()
        self.clock = pygame.time.Clock()

    async def connect_and_run(self):
        """
        Main async method: connect to the WebSocket server and handle events + drawing.
        """
        try:
            async with websockets.connect(SERVER_URI) as websocket:
                print("[CLIENT] Connected to WebSocket at", SERVER_URI)
                # Start a task to receive messages
                receive_task = asyncio.create_task(self.receive_messages(websocket))

                # Main loop
                while self.running:
                    self.clock.tick(60)  # limit to 60 fps

                    # Process Pygame events
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                            break
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            if event.button == 1:  # left click
                                self.drawing = True
                                self.last_pos = pygame.mouse.get_pos()
                        elif event.type == pygame.MOUSEBUTTONUP:
                            if event.button == 1:
                                self.drawing = False
                                self.last_pos = None
                        elif event.type == pygame.MOUSEMOTION:
                            if self.drawing:
                                current_pos = pygame.mouse.get_pos()
                                # Draw locally
                                pygame.draw.line(screen, BLACK, self.last_pos, current_pos, 5)
                                pygame.display.flip()
                                
                                x1, y1 = self.last_pos
                                x2, y2 = current_pos
                                # Send draw message
                                await self.send_draw_data(websocket, x1, y1, x2, y2)
                                
                                self.last_pos = current_pos
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_RETURN:
                                guess_text = self.chat_input.strip()
                                if guess_text:
                                    await self.send_guess(websocket, guess_text)
                                    self.chat_input = ""
                            elif event.key == pygame.K_BACKSPACE:
                                self.chat_input = self.chat_input[:-1]
                            else:
                                self.chat_input += event.unicode
                    
                    # Simple text input box
                    input_box_rect = pygame.Rect(10, HEIGHT - 30, WIDTH - 20, 20)
                    pygame.draw.rect(screen, WHITE, input_box_rect)
                    txt_surface = font.render(self.chat_input, True, BLACK)
                    screen.blit(txt_surface, (input_box_rect.x+5, input_box_rect.y+2))

                    # Show guess result (Correct!/Wrong guess!)
                    if self.guess_result:
                        result_surface = font.render(self.guess_result, True, RED)
                        screen.blit(result_surface, (10, HEIGHT - 60))

                    pygame.display.flip()

                # Cancel the receive task if still running
                receive_task.cancel()

        except websockets.ConnectionClosedError:
            print("[CLIENT] Connection closed unexpectedly.")
        except OSError as e:
            print(f"[CLIENT] Error connecting to server: {e}")

        finally:
            pygame.quit()
            sys.exit()

    async def receive_messages(self, websocket):
        """
        Wait for messages from the server and process them.
        """
        async for message in websocket:
            if message.startswith("SECRET_WORD:"):
                self.secret_word = message.split(":", 1)[1]
                print("[CLIENT] The secret word is:", self.secret_word)
            elif message.startswith("DRAW:"):
                coords = message.split(":", 1)[1]
                parts = coords.split(",")
                if len(parts) == 4:
                    try:
                        x1, y1, x2, y2 = map(int, parts)
                        pygame.draw.line(screen, BLACK, (x1, y1), (x2, y2), 5)
                        pygame.display.flip()
                    except ValueError:
                        print("[CLIENT] Invalid draw data:", coords)
            elif message.startswith("RESULT:"):
                result_text = message.split(":", 1)[1]
                if result_text == "CORRECT":
                    self.guess_result = "Correct!"
                else:
                    self.guess_result = "Wrong guess!"
            else:
                # Could be chat or something else
                pass

    async def send_draw_data(self, websocket, x1, y1, x2, y2):
        await websocket.send(f"DRAW:{x1},{y1},{x2},{y2}")

    async def send_guess(self, websocket, guess_text):
        await websocket.send(f"GUESS:{guess_text}")



def main():
    client = PictionaryClient()
    asyncio.run(client.connect_and_run())

if __name__ == "__main__":
    main()
