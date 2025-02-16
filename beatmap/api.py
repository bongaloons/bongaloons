import json
import time
import asyncio
import os
import mediapipe as mp

from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from detect_hand_position import check_hand_position_api, setup_model
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
from serial_handler import SerialHandler
from redis_client import add_score, get_leaderboard

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load settings from settings.json (located in ../frontend/public/)
with open("../frontend/public/settings.json", "r") as f:
    settings = json.load(f)

# Convert fall_duration and end_pause from ms to seconds.
T_FALL = settings.get("fall_duration", 2000) / 1000
T_END = settings.get("end_pause", 0) / 1000
DEFAULT_BPM = settings.get("default_bpm", 120)

# Global GAME_STATE holds the game state.
GAME_STATE = {
    "is_running": False,
    "is_paused": False,         # Whether the game is currently paused
    "pause_timestamp": None,    # Timestamp when pause started (in seconds)
    "total_paused_time": 0,     # Total paused time (in seconds)
    "start_time": None,         # Game start time (in seconds; set via time.perf_counter())
    "game_duration": 0,
    "bpm": DEFAULT_BPM,
    "songPath": "",             # Audio file path
    "midiPath": "",             # MIDI file path from the catalog
    "songName": "",             # Name of the song from the catalog
    "total_score": 0,
    "current_streak": 0,
    "max_streak": 0
}

# Start the serial handler at startup.
serial_handler = SerialHandler()

@app.on_event("startup")
async def startup_event():
    serial_handler.start()

@app.on_event("shutdown")
async def shutdown_event():
    serial_handler.stop()

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
    # Get song info from catalog.json.
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

    # Build the full MIDI path using the frontend public folder.
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
            target_time=note.start * 1000,  # Convert to ms
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

async def process_hit(websocket: WebSocket, move: str, current_time: float):
    """Helper function to process a hit (from keyboard or serial)"""
    hit = Note(move_type=move, start=current_time, duration=0.0, subdivision=0)
    judgement = score_live_note(move, current_time, hit, bpm=GAME_STATE["bpm"], threshold_fraction=1/2)
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

async def handle_game_over(websocket: WebSocket, current_time: float):
    """Helper function to handle game over state"""
    for move in list(global_truth_map.keys()):
        while global_truth_map[move]:
            judgement = score_live_note(move, current_time, None, bpm=GAME_STATE["bpm"], threshold_fraction=1/2)
            if judgement == "MISS":
                GAME_STATE["total_score"] += calculate_score(judgement, GAME_STATE["current_streak"])
                GAME_STATE["current_streak"] = 0
    await websocket.send_json({
        "type": "game_over",
        "message": "Game over!",
        "totalScore": GAME_STATE["total_score"]
    })
    GAME_STATE["is_running"] = False

async def game_status_checker(websocket: WebSocket):
    """
    Background task that continuously checks for missed notes and whether the game is over.
    Only acts when the game is running and not paused.
    """
    threshold_fraction = 1 / 2  # Threshold for missed note checking.
    while True:
        print("START OPF LOOP")
        if not GAME_STATE["is_running"]:
            await asyncio.sleep(0.05)
            continue
        if GAME_STATE["is_paused"]:
            await asyncio.sleep(0.05)
            continue
        current_time = time.perf_counter() - GAME_STATE["start_time"] - GAME_STATE["total_paused_time"]
        print("Effective time:", current_time, "Game duration + T_END:", GAME_STATE["game_duration"] + T_END)
        if current_time >= GAME_STATE["game_duration"] + T_END:
            await websocket.send_json({
                "type": "game_over",
                "message": "Game over!",
                "totalScore": GAME_STATE["total_score"]
            })
            GAME_STATE["is_running"] = False
            break
        for move in list(global_truth_map.keys()):
            print(list(global_truth_map.keys()))
            while global_truth_map.get(move):
                print("a")
                judgement = score_live_note(
                    move,
                    current_time - T_FALL,
                    None,
                    bpm=GAME_STATE["bpm"],
                    threshold_fraction=threshold_fraction
                )
                print("b", judgement)
                if judgement == "waiting":
                    break
                else:
                    print("b2")
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
                print("c")
            print("D")
        await asyncio.sleep(0.02)
    print("difhdifh")


@app.websocket("/game/ws")
async def game_websocket(websocket: WebSocket):
    await websocket.accept()
    game_checker_task = asyncio.create_task(game_status_checker(websocket))
    try:
        while True:
            serial_key = serial_handler.get_key()
            if serial_key in ["a", "l"]:
                move = "left" if serial_key == "a" else "right"
                if GAME_STATE["is_running"]:
                    current_time = time.perf_counter() - GAME_STATE["start_time"]
                    # TODO: remove following line, this is to just temp patch the serial input which seems delayed
                    current_time -= 0.05
                    print(f"Processing serial hit: {move} at time {current_time}")  # Debug print
                    await process_hit(websocket, move, current_time)
            
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=0.01)
            except asyncio.TimeoutError:
                data = None

            if not GAME_STATE["is_running"]:
                continue

            # Handle pause toggle message.
            if data and data.get("type") == "toggle_pause":
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

            if GAME_STATE["is_paused"]:
                continue

            current_time = time.perf_counter() - GAME_STATE["start_time"] - GAME_STATE["total_paused_time"]

            if data and data.get("key") in ["a", "l"]:
                move = "left" if data["key"] == "a" else "right"
                await process_hit(websocket, move, current_time)
            
            print("hello", current_time, GAME_STATE["game_duration"] + T_END)

            if current_time >= GAME_STATE["game_duration"] + T_END:
                await handle_game_over(websocket, current_time)
                break

            await asyncio.sleep(0.005)
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

@app.post("/leaderboard/add")
async def add_to_leaderboard(name: str, score: int, max_streak: int):
    add_score(name, score, max_streak)
    return {"status": "success"}

@app.get("/leaderboard")
async def get_top_scores():
    scores = get_leaderboard()
    return {"scores": scores}


@app.post("/video/upload")
async def upload_video_segment(
    start: int,
    end: int,
    video: UploadFile = File(...)
):
    """
    Receives video segments from the frontend and saves them for processing.
    start: timestamp when segment starts (ms)
    end: timestamp when segment ends (ms)
    """
    # Create videos directory if it doesn't exist
    os.makedirs("videos", exist_ok=True)
    
    # Generate unique filename using timestamps
    filename = f"videos/segment_{start}_{end}.bin"
    print(f"Saving to file: {filename}")
    
    # Save the uploaded file
    try:
        contents = await video.read()
        print(f"Read {len(contents)} bytes from upload")
        with open(filename, "wb") as f:
            f.write(contents)
        print("File saved successfully")
        return {"status": "success", "filename": filename}
    except Exception as e:
        print(f"Error saving video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event(use_double=False):
    global interpreter, input_details, output_details
    tflite_save_path = "./model/model_doubleTrue.tflite" if use_double else "./model/model_doubleFalse.tflite"
    interpreter, input_details, output_details = setup_model(tflite_save_path)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

    while True:
        data = await websocket.receive_bytes()
        if data["type"] == "super_detected":
            left, right = check_hand_position_api(data, hands, mp_hands, interpreter, input_details, output_details, use_double=False)
            await websocket.send_json({"left": left, "right": right})
