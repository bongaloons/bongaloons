import { useState } from 'react';
import { useContext } from 'react';
import { GameContext } from '../context/GameContext';
import PushButton from './PushButton';
import SquigglyText from './SquigglyText';

export default function BeatmapUpload({onSubmit}: {onSubmit: () => void}) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [difficulty, setDifficulty] = useState<number>(2);
  const { startGame, setShowSongSelect } = useContext(GameContext);

  const handleSubmit = async () => {
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('audio', file);

    try {
      const response = await fetch(`http://127.0.0.1:8000/beatmap/create?difficulty=${difficulty}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to create beatmap');
      }

      const data = await response.json();
      setShowSongSelect(true);
      onSubmit()
      
    } catch (error) {
      console.error('Error creating beatmap:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyText = (diff: number) => {
    switch (diff) {
      case 1: return "Easy";
      case 2: return "Normal";
      case 3: return "Hard";
      case 4: return "Expert";
      case 5: return "Master";
      default: return "Unknown";
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
            <label className="text-xl font-display">Difficulty</label>
            <div className="flex items-center gap-4">
              <div className="rating">
                <input type="radio" name="rating" value="5" id="rate5" onChange={() => setDifficulty(5)} checked={difficulty === 5} className="hidden" />
                <label htmlFor="rate5">★</label>
                <input type="radio" name="rating" value="4" id="rate4" onChange={() => setDifficulty(4)} checked={difficulty === 4} className="hidden" />
                <label htmlFor="rate4">★</label>
                <input type="radio" name="rating" value="3" id="rate3" onChange={() => setDifficulty(3)} checked={difficulty === 3} className="hidden" />
                <label htmlFor="rate3">★</label>
                <input type="radio" name="rating" value="2" id="rate2" onChange={() => setDifficulty(2)} checked={difficulty === 2} className="hidden" />
                <label htmlFor="rate2">★</label>
                <input type="radio" name="rating" value="1" id="rate1" onChange={() => setDifficulty(1)} checked={difficulty === 1} className="hidden" />
                <label htmlFor="rate1">★</label>
              </div>
              <span className="text-xl font-display w-32">
                {getDifficultyText(difficulty)}
              </span>
            </div>
            <div className="text-sm text-gray-600 mt-1">
              Higher difficulty = more notes and complexity
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