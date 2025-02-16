import '../App.css'
import Track from '../components/Track'
import { useContext, useEffect, useRef, useState} from 'react'
import { GameContext } from '../context/GameContext'
import Judgement from '../components/Judgement';
import Table from '../components/cosmetics/Table';
import BongoCat from '../components/BongoCat';
import { StreakDisplay } from '../components/StreakDisplay';
import BigJudgement from '../components/BigJudgement';
import { playSoundFile, clearAudio } from '../utils/audioPlayer';

function Game() {
  const { isStarted, gameState, ws, startGame, updatePose, togglePause, endGame } = useContext(GameContext)
  // Create a ref for the audio element.
  const audioRef = useRef<HTMLAudioElement | null>(null)
  // Track audio resume delay and whether the audio is ready.
  const [audioDelay, setAudioDelay] = useState(0)
  const [audioReady, setAudioReady] = useState(true)
  // A ref to store the time when the resume was triggered.
  const resumeTriggerTimeRef = useRef<number | null>(null)

  // When the game starts, clear any audio (like the title screen music)
  useEffect(() => {
    if (gameState.isRunning) {
      clearAudio(); // Clear title screen audio once when the game starts.
    }
  }, [gameState.isRunning]);

  useEffect(() => {
    if (gameState.isRunning) {
      if (gameState.isPaused) {
        // When paused, pause the audio (if it exists) and block note movement.
        if (audioRef.current) {
          audioRef.current.pause();
        }
        setAudioReady(false);
      } else {
        // When unpausing:
        if (audioRef.current) {
          // Audio already exists (i.e. we're resuming playback after the initial start)
          resumeTriggerTimeRef.current = performance.now();
          audioRef.current.play().catch((err) =>
            console.error("Audio resume error:", err)
          );
          const handlePlaying = () => {
            if (resumeTriggerTimeRef.current) {
              const delay = performance.now() - resumeTriggerTimeRef.current;
              setAudioDelay(delay);
              console.log("Audio resume delay:", delay, "ms");
              resumeTriggerTimeRef.current = null;
            }
            setAudioReady(true);
            audioRef.current?.removeEventListener("playing", handlePlaying);
          };
          audioRef.current.addEventListener("playing", handlePlaying);
        } else {
          // For initial playback: start a countdown that respects pauses.
          // We assume gameState.startTime is set when the game starts.
          const intervalId = setInterval(() => {
            // If paused, do nothing (the effective elapsed time won't increase).
            if (gameState.isPaused) return;
            // Calculate effective elapsed time:
            const effectiveTime = performance.now() - gameState.startTime - gameState.totalPausedTime;
            const remainingDelay = gameState.delay - effectiveTime;
            console.log("Remaining delay:", remainingDelay, "ms");
            if (remainingDelay <= 0) {
              clearInterval(intervalId);
              // Time to start the audio.
              audioRef.current = new Audio(gameState.songPath);
              resumeTriggerTimeRef.current = performance.now();
              audioRef.current.play().catch((err) =>
                console.error("Audio play error:", err)
              );
              const handlePlaying = () => {
                if (resumeTriggerTimeRef.current) {
                  const delay = performance.now() - resumeTriggerTimeRef.current;
                  setAudioDelay(delay);
                  console.log("Audio resume delay:", delay, "ms");
                  resumeTriggerTimeRef.current = null;
                }
                setAudioReady(true);
                audioRef.current?.removeEventListener("playing", handlePlaying);
              };
              audioRef.current.addEventListener("playing", handlePlaying);
            }
          }, 50);
          return () => clearInterval(intervalId);
        }
      }
    } else {
      // When game stops, pause and reset the audio.
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
    }
  }, [
    gameState.isRunning,
    gameState.songPath,
    gameState.isPaused,
    gameState.delay,
    gameState.startTime,
    gameState.totalPausedTime,
  ]);
  

  // Now you can use the "audioReady" flag in your note/update logic.

    // Refs for video recording
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const videoStreamRef = useRef<MediaStream | null>(null);
    const recordedChunksRef = useRef<Blob[]>([]);
    const [isRecording, setIsRecording] = useState(false);
    const [startTime, setStartTime] = useState<number | null>(null);
    const [endTime, setEndTime] = useState<number | null>(null);

    // Start recording video

    /** Start Recording Continuously */
    useEffect(() => {
      async function startContinuousRecording() {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "user" },
            audio: false,
          });

          videoStreamRef.current = stream;
          recordedChunksRef.current = [];

          const recorder = new MediaRecorder(stream, { mimeType: "video/webm" });
          mediaRecorderRef.current = recorder;

          recorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
              recordedChunksRef.current.push(event.data); // Store chunks continuously
            }
          };

          recorder.start(100); // Save small chunks every 100ms
          setIsRecording(true);
        } catch (error) {
          console.error("Error accessing camera:", error);
        }
      }

      startContinuousRecording();

      return () => stopRecording();
    }, []);
    
    /** Stop Recording (when unmounting or game ends) */
    const stopRecording = () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      if (videoStreamRef.current) {
        videoStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      setIsRecording(false);
    };
    /** Track when to extract video */
    useEffect(() => {
      if (gameState.isRunning && !gameState.isPaused) {
        setStartTime(Date.now()); // Set when audio starts
      } else if (!gameState.isRunning) {
        setEndTime(Date.now()); // Set when audio stops
        if (startTime) {
          saveSegmentAsBinary(startTime, Date.now());
        }
      }
    }, [gameState.isRunning, gameState.isPaused]);

    const saveSegmentAsBinary = async (start: number, end: number) => {
        if (!recordedChunksRef.current.length) return;

        // Convert all chunks to a single Blob
        const fullBlob = new Blob(recordedChunksRef.current, { type: "video/webm" });

        // Create a FileReader to extract portion of video
        const reader = new FileReader();
        reader.readAsArrayBuffer(fullBlob);
        reader.onload = async () => {
          const fullBuffer = reader.result as ArrayBuffer;
          const duration = (end - start) / 1000; // Convert to seconds

          // Trim the video (not natively supported in JS, so sending full video for backend to trim)
          const byteArray = new Uint8Array(fullBuffer);
          const binBlob = new Blob([byteArray], { type: "application/octet-stream" });

          // Download the .bin file (replace this with API upload if needed)
          const url = URL.createObjectURL(binBlob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `segment_${start}_${end}.bin`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        };
      };

  return (
    <div className="fixed inset-0 w-screen h-screen bg-[#E9967A] overflow-hidden">
      {/* Pause Menu Overlay */}
      {gameState.isPaused && (
        <div 
          className="fixed inset-0 z-30 flex items-center justify-center" 
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
        >
          <div className="bg-white p-8 rounded-lg shadow-lg text-center space-y-4">
            <h1 className="text-4xl font-display mb-4">Paused</h1>
            <div className="flex justify-center gap-4">
              <button
                onClick={() => {
                  togglePause()
                  if (ws) {
                    ws.send(JSON.stringify({ type: "toggle_pause" }))
                  }
                }}
                className="bg-blue-500 hover:bg-blue-600 text-white font-display text-xl px-6 py-3 rounded-lg transition-colors duration-200"
              >
                Resume
              </button>
              <button
                onClick={() => {
                  endGame()
                }}
                className="bg-gray-500 hover:bg-gray-600 text-white font-display text-xl px-6 py-3 rounded-lg transition-colors duration-200"
              >
                Menu
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Now Playing text */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-20">
        {gameState.songName && (
          <div className="text-white font-display text-2xl">
            Now playing: {gameState.songName}
          </div>
        )}
      </div>

      {/* Connection status */}
      <div className={`absolute top-4 right-4 px-3 py-1 rounded-full text-white z-20 font-display ${
        gameState.connectionStatus === 'connected' ? 'bg-green-500' :
        gameState.connectionStatus === 'connecting' ? 'bg-yellow-500' :
        'bg-red-500'
      }`}>
        WS: {gameState.connectionStatus}
      </div>

      {/* Score & Streak display */}
      <div className="absolute flex flex-col gap-2 top-4 left-4 z-20">
        <div className="flex flex-row gap-2 px-4 py-2 bg-white rounded-lg shadow-lg justify-between items-center">
        <button
            onClick={() => {
              togglePause()
              if (ws) {
                ws.send(JSON.stringify({ type: "toggle_pause" }))
              }
              // Play a sound effect on pause toggle
              playSoundFile('/sfx/pause.ogg');
            }}
            className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 z-20 font-display text-xl inline-flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25v13.5m-7.5-13.5v13.5" />
            </svg>
            {"Pause"}
          </button>
          <div className="font-display text-xl">Total Score: {gameState.totalScore}</div>
        </div>
        <StreakDisplay />
      </div>

      {gameState.lastJudgement && (
        <Judgement judgement={gameState.lastJudgement} />
      )}
      {gameState.lastJudgement && (
        <BigJudgement judgement={gameState.lastJudgement} />
      )}

      <div className="relative w-full h-screen bg-[#E9967A]">
        <div
          className="absolute w-full h-1.5 bg-black z-10"
          style={{ 
            top: '50%',
            left: '50%',
            transform: "translate(-50%, -50%) rotate(-167deg)"
          }}
        />
        <div className="absolute top-[50%] left-[0%] -translate-x-[0%] -translate-y-[75%] w-full z-10 ">
          <div className="mx-auto max-w-[400px]">
            <BongoCat pose={gameState.currentPose} />
          </div>
        </div>
      </div>
      <Table />
      <div 
        className="w-40 h-[64%] fixed bottom-[-9%] right-[60%] z-1 overflow-hidden"
        style={{
          transform: "rotate(13deg)",
          transformOrigin: "bottom center",
          background: "linear-gradient(to top, #bfdbfe, #60a5fa)"
        }}
      >
          <Track position="left" text="Left Track (A)" />
      </div>
      <div 
        className="w-40 h-[60%] fixed bottom-[-13%] right-[40%] z-1 overflow-hidden"
        style={{
          transform: "rotate(13deg)",
          transformOrigin: "bottom center",
          background: "linear-gradient(to top, #fef08a, #facc15)"
        }}
      >
          <Track position="right" text="Right Track (L)" />
      </div>
    </div>
  )
}

export default Game;
