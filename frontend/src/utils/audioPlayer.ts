// src/utils/audioPlayer.ts
export function playSoundFile(path: string): HTMLAudioElement {
    const audio = new Audio(path);
    audio.play().catch(error => {
      console.error("Error playing sound:", error);
    });
    return audio;
  }
  