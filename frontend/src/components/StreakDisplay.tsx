import { useContext } from 'react';
import { GameContext } from '../context/GameContext';

export const StreakDisplay = () => {
  const { gameState } = useContext(GameContext);

  if (!gameState.isRunning) {
    return null;
  }

  return (
    <div className="text-white text-xl">
      <div className="mb-2">
        Current Streak: {gameState.currentStreak || 0}
      </div>
      <div>
        Max Streak: {gameState.maxStreak || 0}
      </div>
    </div>
  );
}; 