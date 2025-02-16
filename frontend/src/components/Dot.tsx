import { FC, useEffect, useState, useContext, useRef } from 'react';
import { GameContext } from '../context/GameContext';

interface DotProps {
  targetTime: number;  // Time (ms) when the dot is meant to be hit
}

const Dot: FC<DotProps> = ({targetTime}) => {
  const dotStartPosition = 0;
  const { gameState } = useContext(GameContext);
  const [position, setPosition] = useState(dotStartPosition);
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

  // Always get the latest gameState via a ref.
  const gameStateRef = useRef(gameState);
  useEffect(() => {
    gameStateRef.current = gameState;
  }, [gameState]);

  // Ref to hold the effective game time (time elapsed that doesn't advance when paused)
  const effectiveTimeRef = useRef(0);

  // Local state to determine when to spawn (i.e. start animation)
  const [spawned, setSpawned] = useState(false);

  // Ref for the dot element to log its position.
  const dotRef = useRef<HTMLDivElement>(null);

  // Effect to update effective time and check for spawn.
  useEffect(() => {
    // Calculate the intended spawn time (ms)
    const spawnTime = targetTime - gameState.fallDuration + gameState.delay;
    const checkSpawn = () => {
      // Compute effective time: subtract totalPausedTime from elapsed time.
      const effectiveTime = gameState.startTime
        ? performance.now() - gameState.startTime - gameState.totalPausedTime
        : 0;
      // console.log("Effective time:", effectiveTime);
      if (effectiveTime >= spawnTime) {
        setSpawned(true);
      }
    };
    const intervalId = setInterval(checkSpawn, 50);
    return () => clearInterval(intervalId);
  }, [gameState.delay, targetTime, gameState.fallDuration, gameState.startTime, gameState.totalPausedTime]);

  // Effect to animate the dot once it has spawned.
  useEffect(() => {
    if (!spawned) return;
    const animate = () => {
      setPosition(prev => {
        const limit = 80;
        if (prev >= limit) {
          if (prev !== limit) {
            console.log("Dot hit the line!");
          }
          return limit;
        }
        const totalDistance = limit - dotStartPosition;
        // Use the latest pause status from our ref.
        const isPaused = gameStateRef.current.isPaused;
        const speedPer50ms = isPaused ? 0 : (totalDistance / gameState.fallDuration) * 50;
        console.log(" dfnjid ", gameState.fallDuration, speedPer50ms);
        // console.log((prev - dotStartPosition) / totalDistance, (performance.now() - (gameState.startTime ? gameState.startTime : 0) - (targetTime - fallDuration + delay)) / fallDuration)
        return prev + speedPer50ms;
      });
    };
    const interval = setInterval(animate, 50);
    return () => clearInterval(interval);
  }, [spawned, gameState.fallDuration]);

  // Log the dot's x and y coordinates whenever position updates.
  useEffect(() => {
    if (dotRef.current) {
      const rect = dotRef.current.getBoundingClientRect();
      console.log(`Dot position - x: ${rect.x.toFixed(2)}, y: ${rect.y.toFixed(2)}`);
    }
  }, [position]);

  // Do not render the dot until it has spawned.
  if (!spawned) return null;

  return (
    <div 
      ref={dotRef}
      className="absolute rounded-full"
      style={{
        bottom: `${position}%`,
        left: "25%", // Adjust as needed to center in track
        width: "80px",
        height: "80px",
        background: `radial-gradient(circle at 30% 30%, ${color}ee, ${color}aa, ${color}88)`,
        boxShadow: `0 0 10px ${color}66`,
        transition: 'bottom 0.05s linear'
      }}
    >
      {isSprite && (
        <div
          className="absolute"
          style={{
            width: "100%",
            height: "100%",
            backgroundImage: `url(/dots/chicken.png)`, // Replace with dynamic sprite if desired
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
