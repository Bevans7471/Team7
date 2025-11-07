#
# Software Engineering Project
# Sprint 4 - Team 7
#
import pygame
import sys
import socket
from db_players import get_player, save_player

# Initialize pygame
pygame.init()

# Color constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
GRAY = (150, 150, 150)
YELLOW = (255, 255, 0)

# Screen dimensions
WIDTH, HEIGHT = 1100, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Photon Laser Tag - Player Entry")

# Fonts
FONT = pygame.font.SysFont("arial", 24)
SMALL_FONT = pygame.font.SysFont("arial", 18)
FPS = 60

# UDP Configuration
BROADCAST_ADDRESS = "127.0.0.1"  # localhost
BROADCAST_PORT = 7500  # Transmit
RECEIVE_PORT = 7501    # Receive

# UDP Sockets
transmit_socket = None
receive_socket = None

# Track individual player scores
player_scores = {}

def init_udp_sockets():
    """Initialize UDP sockets for transmission and reception"""
    global transmit_socket, receive_socket

    transmit_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    transmit_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    transmit_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receive_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    receive_socket.bind(("0.0.0.0", RECEIVE_PORT))
    receive_socket.settimeout(0.1)

    print(f"[UDP] Transmit socket ready for {BROADCAST_ADDRESS}:{BROADCAST_PORT}")
    print(f"[UDP] Receive socket listening on 0.0.0.0:{RECEIVE_PORT}")

def udp_transmit(data):
    """Transmit data via UDP (single integer)"""
    global transmit_socket, BROADCAST_ADDRESS, BROADCAST_PORT
    try:
        message = str(data).encode('utf-8')
        transmit_socket.sendto(message, (BROADCAST_ADDRESS, BROADCAST_PORT))
        print(f"[UDP TX] Sent: {data} to {BROADCAST_ADDRESS}:{BROADCAST_PORT}")
        return True
    except Exception as e:
        print(f"[UDP TX] Error: {e}")
        return False

# --- Helper to update individual player scores ---
def update_player_score(player_id, points):
    """
    Update the score for a specific player.
    Automatically updates team score in display.
    """
    global player_scores
    if player_id not in player_scores:
        player_scores[player_id] = 0
    player_scores[player_id] += points
    print(f"[SCORE] Player {player_id} +{points}, new score: {player_scores[player_id]}")

# Splash screen
def show_splash():
    """Display the splash logo for 3 seconds"""
    logo = pygame.image.load("logo.jpg")
    logo = pygame.transform.scale(logo, (WIDTH, HEIGHT))
    screen.blit(logo, (0, 0))
    pygame.display.flip()
    pygame.time.wait(3000)

# --- Button class ---
class Button:
    """Clickable button class"""
    def __init__(self, x, y, w, h, color, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.text = text

    def draw(self, screen):
        """Draw button on screen"""
        pygame.draw.rect(screen, self.color, self.rect)
        label = FONT.render(self.text, True, BLACK)
        screen.blit(label, (self.rect.x + (self.rect.width - label.get_width()) // 2,
                            self.rect.y + (self.rect.height - label.get_height()) // 2))

    def is_clicked(self, pos):
        """Check if mouse click is within button"""
        return self.rect.collidepoint(pos)

# --- Input slot class ---
class InputSlot:
    """Text input slot for player ID or name"""
    def __init__(self, x, y, w, h, max_length, outline_color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.active = False
        self.max_length = max_length
        self.outline_color = outline_color

    def draw(self, screen):
        """Draw input slot with border highlighting if active"""
        pygame.draw.rect(screen, BLACK, self.rect)
        border_color = YELLOW if self.active else self.outline_color
        pygame.draw.rect(screen, border_color, self.rect, 2)
        label = FONT.render(self.text, True, WHITE)
        screen.blit(label, (self.rect.x + 5, self.rect.y + (self.rect.height - label.get_height()) // 2))

    def handle_event(self, event):
        """Handle keyboard input for this slot"""
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
                return "ENTER"
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < self.max_length:
                self.text += event.unicode
        return None

# --- Team class ---
class Team:
    """A team containing multiple player slots"""
    def __init__(self, color, start_x, start_y, slot_spacing, team_name):
        self.color = color
        self.team_name = team_name  # "red" or "green"
        self.slots = []
        for i in range(15):
            y = start_y + i * slot_spacing
            id_slot = InputSlot(start_x, y, 75, 30, 4, color)
            name_slot = InputSlot(start_x + 85, y, 200, 30, 14, color)
            self.slots.append((id_slot, name_slot))

    def draw(self, screen):
        """Draw all player slots"""
        for id_slot, name_slot in self.slots:
            id_slot.draw(screen)
            name_slot.draw(screen)

    def handle_click(self, pos):
        """Handle mouse click, activate the appropriate slot"""
        for id_slot, name_slot in self.slots:
            if id_slot.rect.collidepoint(pos):
                id_slot.active = True
                name_slot.active = False
                return id_slot, name_slot
            elif name_slot.rect.collidepoint(pos):
                name_slot.active = True
                id_slot.active = False
                return id_slot, name_slot
        return None, None

    def handle_event(self, event):
        """Handle keyboard events for slots"""
        for id_slot, name_slot in self.slots:
            result = id_slot.handle_event(event)
            if result == "ENTER":
                return "ID_ENTERED", id_slot, name_slot
            result = name_slot.handle_event(event)
            if result == "ENTER":
                # Save player to DB if both ID and name provided
                player_id = id_slot.text
                player_name = name_slot.text
                if player_id and player_name:
                    save_player(player_id, player_name)
                name_slot.active = False
        return None, None, None

    def clear(self):
        """Clear all slots for this team and remove assigned equipment"""
        global player_equipment
        for id_slot, name_slot in self.slots:
            player_id = id_slot.text.strip()
            if player_id in player_equipment:
                del player_equipment[player_id]
            id_slot.text = ""
            name_slot.text = ""

    def get_players(self):
        """Get list of players with ID, name, and equipment ID"""
        global player_equipment
        players = []
        for id_slot, name_slot in self.slots:
            if id_slot.text.strip() and name_slot.text.strip():
                player_id = id_slot.text.strip()
                codename = name_slot.text.strip()
                equipment_id = player_equipment.get(player_id)
                if equipment_id:  # Include only if they have equipment assigned
                    players.append({'player_id': player_id, 'codename': codename, 'equipment_id': equipment_id})
        return players

# --- Buttons ---
clear_red_button = Button(50, 640, 200, 50, RED, "Clear Red Team")
clear_green_button = Button(270, 640, 230, 50, GREEN, "Clear Green Team")
clear_all_button = Button(520, 640, 200, 50, GRAY, "Clear All")
start_button = Button(740, 640, 160, 50, YELLOW, "Start Game")

def clear_all_teams():
    """Clear all teams"""
    red_team.clear()
    green_team.clear()

# Initialize teams
red_team = Team(RED, 50, 100, 35, "red")
green_team = Team(GREEN, 600, 100, 35, "green")

# Dictionary to track player equipment assignment
player_equipment = {}

# Equipment popup variables
equip_popup_active = False
equip_text = ""
current_player = None

def draw_equip_popup():
    """Draw popup to enter equipment code"""
    popup_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 25, 300, 50)
    pygame.draw.rect(screen, WHITE, popup_rect)
    pygame.draw.rect(screen, YELLOW, popup_rect, 3)
    label = FONT.render(f"Enter Equipment Code: {equip_text}", True, BLACK)
    screen.blit(label, (popup_rect.x + 10, popup_rect.y + 10))

def pre_game_countdown():
    """Show a full-screen countdown before starting the play action display"""
    countdown = 5
    clock = pygame.time.Clock()
    last_tick = pygame.time.get_ticks()

    while countdown >= 0:
        screen.fill(BLACK)

        # Display countdown or Gametime
        if countdown > 0:
            text = FONT.render(f"Game starting in {countdown}", True, YELLOW)
        else:
            text = FONT.render("Gametime!", True, GREEN)

        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
        pygame.display.flip()
        clock.tick(FPS)

        # Quit events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Countdown tick every second
        current_time = pygame.time.get_ticks()
        if current_time - last_tick >= 1000:
            countdown -= 1
            last_tick = current_time

    # Fully clear the screen and events before switching
    screen.fill(BLACK)
    pygame.display.flip()
    pygame.event.clear()
    pygame.time.wait(0)
    print("[COUNTDOWN] Complete - transitioning to game screen.")

# --- Play action display ---
def play_action_display():
    """Display game action including team/player scores"""
    # Get players from both teams
    red_players = red_team.get_players()
    green_players = green_team.get_players()

    # Initialize player scores if not yet present
    for player in red_players + green_players:
        if player['player_id'] not in player_scores:
            player_scores[player['player_id']] = 0

    clock = pygame.time.Clock()
    running = True
    while running:
        screen.fill(BLACK)

        # Draw red team area (top left)
        red_rect = pygame.Rect(25, 50, 500, 280)
        pygame.draw.rect(screen, RED, red_rect, 3)
        red_label = FONT.render("Red Team", True, RED)
        screen.blit(red_label, (red_rect.x + (red_rect.width - red_label.get_width()) // 2, red_rect.y + 10))

        # Display red team total score
        red_team_score = sum(player_scores.get(p['player_id'], 0) for p in red_players)
        score_x_red = red_rect.x + red_rect.width - 50
        red_score_text = FONT.render(str(red_team_score), True, RED)
        screen.blit(red_score_text, (score_x_red - red_score_text.get_width() // 2, red_rect.y + 10))

        # Display individual red player scores
        y_offset = red_rect.y + 45
        for player in red_players:
            # Only display the player's codename
            player_text = SMALL_FONT.render(f"{player['codename']}", True, WHITE)
            screen.blit(player_text, (red_rect.x + 10, y_offset))
    
            # Player's individual score
            score_text = SMALL_FONT.render(str(player_scores.get(player['player_id'], 0)), True, WHITE)
            screen.blit(score_text, (score_x_red - score_text.get_width() // 2, y_offset))
            y_offset += 25

        # Draw green team area (top right)
        green_rect = pygame.Rect(575, 50, 500, 280)
        pygame.draw.rect(screen, GREEN, green_rect, 3)
        green_label = FONT.render("Green Team", True, GREEN)
        screen.blit(green_label, (green_rect.x + (green_rect.width - green_label.get_width()) // 2, green_rect.y + 10))

        # Display green team total score
        green_team_score = sum(player_scores.get(p['player_id'], 0) for p in green_players)
        score_x_green = green_rect.x + green_rect.width - 50
        green_score_text = FONT.render(str(green_team_score), True, GREEN)
        screen.blit(green_score_text, (score_x_green - green_score_text.get_width() // 2, green_rect.y + 10))

        # Display individual green player scores
        y_offset = green_rect.y + 45
        for player in green_players:
            player_text = SMALL_FONT.render(f"{player['codename']}", True, WHITE)
            screen.blit(player_text, (green_rect.x + 10, y_offset))
    
            # Player's individual score
            score_text = SMALL_FONT.render(str(player_scores.get(player['player_id'], 0)), True, WHITE)
            screen.blit(score_text, (score_x_green - score_text.get_width() // 2, y_offset))
            y_offset += 25

        # Draw event log area (bottom)
        event_rect = pygame.Rect(25, 350, 1050, 325)
        pygame.draw.rect(screen, WHITE, event_rect, 3)
        event_label = FONT.render("Current Game Action", True, WHITE)
        screen.blit(event_label, (event_rect.x + (event_rect.width - event_label.get_width()) // 2, event_rect.y + 10))

        # Placeholder text
        placeholder = SMALL_FONT.render("Game events will appear here...", True, GRAY)
        screen.blit(placeholder, (event_rect.x + 20, event_rect.y + 50))

        pygame.display.flip()
        clock.tick(FPS)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:
                    print("[GAME] Returning to player entry...")
                    running = False

# --- Main loop ---
def main():
    """Main player entry loop"""
    global equip_popup_active, equip_text, current_player
    active_slot = None

    while True:
        screen.fill(BLACK)

        # Draw headers
        screen.blit(FONT.render("Red Team", True, RED), (50, 60))
        screen.blit(FONT.render("Green Team", True, GREEN), (600, 60))

        # Draw teams
        red_team.draw(screen)
        green_team.draw(screen)

        # Draw buttons
        clear_red_button.draw(screen)
        clear_green_button.draw(screen)
        clear_all_button.draw(screen)
        start_button.draw(screen)

        # Draw equipment popup if active
        if equip_popup_active:
            draw_equip_popup()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for id_slot, name_slot in red_team.slots + green_team.slots:
                    id_slot.active = False
                    name_slot.active = False
                if clear_red_button.is_clicked(pos):
                    red_team.clear()
                elif clear_green_button.is_clicked(pos):
                    green_team.clear()
                elif clear_all_button.is_clicked(pos):
                    red_team.clear()
                    green_team.clear()
                elif start_button.is_clicked(pos):
                    print("Game starting...")
                    pre_game_countdown()
                    pygame.event.clear()
                    screen.fill(BLACK)
                    pygame.display.flip()
                    play_action_display()
                if not equip_popup_active:
                    active_slot, _ = red_team.handle_click(pos)
                    if not active_slot:
                        active_slot, _ = green_team.handle_click(pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:
                    print("F5 pressed - Starting game...")
                    pre_game_countdown()
                    pygame.event.clear()
                    screen.fill(BLACK)
                    pygame.display.flip()
                    play_action_display()
                elif event.key == pygame.K_F12:
                    print("F12 pressed - Clearing all entries...")
                    red_team.clear()
                    green_team.clear()

                elif equip_popup_active:
                    # Equipment code entry
                    if event.key == pygame.K_RETURN:
                        equipment_id = equip_text.strip()
                        player_id = current_player["id_text"]
                        codename = current_player["name_slot"].text

                        # Save player codename
                        if player_id and codename:
                            save_player(player_id, codename)

                        # Assign equipment locally
                        if equipment_id:
                            try:
                                equip_id_int = int(equipment_id)
                                player_equipment[player_id] = equip_id_int
                                udp_transmit(equip_id_int)
                                print(f"[PLAYER ENTRY] Player {codename} assigned equipment {equip_id_int}")
                            except ValueError:
                                print(f"[ERROR] Invalid equipment ID: {equipment_id}")

                        equip_text = ""
                        equip_popup_active = False
                        current_player["name_slot"].active = True
                        active_slot = current_player["name_slot"]

                    elif event.key == pygame.K_BACKSPACE:
                        equip_text = equip_text[:-1]
                    elif len(equip_text) < 6 and event.unicode.isdigit():
                        equip_text += event.unicode

                elif active_slot:
                    # Handle player ID/name input
                    for team in [red_team, green_team]:
                        result, id_slot, name_slot = team.handle_event(event)
                        if result == "ID_ENTERED":
                            player_id = id_slot.text
                            existing_name = get_player(player_id)
                            current_player = {"id_slot": id_slot, "name_slot": name_slot, "id_text": player_id, "team": team}
                            id_slot.active = False
                            active_slot = None
                            equip_popup_active = True
                            equip_text = ""
                            if existing_name:
                                name_slot.text = existing_name

        pygame.display.flip()

# --- Run ---
if __name__ == "__main__":
    init_udp_sockets()
    show_splash()
    main()
