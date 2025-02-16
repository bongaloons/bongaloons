import { useContext, useEffect, useState } from 'react';
import { GameContext } from '../context/GameContext';
import PushButton from '../components/PushButton';

interface Song {
  id: number;
  name: string;
  path: string;
  song: string;
  bpm: number;
}

export default function SongSelect() {
  const { startGame, setShowSongSelect } = useContext(GameContext);
  const [songs, setSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/songs')
      .then(res => res.json())
      .then(data => {
        setSongs(data.songs);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching songs:', err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="w-screen h-screen bg-gradient-to-b from-[#FFB07C] to-[#E88165] flex items-center justify-center">
        <div className="text-white text-2xl font-display">Loading songs...</div>
      </div>
    );
  }

  return (
    <div className="w-screen h-screen bg-gradient-to-b from-[#FFB07C] to-[#E88165] flex flex-col items-center justify-center gap-8">
      <div className="p-8 bg-white rounded-lg shadow-md w-1/2">
        <h1 className="text-6xl text-black mb-8 font-display">Select a Song</h1>
        <div className="flex flex-col gap-4 w-96">
          {songs.map(song => (
            <PushButton
              align="left"
              key={song.id}
              onClick={() => startGame(song.id)}
            >
              {song.name}
            </PushButton>
          ))}
          <PushButton
            onClick={() => setShowSongSelect(false)}
            color="black"
            className="relative bg-black hover:bg-gray-800 text-white font-display text-2xl py-4 px-6 rounded-lg shadow-[4px_4px_0px_0px_rgba(255,255,255,0.3)] hover:shadow-[2px_2px_0px_0px_rgba(255,255,255,0.3)] active:shadow-[0px_0px_0px_0px_rgba(255,255,255,0.3)] transform hover:translate-y-0.5 active:translate-y-1 transition-all duration-150 [box-shadow:inset_0px_2px_8px_rgba(255,255,255,0.1)]"
          >
            Back
          </PushButton>
        </div>
      </div>
    </div>
  );
} 