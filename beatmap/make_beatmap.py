import librosa
import numpy as np
from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo

MAX_NOTES = 500 # Default maximum notes in the final MIDI file


def process_audio_to_midi(input_mp3, output_midi, difficulty=2) -> float:
    """
    Creates a MIDI beatmap from an MP3 file based on difficulty level (1-5).
    Returns the detected BPM of the song.
    
    Difficulty levels determine notes per minute (NPM):
    1 (Easy): ~30 NPM
    2 (Normal): ~60 NPM
    3 (Hard): ~90 NPM
    4 (Expert): ~120 NPM
    5 (Master): ~150 NPM
    """
    # --- Step 1: Load the audio and determine BPM ---
    y, sr = librosa.load(input_mp3, sr=22050)
    duration = librosa.get_duration(y=y, sr=sr)
    # Add 2 seconds of padding at the end
    padded_duration = duration + 2.0
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    
    # Convert numpy array to float if necessary
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0])  # Take first value if it's an array
    
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    print(f"Estimated BPM: {tempo:.2f}")
    
    # Calculate desired notes per minute based on difficulty
    npm = difficulty * 30
    target_notes = int((duration / 60) * npm)  # Use original duration for note calculation

    # Ensure reasonable bounds (20-1000 notes)
    max_notes = max(20, min(target_notes, 1000))
    print(f"Targeting {max_notes} notes for difficulty {difficulty} ({npm} notes per minute)")

    # Calculate tempo-dependent tolerance (1/8 of the time between beats)
    beat_duration = 60.0 / tempo  # seconds per beat
    tol = beat_duration * 0.125   # 1/8 of a beat duration
    print(f"Using tolerance: {tol:.3f} seconds")

    # Add onset strength detection
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    onset_strengths = librosa.onset.onset_strength(y=y, sr=sr)
    
    # Normalize onset strengths to MIDI velocity range (0-127)
    onset_strengths = onset_strengths[onset_frames]
    onset_velocities = np.clip(onset_strengths * 127 / onset_strengths.max(), 40, 127).astype(int)
    
    # Create a mapping of onset times to velocities
    onset_velocity_map = dict(zip(onset_times, onset_velocities))
    
    # --- Step 2: Merge events and assign notes ---
    # Combine the beat times and onset times.
    all_times = np.union1d(beat_times, onset_times)
    all_times.sort()

    events = []
    for t in all_times:
        # Get velocity from nearby onset, or use default if not found
        velocity = 64  # default velocity
        for onset_time, onset_vel in onset_velocity_map.items():
            if abs(t - onset_time) < tol:
                velocity = onset_vel
                break
                
        is_beat = np.any(np.isclose(t, beat_times, atol=tol))
        is_onset = np.any(np.isclose(t, onset_times, atol=tol))
        
        if is_beat and is_onset:
            events.append((t, [67, 72], velocity))
        else:
            if len(events) % 2 == 0:
                events.append((t, [67], velocity))
            else:
                events.append((t, [72], velocity))
    
    # --- Step 3: Downsample if there are too many note events ---
    if len(events) > max_notes:
        # Use exponential distribution to favor keeping stronger onsets
        strengths = np.array([e[2] for e in events])  # Get velocities
        probs = strengths / strengths.sum()
        
        # If difficulty is higher, prefer to keep more complex patterns
        if difficulty >= 4:
            # For expert/master, keep more consecutive notes
            indices = sorted(np.random.choice(
                len(events), 
                size=max_notes, 
                p=probs, 
                replace=False
            ))
        else:
            # For easier difficulties, space out the notes more evenly
            indices = np.linspace(0, len(events) - 1, num=max_notes, dtype=int)
        
        events = [events[i] for i in indices]
        print(f"Downsampled events to {max_notes} total notes.")

    # --- Create the MIDI file ---
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    
    # Set the MIDI tempo
    midi_tempo = bpm2tempo(float(tempo))
    track.append(MetaMessage('set_tempo', tempo=midi_tempo, time=0))
    
    # Calculate ticks per second
    ticks_per_beat = mid.ticks_per_beat
    ticks_per_second = ticks_per_beat * (tempo / 60.0)
    
    # Create a list for MIDI messages with absolute timing
    midi_messages = []
    min_duration = 60  # Minimum duration in ticks to prevent very short notes
    
    # Calculate note durations based on time to next event
    for i, (t, pitches, velocity) in enumerate(events):
        note_on_tick = int(t * ticks_per_second)
        
        # Calculate duration based on time to next event
        if i < len(events) - 1:
            next_time = events[i + 1][0]
            duration = int((next_time - t) * ticks_per_second * 0.8)  # Use 80% of time to next event
            duration = max(duration, min_duration)  # Ensure minimum duration
        else:
            # For the last event, use padded duration to ensure silence at the end
            duration = int(2.0 * ticks_per_second)  # 2 seconds duration for last note
        
        for pitch in pitches:
            midi_messages.append((note_on_tick, Message('note_on', note=pitch, velocity=velocity, time=0)))
            midi_messages.append((note_on_tick + duration, Message('note_off', note=pitch, velocity=velocity, time=0)))
    
    # Sort messages by absolute tick, with note_on before note_off at same tick
    midi_messages.sort(key=lambda x: (x[0], 0 if x[1].type == 'note_on' else 1))
    
    # Convert absolute ticks to delta times
    current_tick = 0
    for abs_tick, msg in midi_messages:
        delta = abs_tick - current_tick
        delta = max(0, delta)  # Ensure non-negative delta time
        msg.time = delta
        current_tick = abs_tick
        track.append(msg)
    
    mid.save(output_midi)
    print(f"MIDI file saved as {output_midi}")
    return int(tempo)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Usage: python make_beatmap.py input.mp3 output.mid [difficulty]")
    else:
        input_mp3 = sys.argv[1]
        output_midi = sys.argv[2]
        difficulty = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        process_audio_to_midi(input_mp3, output_midi, difficulty)
