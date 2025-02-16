import { FC, useEffect, useState, useContext, useRef } from 'react';
import { GameContext } from '../context/GameContext';

interface DotProps {
  delay: number;       // Initial delay (ms) before the dot should appear (relative to game timeline)
  targetTime: number;  // Time (ms) when the dot is meant to be hit
  fallDuration: number; // Duration (ms) for the dot to fall from its spawn position to the target
}

const Dot: FC<DotProps> = ({ delay, targetTime, fallDuration }) => {
  const { gameState } = useContext(GameContext);
  const [position, setPosition] = useState(-100);
  const [isSprite] = useState(() => Math.random() < 0.4);
  const [visual] = useState(() => {
    if (isSprite) {
      const sprites = ['chicken.png', 'chip.png', 'toy.png', 'tree.png', 'yarn.png'];
      return sprites[Math.floor(Math.random() * sprites.length)];
    } else {
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
    }
  });

  // Always get the latest gameState via a ref.
  const gameStateRef = useRef(gameState);
  useEffect(() => {
    gameStateRef.current = gameState;
  }, [gameState]);

  // Ref to hold the effective game time (time elapsed that doesn't advance when paused)
  const effectiveTimeRef = useRef(0);

  // Local state to determine when to spawn (i.e. start animation)
  const [spawned, setSpawned] = useState(false);

  // Effect to update effective time and check for spawn.
  useEffect(() => {
    // Calculate the intended spawn time (ms)
    const spawnTime = targetTime - fallDuration + delay;
    const checkSpawn = () => {
      // Compute effective time: subtract totalPausedTime from elapsed time.
      const effectiveTime = gameState.startTime 
        ? performance.now() - gameState.startTime - gameState.totalPausedTime 
        : 0;
        // console.log("Paused time:", gameState.totalPausedTime );
        // console.log("Effective time:", effectiveTime );
        if (effectiveTime >= spawnTime) {
        setSpawned(true);
      }
    };
    const intervalId = setInterval(checkSpawn, 50);
    return () => clearInterval(intervalId);
  }, [delay, targetTime, fallDuration, gameState.startTime, gameState.totalPausedTime]);
  

  // Effect to animate the dot once it has spawned.
  useEffect(() => {
    if (!spawned) return;
    const animate = () => {
      setPosition(prev => {
        if (prev >= 100) return 100;
        const totalDistance = 200;
        // Use the latest pause status from our ref.
        const isPaused = gameStateRef.current.isPaused;
        const speedPer50ms = isPaused ? 0 : (totalDistance / fallDuration) * 50;
        return prev + speedPer50ms;
      });
    };
    const interval = setInterval(animate, 50);
    return () => clearInterval(interval);
  }, [spawned, fallDuration]);

  // Do not render the dot until it has spawned.
  if (!spawned) return null;

  return (
    <div 
      className="absolute rounded-full"
      style={{
        bottom: `${position}%`,
        left: isSprite ? "20%" : "25%",
        width: isSprite ? "150px" : "80px",
        height: isSprite ? "150px" : "80px",
        ...(isSprite 
          ? {
              backgroundImage: `url(/dots/${visual})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              borderRadius: 0,
            }
          : {
              background: `radial-gradient(circle at 30% 30%, ${visual}ee, ${visual}aa, ${visual}88)`,
              boxShadow: `0 0 10px ${visual}66`,
              transition: 'bottom 0.05s linear',
              border: '4px solid rgba(0, 0, 0, 0.8)',
            }
        )
      }}
    />
  );
};

export default Dot;
