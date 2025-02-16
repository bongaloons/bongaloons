interface PushButtonProps {
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
  color?: 'white' | 'black';
  align?: 'center' | 'left' | 'right';
  size?: 'sm' | 'md' | 'lg';
}

export default function PushButton({ 
  onClick, 
  children, 
  className = '',
  color = 'white',
  align = 'center',
  size = 'md'
}: PushButtonProps) {
  const colorStyles = {
    white: {
      button: 'bg-[#eee] text-black',
      vars: {
        '--top-color': '#eee',
        '--bottom-color': '#999',
        '--right-color': '#ddd'
      } as React.CSSProperties
    },
    black: {
      button: 'bg-[#333] text-white',
      vars: {
        '--top-color': '#333',
        '--bottom-color': '#000',
        '--right-color': '#222'
      } as React.CSSProperties
    }
  };

  return (
    <button
      onClick={onClick}
      style={colorStyles[color].vars}
      className={`
        relative 
        ${size === 'sm' ? 'px-4 py-2 text-lg' : 'px-6 py-3 text-2xl'}
        font-bold font-display
        rounded-md border-0
        transition-all duration-200
        ${colorStyles[color].button}
        ${align === 'left' ? 'text-left' : align === 'right' ? 'text-right' : 'text-center'}
        shadow-[1px_0_0_var(--right-color),1px_1px_0_var(--bottom-color),2px_1px_0_var(--right-color),2px_2px_0_var(--bottom-color),3px_2px_0_var(--right-color),3px_3px_0_var(--bottom-color),4px_3px_0_var(--right-color),4px_4px_0_var(--bottom-color),5px_4px_0_var(--right-color),5px_5px_0_var(--bottom-color),6px_5px_0_var(--right-color),6px_6px_0_var(--bottom-color),-5px_20px_40px_-8px_#999]
        hover:shadow-[1px_0_0_var(--right-color),1px_1px_0_var(--bottom-color),2px_1px_0_var(--right-color),2px_2px_0_var(--bottom-color),3px_2px_0_var(--right-color),3px_3px_0_var(--bottom-color),4px_3px_0_var(--right-color),4px_4px_0_var(--bottom-color),-5px_5px_12px_-8px_#999]
        hover:translate-y-[3px] hover:translate-x-[3px]
        active:shadow-[1px_0_0_var(--right-color),1px_1px_0_var(--bottom-color)]
        active:translate-y-[5px] active:translate-x-[5px]
        ${className}
      `}
    >
      {children}
    </button>
  );
}
