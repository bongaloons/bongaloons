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
          <pre 
            className="text-[300px] font-broken"
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