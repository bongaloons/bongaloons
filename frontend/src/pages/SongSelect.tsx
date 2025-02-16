import { useContext, useEffect, useState } from 'react';
import { GameContext } from '../context/GameContext';

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
      <h1 className="text-6xl font-display text-white mb-8">Select a Song</h1>
      <div className="flex flex-col gap-4 w-96">
        {songs.map(song => (
          <button
            key={song.id}
            onClick={() => startGame(song.id)}
            className="bg-white hover:bg-gray-100 text-black font-display text-2xl py-4 px-6 rounded-lg shadow-md transition-colors duration-200"
          >
            {song.name}
          </button>
        ))}
        <button
          onClick={() => setShowSongSelect(false)}
          className="bg-black hover:bg-gray-100 text-white font-display text-2xl py-4 px-6 rounded-lg shadow-md transition-colors duration-200"
        >
          Back
        </button>
      </div>
    </div>
  );
} 