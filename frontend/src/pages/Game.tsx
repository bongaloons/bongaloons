import '../App.css'
import Track from '../components/Track'
import { useContext, useEffect, useRef } from 'react'
import { GameContext } from '../context/GameContext'
import Judgement from '../components/Judgement';
import Table from '../components/cosmetics/Table';
import BongoCat from '../components/BongoCat';
import { StreakDisplay } from '../components/StreakDisplay';
import BigJudgement from '../components/BigJudgement';
import { playSoundFile } from '../utils/audioPlayer';

function Game() {
  const { isStarted, gameState, ws, startGame, updatePose, togglePause, endGame } = useContext(GameContext)
  // Create a ref for the audio element.
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    if (gameState.isRunning) {
      if (gameState.isPaused) {
        // When paused, simply pause the audio without resetting currentTime.
        if (audioRef.current) {
          audioRef.current.pause();
        }
      } else {
        // When running and not paused:
        // If audio already exists, resume playback.
        if (audioRef.current) {
          audioRef.current.play().catch((err) =>
            console.error("Audio resume error:", err)
          );
        } else {
          // Otherwise, delay initial playback by 1500ms.
          const timer = setTimeout(() => {
            audioRef.current = new Audio(gameState.songPath);
            audioRef.current.play().catch((err) =>
              console.error("Audio play error:", err)
            );
          }, 1500);
          return () => clearTimeout(timer);
        }
      }
    } else {
      // When game stops, pause and reset the audio.
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
    }
  }, [gameState.isRunning, gameState.songPath, gameState.isPaused]);

  // Key event handling: ignore keys if game is paused.
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!ws || !['a', 'l'].includes(e.key) || gameState.isPaused || gameState.pressedKeys.has(e.key)) return;
      
      const newPressedKeys = new Set(gameState.pressedKeys).add(e.key);
      ws.send(JSON.stringify({ key: e.key }));
      
      if (newPressedKeys.has('a') && newPressedKeys.has('l')) {
        updatePose('both');
      } else if (newPressedKeys.has('a')) {
        updatePose('left');
      } else if (newPressedKeys.has('l')) {
        updatePose('right');
      } else {
        updatePose('idle');
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (!['a', 'l'].includes(e.key)) return;
      
      const newPressedKeys = new Set(gameState.pressedKeys);
      newPressedKeys.delete(e.key);
      
      if (newPressedKeys.has('a') && newPressedKeys.has('l')) {
        updatePose('both');
      } else if (newPressedKeys.has('a')) {
        updatePose('left');
      } else if (newPressedKeys.has('l')) {
        updatePose('right');
      } else {
        updatePose('idle');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [ws, gameState.pressedKeys, gameState.isPaused, updatePose]);

  return (
    <div className="fixed inset-0 w-screen h-screen bg-[#E9967A] overflow-hidden">
      {/* Pause Menu Overlay */}
      {gameState.isPaused && (
  <div 
    className="fixed inset-0 z-30 flex items-center justify-center" 
    style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }} // Semi-transparent overlay
  >
    <div className="bg-white p-8 rounded-lg shadow-lg text-center space-y-4">
      <h1 className="text-4xl font-display mb-4">Paused</h1>
      <div className="flex justify-center gap-4">
        <button
          onClick={() => {
            togglePause();
            if (ws) {
              ws.send(JSON.stringify({ type: "toggle_pause" }));
            }
          }}
          className="bg-blue-500 hover:bg-blue-600 text-white font-display text-xl px-6 py-3 rounded-lg transition-colors duration-200"
        >
          Resume
        </button>
        <button
          onClick={() => {
            // Logic for menu navigation; here we call endGame to exit the game.
            endGame();
          }}
          className="bg-gray-500 hover:bg-gray-600 text-white font-display text-xl px-6 py-3 rounded-lg transition-colors duration-200"
        >
          Menu
        </button>
      </div>
    </div>
  </div>
)}


      {/* Now Playing text, centered horizontally just below the top */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-20">
        {gameState.songName && (
          <div className="text-white font-display text-2xl">
            Now playing: {gameState.songName}
          </div>
        )}
      </div>

      <div className={`absolute top-4 right-4 px-3 py-1 rounded-full text-white z-20 font-display ${
        gameState.connectionStatus === 'connected' ? 'bg-green-500' :
        gameState.connectionStatus === 'connecting' ? 'bg-yellow-500' :
        'bg-red-500'
      }`}>
        WS: {gameState.connectionStatus}
      </div>

      <div className="absolute flex flex-col gap-2 top-4 left-4 z-20">
        <div className="flex flex-row gap-2 px-4 py-2 bg-white rounded-lg shadow-lg justify-between items-center">
        <button
            onClick={() => {
              togglePause();
              if (ws) {
                ws.send(JSON.stringify({ type: "toggle_pause" }));
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
        className="w-40 h-[64%] bg-blue-200 fixed bottom-[-9%] right-[60%] z-1 overflow-hidden"
        style={{
          transform: "rotate(13deg)",
          transformOrigin: "bottom center"
        }}
      >
          <Track position="left" text="Left Track (A)" />
      </div>
      <div 
        className="w-40 h-[60%] bg-yellow-200 fixed bottom-[-13%] right-[40%] z-1 overflow-hidden"
        style={{
          transform: "rotate(13deg)",
          transformOrigin: "bottom center"
        }}
      >
          <Track position="right" text="Right Track (L)" />
      </div>
    </div>
  )
}

export default Game;
