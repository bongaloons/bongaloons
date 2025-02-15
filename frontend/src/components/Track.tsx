import { FC, useEffect, useContext } from 'react';
import Dot from './Dot';
import { GameContext } from '../context/GameContext';

interface TrackProps {
  position: 'left' | 'right';
  text: string;
}

const Track: FC<TrackProps> = ({ position, text }) => {
  const { gameState, ws, updatePose } = useContext(GameContext);
  const isRight = position === 'right';
  
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (!ws) return;
      
      if ((position === 'left' && e.key === 'a') || 
          (position === 'right' && e.key === 'l')) {
        ws.send(JSON.stringify({ key: e.key }));
        updatePose(position);
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [ws, position, updatePose]);

  return (
    <div 
    className={`w-40 h-[${isRight ? '60%' : '60%'}] ${isRight ? 'bg-yellow-400' : 'bg-blue-200'} relative`}
    >
      {text}
      {gameState.fallingDots
        .filter(dot => dot.track === position)
        .map((dot, i) => (
          <Dot 
            key={i} 
            targetTime={dot.target_time} 
            fallDuration={2000} 
            delay={i * 1000}
          />
        ))}
    </div>
  );
};

export default Track;
