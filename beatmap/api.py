import json
import time
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from midi import (
    parse_midi,
    load_truth_note,
    score_live_note,
    Note,
    global_truth_map
)
from models import (
    GameStatusResponse,
    GetSongsResponse,
    HealthCheckResponse,
    FallingDot,
    Song
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
T_END = 2.0  # Delay after song end
DEFAULT_BPM = 120.0  # fallback BPM

GAME_STATE = {
    "is_running": False,
    "is_paused": False,         # Whether the game is currently paused
    "pause_timestamp": None,    # Timestamp when pause started (in seconds)
    "total_paused_time": 0,     # Total time (in seconds) the game has been paused
    "start_time": None,
    "game_duration": 0,
    "bpm": DEFAULT_BPM,
    "songPath": "",             # Audio file path
    "midiPath": "",             # MIDI file path from the catalog
    "songName": "",             # Name of the song from the catalog
    "total_score": 0,
    "current_streak": 0,
    "max_streak": 0
}


def get_song_info_from_catalog(id: int) -> tuple:
    """
    Reads catalog.json and returns a tuple (bpm, songPath, midiPath, songName)
    for the given id. If not found, returns (DEFAULT_BPM, "", "", "").
    """
    try:
        with open("catalog.json", "r") as f:
            catalog = json.load(f)
        for entry in catalog:
            if entry.get("id") == id:
                bpm = entry.get("bpm", DEFAULT_BPM)
                song = entry.get("song", "")
                midi_path = entry.get("path", "")
                song_name = entry.get("name", "")
                return bpm, song, midi_path, song_name
    except Exception as e:
        print(f"Error reading catalog.json: {e}")
    return DEFAULT_BPM, "", "", ""


@app.get("/songs")
async def get_songs() -> GetSongsResponse:
    try:
        with open("catalog.json", "r") as f:
            catalog = json.load(f)
        return GetSongsResponse(songs=[Song(**entry) for entry in catalog])
    except Exception as e:
        print(f"Error reading catalog.json: {e}")
        return GetSongsResponse(songs=[])


@app.post("/game/start")
async def start_game(id: int = 0):
    # Get BPM, song path, MIDI path, and song name from catalog.json using id.
    bpm, song_path, midi_path, song_name = get_song_info_from_catalog(id)
    GAME_STATE["bpm"] = bpm
    GAME_STATE["songPath"] = song_path
    GAME_STATE["midiPath"] = midi_path
    GAME_STATE["songName"] = song_name
    # Reset pause-related values.
    GAME_STATE["is_paused"] = False
    GAME_STATE["pause_timestamp"] = None
    GAME_STATE["total_paused_time"] = 0

    print(f"Using BPM: {bpm}, Song path: {song_path}, MIDI path: {midi_path}, Song name: {song_name}")

    frontend_prefix = "../frontend/public/"
    full_midi_path = f"{frontend_prefix}{midi_path.lstrip('/')}"
    print("Full MIDI path:", full_midi_path)

    truth_moves = parse_midi(full_midi_path)
    global_truth_map.clear()
    for move, notes in truth_moves.items():
        for note in notes:
            load_truth_note(move, note)

    max_time = 0.0
    for notes in truth_moves.values():
        if notes:
            max_time = max(max_time, notes[-1].start)
    game_duration = max_time + 2.0
    GAME_STATE["game_duration"] = game_duration
    GAME_STATE["start_time"] = time.perf_counter()
    GAME_STATE["is_running"] = True
    GAME_STATE["total_score"] = 0
    GAME_STATE["current_streak"] = 0
    GAME_STATE["max_streak"] = 0

    falling_dots = [
        FallingDot(
            move=move,
            target_time=note.start * 1000,
            track=move
        )
        for move, notes in truth_moves.items()
        for note in notes
    ]
    
    return {
        "status": "started",
        "duration": game_duration,
        "falling_dots": falling_dots,
        "songPath": song_path,
        "midiPath": midi_path,
        "songName": song_name
    }


async def game_status_checker(websocket: WebSocket):
    """
    Background task that continuously checks for missed notes and whether the game is over.
    It only acts when the game is running and not paused.
    """
    threshold_fraction = 1 / 2  # Use the desired threshold for missed note checking.
    while True:
        if not GAME_STATE["is_running"]:
            # Game has not started or has ended; sleep and check again.
            await asyncio.sleep(0.05)
            continue

        if GAME_STATE["is_paused"]:
            await asyncio.sleep(0.05)
            continue

        current_time = time.perf_counter() - GAME_STATE["start_time"] - GAME_STATE["total_paused_time"]

        # Check if game duration has passed (with extra delay T_END).
        if current_time >= GAME_STATE["game_duration"] + T_END:
            await websocket.send_json({
                "type": "game_over",
                "message": "Game over!",
                "totalScore": GAME_STATE["total_score"]
            })
            GAME_STATE["is_running"] = False
            break

        # Process missed notes.
        for move in list(global_truth_map.keys()):
            while global_truth_map.get(move):
                # Adjust time by subtracting T_FALL.
                judgement = score_live_note(
                    move,
                    current_time - T_FALL,
                    None,
                    bpm=GAME_STATE["bpm"],
                    threshold_fraction=threshold_fraction
                )
                if judgement == "waiting":
                    break
                else:
                    print("hi")
                    if judgement == "MISS":
                        score_delta = calculate_score(judgement, GAME_STATE["current_streak"])
                        GAME_STATE["total_score"] += score_delta
                        GAME_STATE["current_streak"] = 0
                        await websocket.send_json({
                            "type": "note_missed",
                            "move": move,
                            "time": current_time - T_FALL,
                            "judgement": judgement,
                            "totalScore": GAME_STATE["total_score"],
                            "currentStreak": GAME_STATE["current_streak"],
                        })
        await asyncio.sleep(0.02)  # Check roughly every 20ms


@app.websocket("/game/ws")
async def game_websocket(websocket: WebSocket):
    await websocket.accept()

    # Start the background task that checks for missed notes and game over.
    game_checker_task = asyncio.create_task(game_status_checker(websocket))
    
    try:
        while True:
            data = await websocket.receive_json()

            # If the game isn't running, ignore messages.
            if not GAME_STATE["is_running"]:
                continue

            # Handle pause toggle messages.
            if data.get("type") == "toggle_pause":
                if not GAME_STATE["is_paused"]:
                    GAME_STATE["is_paused"] = True
                    GAME_STATE["pause_timestamp"] = time.perf_counter()
                    await websocket.send_json({"type": "pause_toggled", "status": "paused"})
                else:
                    paused_duration = time.perf_counter() - GAME_STATE["pause_timestamp"]
                    GAME_STATE["total_paused_time"] += paused_duration
                    GAME_STATE["is_paused"] = False
                    GAME_STATE["pause_timestamp"] = None
                    await websocket.send_json({"type": "pause_toggled", "status": "running"})
                continue

            # Only process key events if not paused.
            if GAME_STATE["is_paused"]:
                continue

            # Compute effective current time (excluding paused time).
            current_time = time.perf_counter() - GAME_STATE["start_time"] - GAME_STATE["total_paused_time"]

            if data.get("key") in ["a", "l"]:
                move = "left" if data["key"] == "a" else "right"
                hit = Note(move_type=move, start=current_time, duration=0.0, subdivision=0)
                judgement = score_live_note(
                    move,
                    current_time,
                    hit,
                    bpm=GAME_STATE["bpm"],
                    threshold_fraction=1 / 2
                )
                print("Judgement: ", judgement)

                score_delta = calculate_score(judgement, GAME_STATE["current_streak"])
                GAME_STATE["total_score"] += score_delta
                if judgement in ["MISS", "OOPS"]:
                    GAME_STATE["current_streak"] = 0
                else:
                    GAME_STATE["current_streak"] += 1
                    GAME_STATE["max_streak"] = max(GAME_STATE["max_streak"], GAME_STATE["current_streak"])

                await websocket.send_json({
                    "type": "hit_registered",
                    "move": move,
                    "time": current_time,
                    "lastJudgement": judgement,
                    "totalScore": GAME_STATE["total_score"],
                    "currentStreak": GAME_STATE["current_streak"],
                    "maxStreak": GAME_STATE["max_streak"],
                    "scoreDelta": score_delta
                })

        # The loop will naturally break when GAME_STATE["is_running"] becomes False.
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        game_checker_task.cancel()
        await websocket.close()


@app.get("/game/status")
async def get_game_status() -> GameStatusResponse:
    if not GAME_STATE["is_running"]:
        return GameStatusResponse(status="not_running")

    current_time = time.perf_counter() - GAME_STATE["start_time"] - GAME_STATE["total_paused_time"]
    return GameStatusResponse(
        status="running",
        elapsed_time=current_time,
        total_duration=GAME_STATE["game_duration"]
    )


@app.get("/health")
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(status="ok")
