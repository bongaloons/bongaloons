import BongoCat from "../components/BongoCat";
import { useContext, useEffect, useState } from "react";
import { Pose } from "../types";
import { GameContext } from "../context/GameContext";

export default function TitleScreen() {
    const [pose, setPose] = useState<Pose>('idle');
    const [keysPressed, setKeysPressed] = useState<Set<string>>(new Set());
    const { setShowSongSelect } = useContext(GameContext);

    useEffect(() => {
        const handleKeyPress = (event: KeyboardEvent) => {
            setKeysPressed(prev => {
                const newKeys = new Set(prev);
                newKeys.add(event.key);
                return newKeys;
            });
        };
        

        const handleKeyUp = (event: KeyboardEvent) => {
            setKeysPressed(prev => {
                const newKeys = new Set(prev);
                newKeys.delete(event.key);
                return newKeys;
            });
        };

        window.addEventListener('keydown', handleKeyPress);
        window.addEventListener('keyup', handleKeyUp);

        return () => {
            window.removeEventListener('keydown', handleKeyPress);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, []);

    useEffect(() => {
        if (keysPressed.has('a') && keysPressed.has('l')) {
            setPose('both');
        } else if (keysPressed.has('a')) {
            setPose('left');
        } else if (keysPressed.has('l')) {
            setPose('right');
        } else {
            setPose('idle');
        }
    }, [keysPressed]);

    return (
        <div className="w-screen h-screen bg-gradient-to-b from-[#FFB07C] to-[#E88165] overflow-hidden flex-col items-center justify-center gap-4">
            <div className="flex items-center justify-center">
                <img 
                    className="max-w-[800px] z-10 relative bottom-[-20%] right-[-10%]"
                    src="title.png" 
                    alt="Bongaloons" 
                    style={{
                        animation: 'titleImpact 0.5s ease-out forwards, titleRock 3s ease-in-out infinite 0.5s'
                    }}
                /> 
                <div className="relative bottom-[0 left-[-10%]">
                    <div className="mx-auto w-3/4 max-w-[800px]">
                        <BongoCat pose={pose} />
                    </div>
                </div>
            </div>
            <div className="flex flex-col gap-4 z-20 w-full items-center justify-center">
                <button 
                    className="w-64 bg-white hover:bg-gray-100 text-black font-semibold py-3 px-6 rounded-lg shadow-md transition-colors duration-200 text-2xl"
                    onClick={() => setShowSongSelect(true)}
                >
                    Start Game
                </button>
                <button 
                    className="w-64 bg-white hover:bg-gray-100 text-black font-semibold py-3 px-6 rounded-lg shadow-md transition-colors duration-200 text-2xl"
                >
                    Settings
                </button>
            </div>
        </div>
    )
}