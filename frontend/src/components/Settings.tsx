import { useEffect, useState } from 'react';
import PushButton from './PushButton';
import SquigglyText from './SquigglyText';
import Slider from './Slider';

interface VolumeSettings {
  master: number;
  song: number;
  sfx: number;
}

export default function Settings({ onClose }: { onClose: () => void }) {
  const [volumes, setVolumes] = useState<VolumeSettings>(() => {
    const saved = localStorage.getItem('volumeSettings');
    return saved ? JSON.parse(saved) : {
      master: 100,
      song: 100,
      sfx: 100
    };
  });

  useEffect(() => {
    localStorage.setItem('volumeSettings', JSON.stringify(volumes));
  }, [volumes]);

  const handleVolumeChange = (type: keyof VolumeSettings, value: number) => {
    setVolumes(prev => ({
      ...prev,
      [type]: value
    }));
  };

  return (
    <div className="absolute top-0 left-0 w-screen h-screen bg-black/50 flex items-center justify-center z-20">
      <div className="bg-white p-8 rounded-lg w-[500px]">
        <SquigglyText className="text-4xl mb-6">Settings</SquigglyText>
        
        <div className="flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <label className="text-xl font-display">Master Volume: {volumes.master}%</label>
            <Slider 
              value={volumes.master}
              onChange={(value) => handleVolumeChange('master', value)}
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-xl font-display">Song Volume: {volumes.song}%</label>
            <Slider 
              value={volumes.song}
              onChange={(value) => handleVolumeChange('song', value)}
            />
            <span className="text-sm text-gray-500">
              Actual: {Math.round(volumes.song * volumes.master / 100)}%
            </span>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-xl font-display">SFX Volume: {volumes.sfx}%</label>
            <Slider 
              value={volumes.sfx}
              onChange={(value) => handleVolumeChange('sfx', value)}
            />
            <span className="text-sm text-gray-500">
              Actual: {Math.round(volumes.sfx * volumes.master / 100)}%
            </span>
          </div>

          <PushButton onClick={onClose} color="black">
            Close
          </PushButton>
        </div>
      </div>
    </div>
  );
} 