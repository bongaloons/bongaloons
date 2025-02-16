import { useContext } from 'react';
import { GameContext } from '../context/GameContext';
import PushButton from './PushButton';
// Rank thresholds and comments
const RANK_THRESHOLDS = {
  SSS: { score: 100000, streak: 50, comment: "Are you even human? That was incredible!" },
  SS: { score: 75000, streak: 40, comment: "Almost perfect! Touch grass maybe?" },
  S: { score: 50000, streak: 30, comment: "Impressive! You've clearly been practicing!" },
  A: { score: 35000, streak: 20, comment: "Pretty good! Your cat would be proud." },
  B: { score: 25000, streak: 15, comment: "Not bad, but your cat could do better." },
  C: { score: 15000, streak: 10, comment: "Meow-diocre performance..." },
  D: { score: 10000, streak: 5, comment: "Did your cat walk across the keyboard?" },
  E: { score: 5000, streak: 3, comment: "Paw-sitively disappointing." },
  F: { score: 0, streak: 0, comment: "Maybe stick to petting cats instead?" }
};

function calculateRank(score: number, maxStreak: number): {rank: string, comment: string} {
  for (const [rank, criteria] of Object.entries(RANK_THRESHOLDS)) {
    if (score >= criteria.score && maxStreak >= criteria.streak) {
      return { rank, comment: criteria.comment };
    }
  }
  return { rank: 'F', comment: RANK_THRESHOLDS.F.comment };
}

export default function GameOver() {
  const { gameState, playAgain } = useContext(GameContext);
  const { rank, comment } = calculateRank(gameState.totalScore || 0, gameState.maxStreak || 0);

  return (
    <div className="fixed inset-0 w-screen h-screen bg-gradient-to-b from-[#FFB07C] to-[#E88165] overflow-hidden flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg text-center">
        <h1 className="text-4xl font-display mb-4">Game Over!</h1>
        <div className="text-9xl font-display mb-4" style={{
          color: rank === 'SSS' ? 'gold' : 
                 rank === 'SS' ? '#FFC107' :
                 rank === 'S' ? '#2196F3' :
                 rank === 'A' ? '#4CAF50' :
                 rank === 'B' ? '#00BCD4' :
                 rank === 'C' ? '#FF9800' :
                 rank === 'D' ? '#F44336' :
                 rank === 'E' ? '#795548' : '#9E9E9E'
        }}>
          {rank}
        </div>
        <p className="text-xl font-display mb-2 italic text-gray-600">"{comment}"</p>
        <div className="space-y-2 mb-6">
          <p className="text-2xl font-display">Total Score: {gameState.totalScore}</p>
          <p className="text-xl font-display">Highest Streak: {gameState.maxStreak}</p>
        </div>
        <PushButton 
          onClick={playAgain}
          color='black'
        >
          Play Again
        </PushButton>
      </div>
    </div>
  );
} 