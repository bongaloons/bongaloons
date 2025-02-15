import { FC } from 'react';
import Dot from './Dot';

interface TrackProps {
  position: 'left' | 'right';
  text: string;
}

const Track: FC<TrackProps> = ({ position, text }) => {
  const isRight = position === 'right';
  
  return (
    <div 
      className={`w-40 h-[${isRight ? '60%' : '60%'}] ${isRight ? 'bg-yellow-400' : 'bg-blue-200'} relative`}
    >
      {text}
      {[...Array(5)].map((_, i) => (
        <Dot key={i} delay={i * 1000} />
      ))}
    </div>
  );
};

export default Track;
