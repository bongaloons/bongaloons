import './dvd-logo.css';

export default function DvdLogo() {
    return (
        <div 
            className="ball opacity-50"
            style={{
                '--width': '200px',
                '--height': '200px'
            } as React.CSSProperties}
        />
    )
}