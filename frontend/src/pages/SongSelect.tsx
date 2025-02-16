import { useContext, useEffect, useState } from 'react';
import { GameContext } from '../context/GameContext';
import PushButton from '../components/PushButton';
import SquigglyText from '../components/SquigglyText';
import SongCard, { Song } from './SongCard';
import BeatmapUpload from '../components/BeatmapUpload';


export default function SongSelect() {
  const { startGame, setShowSongSelect } = useContext(GameContext);
  const [showUploadForm, setShowUploadForm] = useState(false);
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

  console.log("Loading", loading);

  if (loading) {
    return (
      <div className="w-screen h-screen bg-gradient-to-b from-[#FFB07C] to-[#E88165] flex items-center justify-center">
        <div className="text-white text-2xl font-display">Loading songs...</div>
      </div>
    );
  }

  return (
    <div className="w-screen h-screen bg-gradient-to-b from-[#FFB07C] to-[#E88165] flex flex-col items-center justify-center gap-8">
      <div className="p-8 bg-white rounded-lg shadow-md w-1/2 flex flex-col gap-2">
        <div className="flex flex-row justify-between w-full">
          <SquigglyText className="text-6xl text-black font-display">Select a Song</SquigglyText>
          <PushButton size="sm" onClick={() => setShowUploadForm(true)}>
            Make Your Own
          </PushButton>
        </div>
        <div className="flex flex-col gap-4">
          <div className="max-h-[400px] mx-[-20px] w-[calc(100%+40px)] overflow-y-auto px-6 py-4 mb-4">
            {songs.map(song => (
              <SongCard key={song.id} song={song} startGame={startGame} />
            ))}
          </div>
          <PushButton
            onClick={() => setShowSongSelect(false)}
            color="black"
            className="relative bg-black hover:bg-gray-800 text-white font-display text-2xl py-4 px-6 rounded-lg shadow-[4px_4px_0px_0px_rgba(255,255,255,0.3)] hover:shadow-[2px_2px_0px_0px_rgba(255,255,255,0.3)] active:shadow-[0px_0px_0px_0px_rgba(255,255,255,0.3)] transform hover:translate-y-0.5 active:translate-y-1 transition-all duration-150 [box-shadow:inset_0px_2px_8px_rgba(255,255,255,0.1)]"
          >
            Back
          </PushButton>
        </div>
      </div>
      {showUploadForm && (
        <div className="absolute top-0 left-0 w-screen h-screen bg-black/50 flex items-center justify-center">
          <BeatmapUpload />
        </div>
      )}
    </div>
  );
} 