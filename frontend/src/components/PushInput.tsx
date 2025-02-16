interface PushInputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  className?: string;
  color?: 'white' | 'black';
  maxLength?: number;
}

export default function PushInput({
  value,
  onChange,
  placeholder = '',
  className = '',
  color = 'white',
  maxLength,
}: PushInputProps) {
  const colorStyles = {
    white: {
      input: 'bg-[#eee] text-black',
      vars: {
        '--top-color': '#eee',
        '--bottom-color': '#999',
        '--right-color': '#ddd'
      } as React.CSSProperties
    },
    black: {
      input: 'bg-[#333] text-white placeholder:text-gray-400',
      vars: {
        '--top-color': '#333',
        '--bottom-color': '#000',
        '--right-color': '#222'
      } as React.CSSProperties
    }
  };

  return (
    <input
      type="text"
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      maxLength={maxLength}
      style={colorStyles[color].vars}
      className={`
        relative 
        px-6 py-3
        text-2xl font-display
        rounded-md border-0
        transition-all duration-200
        outline-none
        ${colorStyles[color].input}
        shadow-[1px_0_0_var(--right-color),1px_1px_0_var(--bottom-color),2px_1px_0_var(--right-color),2px_2px_0_var(--bottom-color),3px_2px_0_var(--right-color),3px_3px_0_var(--bottom-color),4px_3px_0_var(--right-color),4px_4px_0_var(--bottom-color),-5px_8px_20px_-8px_#999]
        focus:shadow-[1px_0_0_var(--right-color),1px_1px_0_var(--bottom-color),2px_1px_0_var(--right-color),2px_2px_0_var(--bottom-color)]
        focus:translate-y-[2px] focus:translate-x-[2px]
        ${className}
      `}
    />
  );
} 