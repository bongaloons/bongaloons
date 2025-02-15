import { FC, useEffect, useState } from 'react';

interface DotProps {
  delay: number;
  targetTime: number;
  fallDuration: number;
}

const Dot: FC<DotProps> = ({ delay, targetTime, fallDuration }) => {
  const [position, setPosition] = useState(-100);
  const [color] = useState(() => {
    const colors = [
      '#FF6B6B', // red
      '#4ECDC4', // teal
      '#45B7D1', // blue
      '#96CEB4', // green
      '#FFEEAD', // yellow
      '#D4A5A5', // pink
      '#9B59B6', // purple
      '#E67E22', // orange
    ];
    return colors[Math.floor(Math.random() * colors.length)];
  });

  useEffect(() => {
    const animate = () => {
      setPosition((prev) => {
        if (prev >= 100) return 100;
        
        const totalDistance = 200;
        const speedPer50ms = (totalDistance / fallDuration) * 50;
        
        return prev + speedPer50ms;
      });
    };

    const timeout = setTimeout(() => {
      const interval = setInterval(animate, 50);

      return () => clearInterval(interval);
    }, targetTime - fallDuration + delay);

    return () => clearTimeout(timeout);
  }, [fallDuration, targetTime, delay]);

  // If the position is -100, return null (don't render the dot)
  if (position === -100) {
    return null; // disappear
  }

  return (
    <div 
      className="absolute rounded-full"
      style={{
        bottom: `${position}%`,
        left: "25%",
        width: "80px",
        height: "80px",
        background: `radial-gradient(circle at 30% 30%, ${color}ee, ${color}aa, ${color}88)`,
        boxShadow: `0 0 10px ${color}66`,
        transition: 'bottom 0.05s linear'
      }}
    />
  );
};

export default Dot;
