import pygame, sys, random, os, statistics

pygame.init()
try:
    pygame.mixer.init()
    AUDIO_OK = True
except:
    AUDIO_OK = False
    print("Audio disabled")


# ================= WINDOW =================
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()
FPS = 60
PIPE_IMG_WIDTH = 80

# ================= FONTS =================
font = pygame.font.SysFont("Arial", 48)
stat_font = pygame.font.SysFont("Roboto", 40)
small_font = pygame.font.SysFont("Arial", 24)
title_font = pygame.font.SysFont("Goudy Stout", 80)

# ================= COLORS =================
BLACK = (30,30,30)
WHITE = (245,245,245)
GRAY = (140,140,140)
RED = (210,80,80)
GREEN = (60,180,90)
BLUE = (90,140,220)
HIGHLIGHT = (206, 163, 116)
F_Color = (78, 86, 90)
Title_col = (250, 72, 83)
var_color = (42, 172, 184)

# ================= ASSET LOADERS =================
def load_image(path):
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (WIDTH, HEIGHT))
    return None

def load_sprite(path, size):
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    return None

def load_sound(path):
    if AUDIO_OK and os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None

# ================= LOAD BACKGROUNDS =================
themes = {
    "Classic": {
        "bg": load_image("assets/backgrounds/classic.jpg"),
        "pipe_top": load_sprite("assets/pipe/pipe-up.png", (60, HEIGHT)),
        "pipe_bottom": load_sprite("assets/pipe/pipe-down.png", (60, HEIGHT)),
        "pipe": WHITE
    },
    "Night": {
        "bg": load_image("assets/backgrounds/night.png"),
        "pipe_top": load_sprite("assets/pipe/dark-pipe-up.png", (60, HEIGHT)),
        "pipe_bottom": load_sprite("assets/pipe/dark-pipe-down.png", (60, HEIGHT)),
        "pipe": BLUE
    },
    "Zen": {
        "bg": load_image("assets/backgrounds/zen.jpg" ),
        "pipe_top": load_sprite("assets/pipe/dark-pipe-up.png", (60, HEIGHT)),
        "pipe_bottom": load_sprite("assets/pipe/dark-pipe-down", (60, HEIGHT)),
        "pipe": (120,200,160)
    },
    "Custom": {
        "bg": load_image("assets/backgrounds/Jungle.jpg"),
        "pipe_top": load_sprite("assets/pipe/pipe-up.png", (60, HEIGHT)),
        "pipe_bottom": load_sprite("assets/pipe/pipe-down.png", (60, HEIGHT)),
        "pipe": (180,140,90)
    }
}
skin = {
    "Classic":{
        "skin": load_sprite("assets/ui/bird/classic.png", (30, 30))
    },
    "Red": {
        "skin": load_sprite("assets/ui/bird/red.png", (30, 30))
    },
    "Blue": {
        "skin": load_sprite("assets/ui/bird/blue.png", (30, 30))
    },
    "Custom": {
        "skin": load_sprite("assets/ui/bird/4.png", (30, 30))
    }
}

current_skin = "Classic"
current_theme = "Classic"
theme_names = list(themes.keys())
skin_names = list(skin.keys())

# ================= LOAD SOUNDS =================
snd_flap = load_sound("assets/sounds/flap.mp3")
snd_hit = load_sound("assets/sounds/hit.mp3")

menu_music_path = "assets/sounds/menu.mp3"
menu_music_loaded = os.path.exists(menu_music_path)

# ================= STATES =================
HOME, FREE, FOCUS, PAUSE, SETTINGS, STATS = range(6)
state = HOME
last_play_state = FREE

# ================= DIFFICULTY =================
difficulty_levels = ["Easy", "Normal", "Hard", "God"]
difficulty_index = 1
GRAVITY, PIPE_SPEED, PIPE_GAP = 1,1,1

def apply_difficulty():
    global GRAVITY, PIPE_SPEED, PIPE_GAP
    if difficulty_levels[difficulty_index] == "Easy":
        GRAVITY, PIPE_SPEED, PIPE_GAP = 0.32, 2.3, 190
    elif difficulty_levels[difficulty_index] == "Hard":
        GRAVITY, PIPE_SPEED, PIPE_GAP = 0.48, 3.5, 145
    elif difficulty_levels[difficulty_index] == "God":
        GRAVITY, PIPE_SPEED, PIPE_GAP = 0.70, 4, 100
    else:
        GRAVITY, PIPE_SPEED, PIPE_GAP = 0.38, 2.8, 170

apply_difficulty()

# ================= STATS DATA =================
total_runs = 0
best_score = 0
focus_history = []
reaction_history = []
panic_history = []

# ================= GAME VARS =================
bird_x = 500
bird_y = HEIGHT // 2
bird_v = 0
FLAP = -7.2
MAX_FALL = 9
BASE_GRAVITY = GRAVITY
BASE_PIPE_GAP = PIPE_GAP

BIRD_SIZE = (30, 30)   # width, height (adjust if needed)

PIPE_W = 60
pipes = []
pipe_timer = 0
score = 0

# ================= FOCUS ANALYTICS =================
click_times = []
panic_flaps = 0
decision_times = []
reaction_times = []
DECISION_ZONE_OFFSET = 80

def compute_focus_panic():
    if len(click_times) < 5:
        return 0, "Low"

    intervals = [click_times[i+1] - click_times[i] for i in range(len(click_times)-1)]
    variance = statistics.pstdev(intervals) if len(intervals) > 1 else 0
    panic_ratio = panic_flaps / len(click_times)

    focus = max(0, min(100, int(100 - variance * 0.15 - panic_ratio * 120)))

    if panic_ratio > 0.35:
        panic = "High"
    elif panic_ratio > 0.18:
        panic = "Medium"
    else:
        panic = "Low"
    return focus, panic

# ================= MENUS =================
menu = ["Free Play", "Focus Mode", "Settings", "Stats", "Exit"]
menu_i = 0
settings_menu = ["Difficulty", "Theme", "Skin", "Back"]
settings_i = 0

# ================= PIPE =================
class Pipe:
    def __init__(self):
        self.x = WIDTH
        self.top = random.randint(80, HEIGHT - PIPE_GAP - 120)
        self.bottom = self.top + PIPE_GAP
        self.passed = False
        self.decision_marked = False
        self.decision_time = None

    def update(self):
        self.x -= PIPE_SPEED

    def draw(self):
        pipe_top = themes[current_theme].get("pipe_top")
        pipe_bottom = themes[current_theme].get("pipe_bottom")

        if pipe_top and pipe_bottom:
            # Top pipe
            top_rect = pipe_top.get_rect(
                bottomleft=(self.x, self.top)
            )
            screen.blit(pipe_top, top_rect)

            # Bottom pipe
            bottom_rect = pipe_bottom.get_rect(
                topleft=(self.x, self.bottom)
            )
            screen.blit(pipe_bottom, bottom_rect)
        else:
            # Fallback rectangles (safety)
            pygame.draw.rect(screen, GREEN, (self.x,0,PIPE_W,self.top), border_radius=6)
            pygame.draw.rect(screen, GREEN, (self.x,self.bottom,PIPE_W,HEIGHT), border_radius=6)

# ================= HELPERS =================
def reset_game():
    global bird_y, bird_v, pipes, pipe_timer, score
    global click_times, panic_flaps, decision_times, reaction_times
    global GRAVITY, PIPE_GAP

    bird_y = HEIGHT // 2
    bird_v = 0
    pipes.clear()
    pipe_timer = 0
    score = 0

    global total_runs, best_score

    # Save stats BEFORE reset
    if state in (FREE, FOCUS):
        total_runs += 1
        best_score = max(best_score, score)

        if state == FOCUS:
            focus, panic = compute_focus_panic()
            focus_history.append(focus)
            panic_history.append(panic)
            reaction_history.extend(reaction_times)

    click_times.clear()
    panic_flaps = 0
    decision_times.clear()
    reaction_times.clear()

def draw_bg():
    bg = themes[current_theme]["bg"]
    if bg:
        screen.blit(bg, (0,0))
    else:
        screen.fill(WHITE)

# ================= DRAW SCREENS =================
def draw_home():
    draw_bg()
    title = title_font.render("FLAPPY BIRD", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 120))

    for i,item in enumerate(menu):
        y = 180 + i * 50
        if i == menu_i:
            pygame.draw.rect(screen, F_Color, (WIDTH//2-180,y+95,27*len(menu[i]),50), border_radius=15)
        screen.blit(font.render(item, True, WHITE), (WIDTH//2-160, y+90))

def draw_settings():
    draw_bg()
    screen.blit(title_font.render("SETTINGS", True, WHITE), (WIDTH//2-350, 100))
    for i,item in enumerate(settings_menu):
        y = 120 + i * 50
        if i == settings_i:
            pygame.draw.rect(screen, F_Color,((WIDTH // 2)-(y//2), y + 150, y//4*(len(settings_menu[i])), 50),border_radius=15)
            pygame.draw.rect(screen, F_Color, (WIDTH//2-180, y+150,5*(len(settings_menu[i])+25),50), border_radius=15)
        label = item
        if item == "Difficulty":
            label += f": {difficulty_levels[difficulty_index]}"
        if item == "Theme":
            label += f": {current_theme}"
        if item == "Skin":
            label += f": {current_skin}"

        preview_img = skin[current_skin]["skin"]
        if preview_img:
            preview = pygame.transform.smoothscale(preview_img, (50, 50))
            screen.blit(preview, (WIDTH//2+400, 300))
            screen.blit(small_font.render("Current Skin :", True, var_color), (WIDTH//2+270, 320))
        screen.blit(font.render(label, True, WHITE), (WIDTH//2-160,150+y))

def draw_hud():
    screen.blit(font.render(f"Score: {score}", True, (255,255,0)), (10, 10))

    if state == FOCUS:
        focus, panic = compute_focus_panic()
        screen.blit(font.render(f"Focus: {focus}%", True, F_Color), (10, 60))
        screen.blit(font.render(f"Panic: {panic}", True, F_Color), (10, 100))

        if reaction_times:
            avg_rt = sum(reaction_times[-10:]) // len(reaction_times[-10:])
            screen.blit(font.render(f"RT: {avg_rt} ms", True, F_Color), (10, 140))

def draw_stats():
    draw_bg()
    screen.blit(title_font.render("STATS", True, WHITE), (WIDTH//2 - 200, 100))

    y = 200
    line_gap = 50

    avg_focus = int(sum(focus_history)/len(focus_history)) if focus_history else 0
    avg_rt = int(sum(reaction_history)/len(reaction_history)) if reaction_history else 0

    low_panic = panic_history.count("Low")
    med_panic = panic_history.count("Medium")
    high_panic = panic_history.count("High")

    stats = [
        f"Total Runs: {total_runs}",
        f"Best Score: {best_score}",
        f"Average Focus: {avg_focus}%",
        f"Average Reaction Time: {avg_rt} ms",
        f"Panic Levels:",
        f"  Low: {low_panic}",
        f"  Medium: {med_panic}",
        f"  High: {high_panic}",
        "",
        "Press ESC to return"
    ]
    pygame.draw.rect(screen, F_Color, (WIDTH // 2 - 200, y, 500, 520), border_radius=15)
    for line in stats:
        screen.blit(stat_font.render(line, True, WHITE), (500, y+30))
        y += line_gap

def draw_pause_overlay():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    title = title_font.render("PAUSED", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 120))

    msg1 = font.render("SPACE  -  Continue", True, WHITE)
    msg2 = font.render("ESC  -  Home", True, WHITE)

    screen.blit(msg1, (WIDTH//2 - msg1.get_width()//2, HEIGHT//2))
    screen.blit(msg2, (WIDTH//2 - msg2.get_width()//2, HEIGHT//2 + 60))
# ================= MUSIC CONTROL =================
if menu_music_loaded:
    pygame.mixer.music.load(menu_music_path)
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)

# ================= MAIN LOOP =================
running = True
while running:
    clock.tick(FPS)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE and state not in (PAUSE, STATS):
                state = HOME
                focus, panic = compute_focus_panic()
                focus_history.append(focus)
                panic_history.append(panic)
                reaction_history.extend(reaction_times)
                reset_game()
                if menu_music_loaded:
                    if AUDIO_OK and not pygame.mixer.music.get_busy():
                        pygame.mixer.music.play(-1)
            if state == HOME:
                if e.key == pygame.K_UP:
                    menu_i = (menu_i - 1) % len(menu)
                if e.key == pygame.K_DOWN:
                    menu_i = (menu_i + 1) % len(menu)
                if e.key == pygame.K_RETURN:
                    choice = menu[menu_i]
                    if choice == "Free Play":
                        state = FREE
                        last_play_state = FREE
                        reset_game()
                        pygame.mixer.music.stop()
                    elif choice == "Focus Mode":
                        state = FOCUS
                        last_play_state = FOCUS
                        reset_game()
                        pygame.mixer.music.stop()
                    elif choice == "Stats":
                        state = STATS
                    elif choice == "Settings":
                        state = SETTINGS
                    elif choice == "Exit":
                        running = False

            elif state == SETTINGS:
                if e.key == pygame.K_UP:
                    settings_i = (settings_i - 1) % len(settings_menu)
                if e.key == pygame.K_DOWN:
                    settings_i = (settings_i + 1) % len(settings_menu)
                if e.key == pygame.K_LEFT:
                    if settings_menu[settings_i] == "Difficulty":
                        difficulty_index = (difficulty_index - 1) % 4
                        apply_difficulty()
                    if settings_menu[settings_i] == "Theme":
                        current_theme = theme_names[(theme_names.index(current_theme)-1)%len(theme_names)]
                    if settings_menu[settings_i] == "Skin":
                        current_skin = skin_names[(skin_names.index(current_skin)-1)%len(skin_names)]
                if e.key == pygame.K_RIGHT:
                    if settings_menu[settings_i] == "Difficulty":
                        difficulty_index = (difficulty_index + 1) % 4
                        apply_difficulty()
                    if settings_menu[settings_i] == "Theme":
                        current_theme = theme_names[(theme_names.index(current_theme)+1)%len(theme_names)]
                    if settings_menu[settings_i] == "Skin":
                        current_skin = skin_names[(skin_names.index(current_skin)+1)%len(skin_names)]
                if e.key == pygame.K_RETURN and settings_menu[settings_i] == "Back":
                    state = HOME

            elif state == STATS:
                draw_stats()
                if e.key == pygame.K_ESCAPE:
                    state = HOME

            elif state in (FREE, FOCUS) and e.key == pygame.K_SPACE:
                bird_v = FLAP
                if snd_flap: snd_flap.play()

                if state == FOCUS:
                    now = pygame.time.get_ticks()
                    click_times.append(now)

                    if decision_times:
                        rt = now - decision_times[-1]
                        if 50 < rt < 1200:
                            reaction_times.append(rt)

                    if len(click_times) > 1 and click_times[-1] - click_times[-2] < 150:
                        panic_flaps += 1
            elif state == PAUSE:
                if e.key == pygame.K_SPACE:
                    # Continue
                    state = last_play_state
                    reset_game()
                elif e.key == pygame.K_ESCAPE:
                    # Go Home
                    reset_game()
                    state = HOME

    # ================= GAME =================
    if state in (FREE, FOCUS):
        draw_bg()

        bird_v = min(bird_v + GRAVITY, MAX_FALL)
        bird_y += bird_v
        bird_rect = pygame.Rect(bird_x, bird_y, BIRD_SIZE[0], BIRD_SIZE[1])
        bird_image = skin[current_skin]["skin"]

        if bird_image:
            angle = max(-25, min(25, -bird_v * 3))
            rotated_bird = pygame.transform.rotate(bird_image, angle)
            rect = rotated_bird.get_rect(center=bird_rect.center)
            screen.blit(rotated_bird, rect.topleft)
        else:
            # Fallback (if image missing)
            pygame.draw.rect(screen, (225, 44, 255), bird_rect, border_radius=20)

        pipe_timer += 1
        if pipe_timer > 95:
            pipes.append(Pipe())
            pipe_timer = 0

        for p in pipes[:]:
            p.update()
            p.draw()

            if not p.passed and p.x + PIPE_W < bird_x:
                p.passed = True
                score += 1

            if state == FOCUS and not p.decision_marked and p.x <= bird_x + DECISION_ZONE_OFFSET:
                p.decision_marked = True
                decision_times.append(pygame.time.get_ticks())

            if bird_rect.colliderect(pygame.Rect(p.x, 0, PIPE_W, p.top)) or \
               bird_rect.colliderect(pygame.Rect(p.x, p.bottom, PIPE_W, HEIGHT)) or bird_y < 0 or bird_y + BIRD_SIZE[1] > HEIGHT:
                if snd_hit: snd_hit.play()
                bird_v = 0
                state = PAUSE
                break

            if p.x + PIPE_W < 0:
                pipes.remove(p)

        draw_hud()

    elif state == HOME:
        draw_home()

    elif state == PAUSE:
        draw_pause_overlay()

    elif state == SETTINGS:
        draw_settings()

    pygame.display.update()

pygame.quit()
sys.exit()