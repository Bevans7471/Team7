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
pygame.display.set_caption("Photon Laser Tag")

# Fonts
FONT = pygame.font.SysFont("arial", 24)
SMALL_FONT = pygame.font.SysFont("arial", 18)
FPS = 60

# UDP Configuration
BROADCAST_ADDRESS = "127.0.0.1"  # localhost
BROADCAST_PORT = 7500  # Transmit
RECEIVE_PORT = 7501  # Receive

# UDP Sockets
transmit_socket = None
receive_socket = None

# Track individual player scores
player_scores = {}

# Player team
equipment_teams = {}
equipment_to_player = {}
base_icons = {}

# messages for game action box
game_messages = []
MAX_MESSAGES = 13


def init_udp_sockets():
    """Initialize UDP sockets for transmission and reception"""
    global transmit_socket, receive_socket

    transmit_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    transmit_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    transmit_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receive_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    receive_socket.bind(("0.0.0.0", RECEIVE_PORT))
    receive_socket.setblocking(False)

    print(f"[UDP] Transmit socket ready for {BROADCAST_ADDRESS}:{BROADCAST_PORT}")
    print(f"[UDP] Receive socket listening on 0.0.0.0:{RECEIVE_PORT}")


def udp_transmit(equipment_id):
    """Transmit equipment ID via UDP"""
    global transmit_socket, BROADCAST_ADDRESS, BROADCAST_PORT
    try:
        message = str(equipment_id).encode('utf-8')
        transmit_socket.sendto(message, (BROADCAST_ADDRESS, BROADCAST_PORT))
        print(f"[UDP TX] Sent: {equipment_id}")
        return True
    except Exception as e:
        print(f"[UDP TX] Error: {e}")
        return False


def update_player_score(player_id, points):
    """Update the score for a specific player"""
    global player_scores
    if player_id not in player_scores:
        player_scores[player_id] = 0
    player_scores[player_id] += points
    print(f"[SCORE] Player {player_id} {points:+d}, new score: {player_scores[player_id]}")

def add_game_message(message):
    global game_messages
    game_messages.append(message)
    if len(game_messages) > MAX_MESSAGES:
        game_messages.pop(0)  # remove oldest message

# Track last shooter for base scoring
last_shooter_equipment = None


def receive_udp_messages():
    """Non-blocking receive of UDP messages"""
    global receive_socket, last_shooter_equipment

    try:
        while True:
            data, addr = receive_socket.recvfrom(4096)
            message = data.decode('utf-8').strip()
            print(f"[UDP RX] Received: {message}")

            # Check for base codes
            if message == "53":
                # Red base scored - award green team player who last shot
                handle_base_score("green", 53)
                continue
            elif message == "43":
                # Green base scored - award red team player who last shot
                handle_base_score("red", 43)
                continue

            # Analize hit data
            if ":" in message:
                parts = message.split(":")
                if len(parts) == 2:
                    try:
                        shooter_equip = int(parts[0])
                        target_equip = int(parts[1])
                        last_shooter_equipment = shooter_equip  # Track for base scoring
                        process_hit(shooter_equip, target_equip)
                    except ValueError:
                        print(f"[UDP RX] Invalid format: {message}")

    except BlockingIOError:
        pass
    except Exception as e:
        print(f"[UDP RX] Error: {e}")


def handle_base_score(scoring_team, base_code):
    """Handle base scoring - award player who last shot and is on correct team"""
    global last_shooter_equipment

    if last_shooter_equipment is None:
        print(f"[BASE] Base code {base_code} received but no shooter tracked")
        return

    shooter_team = equipment_teams.get(last_shooter_equipment)
    shooter_player = equipment_to_player.get(last_shooter_equipment)

    if shooter_team == scoring_team and shooter_player:
        # Award 100 points and add base icon
        update_player_score(shooter_player, 100)
        base_icons[shooter_player] = base_icons.get(shooter_player, 0) + 1
        print(f"[BASE] Player {shooter_player} (equip {last_shooter_equipment}) scored on base! +100 points")
        add_game_message(f"[BASE] Player {shooter_player} scored on base! +100 points")
    else:
        print(f"[BASE] Wrong team or unknown player for base score")
    # Award 100 points to the scoring player and add base icon


def process_hit(shooter_equip, target_equip):
    """Process a hit between two players"""
    shooter_team = equipment_teams.get(shooter_equip)
    target_team = equipment_teams.get(target_equip)

    shooter_player = equipment_to_player.get(shooter_equip)
    target_player = equipment_to_player.get(target_equip)

    # Get codenames if available
    shooter_name = None
    target_name = None
    for player in red_team.get_players() + green_team.get_players():
        if player['player_id'] == shooter_player:
            shooter_name = player['codename']
        if player['player_id'] == target_player:
            target_name = player['codename']

    if not shooter_team or not target_team:
        print(f"[HIT] Unknown equipment: shooter={shooter_equip}, target={target_equip}")
        return

    # Broadcast target equipment ID
    udp_transmit(target_equip)

    if shooter_team == target_team:
        # FRIENDLY FIRE - broadcast both equipment IDs
        udp_transmit(shooter_equip)

        # Both lose 10 points
        if shooter_player:
            update_player_score(shooter_player, -10)
        if target_player:
            update_player_score(target_player, -10)

        print(f"[HIT] FRIENDLY FIRE: {shooter_equip} hit teammate {target_equip}")
        add_game_message(f"FRIENDLY FIRE: {shooter_name} hit {target_name}")
    else:
        # NORMAL HIT - shooter gains 10 points
        if shooter_player:
            update_player_score(shooter_player, 10)
        print(f"[HIT] {shooter_equip} hit enemy {target_equip}")
        add_game_message(f"{shooter_name} hit {target_name}")


# Splash screen
def show_splash():
    """Display the splash logo for 3 seconds"""
    try:
        logo = pygame.image.load("logo.jpg")
        logo = pygame.transform.scale(logo, (WIDTH, HEIGHT))
        screen.blit(logo, (0, 0))
        pygame.display.flip()
        pygame.time.wait(3000)
    except:
        print("[SPLASH] Could not load logo.jpg")


# --- Button class ---
class Button:
    """Clickable button class"""

    def __init__(self, x, y, w, h, color, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.text = text

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        label = FONT.render(self.text, True, BLACK)
        screen.blit(label, (self.rect.x + (self.rect.width - label.get_width()) // 2,
                            self.rect.y + (self.rect.height - label.get_height()) // 2))

    def is_clicked(self, pos):
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
        pygame.draw.rect(screen, BLACK, self.rect)
        border_color = YELLOW if self.active else self.outline_color
        pygame.draw.rect(screen, border_color, self.rect, 2)
        label = FONT.render(self.text, True, WHITE)
        screen.blit(label, (self.rect.x + 5, self.rect.y + (self.rect.height - label.get_height()) // 2))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
                return "ENTER"
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < self.max_length:
                self.text += event.unicode
        return None


class Team:
    """A team containing multiple player slots"""

    def __init__(self, color, start_x, start_y, slot_spacing, team_name):
        self.color = color
        self.team_name = team_name
        self.slots = []
        for i in range(15):
            y = start_y + i * slot_spacing
            id_slot = InputSlot(start_x, y, 75, 30, 4, color)
            name_slot = InputSlot(start_x + 85, y, 200, 30, 14, color)
            self.slots.append((id_slot, name_slot))

    def draw(self, screen):
        for id_slot, name_slot in self.slots:
            id_slot.draw(screen)
            name_slot.draw(screen)

    def handle_click(self, pos):
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
        for id_slot, name_slot in self.slots:
            result = id_slot.handle_event(event)
            if result == "ENTER":
                return "ID_ENTERED", id_slot, name_slot
            result = name_slot.handle_event(event)
            if result == "ENTER":
                player_id = id_slot.text
                player_name = name_slot.text
                if player_id and player_name:
                    save_player(player_id, player_name)
                name_slot.active = False
        return None, None, None

    def clear(self):
        global player_equipment, equipment_teams, equipment_to_player, player_scores, base_icons
        for id_slot, name_slot in self.slots:
            player_id = id_slot.text.strip()
            if player_id in player_equipment:
                equip_id = player_equipment[player_id]
                if equip_id in equipment_teams:
                    del equipment_teams[equip_id]
                if equip_id in equipment_to_player:
                    del equipment_to_player[equip_id]
                del player_equipment[player_id]
            if player_id in player_scores:
                del player_scores[player_id]
            if player_id in base_icons:
                del base_icons[player_id]
            id_slot.text = ""
            name_slot.text = ""

    def get_players(self):
        global player_equipment
        players = []
        for id_slot, name_slot in self.slots:
            if id_slot.text.strip() and name_slot.text.strip():
                player_id = id_slot.text.strip()
                codename = name_slot.text.strip()
                equipment_id = player_equipment.get(player_id)
                if equipment_id:
                    players.append({
                        'player_id': player_id,
                        'codename': codename,
                        'equipment_id': equipment_id
                    })
        return players


# --- Buttons ---
clear_red_button = Button(50, 640, 200, 50, RED, "Clear Red Team")
clear_green_button = Button(270, 640, 230, 50, GREEN, "Clear Green Team")
clear_all_button = Button(520, 640, 200, 50, GRAY, "Clear All")
start_button = Button(740, 640, 160, 50, YELLOW, "Start Game")

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
    """Show countdown and broadcast code 202 when finished"""
    countdown = 5
    clock = pygame.time.Clock()
    last_tick = pygame.time.get_ticks()

    while countdown >= 0:
        screen.fill(BLACK)

        if countdown > 0:
            text = FONT.render(f"Game starting in {countdown}", True, YELLOW)
        else:
            text = FONT.render("Gametime!", True, GREEN)

        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        current_time = pygame.time.get_ticks()
        if current_time - last_tick >= 1000:
            countdown -= 1
            last_tick = current_time

    # Broadcast code 202 (game start)
    udp_transmit(202)

    screen.fill(BLACK)
    pygame.display.flip()
    pygame.event.clear()
    print("[COUNTDOWN] Complete - game starting (broadcast 202)")


def play_action_display():
    """Display game action with scores sorted highest to lowest"""
    red_players = red_team.get_players()
    green_players = green_team.get_players()

    # Initialize scores and mappings
    for player in red_players:
        if player['player_id'] not in player_scores:
            player_scores[player['player_id']] = 0
        equipment_teams[player['equipment_id']] = "red"
        equipment_to_player[player['equipment_id']] = player['player_id']
        if player['player_id'] not in base_icons:
            base_icons[player['player_id']] = 0

    for player in green_players:
        if player['player_id'] not in player_scores:
            player_scores[player['player_id']] = 0
        equipment_teams[player['equipment_id']] = "green"
        equipment_to_player[player['equipment_id']] = player['player_id']
        if player['player_id'] not in base_icons:
            base_icons[player['player_id']] = 0

    clock = pygame.time.Clock()
    running = True

    while running:
        receive_udp_messages()
        screen.fill(BLACK)

        # Sort players by score (highest to lowest)
        red_sorted = sorted(red_players, key=lambda p: player_scores.get(p['player_id'], 0), reverse=True)
        green_sorted = sorted(green_players, key=lambda p: player_scores.get(p['player_id'], 0), reverse=True)

        # Red team area
        red_rect = pygame.Rect(25, 50, 500, 280)
        pygame.draw.rect(screen, RED, red_rect, 3)
        red_label = FONT.render("Red Team", True, RED)
        screen.blit(red_label, (red_rect.x + (red_rect.width - red_label.get_width()) // 2, red_rect.y + 10))

        red_team_score = sum(player_scores.get(p['player_id'], 0) for p in red_players)
        score_x_red = red_rect.x + red_rect.width - 50
        red_score_text = FONT.render(str(red_team_score), True, RED)
        screen.blit(red_score_text, (score_x_red - red_score_text.get_width() // 2, red_rect.y + 10))

        y_offset = red_rect.y + 45
        for player in red_sorted:
            # Display base icons if any
            icon_str = "⚑ " * base_icons.get(player['player_id'], 0)
            player_text = SMALL_FONT.render(f"{icon_str}{player['codename']}", True, WHITE)
            screen.blit(player_text, (red_rect.x + 10, y_offset))

            score_text = SMALL_FONT.render(str(player_scores.get(player['player_id'], 0)), True, WHITE)
            screen.blit(score_text, (score_x_red - score_text.get_width() // 2, y_offset))
            y_offset += 25

        # Green team area
        green_rect = pygame.Rect(575, 50, 500, 280)
        pygame.draw.rect(screen, GREEN, green_rect, 3)
        green_label = FONT.render("Green Team", True, GREEN)
        screen.blit(green_label, (green_rect.x + (green_rect.width - green_label.get_width()) // 2, green_rect.y + 10))

        green_team_score = sum(player_scores.get(p['player_id'], 0) for p in green_players)
        score_x_green = green_rect.x + green_rect.width - 50
        green_score_text = FONT.render(str(green_team_score), True, GREEN)
        screen.blit(green_score_text, (score_x_green - green_score_text.get_width() // 2, green_rect.y + 10))

        y_offset = green_rect.y + 45
        for player in green_sorted:
            icon_str = "⚑ " * base_icons.get(player['player_id'], 0)
            player_text = SMALL_FONT.render(f"{icon_str}{player['codename']}", True, WHITE)
            screen.blit(player_text, (green_rect.x + 10, y_offset))

            score_text = SMALL_FONT.render(str(player_scores.get(player['player_id'], 0)), True, WHITE)
            screen.blit(score_text, (score_x_green - score_text.get_width() // 2, y_offset))
            y_offset += 25

        # Event log area
        event_rect = pygame.Rect(25, 350, 1050, 325)
        pygame.draw.rect(screen, WHITE, event_rect, 3)
        event_label = FONT.render("Current Game Action", True, WHITE)
        screen.blit(event_label, (event_rect.x + (event_rect.width - event_label.get_width()) // 2, event_rect.y + 10))
        # Event log
        y_offset = event_rect.y + 40
        for msg in game_messages:
            msg_surface = SMALL_FONT.render(msg, True, WHITE)
            screen.blit(msg_surface, (event_rect.x + 10, y_offset))
            y_offset += 20

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:
                    print("[GAME] Ending game - broadcasting 221 three times")
                    # Broadcast code 221 three times
                    for _ in range(3):
                        udp_transmit(221)
                    running = False


def main():
    """Main player entry loop"""
    global equip_popup_active, equip_text, current_player
    active_slot = None
    clock = pygame.time.Clock()

    while True:
        screen.fill(BLACK)

        screen.blit(FONT.render("Red Team", True, RED), (50, 60))
        screen.blit(FONT.render("Green Team", True, GREEN), (600, 60))

        red_team.draw(screen)
        green_team.draw(screen)

        clear_red_button.draw(screen)
        clear_green_button.draw(screen)
        clear_all_button.draw(screen)
        start_button.draw(screen)

        if equip_popup_active:
            draw_equip_popup()

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
                    pre_game_countdown()
                    pygame.event.clear()
                    play_action_display()

                if not equip_popup_active:
                    active_slot, _ = red_team.handle_click(pos)
                    if not active_slot:
                        active_slot, _ = green_team.handle_click(pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:
                    pre_game_countdown()
                    pygame.event.clear()
                    play_action_display()
                elif event.key == pygame.K_F12:
                    red_team.clear()
                    green_team.clear()

                elif equip_popup_active:
                    if event.key == pygame.K_RETURN:
                        equipment_id = equip_text.strip()
                        player_id = current_player["id_text"]
                        codename = current_player["name_slot"].text

                        if player_id and codename:
                            save_player(player_id, codename)

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
                    for team in [red_team, green_team]:
                        result, id_slot, name_slot = team.handle_event(event)
                        if result == "ID_ENTERED":
                            player_id = id_slot.text
                            existing_name = get_player(player_id)
                            current_player = {
                                "id_slot": id_slot,
                                "name_slot": name_slot,
                                "id_text": player_id,
                                "team": team
                            }
                            id_slot.active = False
                            active_slot = None
                            equip_popup_active = True
                            equip_text = ""
                            if existing_name:
                                name_slot.text = existing_name

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    init_udp_sockets()
    show_splash()
    main()
