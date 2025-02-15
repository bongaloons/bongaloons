export default function Judegment({ judgement }: { judgement: string }) {
    return (
        <div 
          key={judgement}
          className="absolute p-4 bg-white rounded-lg shadow-lg z-20 animate-fade-in-out"
          style={{
            top: `${Math.random() * 30 + 35}%`,
            left: `${Math.random() * 40 + 30}%`,
          }}
        >
          <pre className="text-2xl font-display">
            {judgement}
          </pre>
        </div>
    )
}