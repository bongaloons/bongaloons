// src/utils/audioPlayer.ts

let audioContext: AudioContext | null = null;
const audioBufferCache: { [key: string]: AudioBuffer } = {};
const activeSources: AudioBufferSourceNode[] = [];

function getAudioContext(): AudioContext {
  if (!audioContext) {
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  return audioContext;
}

export async function loadAudioBuffer(path: string): Promise<AudioBuffer> {
  if (audioBufferCache[path]) {
    return audioBufferCache[path];
  }
  const response = await fetch(path);
  const arrayBuffer = await response.arrayBuffer();
  const ctx = getAudioContext();
  const buffer = await ctx.decodeAudioData(arrayBuffer);
  audioBufferCache[path] = buffer;
  return buffer;
}

/**
 * Plays the specified sound file.
 * @param path - The path to the audio file.
 * @param volume - A number between 0 and 1 representing the volume (default is 1 for 100%).
 * @returns A promise resolving to the AudioBufferSourceNode playing the sound.
 */
export async function playSoundFile(path: string, volume: number = 1): Promise<AudioBufferSourceNode> {
  const ctx = getAudioContext();
  const buffer = await loadAudioBuffer(path);
  const source = ctx.createBufferSource();
  source.buffer = buffer;
  
  // Create a GainNode for volume control.
  const gainNode = ctx.createGain();
  gainNode.gain.value = volume;
  
  // Connect the source to the gain node, then to the destination.
  source.connect(gainNode);
  gainNode.connect(ctx.destination);
  
  source.start(0);
  activeSources.push(source);
  
  // Remove source from activeSources when finished.
  source.onended = () => {
    const index = activeSources.indexOf(source);
    if (index !== -1) {
      activeSources.splice(index, 1);
    }
  };
  return source;
}

export function clearAudio(): void {
  activeSources.forEach(source => {
    try {
      source.stop(0);
    } catch (e) {
      console.error("Error stopping source:", e);
    }
  });
  activeSources.length = 0;
}
