import { useState } from 'react';
import { useContext } from 'react';
import { GameContext } from '../context/GameContext';
import PushButton from './PushButton';
import SquigglyText from './SquigglyText';

export default function BeatmapUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [noteCount, setNoteCount] = useState<number>(100);
  const { startGame, setShowSongSelect } = useContext(GameContext);

  const handleSubmit = async () => {
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('audio', file);
    formData.append('max_notes', noteCount.toString());

    try {
      const response = await fetch('http://127.0.0.1:8000/beatmap/create', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to create beatmap');
      }

      const data = await response.json();
      // Instead of starting the game, close the upload form and let SongSelect refresh
      setShowSongSelect(true);
      
    } catch (error) {
      console.error('Error creating beatmap:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 bg-white rounded-lg shadow-md w-1/2">
      <div className="flex flex-col gap-6">
        <SquigglyText className="text-6xl text-black font-display">
          Create Your Beatmap
        </SquigglyText>
        
        <form onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }} 
          className="flex flex-col gap-4"
        >
          <div className="flex flex-col gap-2">
            <label className="text-xl font-display">Upload MP3 File</label>
            <input
              type="file"
              accept=".mp3"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="file-input file-input-bordered file-input-lg w-full 
                bg-gradient-to-r from-red-500 to-orange-500 text-white
                hover:from-red-600 hover:to-orange-600 transition-all
                file:mr-4 file:py-2 file:px-4
                file:rounded-full file:border-0
                file:text-sm file:font-semibold
                file:bg-red-50 file:text-red-700
                hover:file:bg-red-100 p-4"
              required
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-xl font-display">Number of Notes</label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="20"
                max="1000"
                value={noteCount}
                onChange={(e) => setNoteCount(parseInt(e.target.value))}
                className="range range-lg range-primary flex-1"
              />
              <span className="text-xl font-display w-20 text-center">
                {noteCount}
              </span>
            </div>
            <div className="text-sm text-gray-600 mt-1">
              More notes = higher difficulty. Recommended: 50-200 notes
            </div>
          </div>
          
          <div className="flex flex-row gap-4">
            <PushButton
              disabled={loading || !file}
              className="flex-1"
              type="submit"
            >
              {loading ? 'Creating...' : 'Create Beatmap'}
            </PushButton>
            
            <PushButton
              onClick={() => setShowSongSelect(true)}
              color="black"
              className="flex-1"
              type="button"
            >
              Back to Songs
            </PushButton>
          </div>
        </form>
      </div>
    </div>
  );
} 