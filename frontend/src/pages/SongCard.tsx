import PushButton from "../components/PushButton";


export interface Song {
    id: number;
    name: string;
    path: string;
    song: string;
    bpm: number;
    difficulty: number;
}

export default function SongCard({ song, startGame }: { song: Song, startGame: (id: number) => void }) {
  // Helper function to get difficulty color
  const getDifficultyColor = (diff: number) => {
    switch (diff) {
      case 1: return "bg-green-500";
      case 2: return "bg-blue-500";
      case 3: return "bg-yellow-500";
      case 4: return "bg-orange-500";
      case 5: return "bg-red-500";
      default: return "bg-gray-500";
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
    <PushButton
        align="left"
        key={song.id}
        onClick={() => startGame(song.id)}
        className="mb-4 last:mb-0 w-full"
    >
       <div className="w-full flex flex-row justify-between items-center">
        <div className="flex flex-col"> 
            <span className="text-2xl font-display">{song.name}</span>
            <span className="text-xl">{song.bpm} BPM</span>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className={`px-3 py-1 rounded-lg ${getDifficultyColor(song.difficulty)}`}>
            <span className="text-white font-bold">
              {getDifficultyText(song.difficulty)} {`★`.repeat(song.difficulty)}
            </span>
          </div>
        </div>
       </div>
    </PushButton>
  );
}