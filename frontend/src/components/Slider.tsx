interface SliderProps {
    value: number;
    onChange: (value: number) => void;
    min?: number;
    max?: number;
    className?: string;
    ariaLabel?: string;
}

export default function Slider({ 
    value, 
    onChange, 
    min = 0, 
    max = 100,
    className = '',
    ariaLabel = 'Slider'
}: SliderProps) {
    return (
        <input
            type="range"
            min={min}
            max={max}
            value={value}
            className={`w-full h-2 bg-orange-100 rounded-full appearance-none cursor-pointer 
            dark:bg-orange-900/30 accent-orange-500 hover:accent-orange-600 
            transition-colors [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 
            [&::-webkit-slider-thumb]:rounded-sm [&::-moz-range-thumb]:w-4 
            [&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:rounded-sm 
            [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:bg-orange-500
            [&::-moz-range-thumb]:appearance-none [&::-moz-range-thumb]:bg-orange-500 ${className}`}
            aria-label={ariaLabel}
            onChange={(e) => onChange(Number(e.currentTarget.value))}
        />
    );
}
  