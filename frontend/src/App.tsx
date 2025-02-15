import './App.css'
import Track from './components/Track'

function App() {
  return (
    <div className="fixed inset-0 w-screen h-screen bg-[#E9967A] overflow-hidden">
      <div className="relative w-full h-screen bg-[#E9967A]">
        <div
          className="absolute w-full h-1.5 bg-black z-10"
          style={{ 
            top: '50%',
            left: '50%',
            transform: "translate(-50%, -50%) rotate(-167deg)"
          }}
        />
        <div className="absolute top-[50%] left-[0%] -translate-x-[0%] -translate-y-[75%] w-full z-10">
          <div className="relative flex justify-center">
            {/* 
              Using responsive width classes (e.g. 30vw) so that the cat scales with the window.
              You can adjust this value (30vw) to achieve your desired size.
            */}
            <img 
              src="/bongo_00.png" 
              style={{ width: `1000px` }}
              className="max-w-[400px]" 
              alt="Bongo cat" 
            />
          </div>
        </div>
      </div>
      <div 
        className="w-40 h-[64%] bg-blue-200 fixed bottom-[-9%] right-[60%] z-1 overflow-hidden"
        style={{
          transform: "rotate(13deg)",
          transformOrigin: "bottom center"
        }}
      >
          <Track position="left" text="Track 1" />
      </div>
      <div 
        className="w-40 h-[60%] bg-yellow-400 fixed bottom-[-13%] right-[40%] z-1 overflow-hidden"
        style={{
          transform: "rotate(13deg)",
          transformOrigin: "bottom center"
        }}
      >
          <Track position="right" text="Track 2" />
      </div>
    </div>
  )
}

export default App
