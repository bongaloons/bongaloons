import { createContext, useState, useEffect, ReactNode } from 'react';
import { Pose } from '../types';

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

interface GameState {
  isRunning: boolean;
  songPath: string;
  mapPath: string;      // New: Path of the MIDI file
  songName: string;     // New: Name of the song
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
}

interface GameContextType {
  isStarted: boolean;
  gameState: GameState;
  ws: WebSocket | null;
  startGame: () => Promise<void>;
  updatePose: (pose: Pose) => void;
  endGame: () => void;
}

export const GameContext = createContext<GameContextType>({
  isStarted: false,
  gameState: {
    isRunning: false,
    songPath: "",
    mapPath: "",
    songName: "",
    currentPose: "idle",
    fallingDots: [],
    connectionStatus: 'disconnected',
    scores: null,
    lastJudgement: null,
    totalScore: null,
    currentStreak: null,
    maxStreak: null,
    pressedKeys: new Set<string>(),
  },
  ws: null,
  startGame: async () => {},
  updatePose: () => {},
  endGame: () => {},
});

export const GameProvider = ({ children }: { children: ReactNode }) => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isStarted, setIsStarted] = useState(false);
  const [gameState, setGameState] = useState<GameState>({
    isRunning: false,
    songPath: "",
    mapPath: "",
    songName: "",
    currentPose: "idle",
    fallingDots: [],
    connectionStatus: 'disconnected',
    scores: null,
    lastJudgement: null,
    totalScore: null,
    currentStreak: null,
    maxStreak: null,
    pressedKeys: new Set<string>(),
  });

  const updatePose = (pose: Pose) => {
    setGameState(prev => ({ ...prev, currentPose: pose }));
  };

  const startGame = async () => {
    setIsStarted(true);
    try {
      // First check if backend is alive
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
          const response = await fetch('http://127.0.0.1:8000/game/start?id=0', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              midi_file: 'jellyfish.mid'
            })
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          const data = await response.json();
          console.log('Game started successfully:', data);
          setGameState(prev => ({
            ...prev,
            isRunning: true,
            songPath: data.songPath,     // Updated field from API
            mapPath: data.midiPath,      // New field from API
            songName: data.songName,     // New field from API (if provided)
            fallingDots: data.falling_dots
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

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (ws) {
        console.log('Cleaning up WebSocket connection');
        ws.close();
      }
    };
  }, [ws]);

  const endGame = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'end_game' }));
    }
    setGameState(prev => ({
      ...prev,
      isRunning: false,
      fallingDots: [],
    }));
    setIsStarted(false);
  };

  return (
    <GameContext.Provider value={{ isStarted, gameState, ws, startGame, updatePose, endGame }}>
      {children}
    </GameContext.Provider>
  );
};
