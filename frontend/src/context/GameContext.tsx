import { createContext, useState, useEffect, ReactNode } from 'react';
import { Pose } from '../types';
import { clearAudio, playSoundFile } from '../utils/audioPlayer';

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

interface GameState {
  isRunning: boolean;
  isPaused: boolean;          // Pause state
  startTime: number | null;   // Game start time (ms)
  totalPausedTime: number;    // Total paused time (ms)
  pauseTimestamp: number | null; // Timestamp when pause started (ms)
  songPath: string;
  mapPath: string;
  songName: string;
  bpm: number;
  currentPose: Pose;
  fallingDots: Array<{
    move: string;
    target_time: number;
    track: string;
  }>;
  connectionStatus: ConnectionStatus;
  lastJudgement: string | null;
  totalScore: number | null;
  currentStreak: number | null;
  maxStreak: number | null;
  scores: {
    [key: string]: Array<{
      truth_time: number | null;
      hit_time: number | null;
      difference: number | null;
      judgement: string;
    }>;
  } | null;
  pressedKeys: Set<string>;
  fallDuration: number;
  delay: number;
  reactionTime: number;
}

interface GameContextType {
  isStarted: boolean;
  gameState: GameState;
  ws: WebSocket | null;
  startGame: (songId?: number) => Promise<void>;
  updatePose: (pose: Pose) => void;
  togglePause: () => void;
  endGame: () => void;
  showSongSelect: boolean;
  setShowSongSelect: (show: boolean) => void;
  playAgain: () => void;
}

const DEFAULT_FALL_DURATION = 2000;
const DEFAULT_DELAY = 2000;
const DEFAULT_REACTION_TIME = 250;

export const GameContext = createContext<GameContextType>({
  isStarted: false,
  gameState: {
    isRunning: false,
    isPaused: false,
    startTime: null,
    totalPausedTime: 0,
    pauseTimestamp: null,
    songPath: "",
    mapPath: "",
    songName: "",
    bpm: 0,
    currentPose: "idle",
    fallingDots: [],
    connectionStatus: 'disconnected',
    scores: null,
    lastJudgement: null,
    totalScore: null,
    currentStreak: null,
    maxStreak: null,
    pressedKeys: new Set<string>(),
    fallDuration: DEFAULT_FALL_DURATION,
    delay: DEFAULT_DELAY,
    reactionTime: DEFAULT_REACTION_TIME,
  },
  ws: null,
  startGame: async () => {},
  updatePose: () => {},
  togglePause: () => {},
  endGame: () => {},
  showSongSelect: false,
  setShowSongSelect: () => {},
  playAgain: () => {},
});

export const GameProvider = ({ children }: { children: ReactNode }) => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isStarted, setIsStarted] = useState(false);
  const [showSongSelect, setShowSongSelect] = useState(false);
  const [gameState, setGameState] = useState<GameState>({
    isRunning: false,
    isPaused: false,
    startTime: null,
    totalPausedTime: 0,
    pauseTimestamp: null,
    songPath: "",
    mapPath: "",
    songName: "",
    bpm: 0,
    currentPose: "idle",
    fallingDots: [],
    connectionStatus: 'disconnected',
    scores: null,
    lastJudgement: null,
    totalScore: null,
    currentStreak: null,
    maxStreak: null,
    pressedKeys: new Set<string>(),
    fallDuration: DEFAULT_FALL_DURATION,
    delay: DEFAULT_DELAY,
    reactionTime: DEFAULT_REACTION_TIME,
  });

  const updatePose = (pose: Pose) => {
    setGameState(prev => ({ ...prev, currentPose: pose }));
  };

  // Toggle pause: record pause timestamp when pausing, and update totalPausedTime when resuming.
  const togglePause = () => {
    setGameState(prev => {
      if (!prev.isPaused) {
        return { ...prev, isPaused: true, pauseTimestamp: performance.now() };
      } else {
        const pausedDuration = performance.now() - (prev.pauseTimestamp || performance.now());
        return {
          ...prev,
          isPaused: false,
          totalPausedTime: prev.totalPausedTime + pausedDuration,
          pauseTimestamp: null
        };
      }
    });
  };

  // New effect: fetch fallDuration and delay from samples.json in the public folder.
  useEffect(() => {
    fetch('/settings.json')
      .then(res => res.json())
      .then(data => {
        // Assuming your JSON looks like: { "fall_duration": 2000, "delay": 3000 }
        setGameState(prev => ({
          ...prev,
          fallDuration: data.fall_duration,
          delay: data.delay,
          reactionTime: data.reaction_time
        }));
      })
      .catch(err => console.error("Error fetching settings.json:", err));
  }, []);

  const startGame = async (songId: number = 0) => {
    setIsStarted(true);
    try {
      console.log('Checking backend health...');
      const healthCheck = await fetch('http://127.0.0.1:8000/health');
      if (!healthCheck.ok) {
        throw new Error('Backend health check failed');
      }
      console.log('Backend health check passed');

      setGameState(prev => ({ ...prev, connectionStatus: 'connecting' }));

      console.log('Attempting WebSocket connection...');
      const newWs = new WebSocket('ws://127.0.0.1:8000/game/ws');

      newWs.onopen = async () => {
        console.log('WebSocket connected successfully');
        setGameState(prev => ({ ...prev, connectionStatus: 'connected' }));

        try {
          console.log('Starting game...');
          const response = await fetch(`http://127.0.0.1:8000/game/start?id=${songId}`, {
            method: 'POST'
          });
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          const data = await response.json();
          console.log('Game started successfully:', data);
          setGameState(prev => ({
            ...prev,
            isRunning: true,
            songPath: data.songPath,
            mapPath: data.midiPath,
            songName: data.songName,
            bpm: data.bpm,
            fallingDots: data.falling_dots,
            startTime: performance.now(), // Set the game start time
            totalPausedTime: 0,
            pauseTimestamp: null
          }));
        } catch (error) {
          console.error('Error starting game:', error);
          throw error;
        }
      };

      newWs.onerror = (error) => {
        console.error('WebSocket error:', error);
        setGameState(prev => ({
          ...prev,
          connectionStatus: 'error',
          isRunning: false
        }));
        setIsStarted(false);
      };

      newWs.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setGameState(prev => ({
          ...prev,
          connectionStatus: 'disconnected',
          isRunning: false
        }));
      };

      newWs.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "hit_registered") {
          setGameState(prev => ({
            ...prev,
            lastJudgement: data.lastJudgement,
            totalScore: data.totalScore,
            currentStreak: data.currentStreak,
            maxStreak: data.maxStreak,
          }));
        }  else if (data.type === "note_missed") {
          // Process note missed events:
          // For example, update lastJudgement to "MISS" and reset the current streak.
          setGameState(prev => ({
            ...prev,
            lastJudgement: data.judgement,  // e.g. "MISS"
            totalScore: data.totalScore,    // updated score if any penalty is applied
            currentStreak: 0,               // reset streak on miss
          }));
        } else if (data.type === "game_over") {
          setGameState(prev => ({
            ...prev,
            scores: data.scores,
            lastJudgement: data.lastJudgement,
            totalScore: data.totalScore,
            currentStreak: 0,
            maxStreak: data.maxStreak,
            isRunning: false
          }));
          setIsStarted(false);
        }
        console.log('Game state updated:', data);
      };

      setWs(newWs);

    } catch (error) {
      console.error('Connection error:', error);
      setGameState(prev => ({
        ...prev,
        connectionStatus: 'error',
        isRunning: false
      }));
      if (ws) {
        ws.close();
      }
    }
  };

  const updatePoseBasedOnKeys = (pressedKeys: Set<string>) => {
    if (pressedKeys.has('a') || pressedKeys.has('l')) {
      playSoundFile('/sfx/hit.ogg');
    }

    if (pressedKeys.has('a') && pressedKeys.has('l')) {
      updatePose('both');
    } else if (pressedKeys.has('a')) {
      updatePose('left');
    } else if (pressedKeys.has('l')) {
      updatePose('right');
    } else {
      updatePose('idle');
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!ws || !['a', 'l'].includes(e.key) || gameState.pressedKeys.has(e.key)) return;

      const newPressedKeys = new Set(gameState.pressedKeys).add(e.key);
      setGameState(prev => ({ ...prev, pressedKeys: newPressedKeys }));
      ws.send(JSON.stringify({ key: e.key }));
      updatePoseBasedOnKeys(newPressedKeys);
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (!['a', 'l'].includes(e.key)) return;

      const newPressedKeys = new Set(gameState.pressedKeys);
      newPressedKeys.delete(e.key);
      setGameState(prev => ({ ...prev, pressedKeys: newPressedKeys }));
      updatePoseBasedOnKeys(newPressedKeys);
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [ws, gameState.pressedKeys, updatePose]);

  // Cleanup WebSocket on unmount.
  useEffect(() => {
    return () => {
      if (ws) {
        console.log('Cleaning up WebSocket connection');
        ws.close();
      }
    };
  }, [ws]);

  const endGame = () => {
    setGameState(prev => ({
      ...prev,
      isPaused: false,
      isRunning: false,
      fallingDots: [],
    }));
    setIsStarted(false);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'end_game' }));
    }
  };

  const playAgain = () => {
    setGameState(prev => ({
      ...prev,
      totalScore: null,
      currentStreak: 0,
      maxStreak: 0,
      scores: null,
      isRunning: false,
      fallingDots: [],
    }));
    clearAudio();
    setShowSongSelect(true);
  };

  return (
    <GameContext.Provider
      value={{
        isStarted,
        gameState,
        ws,
        startGame,
        updatePose,
        togglePause,
        endGame,
        showSongSelect,
        setShowSongSelect,
        playAgain,
      }}
    >
      {children}
    </GameContext.Provider>
  );
};

export default GameProvider;
