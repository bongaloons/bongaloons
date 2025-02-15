import { FC, useEffect, useState } from 'react';

interface DotProps {
  delay: number;
}

const Dot: FC<DotProps> = ({ delay }) => {
  const [position, setPosition] = useState(100);

  useEffect(() => {
    const animate = () => {
      setPosition((prev) => {
        if (prev <= -10) return 100;
        return prev - 0.5;
      });
    };

    const timeout = setTimeout(() => {
      const interval = setInterval(animate, 50);
      return () => clearInterval(interval);
    }, delay);

    return () => clearTimeout(timeout);
  }, [delay]);

  return (
    <div 
      className="absolute w-2 h-2 rounded-full bg-black opacity-50"
      style={{
        bottom: `${position}%`,
        left: `${Math.random() * 80 + 10}%`,
        transition: 'bottom 0.05s linear'
      }}
    />
  );
};

export default Dot; 