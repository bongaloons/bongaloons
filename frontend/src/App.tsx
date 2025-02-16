import './App.css'
import { useContext } from 'react'
import { GameContext } from './context/GameContext'
import Game from './pages/Game';
import TitleScreen from './pages/TitleScreen';
import GameOver from './components/GameOver';
import SongSelect from './pages/SongSelect';

function App() {
  const { isStarted, gameState, showSongSelect } = useContext(GameContext);

  const showGameOver = !isStarted && gameState.totalScore !== null;

  return (
    <div>
      {showGameOver ? (
        <GameOver />
      ) : isStarted ? (
        <Game />
      ) : showSongSelect ? (
        <SongSelect />
      ) : (
        <TitleScreen />
      )}
    </div>
  )
}

export default App
