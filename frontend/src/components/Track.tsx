import { FC, useContext, useState, useEffect } from 'react';
import Dot from './Dot';
import { GameContext } from '../context/GameContext';

interface TrackProps {
  position: 'left' | 'right';
  text: string;
}

const Track: FC<TrackProps> = ({ position, text }) => {
  const { gameState } = useContext(GameContext);
  const [isVibrating, setIsVibrating] = useState(false);
  
  const getVibrateClass = () => {
    if (!isVibrating) return '';
    const streak = gameState.currentStreak || 0;
    if (streak >= 50) return 'animate-track-vibrate-intense';
    if (streak >= 10) return 'animate-track-vibrate-medium';
    return 'animate-track-vibrate-normal';
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((position === 'left' && e.key === 'a') || 
          (position === 'right' && e.key === 'l')) {
        setIsVibrating(true);
        setTimeout(() => setIsVibrating(false), 100);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [position]);

  return (
    <div 
      className={`w-full h-full border-x-4 border-black relative font-display text-xl transition-transform duration-100 ${
        getVibrateClass()
      }`}
    >
      {text}
      {gameState.fallingDots
        .filter(dot => dot.track === position)
        .map((dot, i) => (
          <Dot 
            key={i} 
            targetTime={dot.target_time} // time when dot should be hit
            // fallDuration={gameState.fallDuration}  // time for a dot to traverse track
            // delay={gameState.delay} // time when first dot reaches end of track
          />
        ))}
    </div>
  );
};

export default Track;
