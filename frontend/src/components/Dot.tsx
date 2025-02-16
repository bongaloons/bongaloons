import { FC, useEffect, useState, useContext, useRef } from 'react';
import { GameContext } from '../context/GameContext';

interface DotProps {
  targetTime: number;  // Time (ms) when the dot is meant to be hit
}

const Dot: FC<DotProps> = ({ targetTime }) => {
  const dotStartPosition = 0;
  const { gameState } = useContext(GameContext);
  const [position, setPosition] = useState(dotStartPosition);
  const [isSprite] = useState(() => Math.random() < 0.4);
  const [color] = useState(() => {
    const colors = [
      '#FF4444', // bright red
      '#00FFE5', // bright teal
      '#00BFFF', // bright blue
      '#66FF99', // bright green
      '#FFFF66', // bright yellow
      '#FF99CC', // bright pink
      '#B266FF', // bright purple
      '#FF9933', // bright orange
    ];
    return colors[Math.floor(Math.random() * colors.length)];
  });

  // Always get the latest gameState via a ref.
  const gameStateRef = useRef(gameState);
  useEffect(() => {
    gameStateRef.current = gameState;
  }, [gameState]);

  /**
   * When the game is paused, we want to increment the pause duration
   * continuously so that effective time (used to spawn dots) does not
   * advance during a pause.
   */
  const [pauseAccumulator, setPauseAccumulator] = useState(0);
  useEffect(() => {
    let pauseInterval: NodeJS.Timeout;
    if (gameState.isPaused) {
      const pauseStart = performance.now();
      pauseInterval = setInterval(() => {
        setPauseAccumulator(() => performance.now() - pauseStart);
      }, 50);
    } else {
      // Reset the local pause accumulator when unpaused.
      setPauseAccumulator(0);
    }
    return () => clearInterval(pauseInterval);
  }, [gameState.isPaused]);

  // Local state to determine when to spawn (i.e. start animation)
  const [spawned, setSpawned] = useState(false);

  // Ref for the dot element to log its position.
  const dotRef = useRef<HTMLDivElement>(null);

  // Effect to update effective time and check for spawn.
  useEffect(() => {
    // Calculate the intended spawn time (ms)
    const spawnTime = targetTime - gameState.fallDuration + gameState.delay + gameState.reactionTime;
    const checkSpawn = () => {
      // Compute effective time:
      // elapsed time = current time - game start time
      // then subtract both the totalPausedTime from earlier pauses and the
      // accumulated pause time for the current pause.
      const effectiveTime = gameState.startTime
        ? performance.now() - gameState.startTime - gameState.totalPausedTime - pauseAccumulator
        : 0;
      if (effectiveTime >= spawnTime) {
        setSpawned(true);
      }
    };
    const intervalId = setInterval(checkSpawn, 50);
    return () => clearInterval(intervalId);
  }, [
    gameState.delay, 
    targetTime, 
    gameState.fallDuration, 
    gameState.startTime, 
    gameState.totalPausedTime,
    pauseAccumulator,
  ]);

  const [hasHitLine, setHasHitLine] = useState(false);
  
  // Effect to animate the dot once it has spawned.
  useEffect(() => {
    if (!spawned) return;
    const animate = () => {
      setPosition(prev => {
        const limit = 80;
        if (prev >= limit) {
          if (prev === limit && !hasHitLine) {
            setHasHitLine(true);
            setTimeout(() => {
              setPosition(limit + 0.01);
            }, 50);
          }
          return limit;
        }
        const totalDistance = limit - dotStartPosition;
        const isPaused = gameStateRef.current.isPaused;
        const speedPer50ms = isPaused ? 0 : (totalDistance / gameState.fallDuration) * 50;
        return prev + speedPer50ms;
      });
    };
    const interval = setInterval(animate, 50);
    return () => clearInterval(interval);
  }, [spawned, gameState.fallDuration, hasHitLine]);

  // Log the dot's x and y coordinates whenever position updates.
  useEffect(() => {
    if (dotRef.current) {
      const rect = dotRef.current.getBoundingClientRect();
      console.log(`Dot position - x: ${rect.x.toFixed(2)}, y: ${rect.y.toFixed(2)}`);
    }
  }, [position]);

  // Do not render the dot until it has spawned.
  if (!spawned) return null;
  if (position > 80) return null;

  const scale = position >= 75 ? 1 + ((position - 75) / 10) * 0.5 : 1;
  const opacity = hasHitLine ? 0 : 1;

  return (
    <div 
      ref={dotRef}
      className="absolute rounded-full"
      style={{
        bottom: `${position}%`,
        left: "25%",
        width: "80px",
        height: "80px",
        background: `radial-gradient(circle at 30% 30%, ${color}ee, ${color}aa, ${color}88)`,
        boxShadow: `0 0 10px ${color}66`,
        transition: hasHitLine ? 
          'bottom 0.05s linear, opacity 0.05s linear, transform 0.05s linear' : 
          'bottom 0.05s linear, transform 0.05s linear',
        transform: `scale(${scale})`,
        opacity,
        border: isSprite ? 'none' : '4px solid black'
      }}
    >
      {isSprite && (
        <div
          className="absolute"
          style={{
            width: "100%",
            height: "100%",
            backgroundImage: `url(/dots/chicken.png)`,
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
