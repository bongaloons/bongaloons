from pydantic import BaseModel, Field
import librosa
import numpy as np
from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo
from typing import List, Dict, Tuple, Optional

MAX_NOTES = 500 # Default maximum notes in the final MIDI file

class AudioAnalysis(BaseModel):
    y: np.ndarray
    sr: int
    duration: float
    padded_duration: float
    tempo: float
    beat_times: np.ndarray
    onset_frames: np.ndarray
    onset_times: np.ndarray
    onset_strengths: np.ndarray

    class Config:
        arbitrary_types_allowed = True

class NoteParameters(BaseModel):
    max_notes: int
    tolerance: float

class MIDIEvent(BaseModel):
    time: float
    pitches: List[int]
    velocity: int

class BeatmapGenerator(BaseModel):
    input_mp3: str
    output_midi: str
    difficulty: int = Field(default=2, ge=1, le=5)
    
    def load_and_analyze_audio(self) -> AudioAnalysis:
        """Load audio file and analyze for BPM, beats, and onsets."""
        y, sr = librosa.load(self.input_mp3, sr=22050)
        duration = librosa.get_duration(y=y, sr=sr)
        padded_duration = duration + 2.0
        
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        if isinstance(tempo, np.ndarray):
            tempo = float(tempo[0])
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)
        onset_strengths = librosa.onset.onset_strength(y=y, sr=sr)
        
        return AudioAnalysis(
            y=y, sr=sr, duration=duration, padded_duration=padded_duration,
            tempo=tempo, beat_times=beat_times, onset_frames=onset_frames,
            onset_times=onset_times, onset_strengths=onset_strengths
        )

    def calculate_note_parameters(self, duration: float, tempo: float) -> NoteParameters:
        """Calculate note-related parameters based on difficulty and tempo."""
        npm = self.difficulty * 30
        target_notes = int((duration / 60) * npm)
        max_notes = max(20, min(target_notes, 1000))
        
        beat_duration = 60.0 / tempo
        tol = beat_duration * 0.125
        
        return NoteParameters(max_notes=max_notes, tolerance=tol)

    def process_onset_velocities(self, onset_times, onset_frames, onset_strengths):
        """Process onset strengths into MIDI velocities."""
        onset_strengths = onset_strengths[onset_frames]
        onset_velocities = np.clip(onset_strengths * 127 / onset_strengths.max(), 40, 127).astype(int)
        return dict(zip(onset_times, onset_velocities))

    def generate_initial_events(self, all_times, beat_times, onset_times, onset_velocity_map, tol):
        """Generate initial event list with notes and velocities."""
        events = []
        for t in all_times:
            velocity = 64
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
        return events

    def calculate_note_importance(self, event, beat_times, tol, tempo):
        """Calculate importance score for a note based on musical features."""
        time, pitches, velocity = event
        
        is_beat = np.any(np.isclose(time, beat_times, atol=tol))
        
        beat_position = min([abs(time - beat) for beat in beat_times])
        beat_alignment = 1.0 - (beat_position / (60.0 / tempo))
        
        importance = (
            velocity / 127.0 * 0.4 +  # Velocity importance (40%)
            (1.5 if is_beat else 0.0) * 0.4 +  # Beat importance (40%)
            beat_alignment * 0.2  # Beat alignment importance (20%)
        )
        
        return importance

    def detect_phrases(self, events, beat_times):
        """Detect musical phrases based on velocity patterns and beat structure."""
        if not events:
            return []
            
        phrases = []
        current_phrase = []
        last_velocity = events[0][2]
        velocity_threshold = 20  # Minimum velocity change to mark phrase boundary
        
        for event in events:
            time, pitches, velocity = event
            
            # Check for significant velocity change or strong beat
            is_strong_beat = any(np.isclose(time, beat_times[::2], atol=0.05))
            velocity_change = abs(velocity - last_velocity) > velocity_threshold
            
            if (velocity_change and len(current_phrase) > 4) or (is_strong_beat and len(current_phrase) > 8):
                if current_phrase:
                    phrases.append(current_phrase)
                current_phrase = []
            
            current_phrase.append(event)
            last_velocity = velocity
        
        if current_phrase:
            phrases.append(current_phrase)
            
        return phrases

    def downsample_events(self, events, max_notes, beat_times, tol, total_duration, tempo):
        """Downsample events using musical phrase detection and note importance."""
        phrases = self.detect_phrases(events, beat_times)
        
        total_events = sum(len(phrase) for phrase in phrases)
        processed_phrases = []
        
        for phrase in phrases:
            phrase_ratio = len(phrase) / total_events
            target_notes = max(1, int(max_notes * phrase_ratio))
            
            if len(phrase) > target_notes:
                importance_scores = [
                    (event, self.calculate_note_importance(event, beat_times, tol, tempo))
                    for event in phrase
                ]
                
                importance_scores.sort(key=lambda x: x[1], reverse=True)
                phrase = [event for event, _ in importance_scores[:target_notes]]
                
                phrase.sort(key=lambda x: x[0])
            
            processed_phrases.extend(phrase)
        
        return processed_phrases

    def create_midi_file(self, events, tempo, output_midi):
        """Create and save the MIDI file from the processed events."""
        mid = MidiFile()
        track = MidiTrack()
        mid.tracks.append(track)
        
        midi_tempo = bpm2tempo(float(tempo))
        track.append(MetaMessage('set_tempo', tempo=midi_tempo, time=0))
        ticks_per_beat = mid.ticks_per_beat
        ticks_per_second = ticks_per_beat * (tempo / 60.0)
        
        midi_messages = self.generate_midi_messages(events, ticks_per_second)
        self.write_midi_messages(track, midi_messages)
        
        mid.save(output_midi)
        return int(tempo)

    def generate_midi_messages(self, events, ticks_per_second):
        """Generate MIDI messages from events."""
        midi_messages = []
        min_duration = 60
        
        for i, (t, pitches, velocity) in enumerate(events):
            note_on_tick = int(t * ticks_per_second)
            
            if i < len(events) - 1:
                next_time = events[i + 1][0]
                duration = int((next_time - t) * ticks_per_second * 0.8)
                duration = max(duration, min_duration)
            else:
                duration = int(2.0 * ticks_per_second)
            
            for pitch in pitches:
                midi_messages.append((note_on_tick, Message('note_on', note=pitch, velocity=velocity, time=0)))
                midi_messages.append((note_on_tick + duration, Message('note_off', note=pitch, velocity=velocity, time=0)))
        
        return sorted(midi_messages, key=lambda x: (x[0], 0 if x[1].type == 'note_on' else 1))

    def write_midi_messages(self, track, midi_messages):
        """Write MIDI messages to the track with proper timing."""
        current_tick = 0
        for abs_tick, msg in midi_messages:
            delta = max(0, abs_tick - current_tick)
            msg.time = delta
            current_tick = abs_tick
            track.append(msg)

    def process_audio_to_midi(self) -> float:
        """
        Creates a MIDI beatmap from an MP3 file based on difficulty level (1-5).
        Returns the detected BPM of the song.
        """
        # Load and analyze audio
        analysis = self.load_and_analyze_audio()
        print(f"Estimated BPM: {analysis.tempo:.2f}")
        
        # Calculate parameters
        params = self.calculate_note_parameters(analysis.duration, analysis.tempo)
        print(f"Targeting {params.max_notes} notes for difficulty {self.difficulty} "
              f"({self.difficulty * 30} notes per minute)")
        print(f"Using tolerance: {params.tolerance:.3f} seconds")
        
        # Process onsets and generate events
        onset_velocity_map = self.process_onset_velocities(
            analysis.onset_times,
            analysis.onset_frames,
            analysis.onset_strengths
        )
        all_times = np.union1d(analysis.beat_times, analysis.onset_times)
        all_times.sort()
        
        events = self.generate_initial_events(
            all_times, analysis.beat_times, analysis.onset_times, 
            onset_velocity_map, params.tolerance
        )
        events = self.downsample_events(
            events, params.max_notes, analysis.beat_times, 
            params.tolerance, analysis.padded_duration, analysis.tempo
        )
        print(f"Final total notes: {len(events)}")
        
        # Create and save MIDI file
        return self.create_midi_file(events, analysis.tempo, self.output_midi)

def load_and_analyze_audio(input_mp3: str) -> AudioAnalysis:
    """Load audio file and analyze for BPM, beats, and onsets."""
    y, sr = librosa.load(input_mp3, sr=22050)
    duration = librosa.get_duration(y=y, sr=sr)
    padded_duration = duration + 2.0
    
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    onset_strengths = librosa.onset.onset_strength(y=y, sr=sr)
    
    return AudioAnalysis(
        y=y, sr=sr, duration=duration, padded_duration=padded_duration,
        tempo=tempo, beat_times=beat_times, onset_frames=onset_frames,
        onset_times=onset_times, onset_strengths=onset_strengths
    )

def calculate_note_parameters(duration: float, tempo: float, difficulty: int) -> NoteParameters:
    """Calculate note-related parameters based on difficulty and tempo."""
    npm = difficulty * 30
    target_notes = int((duration / 60) * npm)
    max_notes = max(20, min(target_notes, 1000))
    
    beat_duration = 60.0 / tempo
    tol = beat_duration * 0.125
    
    return NoteParameters(max_notes=max_notes, tolerance=tol)

def process_onset_velocities(onset_times, onset_frames, onset_strengths):
    """Process onset strengths into MIDI velocities."""
    onset_strengths = onset_strengths[onset_frames]
    onset_velocities = np.clip(onset_strengths * 127 / onset_strengths.max(), 40, 127).astype(int)
    return dict(zip(onset_times, onset_velocities))

def generate_initial_events(all_times, beat_times, onset_times, onset_velocity_map, tol):
    """Generate initial event list with notes and velocities."""
    events = []
    for t in all_times:
        velocity = 64
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
    return events

def calculate_note_importance(event, beat_times, tol, tempo):
    """Calculate importance score for a note based on musical features."""
    time, pitches, velocity = event
    
    # Check if note falls on a beat
    is_beat = np.any(np.isclose(time, beat_times, atol=tol))
    
    # Calculate position within the beat (0.0 to 1.0)
    beat_position = min([abs(time - beat) for beat in beat_times])
    beat_alignment = 1.0 - (beat_position / (60.0 / tempo))
    
    # Combine factors into importance score
    importance = (
        velocity / 127.0 * 0.4 +  # Velocity importance (40%)
        (1.5 if is_beat else 0.0) * 0.4 +  # Beat importance (40%)
        beat_alignment * 0.2  # Beat alignment importance (20%)
    )
    
    return importance

def detect_phrases(events, beat_times):
    """Detect musical phrases based on velocity patterns and beat structure."""
    if not events:
        return []
        
    phrases = []
    current_phrase = []
    last_velocity = events[0][2]
    velocity_threshold = 20  # Minimum velocity change to mark phrase boundary
    
    for event in events:
        time, pitches, velocity = event
        
        # Check for significant velocity change or strong beat
        is_strong_beat = any(np.isclose(time, beat_times[::2], atol=0.05))
        velocity_change = abs(velocity - last_velocity) > velocity_threshold
        
        if (velocity_change and len(current_phrase) > 4) or (is_strong_beat and len(current_phrase) > 8):
            if current_phrase:
                phrases.append(current_phrase)
            current_phrase = []
        
        current_phrase.append(event)
        last_velocity = velocity
    
    if current_phrase:
        phrases.append(current_phrase)
        
    return phrases

def downsample_events(events, max_notes, beat_times, tol, total_duration, tempo):
    """Downsample events using musical phrase detection and note importance."""
    # Detect musical phrases
    phrases = detect_phrases(events, beat_times)
    
    # Calculate target notes per phrase proportionally
    total_events = sum(len(phrase) for phrase in phrases)
    processed_phrases = []
    
    for phrase in phrases:
        # Calculate target notes for this phrase
        phrase_ratio = len(phrase) / total_events
        target_notes = max(1, int(max_notes * phrase_ratio))
        
        if len(phrase) > target_notes:
            # Calculate importance scores for all notes in the phrase
            importance_scores = [
                (event, calculate_note_importance(event, beat_times, tol, tempo))
                for event in phrase
            ]
            
            # Sort by importance and keep top notes
            importance_scores.sort(key=lambda x: x[1], reverse=True)
            phrase = [event for event, _ in importance_scores[:target_notes]]
            
            # Resort by time
            phrase.sort(key=lambda x: x[0])
        
        processed_phrases.extend(phrase)
    
    return processed_phrases

def create_midi_file(events, tempo, output_midi):
    """Create and save the MIDI file from the processed events."""
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    
    midi_tempo = bpm2tempo(float(tempo))
    track.append(MetaMessage('set_tempo', tempo=midi_tempo, time=0))
    ticks_per_beat = mid.ticks_per_beat
    ticks_per_second = ticks_per_beat * (tempo / 60.0)
    
    midi_messages = generate_midi_messages(events, ticks_per_second)
    write_midi_messages(track, midi_messages)
    
    mid.save(output_midi)
    return int(tempo)

def generate_midi_messages(events, ticks_per_second):
    """Generate MIDI messages from events."""
    midi_messages = []
    min_duration = 60
    
    for i, (t, pitches, velocity) in enumerate(events):
        note_on_tick = int(t * ticks_per_second)
        
        if i < len(events) - 1:
            next_time = events[i + 1][0]
            duration = int((next_time - t) * ticks_per_second * 0.8)
            duration = max(duration, min_duration)
        else:
            duration = int(2.0 * ticks_per_second)
        
        for pitch in pitches:
            midi_messages.append((note_on_tick, Message('note_on', note=pitch, velocity=velocity, time=0)))
            midi_messages.append((note_on_tick + duration, Message('note_off', note=pitch, velocity=velocity, time=0)))
    
    return sorted(midi_messages, key=lambda x: (x[0], 0 if x[1].type == 'note_on' else 1))

def write_midi_messages(track, midi_messages):
    """Write MIDI messages to the track with proper timing."""
    current_tick = 0
    for abs_tick, msg in midi_messages:
        delta = max(0, abs_tick - current_tick)
        msg.time = delta
        current_tick = abs_tick
        track.append(msg)

def process_audio_to_midi(input_mp3: str, output_midi: str, difficulty: int = 2) -> float:
    """
    Creates a MIDI beatmap from an MP3 file based on difficulty level (1-5).
    Returns the detected BPM of the song.
    """
    # Load and analyze audio
    analysis = load_and_analyze_audio(input_mp3)
    print(f"Estimated BPM: {analysis.tempo:.2f}")
    
    # Calculate parameters
    params = calculate_note_parameters(analysis.duration, analysis.tempo, difficulty)
    print(f"Targeting {params.max_notes} notes for difficulty {difficulty} "
          f"({difficulty * 30} notes per minute)")
    print(f"Using tolerance: {params.tolerance:.3f} seconds")
    
    # Process onsets and generate events
    onset_velocity_map = process_onset_velocities(
        analysis.onset_times,
        analysis.onset_frames,
        analysis.onset_strengths
    )
    all_times = np.union1d(analysis.beat_times, analysis.onset_times)
    all_times.sort()
    
    events = generate_initial_events(
        all_times, analysis.beat_times, analysis.onset_times, 
        onset_velocity_map, params.tolerance
    )
    events = downsample_events(
        events, params.max_notes, analysis.beat_times, 
        params.tolerance, analysis.padded_duration, analysis.tempo
    )
    print(f"Final total notes: {len(events)}")
    
    # Create and save MIDI file
    return create_midi_file(events, analysis.tempo, output_midi)

def main():
    import sys
    if len(sys.argv) < 3:
        print("Usage: python make_beatmap.py input.mp3 output.mid [difficulty]")
    else:
        i_mp3 = sys.argv[1]
        o_midi = sys.argv[2]
        diff = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        process_audio_to_midi(i_mp3, o_midi, diff)

if __name__ == '__main__':
    main()
