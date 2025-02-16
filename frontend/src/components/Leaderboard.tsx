import { useEffect, useState } from 'react';
import PushButton from './PushButton';

interface LeaderboardEntry {
  name: string;
  score: number;
  max_streak: number;
}

export default function Leaderboard({ onClose }: { onClose: () => void }) {
  const [scores, setScores] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/leaderboard')
      .then(res => res.json())
      .then(data => {
        setScores(data.scores);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching leaderboard:', err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="bg-gradient-to-b from-[#FFB07C] to-[#E88165] overflow-hidden flex items-center justify-center z-20">
      <div className="bg-white p-8 rounded-lg shadow-lg text-center max-w-2xl w-full">
        <h1 className="text-4xl font-display mb-6">Top Scores</h1>
        
        {loading ? (
          <p className="text-xl">Loading scores...</p>
        ) : (
          <div className="mb-6 overflow-y-auto max-h-[400px]">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="py-2 px-4 font-display text-center">Rank</th>
                  <th className="py-2 px-4 font-display text-left">Name</th>
                  <th className="py-2 px-4 font-display text-center">Score</th>
                  <th className="py-2 px-4 font-display text-center">Max Streak</th>
                </tr>
              </thead>
              <tbody>
                {scores.map((entry, index) => (
                  <tr key={index} className="border-b border-gray-100">
                    <td className="py-2 px-4 font-display text-center">{index + 1}</td>
                    <td className="py-2 px-4 font-display text-left">{entry.name}</td>
                    <td className="py-2 px-4 font-display text-center">{entry.score}</td>
                    <td className="py-2 px-4 font-display text-center">{entry.max_streak}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        <PushButton onClick={onClose} color="black">
          Back
        </PushButton>
      </div>
    </div>
  );
} 