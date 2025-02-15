from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import time
from midi import parse_midi, score_beatmaps, Note

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

T_FALL = 2.0
GAME_STATE = {
    "is_running": False,
    "start_time": None,
    "truth_moves": None,
    "user_moves": {"left": [], "right": []},
    "game_duration": 0
}

@app.post("/game/start")
async def start_game(midi_file: str = "test.mid"):
    """Initialize a new game session"""
    GAME_STATE["truth_moves"] = parse_midi(midi_file)
    
    max_time = 0.0
    for notes in GAME_STATE["truth_moves"].values():
        if notes:
            max_time = max(max_time, notes[-1].start)
    
    GAME_STATE["game_duration"] = max_time + 2.0
    GAME_STATE["start_time"] = time.perf_counter()
    GAME_STATE["is_running"] = True
    GAME_STATE["user_moves"] = {"left": [], "right": []}
    
    return {
        "status": "started",
        "duration": GAME_STATE["game_duration"],
        "falling_dots": [
            {
                "move": move,
                "target_time": note.start,
                "track": move
            }
            for move, notes in GAME_STATE["truth_moves"].items()
            for note in notes
        ]
    }

@app.websocket("/game/ws")
async def game_websocket(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            if not GAME_STATE["is_running"]:
                continue
                
            current_time = time.perf_counter() - GAME_STATE["start_time"]
            
            if data["key"] in ["a", "l"]:
                move = "left" if data["key"] == "a" else "right"
                hit = Note(start=current_time, duration=0.0, subdivision=0)
                GAME_STATE["user_moves"][move].append(hit)
                
                current_scores = score_beatmaps(
                    GAME_STATE["truth_moves"],
                    GAME_STATE["user_moves"],
                    bpm=120.0,
                    threshold_fraction=1/8
                )
                
                total_score = 0
                last_judgement = None
                for _, results in current_scores.items():
                    for res in results:
                        if res[3]:
                            total_score += 1 if res[3] == "Perfect" else 0.5 if res[3] == "Good" else 0
                            last_judgement = res[3]
                
                await websocket.send_json({
                    "type": "hit_registered",
                    "move": move,
                    "time": current_time,
                    "lastJudgement": last_judgement,
                    "totalScore": total_score
                })
                
            if current_time >= GAME_STATE["game_duration"]:
                scores = score_beatmaps(
                    GAME_STATE["truth_moves"],
                    GAME_STATE["user_moves"],
                    bpm=120.0,
                    threshold_fraction=1/8
                )
                
                total_score = 0
                last_judgement = None
                for move, results in scores.items():
                    for res in results:
                        if res[3]:
                            total_score += 1 if res[3] == "Perfect" else 0.5 if res[3] == "Good" else 0
                            last_judgement = res[3]
                
                await websocket.send_json({
                    "type": "game_over",
                    "scores": {
                        move: [
                            {
                                "truth_time": res[0].start if res[0] else None,
                                "hit_time": res[1].start if res[1] else None,
                                "difference": res[2],
                                "judgement": res[3]
                            }
                            for res in results
                        ]
                        for move, results in scores.items()
                    },
                    "total_score": total_score,
                    "last_judgement": last_judgement
                })
                GAME_STATE["is_running"] = False
                break
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.get("/game/status")
async def get_game_status():
    """Get current game status"""
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
    """Health check endpoint"""
    return {"status": "ok"} 