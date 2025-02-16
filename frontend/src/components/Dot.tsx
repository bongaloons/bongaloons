import { FC, useEffect, useState } from 'react';

interface DotProps {
  delay: number;
  targetTime: number;
  fallDuration: number;
}

const Dot: FC<DotProps> = ({ delay, targetTime, fallDuration }) => {
  const [position, setPosition] = useState(-100);
  const [isSprite] = useState(() => Math.random() < 0.4);
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

  const [sprite] = useState(() => {
    const sprites = ['chicken.png', 'chip.png', 'toy.png', 'tree.png', 'yarn.png'];
    return sprites[Math.floor(Math.random() * sprites.length)];
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
        left: "5%",
        width: "150px",
        height: "150px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        className="rounded-full"
        style={{
          width: "80px",
          height: "80px",
          background: `radial-gradient(circle at 30% 30%, ${color}ee, ${color}aa, ${color}88)`,
          boxShadow: `0 0 10px ${color}66`,
          transition: 'bottom 0.05s linear',
          border: isSprite ? 'none' : '4px solid rgba(0, 0, 0, 0.8)',
        }}
      />
      
      {isSprite && (
        <div
          className="absolute"
          style={{
            width: "100%",
            height: "100%",
            backgroundImage: `url(/dots/${sprite})`,
            backgroundSize: 'contain',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
          }}
        />
      )}
    </div>
  );
};

export default Dot;
