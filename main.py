# client_ws.py
#
# This is your Pygame client that connects via WebSockets (ws://).
# It can run as a normal Python script, or be compiled to WebAssembly
# with PyGBAG for in-browser play.

import pygame
import sys
import asyncio
import websockets

SERVER_URI = "ws://localhost:12000"  # Adjust if server is on another machine/port

# Basic Pygame setup
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
        # Create the clock FIRST
        self.clock = pygame.time.Clock()
        
        # Initial state
        self.running = True
        self.secret_word = None
        self.guess_result = None
        self.drawing = False
        self.last_pos = None
        self.chat_input = ""
        
        # Fill screen white immediately
        screen.fill(WHITE)
        pygame.display.flip()

    async def connect_and_run(self):
        """
        Connect to the WebSocket server and run the main Pygame loop.
        """
        try:
            # Connect to the server
            async with websockets.connect(SERVER_URI) as websocket:
                print("[CLIENT] Connected to WebSocket at", SERVER_URI)
                
                # Start a task to handle incoming messages
                receive_task = asyncio.create_task(self.receive_messages(websocket))

                # Main loop
                while self.running:
                    # Limit to 60 fps
                    self.clock.tick(60)
                    
                    # Clear screen each frame, so no black background remains
                    screen.fill(WHITE)
                    
                    # Debug text to confirm loop is running
                    debug_surface = font.render("Debug: Running (WASM)", True, RED)
                    screen.blit(debug_surface, (10, 10))
                    
                    # Process Pygame events
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                            break
                        
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            if event.button == 1:  # left-click
                                self.drawing = True
                                self.last_pos = pygame.mouse.get_pos()
                        
                        elif event.type == pygame.MOUSEBUTTONUP:
                            if event.button == 1:
                                self.drawing = False
                                self.last_pos = None
                        
                        elif event.type == pygame.MOUSEMOTION:
                            if self.drawing and self.last_pos:
                                current_pos = pygame.mouse.get_pos()
                                # Draw locally (black line on white)
                                pygame.draw.line(screen, BLACK, self.last_pos, current_pos, 5)
                                
                                # Send draw data
                                x1, y1 = self.last_pos
                                x2, y2 = current_pos
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
                    
                    # Simple text input box for guesses
                    input_box_rect = pygame.Rect(10, HEIGHT - 30, WIDTH - 20, 20)
                    pygame.draw.rect(screen, WHITE, input_box_rect)
                    
                    txt_surface = font.render(self.chat_input, True, BLACK)
                    screen.blit(txt_surface, (input_box_rect.x+5, input_box_rect.y+2))
                    
                    # Display guess results (Correct!/Wrong guess!)
                    if self.guess_result:
                        result_surface = font.render(self.guess_result, True, RED)
                        screen.blit(result_surface, (10, HEIGHT - 60))
                    
                    # Final flip for the frame
                    pygame.display.flip()

                # If we exit the loop, cancel the receive task
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
        Receive and handle messages from the server.
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
                        # Draw the line from another user
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
        """
        Send 'DRAW:' message to the server.
        """
        await websocket.send(f"DRAW:{x1},{y1},{x2},{y2}")

    async def send_guess(self, websocket, guess_text):
        """
        Send 'GUESS:' message to the server.
        """
        await websocket.send(f"GUESS:{guess_text}")

def main():
    client = PictionaryClient()
    asyncio.run(client.connect_and_run())

if __name__ == "__main__":
    main()
