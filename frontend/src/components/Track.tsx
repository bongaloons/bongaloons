import { FC, useContext } from 'react';
import Dot from './Dot';
import { GameContext } from '../context/GameContext';

interface TrackProps {
  position: 'left' | 'right';
  text: string;
}

const Track: FC<TrackProps> = ({ position, text }) => {
  const { gameState } = useContext(GameContext);
  const isRight = position === 'right';

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
