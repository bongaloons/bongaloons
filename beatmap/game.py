import time
import pygame
from midi import parse_midi, score_beatmaps, Note

# -------------------------------
# Configuration and Constants
# -------------------------------

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 500
FPS = 60

TARGET_Y = 400         # y-position of the target (hit) line.
DOT_START_Y = -20      # Starting y-coordinate for falling dots.
T_FALL = 2.0           # Time (in seconds) for a dot to fall from DOT_START_Y to TARGET_Y.
SPEED = (TARGET_Y - DOT_START_Y) / T_FALL  # Falling speed in pixels per second.

# X positions for tracks:
TRACK_POSITIONS = {"left": 100, "right": 300}

# Mapping from keys to moves:
KEY_TO_MOVE = {pygame.K_a: "left", pygame.K_l: "right"}

# Global dictionary to record user hit notes.
user_moves = {"left": [], "right": []}

# -------------------------------
# Helper Functions
# -------------------------------

def create_falling_dots(truth_moves):
    """
    Creates a list of falling dot entries from truth_moves.
    Each entry is a tuple: (move, target_time, note).
    """
    dots = []
    for move, notes in truth_moves.items():
        for note in notes:
            dots.append((move, note.start, note))
    # Sort by target_time (i.e. truth note start)
    dots.sort(key=lambda x: x[1])
    return dots

def draw_game(screen, dots, current_time):
    """
    Draws the game elements (tracks, target line, and falling dots) on the screen.
    """
    screen.fill((0, 0, 0))
    
    # Draw the target line.
    pygame.draw.line(screen, (255, 255, 255), (0, TARGET_Y), (WINDOW_WIDTH, TARGET_Y), 2)
    
    # Draw vertical track lines (optional).
    for pos in TRACK_POSITIONS.values():
        pygame.draw.line(screen, (50, 50, 50), (pos, 0), (pos, WINDOW_HEIGHT), 2)
    
    # For each dot, if its scheduled appearance time has passed, compute its y-position.
    for (move, target_time, note) in dots:
        # Dot should appear at time: target_time - T_FALL.
        start_time = target_time - T_FALL
        if current_time < start_time:
            # Not yet appearing.
            continue
        # Calculate elapsed time since dot appeared.
        elapsed = current_time - start_time
        if elapsed > T_FALL:
            # Dot has reached (or passed) the target line.
            y = TARGET_Y
        else:
            y = DOT_START_Y + SPEED * elapsed
        
        # Draw the dot if it is within the screen.
        if y <= WINDOW_HEIGHT:
            x = TRACK_POSITIONS.get(move, WINDOW_WIDTH // 2)
            pygame.draw.circle(screen, (255, 0, 0), (x, int(y)), 10)
    
    pygame.display.flip()

# -------------------------------
# Main Game Code (Pygame)
# -------------------------------

def run_game(truth_moves, game_duration):
    """
    Runs the game for game_duration seconds.
    Captures key presses for left/right moves, displays falling dots,
    and records user hit times.
    """
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Rhythm Game")
    clock = pygame.time.Clock()
    
    # Create falling dots list from truth beatmap.
    falling_dots = create_falling_dots(truth_moves)
    
    # Game start time.
    game_start = time.perf_counter()
    
    running = True
    while running:
        current_time = time.perf_counter() - game_start
        if current_time >= game_duration:
            running = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in KEY_TO_MOVE:
                    move = KEY_TO_MOVE[event.key]
                    hit_time = current_time
                    hit = Note(start=hit_time, duration=0.0, subdivision=0)
                    user_moves.setdefault(move, []).append(hit)
                    print(f"[HIT] {move.upper()} at {hit_time:.2f} sec")
        
        draw_game(screen, falling_dots, current_time)
        clock.tick(FPS)
    
    pygame.quit()

def main():
    # Load truth beatmap from MIDI.
    midi_path = "test.mid"  # Replace with your MIDI file path.
    truth_moves = parse_midi(midi_path)
    bpm = 120.0  # default BPM (since parse_midi returns only the beatmap)
    
    # Determine game duration: 2 seconds after the last truth note.
    max_time = 0.0
    for notes in truth_moves.values():
        if notes:
            max_time = max(max_time, notes[-1].start)
    game_duration = max_time + 2.0
    print(f"[GAME] Game will run for {game_duration:.2f} seconds")
    
    # Run the game.
    run_game(truth_moves, game_duration)
    
    # Sort user moves by hit time.
    for move in user_moves:
        user_moves[move].sort(key=lambda n: n.start)
    
    # Score the beatmaps.
    scores = score_beatmaps(truth_moves, user_moves, bpm=bpm, threshold_fraction=1/2)
    print("\n--- Scoring Results ---")
    for move, results in scores.items():
        print(f"\nMove '{move}':")
        for truth_note, user_note, diff, judgement in results:
            if truth_note is not None and user_note is not None:
                print(f"  Truth at {truth_note.start:.2f} sec matched with hit at {user_note.start:.2f} sec "
                      f"(diff: {diff:+.2f} sec) -> {judgement}")
            elif truth_note is not None:
                print(f"  Truth at {truth_note.start:.2f} sec -> {judgement}")
            elif user_note is not None:
                print(f"  Extra hit at {user_note.start:.2f} sec -> {judgement}")

if __name__ == "__main__":
    main()
