import json
import time
import asyncio
import os
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
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
    "bpm": 0,
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
    Reads catalog.json and returns a tuple (bpm, songPath, midiPath, songName, difficulty)
    for the given id. If not found, returns (DEFAULT_BPM, "", "", "", 1).
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
                difficulty = entry.get("difficulty", 1)
                return bpm, song, midi_path, song_name, difficulty
    except Exception as e:
        print(f"Error reading catalog.json: {e}")
    return DEFAULT_BPM, "", "", "", 1

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
    bpm, song_path, midi_path, song_name, difficulty = get_song_info_from_catalog(id)
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

    print(notes)
    
    return {
        "status": "started",
        "duration": game_duration,
        "falling_dots": falling_dots,
        "songPath": song_path,
        "midiPath": midi_path,
        "songName": song_name,
        "bpm": GAME_STATE["bpm"],
        "difficulty": difficulty
    }

async def process_hit(websocket: WebSocket, move: str, current_time: float):
    """Helper function to process a hit (from keyboard or serial)"""
    hit = Note(move_type=move, start=current_time, duration=0.0, subdivision=0)
    judgement = score_live_note(move, current_time, hit, bpm=GAME_STATE["bpm"], threshold_fraction=1)
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
            judgement = score_live_note(move, current_time, None, bpm=GAME_STATE["bpm"], threshold_fraction=1/8)
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
        if not GAME_STATE["is_running"]:
            await asyncio.sleep(0.05)
            continue
        if GAME_STATE["is_paused"]:
            await asyncio.sleep(0.05)
            continue
        current_time = time.perf_counter() - GAME_STATE["start_time"] - GAME_STATE["total_paused_time"]
        if current_time >= GAME_STATE["game_duration"] + T_END:
            await websocket.send_json({
                "type": "game_over",
                "message": "Game over!",
                "totalScore": GAME_STATE["total_score"]
            })
            GAME_STATE["is_running"] = False
            break
        for move in list(global_truth_map.keys()):
            while global_truth_map.get(move):
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
                    # print("b2")
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
        await asyncio.sleep(0.02)
    print("difhdifh")


@app.websocket("/game/ws")
async def game_websocket(websocket: WebSocket):
    await websocket.accept()
    game_checker_task = asyncio.create_task(game_status_checker(websocket))
    try:
        while True:
            serial_key = serial_handler.get_key()
            if serial_key in ["left", "right", "both"]:
                move = serial_key
                if GAME_STATE["is_running"]:
                    current_time = time.perf_counter() - GAME_STATE["start_time"]
                    await websocket.send_json({
                        "type": "pose_update",
                        "move": move
                    })
                    if move == "both":
                        await process_hit(websocket, "left", current_time)
                        await process_hit(websocket, "right", current_time)
                    else:
                        await process_hit(websocket, move, current_time)
            
            # Check for WebSocket data with a very short timeout
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=0.01)
                
                if not GAME_STATE["is_running"]:
                    continue
                    
                current_time = time.perf_counter() - GAME_STATE["start_time"]
                
                if data.get("key") in ["a", "l"]:
                    move = "left" if data["key"] == "a" else "right"
                    await process_hit(websocket, move, current_time)
                
                if current_time >= GAME_STATE["game_duration"]:
                    await handle_game_over(websocket, current_time)
                    break
                    
            except asyncio.TimeoutError:
                # This is expected, continue to check serial input
                continue
            except Exception as e:
                if "receive" not in str(e):  # Ignore receive timeouts
                    print(f"WebSocket error: {e}")
                    break

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
        with open(filename, "wb") as f:
            f.write(contents)
        return {"status": "success", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/beatmap/create")
async def create_beatmap(
    audio: UploadFile = File(...),
    max_notes: str = "500"
):
    """
    Creates a beatmap from an uploaded MP3 file.
    Returns the generated MIDI file path and other metadata.
    """
    # Create uploads directory if it doesn't exist
    os.makedirs("../frontend/public/uploads", exist_ok=True)
    max_notes = int(max_notes)
    
    difficulty = 1
    if max_notes > 50:
        difficulty = 2
    elif max_notes > 100:
        difficulty = 3
    elif max_notes > 150:
        difficulty = 4
    elif max_notes > 200:
        difficulty = 5
        
    # Save the uploaded MP3
    timestamp = int(time.time())
    mp3_filename = f"upload_{timestamp}.mp3"
    midi_filename = f"upload_{timestamp}.mid"
    
    mp3_path = f"../frontend/public/uploads/{mp3_filename}"
    midi_path = f"../frontend/public/uploads/{midi_filename}"
    
    try:
        # Save MP3
        content = await audio.read()
        with open(mp3_path, "wb") as f:
            f.write(content)
            
        # Process audio to create MIDI
        from make_beatmap import process_audio_to_midi
        bpm = process_audio_to_midi(mp3_path, midi_path, max_notes)
        
        # Get song name from the original filename, removing the extension
        song_name = audio.filename.rsplit('.', 1)[0] if audio.filename else f"Custom Song {timestamp}"
        
        # Read and validate catalog
        catalog = []
        try:
            with open("catalog.json", "r") as f:
                content = f.read().strip()
                # Check if the content ends with a proper closing bracket
                if content and content[-1] == ']':
                    try:
                        catalog = json.loads(content)
                    except json.JSONDecodeError:
                        # If parsing fails, start with default catalog
                        catalog = [
                            {
                                "id": 0,
                                "name": "The Cha Cha Slide (Easy)",
                                "path": "songmaps/chacha.mid",
                                "song": "songs/chacha.mp3",
                                "bpm": 122,
                                "difficulty": 2
                            }
                        ]
        except FileNotFoundError:
            # If file doesn't exist, start with default catalog
            catalog = [
                {
                    "id": 0,
                    "name": "The Cha Cha Slide (Easy)",
                    "path": "songmaps/chacha.mid",
                    "song": "songs/chacha.mp3",
                    "bpm": 122,
                    "difficulty": 2
                }
            ]
            
        # Find max ID from valid entries
        max_id = 0
        for entry in catalog:
            if isinstance(entry, dict) and 'id' in entry:
                max_id = max(max_id, entry['id'])
        
        # Create new catalog entry
        new_entry = {
            "id": max_id + 1,
            "name": song_name,
            "path": f"/uploads/{midi_filename}",
            "song": f"/uploads/{mp3_filename}",
            "bpm": int(bpm) if isinstance(bpm, (int, float)) else int(bpm[0]),
            "difficulty": difficulty
        }
        
        # Remove any incomplete entries
        catalog = [entry for entry in catalog if isinstance(entry, dict) and all(
            key in entry for key in ['id', 'name', 'path', 'song', 'bpm', 'difficulty']
        )]
        
        catalog.append(new_entry)
        
        # Write the updated catalog with proper formatting
        # Use a temporary file to ensure atomic write
        temp_path = "catalog.json.tmp"
        with open(temp_path, "w") as f:
            json.dump(catalog, f, indent=4)
        
        # Atomic rename to prevent corruption
        os.replace(temp_path, "catalog.json")
            
        return {
            "status": "success",
            "song": new_entry
        }
        
    except Exception as e:
        # Clean up files if there was an error
        try:
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
            if os.path.exists(midi_path):
                os.remove(midi_path)
        except:
            pass
        print(f"Error creating beatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))
