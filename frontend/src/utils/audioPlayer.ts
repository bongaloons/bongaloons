// src/utils/audioPlayer.ts

let audioContext: AudioContext | null = null;
const audioBufferCache: { [key: string]: AudioBuffer } = {};
const activeSources: AudioBufferSourceNode[] = [];
const activeGainNodes: GainNode[] = [];

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

export function getVolumeSettings() {
  const saved = localStorage.getItem('volumeSettings');
  const defaults = { master: 100, song: 100, sfx: 100 };
  if (!saved) return defaults;
  return JSON.parse(saved);
}

export function calculateVolume(type: 'song' | 'sfx'): number {
  const settings = getVolumeSettings();
  return (settings[type] / 100) * (settings.master / 100);
}

export function updateAllVolumes() {
  const songVolume = calculateVolume('song');
  const sfxVolume = calculateVolume('sfx');
  
  activeGainNodes.forEach((gainNode, index) => {
    if (activeSources[index]) {
      const type = activeSources[index].userData?.type || 'sfx';
      gainNode.gain.value = type === 'song' ? songVolume : sfxVolume;
    }
  });
}

/**
 * Plays the specified sound file.
 * @param path - The path to the audio file.
 * @param type - The type of sound (song or sfx).
 * @returns A promise resolving to the AudioBufferSourceNode playing the sound.
 */
export async function playSoundFile(path: string, type: 'song' | 'sfx' = 'sfx'): Promise<AudioBufferSourceNode> {
  const volume = calculateVolume(type);
  const ctx = getAudioContext();
  const buffer = await loadAudioBuffer(path);
  const source = ctx.createBufferSource();
  source.buffer = buffer;
  
  source.userData = { type };
  
  const gainNode = ctx.createGain();
  gainNode.gain.value = volume;
  
  source.connect(gainNode);
  gainNode.connect(ctx.destination);
  
  source.start(0);
  activeSources.push(source);
  activeGainNodes.push(gainNode);
  
  source.onended = () => {
    const index = activeSources.indexOf(source);
    if (index !== -1) {
      activeSources.splice(index, 1);
      activeGainNodes.splice(index, 1);
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
