import pygame
import socket
import threading
import sys

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5002

WIDTH, HEIGHT = 800, 600

pygame.init()
pygame.display.set_caption("Pictionary Client")

screen = pygame.display.set_mode((WIDTH, HEIGHT))

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)

font = pygame.font.SysFont(None, 24)

class PictionaryClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.running = True
        self.secret_word = None
        self.guess_result = None
        
        self.drawing = False
        self.last_pos = None
        
        self.chat_input = ""
        self.display_messages = []
    
    def connect_to_server(self):
        try:
            self.client_socket.connect((self.host, self.port))
            print("[CLIENT] Connected to server.")
        except Exception as e:
            print(f"[CLIENT] Failed to connect: {e}")
            sys.exit(1)

    def start_listening(self):
        thread = threading.Thread(target=self.listen_to_server, daemon=True)
        thread.start()
    
    def listen_to_server(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                message = data.decode("utf-8")
                
                if message.startswith("SECRET_WORD:"):
                    self.secret_word = message.split(":", 1)[1]
                    print(f"[CLIENT] The secret word is: {self.secret_word}")
                
                elif message.startswith("DRAW:"):
                    coords = message.split(":", 1)[1]  # e.g. "100,200,120,220"
                    parts = coords.split(",")
                    
                    # Check we actually have 4 items
                    if len(parts) == 4:
                        try:
                            x1, y1, x2, y2 = map(int, parts)
                            pygame.draw.line(screen, BLACK, (x1, y1), (x2, y2), 5)
                            pygame.display.flip()
                        except ValueError:
                            print(f"[CLIENT] Invalid draw coordinates: {coords}")
                    else:
                        print(f"[CLIENT] Malformed DRAW message, ignoring: {message}")
                
                elif message.startswith("RESULT:"):
                    result_text = message.split(":", 1)[1]
                    if result_text == "CORRECT":
                        self.guess_result = "Correct!"
                    else:
                        self.guess_result = "Wrong guess!"
                
                else:
                    # Possibly handle chat messages or other data
                    pass
                
            except ConnectionResetError:
                print("[CLIENT] Connection lost.")
                self.running = False
                break
        
        self.running = False
        self.client_socket.close()
    
    def send_draw_data(self, x1, y1, x2, y2):
        message = f"DRAW:{x1},{y1},{x2},{y2}"
        try:
            self.client_socket.sendall(message.encode("utf-8"))
        except:
            print("[CLIENT] Failed to send draw data.")
            self.running = False

    def send_guess(self, guess_text):
        message = f"GUESS:{guess_text}"
        try:
            self.client_socket.sendall(message.encode("utf-8"))
        except:
            print("[CLIENT] Failed to send guess.")
            self.running = False
    
    def run_game_loop(self):
        clock = pygame.time.Clock()
        screen.fill(WHITE)
        
        while self.running:
            clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.drawing = True
                        self.last_pos = pygame.mouse.get_pos()
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left click
                        self.drawing = False
                        self.last_pos = None
                elif event.type == pygame.MOUSEMOTION:
                    if self.drawing:
                        current_pos = pygame.mouse.get_pos()
                        pygame.draw.line(screen, BLACK, self.last_pos, current_pos, 5)
                        pygame.display.flip()
                        
                        x1, y1 = self.last_pos
                        x2, y2 = current_pos
                        self.send_draw_data(x1, y1, x2, y2)
                        
                        self.last_pos = current_pos
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        guess_text = self.chat_input.strip()
                        if guess_text:
                            self.send_guess(guess_text)
                            self.chat_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.chat_input = self.chat_input[:-1]
                    else:
                        self.chat_input += event.unicode
            
            # Render a basic input box
            screen_rect = screen.get_rect()
            input_box_rect = pygame.Rect(10, HEIGHT - 30, WIDTH - 20, 20)
            pygame.draw.rect(screen, WHITE, input_box_rect)
            txt_surface = font.render(self.chat_input, True, BLACK)
            screen.blit(txt_surface, (input_box_rect.x + 5, input_box_rect.y + 2))
            
            if self.guess_result:
                result_surface = font.render(self.guess_result, True, RED)
                screen.blit(result_surface, (10, HEIGHT - 60))
            
            pygame.display.flip()
        
        pygame.quit()

def main():
    client = PictionaryClient(SERVER_HOST, SERVER_PORT)
    client.connect_to_server()
    client.start_listening()
    client.run_game_loop()

if __name__ == "__main__":
    main()
