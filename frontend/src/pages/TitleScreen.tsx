import BongoCat from "../components/BongoCat";
import { useContext, useEffect, useState } from "react";
import { Pose } from "../types";
import { GameContext } from "../context/GameContext";
import PushButton from "../components/PushButton";
import DvdLogo from "../components/cosmetics/DvdLogo";
import Leaderboard from "../components/Leaderboard";
import { clearAudio, playSoundFile } from '../utils/audioPlayer';
import { getRandomOverlay } from "../utils/display";
import Settings from "../components/Settings";

const GIFS = [
    'gallery/cat-jump.gif',
    'gallery/pop-cat.gif',
    'gallery/thanksgiving.gif',
    'gallery/guitar-cat.gif',
    'gallery/cat-toast.gif',
    'gallery/dance-cat.gif',
    'gallery/sideeye-cat.gif',
];

export default function TitleScreen() {
    const [pose, setPose] = useState<Pose>('idle');
    const [keysPressed, setKeysPressed] = useState<Set<string>>(new Set());
    const [cats, setCats] = useState<Array<{ x: number, y: number, size: number }>>([]);
    const { setShowSongSelect } = useContext(GameContext);
    const PADDING = 50; // pixels from the edge where cats can't spawn
    const [currentGif, setCurrentGif] = useState<string>(GIFS[0]);
    const [showLeaderboard, setShowLeaderboard] = useState(false);
    const [audioUnlocked, setAudioUnlocked] = useState(false);
    const [showSettings, setShowSettings] = useState(false);

    // Unlock audio playback on the first user interaction.
    useEffect(() => {
      const unlockAudio = () => {
        if (!audioUnlocked) {
          clearAudio()
          playSoundFile('/sfx/title.ogg', "song")
            .then(() => {
              setAudioUnlocked(true);
            })
            .catch((err) => {
              console.error("Error playing sound on user interaction:", err);
            });
        }
      };
      // Use the { once: true } option so this listener auto-removes itself.
      window.addEventListener('click', unlockAudio, { once: true });
      return () => {
        window.removeEventListener('click', unlockAudio);
      };
    }, [audioUnlocked]);

    useEffect(() => {
        const interval = setInterval(() => {
            setTimeout(() => {
                setCurrentGif(GIFS[Math.floor(Math.random() * GIFS.length)]);
            }, 100);
        }, 3000);
        return () => clearInterval(interval);
    }, []);

    const spawnCat = (clientX: number, clientY: number) => {
        if (
            clientX < PADDING ||
            clientX > window.innerWidth - PADDING ||
            clientY < PADDING ||
            clientY > window.innerHeight - PADDING
        ) {
            return;
        }
        const x = (clientX / window.innerWidth) * 100;
        const y = (clientY / window.innerHeight) * 100;
        setCats(prevCats => [...prevCats, {
            x: 100 - x,
            y,
            size: Math.random() * 150 + 100,
        }]);
    };

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

    useEffect(() => {
        const initialNumberOfCats = Math.floor(Math.random() * 5) + 3;
        const newCats = Array.from({ length: initialNumberOfCats }, () => {
            const safeX = Math.random() * (window.innerWidth - 2 * PADDING) + PADDING;
            const safeY = Math.random() * (window.innerHeight - 2 * PADDING) + PADDING;
            return {
                x: (100 * safeX / window.innerWidth),
                y: (100 * safeY / window.innerHeight),
                size: Math.random() * 150 + 100,
            };
        });
        setCats(newCats);
    }, [PADDING]);

    // Periodic spawning of new cats
    useEffect(() => {
        console.log("Setting up periodic spawn interval");
        const spawnInterval = setInterval(() => {
            console.log("Checking for spawn");
            if (Math.random() < 0.3) {
                console.log("Spawning new cat");
                const safeX = Math.random() * (window.innerWidth - 2 * PADDING) + PADDING;
                const safeY = Math.random() * (window.innerHeight - 2 * PADDING) + PADDING;
                setCats(prevCats => [...prevCats, {
                    x: (100 * safeX / window.innerWidth),
                    y: (100 * safeY / window.innerHeight),
                    size: Math.random() * 150 + 100,
                }]);
            }
        }, 2000);
        return () => {
            console.log("Cleaning up interval");
            clearInterval(spawnInterval);
        };
    }, [PADDING]);

    useEffect(() => {
        const slapInterval = setInterval(() => {
            if (Math.random() < 0.4) {
                let slapCount = 0;
                const rapidSlaps = setInterval(() => {
                    const randomPose: Pose = ['left', 'right', 'both'][Math.floor(Math.random() * 3)] as Pose;
                    setPose(randomPose);
                    slapCount++;
                    if (slapCount > 10) {
                        clearInterval(rapidSlaps);
                        setPose('idle');
                    }
                }, 50);
                setPose('idle');
            }
        }, 1500);
        return () => {
            setPose('idle');
            clearInterval(slapInterval);
        };
    }, []);

    return (
        <div 
            className="w-screen h-screen bg-gradient-to-b from-[#FFB07C] to-[#E88165] overflow-hidden flex items-center justify-center gap-2"
            onClick={(e) => spawnCat(e.clientX, e.clientY)}
        >
            <DvdLogo />
            <div className="flex flex-col items-center justify-center">
                <img 
                    className="max-w-[800px] z-20 mb-[-15%]"
                    src="title.png" 
                    alt="Bongaloons" 
                    style={{
                        animation: 'titleImpact 0.5s ease-out forwards, titleRock 3s ease-in-out infinite 0.5s'
                    }}
                />
                <div className="w-full flex items-center justify-center py-8">
                    <div className="w-[500px] flex flex-col gap-4 items-center justify-center bg-white p-8 rounded-lg">
                        <div className="flex gap-4 items-center justify-center">
                            <PushButton
                                className="z-20"
                                onClick={() => setShowSongSelect(true)}
                            >
                                Start Game
                            </PushButton>
                            <PushButton className="z-20" onClick={() => setShowSettings(true)}>
                                Settings
                            </PushButton>
                        </div>
                        <PushButton color="black" align="right" className="z-20" onClick={() => setShowLeaderboard(!showLeaderboard)}>
                            {showLeaderboard ? "Hide Leaderboard" : "View Leaderboard"}
                        </PushButton>
                    </div>
                </div>
            </div>
            
            {cats.map((cat, index) => (
                <div 
                    key={index}
                    className="absolute"
                    style={{
                        top: `${cat.y}%`,
                        right: `${cat.x}%`,
                    }}
                >
                    <div style={{ width: `${cat.size}px` }}>
                        <BongoCat pose={pose} overlay={getRandomOverlay()} />
                    </div>
                </div>
            ))}

            <div className="flex items-center justify-center w-[800px] p-4 bg-white rounded-lg h-screen">
                {showLeaderboard ? (
                    <div className="w-full h-full flex items-center justify-center">
                        <Leaderboard onClose={() => setShowLeaderboard(false)} />
                    </div>
                ) : (
                    <img src={currentGif} className="w-full" alt="Animated Content" />
                )}
            </div>

            {showSettings && <Settings onClose={() => setShowSettings(false)} />}
        </div>
    );
}
