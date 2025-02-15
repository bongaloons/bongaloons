import json
import time
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from midi import (
    parse_midi,
    load_truth_note,
    score_live_note,
    Note,
    RANKING_THRESHOLDS,
    global_truth_map
)
from score import calculate_score

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Game settings
T_FALL = 2.0
DEFAULT_BPM = 120.0  # fallback BPM
GAME_STATE = {
    "is_running": False,
    "start_time": None,
    "game_duration": 0,
    "bpm": DEFAULT_BPM,
    "total_score": 0
}

def get_bpm_from_catalog(midi_file: str) -> int:
    """
    Reads catalog.json (in the same directory) and returns the BPM for the given midi_file.
    If not found, returns DEFAULT_BPM.
    """
    try:
        with open("catalog.json", "r") as f:
            catalog = json.load(f)
        for entry in catalog:
            # Assuming the JSON objects have a "path" key that we match against midi_file.
            if entry.get("path") == midi_file:
                return entry.get("bpm", DEFAULT_BPM)
    except Exception as e:
        print(f"Error reading catalog.json: {e}")
    return DEFAULT_BPM

@app.post("/game/start")
async def start_game(midi_file: str = "test.mid"):
    """
    Initialize a new game session.
    Loads the truth beatmap from the MIDI file and loads each note one-by-one into the global truth map.
    Reads the BPM from catalog.json.
    Computes the game duration (2 seconds after the last truth note).
    """
    # Get BPM from catalog.json instead of estimating it.
    bpm = get_bpm_from_catalog(midi_file)
    GAME_STATE["bpm"] = bpm
    print(f"Using BPM from catalog: {bpm}")

    # Parse the entire beatmap.
    truth_moves = parse_midi(midi_file)
    
    # Clear any previous truth notes.
    global_truth_map.clear()
    
    # Load each truth note into the global_truth_map via load_truth_note.
    for move, notes in truth_moves.items():
        for note in notes:
            load_truth_note(move, note)
    
    # Determine game duration: 2 seconds after the last truth note among all moves.
    max_time = 0.0
    for notes in truth_moves.values():
        if notes:
            max_time = max(max_time, notes[-1].start)
    game_duration = max_time + 2.0
    GAME_STATE["game_duration"] = game_duration
    GAME_STATE["start_time"] = time.perf_counter()
    GAME_STATE["is_running"] = True
    GAME_STATE["total_score"] = 0
    
    # Prepare falling dot info.
    falling_dots = [
        {
            "move": move,
            "target_time": note.start * 1000,
            "track": move
        }
        for move, notes in truth_moves.items()
        for note in notes
    ]
    
    return {
        "status": "started",
        "duration": game_duration,
        "falling_dots": falling_dots
    }

@app.websocket("/game/ws")
async def game_websocket(websocket: WebSocket):
    """
    A live WebSocket endpoint.
    
    For each key event, it:
      - Determines the move ("left" for 'a', "right" for 'l').
      - Computes the current time relative to game start.
      - Creates a hit Note.
      - Calls score_live_note to score that hit against the next truth note in the global_truth_map.
      - Sends back the judgement.
    
    When the current time reaches game_duration, any remaining truth notes are marked as MISS,
    and the game is over.
    """
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            if not GAME_STATE["is_running"]:
                continue
                
            current_time = time.perf_counter() - GAME_STATE["start_time"]
            
            if data.get("key") in ["a", "l"]:
                move = "left" if data["key"] == "a" else "right"
                hit = Note(move_type=move, start=current_time, duration=0.0, subdivision=0)
                judgement = score_live_note(move, current_time, hit, bpm=GAME_STATE["bpm"], threshold_fraction=1)
                
                # Calculate and update score
                score_delta = calculate_score(judgement)
                GAME_STATE["total_score"] += score_delta
                
                await websocket.send_json({
                    "type": "hit_registered",
                    "move": move,
                    "time": current_time,
                    "lastJudgement": judgement,
                    "totalScore": GAME_STATE["total_score"],
                    "scoreDelta": score_delta
                })
            
            if current_time >= GAME_STATE["game_duration"]:
                for move in list(global_truth_map.keys()):
                    while global_truth_map[move]:
                        judgement = score_live_note(move, current_time, None, bpm=GAME_STATE["bpm"], threshold_fraction=1/8)
                        if judgement == "MISS":
                            GAME_STATE["total_score"] += calculate_score(judgement)
                
                await websocket.send_json({
                    "type": "game_over",
                    "message": "Game over!",
                    "totalScore": GAME_STATE["total_score"]
                })
                GAME_STATE["is_running"] = False
                break
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.get("/game/status")
async def get_game_status():
    """Get current game status."""
    if not GAME_STATE["is_running"]:
        return {"status": "not_running"}
        
    current_time = time.perf_counter() - GAME_STATE["start_time"]
    return {
        "status": "running",
        "elapsed_time": current_time,
        "total_duration": GAME_STATE["game_duration"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
