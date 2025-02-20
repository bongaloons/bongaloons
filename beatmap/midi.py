import pretty_midi
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Deque
from score import Judgement
from collections import deque
from settings import T_FALL, FALL_DURATION
import json
# Mapping from MIDI pitch to move name.
pitch_to_move = {67: "left", 72: "right", 79: "super"}

@dataclass
class Note:
    move_type: str
    start: float
    duration: float
    subdivision: int  # e.g. 4 for quarter, 8 for eighth, etc.

with open("../frontend/public/settings.json", "r") as f:
    settings = json.load(f)

DELAY_OFFSET = settings.get("delay", 0) / 1000
REACTION_TIME = settings.get("reaction_time", 0) / 1000


def get_note_subdivision(duration: float, bpm: float) -> int:
    """
    Given the duration of a note in seconds and the BPM,
    determine the subdivision (e.g. quarter, eighth, etc.) by comparing
    against standard note lengths in terms of quarter note multiples.
    
    Returns an integer representing the note's subdivision:
        whole: 1, half: 2, quarter: 4, eighth: 8, sixteenth: 16,
        thirty-second: 32, sixty-fourth: 64, 128th: 128.
    """
    quarter_duration = 60.0 / bpm
    note_fraction = duration / quarter_duration

    note_values = {
        "whole": 4.0,
        "half": 2.0,
        "quarter": 1.0,
        "eighth": 0.5,
        "sixteenth": 0.25,
        "thirty-second": 0.125,
        "sixty-fourth": 0.0625,
        "128th": 0.03125,
    }
    note_subdivisions = {
        "whole": 1,
        "half": 2,
        "quarter": 4,
        "eighth": 8,
        "sixteenth": 16,
        "thirty-second": 32,
        "sixty-fourth": 64,
        "128th": 128,
    }
    
    best_match = None
    smallest_diff = float('inf')
    for note_name, value in note_values.items():
        diff = abs(note_fraction - value)
        if diff < smallest_diff:
            smallest_diff = diff
            best_match = note_name

    return note_subdivisions.get(best_match, -1)


def parse_midi(midi_path: str) -> Dict[str, List[Note]]:
    """
    Parses the MIDI file and returns a dictionary where the key is the move name (derived from the MIDI note pitch)
    and the value is a list of Note objects (sorted by start time) associated with that move.
    Only pitches that exist in `pitch_to_move` are included.
    """
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    bpm = midi_data.estimate_tempo()
    print(f"Estimated BPM from MIDI: {bpm:.2f}")
    
    notes_by_move: Dict[str, List[Note]] = {}
    
    for instrument in midi_data.instruments:
        for note in instrument.notes:
            move = pitch_to_move.get(note.pitch)
            if move is None:
                continue

            start = note.start
            duration = note.end - note.start
            subdivision = get_note_subdivision(duration, bpm)
            note_obj = Note(move_type=move, start=start, duration=duration, subdivision=subdivision)
            
            if move not in notes_by_move:
                notes_by_move[move] = []
            notes_by_move[move].append(note_obj)
            print(f"Truth - Move '{move}' (Pitch {note.pitch}) - Start: {note_obj.start:.2f} sec, "
                  f"Duration: {note_obj.duration:.2f} sec, Subdivision: {note_obj.subdivision}")

    for move, note_list in notes_by_move.items():
        note_list.sort(key=lambda n: n.start)
    
    return notes_by_move

# Editable ranking thresholds for early and late hits.
# Each value is the fraction of the threshold that determines the ranking.
# For example, if a hit's error is less than 20% of the threshold, it's "perfect".
RANKING_THRESHOLDS = {
    "early": {
        "perfect": 0.2,
        "good": 0.5,
        "meh": 0.8,
        "bad": 1.0,
    },
    "late": {
        "perfect": 0.2,
        "good": 0.5,
        "meh": 0.8,
        "bad": 1.0,
    }
}

## REFERENCE METHOD VV ##

def score_beatmaps(
    truth: Dict[str, List[Note]],
    user: Dict[str, List[Note]],
    bpm: float,
    threshold_fraction: float = 1  # used for both early and late threshold
) -> Dict[str, List[Tuple[Optional[Note], Optional[Note], Optional[float], str]]]:
    """
    Scores the user's beatmap against the truth beatmap.
    
    For each move, we match hit notes (user) to truth notes by time:
      - If a user note occurs too early (before truth_note.start - threshold), record it as an extra hit ("OOPS").
      - If a user note occurs too late (after truth_note.start + threshold), mark the truth note as "MISS" and move on.
      - Otherwise, assign the hit note to the truth note, compute the time difference,
        and then rank the hit based on how large the difference is relative to the threshold.
      - Once a truth note is matched, move to the next truth note (preventing double hits).
      - After processing, any remaining truth notes are marked as "MISS" and any remaining user notes are marked as "OOPS".
      
    Returns a dictionary mapping each move to a list of tuples:
      (truth_note, user_note, time_difference (user - truth), judgement)
    where judgement is one of:
      "perfect", "perfect early", "good early", "meh early", "bad early",
      "perfect late", "good late", "meh late", "bad late", "MISS", or "OOPS".
    """
    quarter_duration = 60.0 / bpm
    threshold = threshold_fraction * quarter_duration

    score_results: Dict[str, List[Tuple[Optional[Note], Optional[Note], Optional[float], str]]] = {}
    
    for move, truth_notes in truth.items():
        user_notes = user.get(move, [])
        t_idx = 0
        u_idx = 0
        results = []
        
        while t_idx < len(truth_notes) and u_idx < len(user_notes):
            t_note = truth_notes[t_idx]
            u_note = user_notes[u_idx]
            
            # If the user hit is too early for the current truth note, record it as OOPS.
            if u_note.start < t_note.start - threshold:
                results.append((None, u_note, None, Judgement.OOPS))
                u_idx += 1
                continue
            
            # If the user hit is too late for the current truth note, mark the truth note as MISS.
            if u_note.start > t_note.start + threshold:
                results.append((t_note, None, None, Judgement.MISS))
                t_idx += 1
                continue
            
            # Now the user note is within the acceptable window.
            diff = u_note.start - t_note.start
            if diff == 0:
                judgement = Judgement.PERFECT
            else:
                hit_type = "early" if diff < 0 else "late"
                ratio = abs(diff) / threshold
                if ratio < RANKING_THRESHOLDS[hit_type]["perfect"]:
                    rank = "perfect"
                elif ratio < RANKING_THRESHOLDS[hit_type]["good"]:
                    rank = "good"
                elif ratio < RANKING_THRESHOLDS[hit_type]["meh"]:
                    rank = "meh"
                else:
                    rank = "bad"
                
                if hit_type == "early":
                    if rank == "perfect":
                        judgement = Judgement.PERFECT_EARLY
                    elif rank == "good":
                        judgement = Judgement.GOOD_EARLY
                    elif rank == "meh":
                        judgement = Judgement.MEH_EARLY
                    else:
                        judgement = Judgement.BAD_EARLY
                else:
                    if rank == "perfect":
                        judgement = Judgement.PERFECT_LATE
                    elif rank == "good":
                        judgement = Judgement.GOOD_LATE
                    elif rank == "meh":
                        judgement = Judgement.MEH_LATE
                    else:
                        judgement = Judgement.BAD_LATE
            
            results.append((t_note, u_note, diff, judgement))
            t_idx += 1
            u_idx += 1
        
        # Any remaining truth notes are marked as MISS.
        while t_idx < len(truth_notes):
            results.append((truth_notes[t_idx], None, None, Judgement.MISS))
            t_idx += 1
        
        # Any remaining user notes are extra hits: mark them as OOPS.
        while u_idx < len(user_notes):
            results.append((None, user_notes[u_idx], None, Judgement.OOPS))
            u_idx += 1

        score_results[move] = results

    return score_results

## REFERENCE METHOD ^^ ##

class BeatmapSession:
    def __init__(self, truth_beatmap: Dict[str, List[Note]], bpm: float):
        self.bpm = bpm
        # Convert lists to deques for efficient popping from front
        self.move_queues: Dict[str, Deque[Note]] = {}
        for move, notes in truth_beatmap.items():
            sorted_notes = sorted(notes, key=lambda n: n.start)
            self.move_queues[move] = deque(sorted_notes)
            
    def get_remaining_notes(self) -> int:
        """Return total number of remaining notes across all moves."""
        return sum(len(q) for q in self.move_queues.values())
    
    def score_live_note(self, move: str, current_time: float, hit_note: Optional[Note], 
                       threshold_fraction: float = 1/8) -> str:
        """Score a live note hit."""
        if move not in self.move_queues or not self.move_queues[move]:
            return Judgement.OOPS
            
        front_note = self.move_queues[move][0]
        quarter_duration = 60.0 / self.bpm
        threshold = threshold_fraction * quarter_duration
        
        if hit_note is not None:
            # Compare hit time with truth note time, accounting for delay offset and reaction time
            diff = hit_note.start - (front_note.start + DELAY_OFFSET + REACTION_TIME)
            
            if diff < -threshold:
                return Judgement.OOPS
            if diff > threshold:
                self.move_queues[move].popleft()
                return Judgement.MISS
                
            # Within threshold window - calculate precise judgement
            ratio = abs(diff) / threshold
            hit_type = "early" if diff < 0 else "late"
            
            if ratio < 0.2:  # Perfect window
                judgement = Judgement.PERFECT
            elif ratio < 0.5:  # Good window
                judgement = (Judgement.GOOD_EARLY if hit_type == "early" 
                           else Judgement.GOOD_LATE)
            elif ratio < 0.8:  # Meh window
                judgement = (Judgement.MEH_EARLY if hit_type == "early"
                           else Judgement.MEH_LATE)
            else:  # Bad window
                judgement = (Judgement.BAD_EARLY if hit_type == "early"
                           else Judgement.BAD_LATE)
                
            self.move_queues[move].popleft()
            return judgement
            
        else:
            # For checking misses, account for delay offset
            if current_time > front_note.start + DELAY_OFFSET + threshold:
                self.move_queues[move].popleft()
                return Judgement.MISS
            return "waiting"
            
    def check_misses(self, current_time: float, threshold_fraction: float = 1/8) -> List[tuple[str, Note, str]]:
        """Check for missed notes across all moves."""
        missed_notes = []
        quarter_duration = 60.0 / self.bpm
        threshold = threshold_fraction * quarter_duration
        
        for move, queue in self.move_queues.items():
            while queue:
                front_note = queue[0]
                if current_time > front_note.start + threshold:
                    missed_note = queue.popleft()
                    missed_notes.append((move, missed_note, Judgement.MISS))
                else:
                    break
                    
        return missed_notes

# Example usage:
if __name__ == "__main__":
    bpm = 120.0
    threshold_fraction = 1/4

    # Load truth notes one at a time using load_truth_note.
    load_truth_note("left", Note(start=1.00, duration=0.5, subdivision=8))
    load_truth_note("left", Note(start=2.00, duration=0.5, subdivision=8))
    load_truth_note("left", Note(start=3.00, duration=0.5, subdivision=8))
    load_truth_note("right", Note(start=1.50, duration=0.5, subdivision=8))
    load_truth_note("right", Note(start=2.50, duration=0.5, subdivision=8))

    # Case 1: A left hit at 1.02 sec.
    hit_left = Note(start=1.02, duration=0.5, subdivision=8)
    status = score_live_note("left", current_time=1.02, hit_note=hit_left, bpm=bpm, threshold_fraction=threshold_fraction)
    print("Left hit at 1.02 sec:", status)
    
    # Case 2: No hit, current time 2.08 sec for left.
    status = score_live_note("left", current_time=2.08, hit_note=None, bpm=bpm, threshold_fraction=threshold_fraction)
    print("Left, no hit at 2.08 sec:", status)
    
    # Case 3: A right hit at 1.40 sec (too early) for right.
    hit_right = Note(start=1.40, duration=0.5, subdivision=8)
    status = score_live_note("right", current_time=1.40, hit_note=hit_right, bpm=bpm, threshold_fraction=threshold_fraction)
    print("Right hit at 1.40 sec:", status)
    
    # Case 4: A right hit at 1.52 sec (good) for right.
    hit_right_good = Note(start=1.52, duration=0.5, subdivision=8)
    status = score_live_note("right", current_time=1.52, hit_note=hit_right_good, bpm=bpm, threshold_fraction=threshold_fraction)
    print("Right hit at 1.52 sec:", status)


# if __name__ == "__main__":
#     # For testing, we create both a truth beatmap and a user beatmap manually.
#     # We'll assume a sample BPM.
#     sample_bpm = 120.0  # 120 BPM => quarter note = 0.5 sec; with threshold_fraction=1/8, threshold = 0.0625 sec
    
#     # Create a truth beatmap manually.
#     # For "left", truth notes at 1.00 sec, 2.00 sec, and 3.00 sec.
#     truth_moves: Dict[str, List[Note]] = {
#         "left": [
#             Note(start=1.00, duration=0.5, subdivision=8),
#             Note(start=2.00, duration=0.5, subdivision=8),
#             Note(start=3.00, duration=0.5, subdivision=8),
#         ],
#         "right": [
#             Note(start=1.50, duration=0.5, subdivision=8),
#             Note(start=2.50, duration=0.5, subdivision=8),
#         ]
#     }
    
#     # Create a user hit beatmap manually to test various edge cases.
#     user_moves: Dict[str, List[Note]] = {
#         "left": [
#             # Good hit for the first truth note (diff = +0.02 sec)
#             Note(start=1.02, duration=0.5, subdivision=8),
#             # A hit that is too early for the second truth note:
#             # (Truth at 2.00 sec; hit at 1.93 sec is too early)
#             Note(start=1.93, duration=0.5, subdivision=8),
#             # A valid hit for the second truth note (diff = +0.04 sec)
#             Note(start=2.04, duration=0.5, subdivision=8),
#             # A hit that is too late for the third truth note:
#             # (Truth at 3.00 sec; hit at 3.10 sec is beyond 3.0625, so it's a MISS)
#             Note(start=3.10, duration=0.5, subdivision=8),
#             # Extra hit that should be marked as OOPS because there's no corresponding truth note.
#             Note(start=3.15, duration=0.5, subdivision=8),
#         ],
#         "right": [
#             # Good hit for the first truth note (exactly on time)
#             Note(start=1.00, duration=0.5, subdivision=8),
#             # A hit that's too early for the second truth note:
#             # (Truth at 2.50 sec; hit at 2.40 sec is too early)
#             Note(start=2.40, duration=0.5, subdivision=8),
#             # Extra hits beyond the truth notes (should be OOPS)
#             Note(start=2.40, duration=0.5, subdivision=8),
#             Note(start=2.40, duration=0.5, subdivision=8)
#         ]
#     }
    
#     # Score the beatmaps.
#     # (Using threshold_fraction=1/8 so threshold = 0.0625 sec at 120 BPM)
#     scores = score_beatmaps(truth_moves, user_moves, bpm=sample_bpm, threshold_fraction=1)
    
#     print("\nScoring Results:")
#     for move, results in scores.items():
#         print(f"\nMove '{move}':")
#         for truth_note, user_note, diff, judgement in results:
#             if truth_note is not None and user_note is not None:
#                 print(f"  Truth note at {truth_note.start:.2f} sec matched with hit at {user_note.start:.2f} sec "
#                       f"(diff: {diff:+.2f} sec) -> {judgement}")
#             elif truth_note is not None:
#                 print(f"  Truth note at {truth_note.start:.2f} sec -> {judgement}")
#             elif user_note is not None:
#                 print(f"  Extra hit at {user_note.start:.2f} sec -> {judgement}")
