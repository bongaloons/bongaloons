import { FC, useEffect, useState } from 'react';

interface DotProps {
  delay: number;
}

const Dot: FC<DotProps> = ({ delay }) => {
  const [position, setPosition] = useState(100);

  useEffect(() => {
    const animate = () => {
      setPosition((prev) => {
        if (prev >= 100) return -100;
        return prev + 5;
      });
    };

    const timeout = setTimeout(() => {
      const interval = setInterval(animate, 50);
      return () => clearInterval(interval);
    }, delay);

    return () => clearTimeout(timeout);
  }, [delay]);

  // If the position is -100, return null (don't render the dot)
  if (position === -100) {
    return null; // disappear
  }

  return (
    <div 
      className="absolute rounded-full bg-black opacity-50"
      style={{
        bottom: `${position}%`,
        left: "25%",         // Adjust this as needed for horizontal placement
        width: "50%",      // Dot width as a percentage of parent's width
        height: "30%",      // Dot height as a percentage of parent's width
        transition: 'bottom 0.05s linear'
      }}
    />
  );
};

export default Dot;
