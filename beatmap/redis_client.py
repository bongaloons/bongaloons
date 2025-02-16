import redis
import json
from typing import List, Dict

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def add_score(name: str, score: int, max_streak: int) -> None:
    """Add a score to the leaderboard"""
    entry = json.dumps({
        'name': name,
        'score': score,
        'max_streak': max_streak
    })
    redis_client.zadd('leaderboard', {entry: score})
    # Keep only top 100 scores
    redis_client.zremrangebyrank('leaderboard', 0, -101)


def get_leaderboard() -> List[Dict]:
    """Get the top 100 scores"""
    entries = redis_client.zrevrange('leaderboard', 0, 99, withscores=True)
    return [json.loads(entry[0]) for entry in entries] 