import '../App.css'
import Track from '../components/Track'
import { useContext, useEffect, useRef } from 'react'
import { GameContext } from '../context/GameContext'
import Judegment from '../components/Judegment';
import Table from '../components/cosmetics/Table';
import BongoCat from '../components/BongoCat';

function Game() {
  const { gameState, startGame } = useContext(GameContext)
  // Create a ref for the audio element.
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    if (gameState.isRunning) {
      console.log("Game is running. Song path:", gameState.songPath);
      // Delay audio playback by 2000ms
      const timer = setTimeout(() => {
        audioRef.current = new Audio(gameState.songPath);
        audioRef.current.play().catch((err) =>
          console.error("Audio play error:", err)
        );
      }, 1500);
      return () => clearTimeout(timer);
    } else {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
    }
  }, [gameState.isRunning, gameState.songPath]);  

  return (


    <div className="fixed inset-0 w-screen h-screen bg-[#E9967A] overflow-hidden">
        <div className="absolute top-16 text-white z-20 font-display justify-center">
          {gameState.songName && <div>Now playing: {gameState.songName}</div>}
        </div>
      <div className={`absolute top-4 right-4 px-3 py-1 rounded-full text-white z-20 font-display ${
        gameState.connectionStatus === 'connected' ? 'bg-green-500' :
        gameState.connectionStatus === 'connecting' ? 'bg-yellow-500' :
        'bg-red-500'
      }`}>
        WS: {gameState.connectionStatus}
      </div>

      <div className="absolute flex flex-col gap-2 top-4 left-4 px-4 py-2 bg-white rounded-lg shadow-lg z-20">
        <button
          onClick={startGame}
          className="py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 z-20 font-display text-xl"
        >
          Start Game
        </button>
        <div className="font-display text-xl">Total Score: {gameState.totalScore}</div>
      </div>

      {gameState.lastJudgement && (
        <Judegment judgement={gameState.lastJudgement} />
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

export default Game
