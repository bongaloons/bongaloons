const JUDGEMENT_CAT_GIFS: Record<string, string[]> = {
  'PERFECT': ['/gallery/cat-jump.gif', '/gallery/cat-toast.gif', '/gallery/cat-yelled.gif'],
  'GOOD': ['/gallery/cat-jump.gif', '/gallery/cat-toast.gif'],
  'BAD': ['/gallery/cat-yelled.gif', '/gallery/sideeye-cat.gif'],
  'MISS': ['/gallery/angry-cat.gif', '/gallery/sad-thumbsup.gif']
};

export function judgementToString(judgement: string): string {
  if (judgement.startsWith("perfect")) return "PERFECT";
  if (judgement.startsWith("good")) return "GOOD";
  if (judgement.startsWith("meh")) return "MEH";
  if (judgement.startsWith("bad")) return "BAD";
  if (judgement === "MISS") return "MISS";
  if (judgement === "OOPS") return "OOPS";
  return judgement;
}

export function judgementToColor(judgement: string): string {
  if (judgement.startsWith("perfect")) return "#FFD700"; // Gold
  if (judgement.startsWith("good")) return "#00FF00";    // Green
  if (judgement.startsWith("meh")) return "#87CEEB";     // Sky Blue
  if (judgement.startsWith("bad")) return "#FFA500";     // Orange
  if (judgement === "MISS") return "#FF0000";           // Red
  if (judgement === "OOPS") return "#FF69B4";          // Pink
  return "#000000";                                     // Default black
}

export default function BigJudgement({ judgement }: { judgement: string }) {
    return (
        <div 
          className="fixed inset-0 flex items-center justify-center pointer-events-none pb-75"
          style={{
            zIndex: 10
          }}
        >
          <div 
            key={`${judgement}-${Date.now()}`}
            className="animate-slide-across"
          >
            <img src={
              JUDGEMENT_CAT_GIFS[judgement]?.[Math.floor(Math.random() * (JUDGEMENT_CAT_GIFS[judgement]?.length || 1))] || '/cats/default.gif'
            } className="w-[300px] h-[300px] opacity-50" />
          </div>
          <pre 
            className="text-[300px]"
            style={{
              transform: "rotate(13deg)",
              whiteSpace: "nowrap",
              color: judgementToColor(judgement),
              textShadow: `
                -4px -4px 0 #FFF,  
                4px -4px 0 #FFF,
                -4px 4px 0 #FFF,
                4px 4px 0 #FFF`
            }}
          >
            {judgementToString(judgement || "...")}
          </pre>
        </div>
    )
}