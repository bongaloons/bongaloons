import './App.css'
import { useContext } from 'react'
import { GameContext } from './context/GameContext'
import Game from './pages/Game';
import TitleScreen from './pages/TitleScreen';

function App() {
  const { isStarted } = useContext(GameContext);

  return (
    <div>
      {isStarted ? <Game /> : <TitleScreen />}
    </div>
  )
}

export default App
