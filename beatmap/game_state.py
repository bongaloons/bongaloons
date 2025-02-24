import json
import time
from dataclasses import dataclass, replace
from typing import Tuple, List, Dict, Any, Optional
from midi import (
    parse_midi,
    Note,
    BeatmapSession
)
from score import calculate_score
from models import FallingDot

with open("../frontend/public/settings.json", "r") as f:
    settings = json.load(f)

T_FALL = settings.get("fall_duration", 2000) / 1000
T_END = settings.get("end_pause", 0) / 1000
DEFAULT_BPM = settings.get("default_bpm", 120)

@dataclass(frozen=True)
class GameState:
    is_running: bool = False
    is_paused: bool = False
    start_time: float = 0.0
    total_paused_time: float = 0.0
    pause_timestamp: float = None
    total_score: int = 0
    current_streak: int = 0
    max_streak: int = 0
    game_duration: float = 0.0
    bpm: int = DEFAULT_BPM
    song_path: str = ""
    midi_path: str = ""
    song_name: str = ""
    difficulty: int = 1
    session: BeatmapSession = None


def get_song_info_from_catalog(id: int) -> tuple:
    """
    Reads catalog.json and returns song info tuple.
    """
    try:
        with open("catalog.json", "r") as f:
            catalog = json.load(f)
        for entry in catalog:
            if entry.get("id") == id:
                return (
                    entry.get("bpm", DEFAULT_BPM),
                    entry.get("song", ""),
                    entry.get("path", ""),
                    entry.get("name", ""),
                    entry.get("difficulty", 1)
                )
    except Exception as e:
        print(f"Error reading catalog.json: {e}")
    return DEFAULT_BPM, "", "", "", 1

def start_new_game(song_id: int = 0) -> Tuple[GameState, List[FallingDot], List[Dict[str, Any]]]:
    """
    Initialize a new game state with song data.
    Returns (state, falling_dots, messages).
    """
    # Get song info from catalog.json
    bpm, song_path, midi_path, song_name, difficulty = get_song_info_from_catalog(song_id)
    
    print(f"Using BPM: {bpm}, Song path: {song_path}, MIDI path: {midi_path}, Song name: {song_name}")

    # Parse MIDI and load truth notes
    frontend_prefix = "../frontend/public/"
    full_midi_path = f"{frontend_prefix}{midi_path.lstrip('/')}"
    print("Full MIDI path:", full_midi_path)
    truth_moves = parse_midi(full_midi_path)
    
    # Create beatmap session
    session = BeatmapSession(truth_moves, bpm)
    
    # Calculate game duration
    max_time = 0.0
    for notes in truth_moves.values():
        if notes:
            max_time = max(max_time, notes[-1].start)
    game_duration = max_time + 10.0

    # Create falling dots
    falling_dots = [
        FallingDot(
            move=move,
            target_time=note.start * 1000,  # Convert to ms
            track=move
        )
        for move, notes in truth_moves.items()
        for note in notes
    ]

    state = GameState(
        is_running=True,
        start_time=time.perf_counter(),
        game_duration=game_duration,
        bpm=bpm,
        song_path=song_path,
        midi_path=midi_path,
        song_name=song_name,
        difficulty=difficulty,
        session=session  # Store session in state
    )

    messages = [{
        "type": "game_started",
        "duration": game_duration,
        "bpm": bpm,
        "songPath": song_path,
        "midiPath": midi_path,
        "songName": song_name,
        "difficulty": difficulty
    }]

    return state, falling_dots, messages

def process_hit(state: GameState, move: str, current_time: float) -> Tuple[GameState, List[Dict[str, Any]]]:
    """Process a hit event and return new state and messages."""
    if not state.is_running or state.is_paused:
        return state, []

    hit = Note(move_type=move, start=current_time, duration=0.0, subdivision=0)
    judgement = state.session.score_live_note(move, current_time, hit, bpm=state.bpm, threshold_fraction=1)
    score_delta = calculate_score(judgement, state.current_streak)
    new_total_score = state.total_score + score_delta
    max_streak = state.max_streak
    if judgement in ["MISS", "OOPS"]:
        new_streak = 0
    else:
        new_streak = state.current_streak + 1
        max_streak = max(state.max_streak, new_streak)

    new_state = replace(
        state,
        total_score=new_total_score,
        current_streak=new_streak,
        max_streak=max_streak
    )

    messages = [{
        "type": "hit_registered",
        "move": move,
        "time": current_time,
        "lastJudgement": judgement,
        "totalScore": new_state.total_score,
        "currentStreak": new_state.current_streak,
        "maxStreak": new_state.max_streak,
        "scoreDelta": score_delta
    }]

    return new_state, messages

def check_missed_notes(state: GameState, current_time: float) -> Tuple[GameState, List[Dict[str, Any]]]:
    """Check for missed notes and return new state and messages."""
    if not state.is_running or state.is_paused:
        return state, []

    messages = []
    adjusted_time = current_time - state.start_time - state.total_paused_time
    new_state = state

    for move in list(state.session.move_queues.keys()):
        while state.session.move_queues.get(move):
            judgement = state.session.score_live_note(
                move,
                adjusted_time - T_FALL,
                None,
                bpm=state.bpm,
                threshold_fraction=1/2
            )
            if judgement == "waiting":
                break
            elif judgement == "MISS":
                score_delta = calculate_score(judgement, new_state.current_streak)
                new_state = replace(
                    new_state,
                    total_score=new_state.total_score + score_delta,
                    current_streak=0
                )
                messages.append({
                    "type": "note_missed",
                    "move": move,
                    "time": adjusted_time - T_FALL,
                    "judgement": judgement,
                    "totalScore": new_state.total_score,
                    "currentStreak": 0,
                })

    return new_state, messages

def tick(state: GameState, current_time: float) -> Tuple[GameState, List[Dict[str, Any]]]:
    """
    A periodic tick. If the elapsed (unpaused) time exceeds the game duration plus delays,
    the game is ended.
    """
    messages = []

    is_paused = state.is_paused
    is_running = state.is_running

    if is_paused:
        return state, messages
    
    if not is_running:
        return state, messages

    is_game_over = current_time >= state.game_duration + T_END
    if is_game_over:
        new_state = replace(state, is_running=False)
        messages.append({
            "type": "game_over",
            "message": "Game over!",
            "totalScore": state.total_score,
            "maxStreak": state.max_streak,
        })
        return new_state, messages
    return state, messages

def pause_game(state: GameState) -> Tuple[GameState, List[Dict[str, Any]]]:
    """
    Pauses the game if not already paused.
    """
    if state.is_paused:
        return state, []
    current_time = time.perf_counter()
    new_state = replace(state, is_paused=True, pause_timestamp=current_time)
    message = {"type": "paused"}
    return new_state, [message]

def resume_game(state: GameState) -> Tuple[GameState, List[Dict[str, Any]]]:
    """
    Resumes the game if it is paused. The total paused time is updated accordingly.
    """
    if not state.is_paused:
        return state, []
    current_time = time.perf_counter()
    paused_duration = current_time - state.pause_timestamp
    new_state = replace(
        state,
        is_paused=False,
        total_paused_time=state.total_paused_time + paused_duration,
        pause_timestamp=None
    )
    message = {"type": "resumed"}
    return new_state, [message]

def game_over(state: GameState) -> Tuple[GameState, List[Dict[str, Any]]]:
    """
    Force the game over. (E.g. if the client requests it.)
    """
    new_state = replace(state, is_running=False)
    message = {
        "type": "game_over",
        "message": "Game over triggered!",
        "totalScore": state.total_score,
        "maxStreak": state.max_streak,
    }
    return new_state, [message]
