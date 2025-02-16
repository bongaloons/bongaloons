import { ReactNode } from 'react';

interface SquigglyTextProps {
  children: ReactNode;
  className?: string;
}

export default function SquigglyText({ children, className = '' }: SquigglyTextProps) {
  return (
    <>
      <svg style={{ position: 'absolute', width: 0, height: 0 }}>
        <defs>
          <filter id="squiggly-0">
            <feTurbulence baseFrequency="0.02" numOctaves="3" result="noise" seed="0"/>
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="6" />
          </filter>
          <filter id="squiggly-1">
            <feTurbulence baseFrequency="0.02" numOctaves="3" result="noise" seed="1"/>
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="8" />
          </filter>
          <filter id="squiggly-2">
            <feTurbulence baseFrequency="0.02" numOctaves="3" result="noise" seed="2"/>
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="6" />
          </filter>
          <filter id="squiggly-3">
            <feTurbulence baseFrequency="0.02" numOctaves="3" result="noise" seed="3"/>
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="8" />
          </filter>
          <filter id="squiggly-4">
            <feTurbulence baseFrequency="0.02" numOctaves="3" result="noise" seed="4"/>
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="6" />
          </filter>
        </defs>
      </svg>
      <span className={`animate-squiggly ${className}`}>
        {children}
      </span>
    </>
  );
} 