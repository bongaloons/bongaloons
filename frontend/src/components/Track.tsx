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
      className={`w-full h-full border-x-4 border-black ${isRight ? 'bg-yellow-400' : 'bg-blue-200'} relative`}
    >
      {text}
      {gameState.fallingDots.filter(dot => dot.track === position).map((dot, i) => (
        <div key={i}>
            {position}
          {dot.track}
          {dot.target_time}
        </div>
      ))}
      {gameState.fallingDots
        .filter(dot => dot.track === position)
        .map((dot, i) => (
          <Dot 
            key={i} 
            targetTime={dot.target_time} // time when dot should be hit
            fallDuration={2000}  // time for a dot to traverse track
            delay={2000} // time when first dot reaches end of track
          />
        ))}
    </div>
  );
};

export default Track;
