import './App.css'
import Track from './components/Track'
import { useContext } from 'react'
import { GameContext } from './context/GameContext'
import BongoCat from './components/BongoCat';

function App() {
  const { gameState, startGame } = useContext(GameContext);

  return (
    <div className="fixed inset-0 w-screen h-screen bg-[#E9967A] overflow-hidden">
      <div className={`absolute top-4 right-4 px-3 py-1 rounded-full text-white z-20 ${
        gameState.connectionStatus === 'connected' ? 'bg-green-500' :
        gameState.connectionStatus === 'connecting' ? 'bg-yellow-500' :
        'bg-red-500'
      }`}>
        WS: {gameState.connectionStatus}
      </div>


      <div className="absolute flex flex-col gap-2 top-4 left-4 px-4 py-2 bg-white rounded-lg shadow-lg z-20">
        <button
          onClick={startGame}
          className="py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 z-20"
        >
          Start Game
        </button>
        <div className="font-bold text-lg">Total Score: {gameState.totalScore}</div>
      </div>

      {gameState.lastJudgement && (
        <div 
          key={gameState.lastJudgement}
          className="absolute p-4 bg-white rounded-lg shadow-lg z-20 animate-fade-in-out"
          style={{
            top: `${Math.random() * 30 + 35}%`,
            left: `${Math.random() * 40 + 30}%`,
          }}
        >
          <pre className="text-2xl">
            {gameState.lastJudgement}
          </pre>
        </div>
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
        <div className="absolute top-[50%] left-[0%] -translate-x-[0%] -translate-y-[75%] w-full z-10">
          <div className="relative flex justify-center">
            {/* 
              Using responsive width classes (e.g. 30vw) so that the cat scales with the window.
              You can adjust this value (30vw) to achieve your desired size.
            */}
            <BongoCat />
          </div>
        </div>
      </div>
      <div 
        className="w-40 h-[64%] bg-blue-200 fixed bottom-[-9%] right-[60%] z-1 overflow-hidden"
        style={{
          transform: "rotate(13deg)",
          transformOrigin: "bottom center"
        }}
      >
          <Track position="left" text="Track 1" />
      </div>
      <div 
        className="w-40 h-[60%] bg-yellow-400 fixed bottom-[-13%] right-[40%] z-1 overflow-hidden"
        style={{
          transform: "rotate(13deg)",
          transformOrigin: "bottom center"
        }}
      >
          <Track position="right" text="Track 2" />
      </div>
    </div>
  )
}

export default App
