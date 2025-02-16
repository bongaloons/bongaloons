import librosa
import numpy as np
from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo

MAX_NOTES = 100 # Default maximum notes in the final MIDI file


def process_audio_to_midi(input_mp3, output_midi, max_notes=MAX_NOTES):
    # --- Step 1: Load the audio and determine BPM ---
    # sr=None preserves the native sample rate.
    y, sr = librosa.load(input_mp3, sr=22050)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    print("Estimated BPM:", tempo)

    
    
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    
    # --- Step 2: Merge events and assign notes ---
    # Combine the beat times and onset times.
    all_times = np.union1d(beat_times, onset_times)
    all_times.sort()

    events = []
    tol = 0.05
    for t in all_times:
        # Check if the time is close to a beat and/or an onset.
        is_beat = np.any(np.isclose(t, beat_times, atol=tol))
        is_onset = np.any(np.isclose(t, onset_times, atol=tol))
        
        if is_beat and is_onset:
            # When both are present, output both notes simultaneously.
            events.append((t, [67, 72]))
        else:
            # Otherwise, alternate between the two pitches.
            # (You can change this strategy to suit your musical taste.)
            if len(events) % 2 == 0:
                events.append((t, [67]))
            else:
                events.append((t, [72]))
    
    # --- Step 3: Downsample if there are too many note events ---
    if len(events) > max_notes:
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
    note_duration = 120  # Fixed duration in ticks
    
    for t, pitches in events:
        note_on_tick = int(t * ticks_per_second)
        for pitch in pitches:
            midi_messages.append((note_on_tick, Message('note_on', note=pitch, velocity=64, time=0)))
            midi_messages.append((note_on_tick + note_duration, Message('note_off', note=pitch, velocity=64, time=0)))
    
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


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Usage: python make_beatmap.py input.mp3 output.mid [max_notes]")
    else:
        input_mp3 = sys.argv[1]
        output_midi = sys.argv[2]
        max_notes = int(sys.argv[3]) if len(sys.argv) > 3 else MAX_NOTES
        process_audio_to_midi(input_mp3, output_midi, max_notes)
