import { useContext } from 'react';
import { GameContext } from '../context/GameContext';

export default function GameOver() {
  const { gameState, playAgain } = useContext(GameContext);

  return (
    <div className="fixed inset-0 w-screen h-screen bg-gradient-to-b from-[#FFB07C] to-[#E88165] overflow-hidden flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg text-center">
        <h1 className="text-4xl font-display mb-4">Game Over!</h1>
        <p className="text-2xl font-display mb-6">Total Score: {gameState.totalScore}</p>
        <button 
          onClick={playAgain}
          className="bg-blue-500 hover:bg-blue-600 text-white font-display text-xl px-6 py-3 rounded-lg transition-colors duration-200"
        >
          Play Again
        </button>
      </div>
    </div>
  );
} 