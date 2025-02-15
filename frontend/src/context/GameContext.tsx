import { createContext, useState, useEffect, ReactNode } from 'react';
import { Pose } from '../types';

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

interface GameState {
  isRunning: boolean;
  currentPose: Pose;
  fallingDots: Array<{
    move: string;
    target_time: number;
    track: string;
  }>;
  connectionStatus: ConnectionStatus;
  lastJudgement: string | null;
  totalScore: number | null;
  scores: {
    [key: string]: Array<{
      truth_time: number | null;
      hit_time: number | null;
      difference: number | null;
      judgement: string;
    }>;
  } | null;
}

interface GameContextType {
  gameState: GameState;
  ws: WebSocket | null;
  startGame: () => Promise<void>;
  updatePose: (pose: Pose) => void;
}

export const GameContext = createContext<GameContextType>({
  gameState: {
    isRunning: false,
    currentPose: "idle",
    fallingDots: [],
    connectionStatus: 'disconnected',
    scores: null,
    lastJudgement: null,
    totalScore: null
  },
  ws: null,
  startGame: async () => {},
  updatePose: () => {}
});

export const GameProvider = ({ children }: { children: ReactNode }) => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [gameState, setGameState] = useState<GameState>({
    isRunning: false,
    currentPose: "idle",
    fallingDots: [],
    connectionStatus: 'disconnected',
    scores: null,
    lastJudgement: null,
    totalScore: null
  });

  const updatePose = (pose: Pose) => {
    setGameState(prev => ({ ...prev, currentPose: pose }));
  }

  const startGame = async () => {
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
          const response = await fetch('http://127.0.0.1:8000/game/start?midi_file=test.mid', {
            method: 'POST',
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          const data = await response.json();
          console.log('Game started successfully:', data);
          setGameState(prev => ({
            ...prev,
            isRunning: true,
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
            }));
        } else if (data.type === "game_over") {
            setGameState(prev => ({
                ...prev,
                scores: data.scores,
                lastJudgement: data.lastJudgement,
                totalScore: data.totalScore,
                isRunning: false
            }));
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

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (ws) {
        console.log('Cleaning up WebSocket connection');
        ws.close();
      }
    };
  }, [ws]);

  return (
    <GameContext.Provider value={{ gameState, ws, startGame, updatePose }}>
      {children}
    </GameContext.Provider>
  );
}; 