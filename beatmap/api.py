import json
import time
import asyncio
import os
from game_state import start_new_game, process_hit as process_hit_state
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from midi import (
    Note,
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
import signal

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("../frontend/public/settings.json", "r") as f:
    settings = json.load(f)

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
    "bpm": DEFAULT_BPM,
    "total_score": 0,
    "current_streak": 0,
    "max_streak": 0,
    "session": None
}

serial_handler = SerialHandler()

@app.on_event("startup")
async def startup_event():
    serial_handler.start()

@app.on_event("shutdown")
async def shutdown_event():
    serial_handler.stop()


def signal_handler(signum, frame):
    print("Shutting down gracefully...")
    serial_handler.stop()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler) 

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
    state, falling_dots, _ = start_new_game(id)
    for field in state.__dict__.keys():
        if field == 'session':
            GAME_STATE['session'] = state.session
        else:
            GAME_STATE[field] = getattr(state, field)
    return {
        "status": "started",
        "duration": state.game_duration,
        "falling_dots": falling_dots,
        "songPath": state.song_path,
        "midiPath": state.midi_path,
        "songName": state.song_name,
        "bpm": state.bpm,
        "difficulty": state.difficulty
    }

async def process_hit(websocket: WebSocket, move: str, current_time: float):
    """Helper function to process a hit (from keyboard or serial)"""
    if not GAME_STATE["session"]:
        return
        
    hit = Note(move_type=move, start=current_time, duration=0.0, subdivision=0)
    judgement = GAME_STATE["session"].score_live_note(
        move, 
        current_time, 
        hit, 
        threshold_fraction=1
    )
    
    score_delta = calculate_score(judgement, GAME_STATE["current_streak"])
    GAME_STATE["total_score"] += score_delta
    
    if judgement in ["MISS", "OOPS"]:
        GAME_STATE["current_streak"] = 0
    else:
        GAME_STATE["current_streak"] += 1
        GAME_STATE["max_streak"] = max(
            GAME_STATE["max_streak"], 
            GAME_STATE["current_streak"]
        )
        
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
    if not GAME_STATE["session"]:
        return
        
    for move in list(GAME_STATE["session"].move_queues.keys()):
        while GAME_STATE["session"].move_queues[move]:
            judgement = GAME_STATE["session"].score_live_note(
                move, 
                current_time, 
                None,
                threshold_fraction=1
            )
            if judgement == "MISS":
                score_delta = calculate_score(judgement, GAME_STATE["current_streak"])
                GAME_STATE["total_score"] += score_delta
                GAME_STATE["current_streak"] = 0
                
    await websocket.send_json({
        "type": "game_over",
        "message": "Game over!",
        "totalScore": GAME_STATE["total_score"],
        "scores": {
            move: list(queue) for move, queue in GAME_STATE["session"].move_queues.items()
        },
        "lastJudgement": None,
        "maxStreak": GAME_STATE["max_streak"]
    })
    GAME_STATE["is_running"] = False


async def game_status_checker(websocket: WebSocket):
    """Background task that continuously checks for missed notes and game over state."""
    threshold_fraction = 1 / 2
    while True:
        if not GAME_STATE["is_running"] or GAME_STATE["is_paused"] or not GAME_STATE["session"]:
            await asyncio.sleep(0.05)
            continue
            
        current_time = time.perf_counter() - GAME_STATE["start_time"] - GAME_STATE["total_paused_time"]
        
        # Log remaining notes
        remaining_notes = GAME_STATE["session"].get_remaining_notes()
        
        # Check for game duration exceeded
        if current_time >= GAME_STATE["game_duration"] + T_END:
            print(f"Game duration exceeded: {current_time:.2f} >= {GAME_STATE['game_duration'] + T_END:.2f}")
            await handle_game_over(websocket, current_time)
            break
            
        # Check for missed notes
        for move in list(GAME_STATE["session"].move_queues.keys()):
            while GAME_STATE["session"].move_queues.get(move):
                judgement = GAME_STATE["session"].score_live_note(
                    move,
                    current_time - T_FALL,
                    None,
                    threshold_fraction=threshold_fraction
                )
                if judgement == "waiting":
                    break
                elif judgement == "MISS":
                    score_delta = calculate_score(judgement, GAME_STATE["current_streak"])
                    GAME_STATE["total_score"] += score_delta
                    GAME_STATE["current_streak"] = 0
                    await websocket.send_json({
                        "type": "note_missed",
                        "move": move,
                        "time": current_time - T_FALL,
                        "judgement": judgement,
                        "totalScore": GAME_STATE["total_score"],
                        "currentStreak": 0,
                    })
        
        # Check if all notes are completed
        if remaining_notes == 0 and GAME_STATE["is_running"]:
            print(f"All notes completed at time {current_time:.2f}")
            await handle_game_over(websocket, current_time)
            break
                    
        await asyncio.sleep(0.02)


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
            
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=0.01)
                
                if data.get("type") == "end_game":
                    print("Client requested WebSocket closure")
                    break
                    
                if not GAME_STATE["is_running"]:
                    continue
                    
                current_time = time.perf_counter() - GAME_STATE["start_time"]
                
                if data.get("key") in ["a", "l"]:
                    move = "left" if data["key"] == "a" else "right"
                    await process_hit(websocket, move, current_time)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if "receive" not in str(e):
                    print(f"WebSocket error: {e}")
                    break

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        game_checker_task.cancel()

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
    max_notes: str,
    audio: UploadFile = File(...),
):
    """
    Creates a beatmap from an uploaded MP3 file.
    Returns the generated MIDI file path and other metadata.
    """
    print("Creating beatmap with max notes:", max_notes)
    os.makedirs("../frontend/public/uploads", exist_ok=True)
    max_notes = int(max_notes)
    
    difficulty = 1
    if max_notes <= 50:
        difficulty = 1
    elif max_notes <= 100:
        difficulty = 2
    elif max_notes <= 150:
        difficulty = 3
    elif max_notes <= 200:
        difficulty = 4
    else:
        difficulty = 5
        
    timestamp = int(time.time())
    mp3_filename = f"upload_{timestamp}.mp3"
    midi_filename = f"upload_{timestamp}.mid"
    
    mp3_path = f"../frontend/public/uploads/{mp3_filename}"
    midi_path = f"../frontend/public/uploads/{midi_filename}"
    
    try:
        content = await audio.read()
        with open(mp3_path, "wb") as f:
            f.write(content)
            
        from make_beatmap import process_audio_to_midi
        bpm = process_audio_to_midi(mp3_path, midi_path, max_notes)
        
        song_name = audio.filename.rsplit('.', 1)[0] if audio.filename else f"Custom Song {timestamp}"
        
        catalog = []
        try:
            with open("catalog.json", "r") as f:
                content = f.read().strip()
                if content and content[-1] == ']':
                    try:
                        catalog = json.loads(content)
                    except json.JSONDecodeError:
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
            
        max_id = 0
        for entry in catalog:
            if isinstance(entry, dict) and 'id' in entry:
                max_id = max(max_id, entry['id'])
        
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
        
        os.replace(temp_path, "catalog.json")
            
        return {
            "status": "success",
            "song": new_entry
        }
        
    except Exception as e:
        try:
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
            if os.path.exists(midi_path):
                os.remove(midi_path)
        except:
            pass
        print(f"Error creating beatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))
