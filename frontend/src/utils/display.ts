
const OVERLAYS = [
    "accessory/bday.png",
    "accessory/monocle.png",
    "accessory/stache.png",
    "accessory/wig.png",
]
export function getRandomOverlay(): string | undefined {
    if (Math.random() < 0.5) {
        return undefined;
    }
    return OVERLAYS[Math.floor(Math.random() * OVERLAYS.length)];
}

