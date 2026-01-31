import React, { useState, useEffect, useRef } from 'react';
import { 
  Mic, 
  Play, 
  Cpu, 
  Zap, 
  Globe, 
  ArrowDown,
  Hexagon,
  ChevronRight,
  Activity,
  Wind,
  Sun,
  Moon,
  Square,
  Box,
  Layers,
  Settings,
  Plus,
  Save,
  Trash2,
  UploadCloud,
  Volume2,
  X
} from 'lucide-react';

// --- ESTILOS GLOBAIS E ANIMAÇÕES (CSS IN JS) ---
const GlobalStyles = ({ theme }) => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;700;800&display=swap');

    :root {
      /* Paleta Refinada - High Contrast Tech */
      --bg-primary: ${theme === 'dark' ? '#09090b' : '#e4e4e7'}; 
      --bg-secondary: ${theme === 'dark' ? '#000000' : '#f4f4f5'}; 
      --text-primary: ${theme === 'dark' ? '#ffffff' : '#09090b'};
      --text-secondary: ${theme === 'dark' ? '#a1a1aa' : '#52525b'};
      --border-color: ${theme === 'dark' ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.15)'};
      --accent: #7c3aed; 
      --accent-glow: ${theme === 'dark' ? 'rgba(124, 58, 237, 0.5)' : 'rgba(124, 58, 237, 0.3)'};
      
      --depth-color: ${theme === 'dark' ? '#4c1d95' : '#c4b5fd'};
    }

    body {
      background-color: var(--bg-primary);
      color: var(--text-primary);
      font-family: 'Space Grotesk', sans-serif;
      overflow: hidden;
      transition: background-color 0.8s ease, color 0.8s ease;
      cursor: default;
    }

    /* Scroll Snapping */
    .snap-container {
      scroll-snap-type: y mandatory;
      overflow-y: scroll;
      height: 100vh;
      scroll-behavior: smooth;
    }

    .snap-section {
      scroll-snap-align: start;
      height: 100vh;
      width: 100vw;
      position: relative;
      overflow: hidden;
    }

    /* Animações */
    .reveal-text {
      transform: translateY(100%);
      opacity: 0;
      transition: transform 1.2s cubic-bezier(0.22, 1, 0.36, 1), opacity 1.2s ease-out;
      will-change: transform, opacity;
    }

    .active .reveal-text {
      transform: translateY(0);
      opacity: 1;
    }

    .fade-scale {
      opacity: 0;
      transform: scale(0.95);
      transition: all 1.2s cubic-bezier(0.22, 1, 0.36, 1);
    }

    .active .fade-scale {
      opacity: 1;
      transform: scale(1);
    }

    .glass-panel {
      background: ${theme === 'dark' ? 'rgba(10, 10, 10, 0.6)' : 'rgba(255, 255, 255, 0.7)'};
      backdrop-filter: blur(16px);
      border: 1px solid var(--border-color);
      border-radius: 0px; 
    }

    .magnetic-btn {
      transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1);
    }
    .magnetic-btn:hover {
      transform: translateY(-2px);
      box-shadow: 4px 4px 0px var(--text-primary);
    }

    .no-scrollbar::-webkit-scrollbar { display: none; }
    .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    
    .extruded-text {
      text-shadow: 
        1px 1px 0px var(--depth-color),
        2px 2px 0px var(--depth-color),
        3px 3px 0px var(--depth-color),
        4px 4px 0px var(--depth-color),
        5px 5px 0px var(--depth-color),
        6px 6px 0px var(--depth-color),
        0px 20px 40px rgba(0,0,0,0.4);
    }

    /* Hover Center-Out Effect */
    .hover-center-out {
      position: relative;
      overflow: hidden;
    }
    .hover-center-out::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: var(--text-primary);
      transform: scaleX(0);
      transform-origin: center;
      transition: transform 0.5s cubic-bezier(0.22, 1, 0.36, 1);
      z-index: -1;
    }
    .hover-center-out:hover::before {
      transform: scaleX(1);
    }
    .hover-center-out:hover {
      color: var(--bg-primary);
      border-color: var(--text-primary);
    }

    /* Grid Cell Animation Logic */
    .grid-cell {
      border: 1px solid var(--border-color);
      background: transparent;
      transition: background-color 1.5s ease, border-color 1.5s ease;
    }
    .grid-cell:hover {
      background-color: var(--accent-glow);
      border-color: var(--accent);
      transition: background-color 0s, border-color 0s;
      box-shadow: 0 0 15px var(--accent-glow);
      z-index: 1;
    }
    
    /* Input Custom Styles */
    .tech-input {
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-primary);
      padding: 1rem;
      font-family: 'Space Grotesk', sans-serif;
      width: 100%;
      outline: none;
      transition: border-color 0.3s;
    }
    .tech-input:focus {
      border-color: var(--accent);
    }

    /* Animations Utility */
    .animate-fade-in-up {
      animation: fadeInUp 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }
    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade-in {
      animation: fadeIn 0.5s ease forwards;
    }
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
  `}</style>
);

// --- COMPONENTES AUXILIARES ---

const SacredGeometry = ({ activeIndex, theme, minimal = false }) => {
  if (minimal) {
      return (
        <div className="fixed inset-0 pointer-events-none z-0 flex items-center justify-center overflow-hidden transition-all duration-1000">
           <div className="absolute inset-0 opacity-10" 
             style={{ 
               backgroundImage: `linear-gradient(var(--border-color) 1px, transparent 1px), linear-gradient(90deg, var(--border-color) 1px, transparent 1px)`,
               backgroundSize: '40px 40px'
             }} 
           />
           <div className="absolute top-10 right-10 w-[40vh] h-[40vh] border border-[var(--border-color)] opacity-20 rotate-45" />
        </div>
      )
  }

  const shapes = [
    { rotate: 45, scale: 1, border: '1px solid', borderRadius: '0%' }, 
    { rotate: 0, scale: 1.5, border: '1px dashed', borderRadius: '50%' }, 
    { rotate: 20, scale: 0.8, border: '2px dotted', borderRadius: '0%' }, 
    { rotate: 90, scale: 1.2, border: '1px solid', borderRadius: '10%' }, 
    { rotate: 180, scale: 0.5, border: '4px double', borderRadius: '50%' }, 
  ];

  const currentShape = shapes[activeIndex] || shapes[0];

  return (
    <div className="fixed inset-0 pointer-events-none z-0 flex items-center justify-center overflow-hidden transition-all duration-1000">
      <div className="absolute inset-0 opacity-20" 
           style={{ 
             backgroundImage: `linear-gradient(var(--border-color) 1px, transparent 1px), linear-gradient(90deg, var(--border-color) 1px, transparent 1px)`,
             backgroundSize: activeIndex % 2 === 0 ? '100px 100px' : '50px 50px', 
             transition: 'background-size 1s ease'
           }} 
      />
      
      <div 
        className="absolute w-[60vh] h-[60vh] border-[var(--border-color)] transition-all duration-[1500ms] ease-[cubic-bezier(0.22,1,0.36,1)]"
        style={{ 
          transform: `translate(-50%, -50%) rotate(${activeIndex * 45 + currentShape.rotate}deg) scale(${currentShape.scale})`,
          border: `1px solid var(--border-color)`,
          borderRadius: currentShape.borderRadius,
          left: '50%',
          top: '50%'
        }}
      >
        <div className="absolute inset-4 border border-[var(--border-color)] opacity-50 transition-all duration-1000"
             style={{ borderRadius: currentShape.borderRadius }} />
        <div className={`absolute top-1/2 left-0 w-full h-px bg-[var(--border-color)] transition-opacity duration-1000 ${activeIndex % 2 === 0 ? 'opacity-30' : 'opacity-0'}`} />
        <div className={`absolute top-0 left-1/2 w-px h-full bg-[var(--border-color)] transition-opacity duration-1000 ${activeIndex % 2 === 0 ? 'opacity-30' : 'opacity-0'}`} />
      </div>
    </div>
  );
};

const NavigationDots = ({ total, active, scrollTo }) => (
  <div className="fixed right-8 top-1/2 transform -translate-y-1/2 z-50 flex flex-col gap-8 mix-blend-difference">
    {Array.from({ length: total }).map((_, i) => (
      <button
        key={i}
        onClick={() => scrollTo(i)}
        className="group flex items-center justify-end gap-4"
      >
        <span className={`text-[10px] font-bold uppercase tracking-widest transition-all duration-500 ${active === i ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-4'} text-white`}>
          {['Zero', 'Demo', 'Core', 'Plan', 'Link'][i]}
        </span>
        <div 
          className={`w-3 h-3 transition-all duration-700 border border-white 
            ${active === i ? 'bg-white rotate-0 scale-110' : 'bg-transparent rotate-45 group-hover:rotate-[20deg] group-hover:bg-white/20'}
          `} 
        />
      </button>
    ))}
  </div>
);

const Interactive3DText = ({ theme }) => {
  const containerRef = useRef(null);
  const textRef = useRef(null);
  const targetTilt = useRef({ x: 0, y: 0 });
  const currentTilt = useRef({ x: 0, y: 0 });
  const cellCount = 600; 

  useEffect(() => {
    const handleGlobalMove = (e) => {
      const x = (e.clientX / window.innerWidth) * 2 - 1;
      const y = (e.clientY / window.innerHeight) * 2 - 1;
      targetTilt.current = { x, y };
    };

    window.addEventListener('mousemove', handleGlobalMove);
    
    let rafId;
    const animate = () => {
      currentTilt.current.x += (targetTilt.current.x - currentTilt.current.x) * 0.03;
      currentTilt.current.y += (targetTilt.current.y - currentTilt.current.y) * 0.03;

      if (textRef.current) {
        const rotateX = currentTilt.current.y * -25;
        const rotateY = currentTilt.current.x * 25;
        textRef.current.style.transform = `
          perspective(1000px) 
          rotateX(${rotateX}deg) 
          rotateY(${rotateY}deg) 
          scale(1.1)
        `;
      }
      rafId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      window.removeEventListener('mousemove', handleGlobalMove);
      cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <div 
      ref={containerRef}
      className="relative w-full h-[60vh] flex items-center justify-center rounded-none border border-[var(--border-color)] bg-[var(--bg-secondary)] overflow-hidden group transition-colors duration-500"
    >
      <div 
         className="absolute inset-0 grid grid-cols-[repeat(auto-fill,minmax(40px,1fr))] opacity-50 pointer-events-auto"
         style={{ transform: 'scale(1.05)' }} 
      >
        {Array.from({ length: cellCount }).map((_, i) => (
          <div key={i} className="grid-cell" />
        ))}
      </div>
      <h2 
        ref={textRef}
        className="text-[12vw] font-bold leading-none tracking-tighter select-none will-change-transform extruded-text z-10 pointer-events-none relative"
        style={{ color: 'var(--text-primary)' }}
      >
        AETHER
      </h2>
    </div>
  )
}

// --- LANDING SECTIONS (RESTAURADOS) ---

const HeroSection = ({ active }) => (
  <section className={`snap-section flex flex-col items-center justify-center text-center p-6 ${active ? 'active' : ''}`}>
    <div className="reveal-text transition-delay-200 mb-8">
      <div className="inline-flex items-center gap-3 px-4 py-1 border border-[var(--border-color)] bg-[var(--bg-secondary)] backdrop-blur-md">
        <span className="w-2 h-2 bg-green-500 animate-pulse" />
        <span className="text-xs font-mono uppercase tracking-widest text-[var(--text-secondary)]">Sys v2.6.0</span>
      </div>
    </div>
    
    <h1 className="text-6xl md:text-9xl font-extrabold leading-none tracking-tighter mb-8 overflow-hidden">
      <div className="reveal-text" style={{ transitionDelay: '0.2s' }}>AETHER</div>
      <div className="reveal-text text-transparent bg-clip-text bg-gradient-to-r from-[var(--accent)] via-[var(--text-primary)] to-[var(--accent)] bg-300% animate-gradient pb-4" style={{ transitionDelay: '0.4s' }}>
        STUDIO
      </div>
    </h1>

    <div className="max-w-2xl mx-auto overflow-hidden mb-12">
      <p className="text-[var(--text-secondary)] text-lg md:text-xl font-light reveal-text leading-relaxed" style={{ transitionDelay: '0.6s' }}>
        Síntese neural de precisão. Geometria vocal renderizada em latência zero.
      </p>
    </div>

    <div className="flex gap-6 overflow-hidden">
      <div className="reveal-text" style={{ transitionDelay: '0.8s' }}>
        <button className="magnetic-btn px-10 py-5 bg-[var(--text-primary)] text-[var(--bg-primary)] font-bold tracking-wide flex items-center gap-3 rounded-none hover:bg-[var(--accent)] hover:text-white transition-colors">
          INICIAR SISTEMA <Square size={10} fill="currentColor" />
        </button>
      </div>
    </div>
  </section>
);

const DemoSection = ({ active }) => {
  const [playing, setPlaying] = useState(false);
  
  return (
    <section className={`snap-section flex items-center justify-center p-6 ${active ? 'active' : ''}`}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 w-full max-w-7xl items-center">
        
        <div className="space-y-10 order-2 lg:order-1">
          <div className="overflow-hidden">
             <h2 className="text-5xl md:text-7xl font-bold reveal-text tracking-tighter">
               F5-TTS <br/> <span className="text-[var(--accent)]">ENGINE</span>
             </h2>
          </div>
          <div className="overflow-hidden">
            <p className="text-xl text-[var(--text-secondary)] pl-6 border-l-4 border-[var(--accent)] reveal-text" style={{ transitionDelay: '0.3s' }}>
              Zero-shot cloning (6s).
              <br/>Controle emocional vetorial.
              <br/>Latência ~200ms.
            </p>
          </div>
          
          <div className="grid grid-cols-2 gap-px bg-[var(--border-color)] border border-[var(--border-color)] fade-scale" style={{ transitionDelay: '0.5s' }}>
             <div className="p-8 bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] transition-colors group">
               <Cpu size={32} className="text-[var(--text-primary)] mb-4" />
               <h3 className="font-bold text-lg mb-1">ROCm 6.2</h3>
               <p className="text-sm text-[var(--text-secondary)]">AMD Native Accel</p>
             </div>
             <div className="p-8 bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] transition-colors group">
               <Globe size={32} className="text-[var(--text-primary)] mb-4" />
               <h3 className="font-bold text-lg mb-1">Polyglot</h3>
               <p className="text-sm text-[var(--text-secondary)]">PT • EN • ES • ZH</p>
             </div>
          </div>
        </div>

        <div className="fade-scale relative order-1 lg:order-2" style={{ transitionDelay: '0.6s' }}>
          <div className="relative glass-panel p-8 md:p-12 shadow-2xl">
            <div className="absolute top-4 right-4 flex gap-2">
              <div className="w-2 h-2 bg-red-500 rounded-none" />
              <div className="w-2 h-2 bg-yellow-500 rounded-none" />
              <div className="w-2 h-2 bg-green-500 rounded-none" />
            </div>
            
            <div className="flex items-center gap-6 mb-12 relative z-10 pt-4">
               <div className="w-16 h-16 bg-[var(--accent)] flex items-center justify-center font-bold text-white text-xl shadow-lg">JP</div>
               <div>
                 <div className="font-bold text-xl uppercase">João Paulo</div>
                 <div className="text-sm text-[var(--accent)] font-mono mt-1">● REC • 16ms</div>
               </div>
            </div>

            <div className="space-y-6 mb-12 relative z-10">
              <div className="flex items-end justify-between gap-1 h-16 border-b border-[var(--border-color)] pb-2">
                {Array.from({length: 30}).map((_, i) => (
                  <div 
                    key={i} 
                    className="w-1.5 bg-[var(--text-primary)] transition-all duration-100 ease-in-out"
                    style={{ 
                      height: playing ? `${Math.random() * 100}%` : '10%',
                      opacity: playing ? 1 : 0.2
                    }} 
                  />
                ))}
              </div>
            </div>

            <button 
              onClick={() => setPlaying(!playing)}
              className="w-full py-6 border border-[var(--text-primary)] text-[var(--text-primary)] hover:bg-[var(--text-primary)] hover:text-[var(--bg-primary)] font-bold flex items-center justify-center gap-4 transition-all relative z-10"
            >
              {playing ? 'PROCESSANDO STREAM...' : <><Play fill="currentColor" size={20} /> INICIAR DEMO</>}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

const StackSection = ({ active }) => (
  <section className={`snap-section flex flex-col items-center justify-center ${active ? 'active' : ''}`}>
    <div className="w-full max-w-7xl px-6">
      <div className="overflow-hidden mb-20 text-center">
        <h2 className="text-[12vw] font-bold opacity-5 uppercase select-none absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 pointer-events-none whitespace-nowrap">
          SYSTEM
        </h2>
        <h2 className="text-4xl md:text-5xl font-bold reveal-text relative z-10 tracking-widest">ARCHITECTURE</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 fade-scale" style={{ transitionDelay: '0.3s' }}>
        {[
          { title: "Inference", val: "F5-TTS", icon: Mic },
          { title: "Morphing", val: "RVC v2", icon: Globe },
          { title: "API", val: "FastAPI", icon: Zap },
          { title: "Hardware", val: "RX 7800XT", icon: Cpu },
        ].map((item, i) => (
          <div key={i} className="glass-panel p-10 flex flex-col items-center text-center hover:bg-[var(--text-primary)] hover:text-[var(--bg-primary)] transition-colors duration-300 group cursor-crosshair">
            <div className="mb-6 group-hover:scale-110 transition-transform duration-300">
               <item.icon size={32} strokeWidth={1.5} />
            </div>
            <div className="text-xs font-mono uppercase tracking-widest opacity-60 mb-2 group-hover:opacity-100">{item.title}</div>
            <div className="text-2xl font-bold">{item.val}</div>
          </div>
        ))}
      </div>
    </div>
  </section>
);

const PricingSection = ({ active }) => (
  <section className={`snap-section flex flex-col items-center justify-center p-6 ${active ? 'active' : ''}`}>
    <div className="max-w-7xl w-full grid grid-cols-1 md:grid-cols-2 gap-20 items-center">
      <div className="space-y-8">
        <div className="overflow-hidden">
          <h2 className="text-6xl font-bold reveal-text tracking-tighter">ESCALA <br/>REAL</h2>
        </div>
        <div className="overflow-hidden">
          <p className="text-xl text-[var(--text-secondary)] reveal-text leading-relaxed" style={{ transitionDelay: '0.2s' }}>
            Créditos on-demand.
            <br/>Gateway Local (Mercado Pago).
            <br/>Sem lock-in.
          </p>
        </div>
      </div>

      <div className="relative fade-scale group" style={{ transitionDelay: '0.4s' }}>
        <div className="absolute -inset-2 bg-[var(--accent)] opacity-20 blur-xl group-hover:opacity-40 transition-opacity duration-500" />
        
        <div className="relative bg-[var(--bg-secondary)] border border-[var(--border-color)] p-12">
          <div className="flex justify-between items-start mb-8">
            <div>
              <h3 className="text-3xl font-bold mb-2">Creator Pro</h3>
              <p className="text-[var(--text-secondary)] font-mono text-xs uppercase">Tier 01 - Alpha</p>
            </div>
            <span className="px-3 py-1 bg-[var(--accent)] text-white text-xs font-bold uppercase tracking-wider">
              Popular
            </span>
          </div>
          
          <div className="text-7xl font-bold mb-8 flex items-baseline tracking-tighter">
            <span className="text-3xl align-top mr-1">R$</span>99
            <span className="text-lg text-[var(--text-secondary)] font-normal ml-2">/mês</span>
          </div>

          <div className="h-px w-full bg-[var(--border-color)] mb-8" />

          <ul className="space-y-5 mb-10">
            {['5.000 Créditos', 'Fila Prioritária', 'Clone Instantâneo', 'API Access Key'].map((feat, i) => (
              <li key={i} className="flex items-center gap-4 text-sm font-bold uppercase tracking-wide">
                <div className="w-4 h-4 bg-[var(--text-primary)] text-[var(--bg-primary)] flex items-center justify-center text-[10px]">✓</div>
                {feat}
              </li>
            ))}
          </ul>

          <button className="w-full py-5 border border-[var(--text-primary)] text-[var(--text-primary)] font-bold uppercase tracking-widest hover-center-out z-10 transition-colors">
            <span className="relative z-10">Assinar Plano</span>
          </button>
        </div>
      </div>
    </div>
  </section>
);

const FooterSection = ({ active, theme }) => (
  <section className={`snap-section flex flex-col justify-between p-10 md:p-20 bg-[var(--bg-secondary)] ${active ? 'active' : ''}`}>
    <div className="flex-1 flex flex-col justify-center items-center w-full max-w-5xl mx-auto">
      <div className="fade-scale w-full mb-12" style={{ transitionDelay: '0.2s' }}>
        <Interactive3DText theme={theme} />
      </div>
      
      <div className="flex gap-12 reveal-text z-10">
        <a href="#" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors uppercase tracking-widest text-xs font-bold hover-center-out px-2 py-1">Github</a>
        <a href="#" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors uppercase tracking-widest text-xs font-bold hover-center-out px-2 py-1">Discord</a>
        <a href="#" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors uppercase tracking-widest text-xs font-bold hover-center-out px-2 py-1">Docs</a>
      </div>
    </div>
    
    <div className="flex justify-between items-end border-t border-[var(--border-color)] pt-8 reveal-text opacity-50" style={{ transitionDelay: '0.4s' }}>
      <p className="text-xs font-mono">© 2026 AETHER LABS.</p>
      <div className="text-right">
        <p className="text-xs font-bold uppercase">São Paulo, BR</p>
      </div>
    </div>
  </section>
);

// --- DASHBOARD COMPONENTS ---

const DashboardSidebar = ({ activeTab, setActiveTab, onLogout }) => {
  const menuItems = [
    { id: 'library', label: 'Vozes', icon: Layers },
    { id: 'studio', label: 'Estúdio', icon: Mic },
    { id: 'api', label: 'API', icon: Cpu },
  ];

  return (
    <div className="w-20 h-screen border-r border-[var(--border-color)] bg-[var(--bg-secondary)] flex flex-col items-center py-8 z-50">
      <div className="mb-12">
         <Box className="text-[var(--text-primary)]" size={32} strokeWidth={2} />
      </div>

      <nav className="flex-1 flex flex-col gap-6 w-full px-2">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full aspect-square flex items-center justify-center transition-all duration-300 group relative ${
              activeTab === item.id 
                ? 'bg-[var(--text-primary)] text-[var(--bg-primary)]' 
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--border-color)]'
            }`}
          >
            <item.icon size={24} />
            {activeTab === item.id && (
              <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-1 bg-[var(--accent)]" />
            )}
          </button>
        ))}
      </nav>

      <button onClick={onLogout} className="mt-auto text-[var(--text-secondary)] hover:text-red-500 p-4">
        <Wind size={20} />
      </button>
    </div>
  );
};

const VoiceCard = ({ voice, onClick }) => (
  <div 
    onClick={onClick}
    className="group relative aspect-square glass-panel p-6 flex flex-col justify-between cursor-pointer hover:border-[var(--accent)] transition-all duration-500"
  >
    <div className="flex justify-between items-start">
      <div className={`w-10 h-10 flex items-center justify-center font-bold text-lg bg-[var(--text-primary)] text-[var(--bg-primary)]`}>
        {voice.initials}
      </div>
      <div className="opacity-0 group-hover:opacity-100 transition-opacity">
        <Settings size={18} className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]" />
      </div>
    </div>

    <div className="space-y-2">
      <div className="flex items-center gap-2 h-8">
        {/* Fake Waveform Animation */}
        {[...Array(10)].map((_, i) => (
          <div 
            key={i} 
            className="w-1 bg-[var(--accent)] opacity-50 group-hover:opacity-100 transition-all"
            style={{ 
              height: `${Math.random() * 100}%`,
              transitionDelay: `${i * 50}ms`
            }} 
          />
        ))}
      </div>
      <h3 className="font-bold text-xl uppercase tracking-tight">{voice.name}</h3>
      <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-secondary)]">
        <span>{voice.lang}</span>
        <span>•</span>
        <span>{voice.tags[0]}</span>
      </div>
    </div>

    {/* Hover Effect Background */}
    <div className="absolute inset-0 bg-[var(--accent)] opacity-0 group-hover:opacity-5 transition-opacity duration-500 pointer-events-none" />
  </div>
);

const VoiceEditor = ({ voice, onClose }) => {
  const [refText, setRefText] = useState(voice?.refText || "O texto de referência original apareceria aqui para garantir o alinhamento perfeito do F5-TTS.");
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <div className="h-full flex flex-col animate-fade-in">
      <div className="flex justify-between items-center mb-8 pb-4 border-b border-[var(--border-color)]">
        <h2 className="text-3xl font-bold uppercase flex items-center gap-4">
          <button onClick={onClose} className="hover:text-[var(--accent)] transition-colors">
            <ChevronRight className="rotate-180" size={32} />
          </button>
          Editor de Voz <span className="text-[var(--text-secondary)] text-sm ml-2 font-mono">{voice ? 'EDIT MODE' : 'CREATE MODE'}</span>
        </h2>
        <div className="flex gap-4">
          <button className="px-6 py-3 border border-red-500/30 text-red-500 hover:bg-red-500 hover:text-white transition-colors uppercase font-bold text-xs tracking-wider flex items-center gap-2">
            <Trash2 size={16} /> Excluir
          </button>
          <button className="px-6 py-3 bg-[var(--text-primary)] text-[var(--bg-primary)] hover:bg-[var(--accent)] hover:text-white transition-colors uppercase font-bold text-xs tracking-wider flex items-center gap-2">
            <Save size={16} /> Salvar Perfil
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 h-full overflow-y-auto">
        {/* Coluna Esquerda: Dados Básicos */}
        <div className="lg:col-span-4 space-y-8">
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Nome da Voz</label>
            <input type="text" defaultValue={voice?.name} className="tech-input" placeholder="Ex: Narrador Corporativo" />
          </div>

          <div className="space-y-2">
             <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Avatar / Cor</label>
             <div className="flex gap-4">
               {['#7c3aed', '#10b981', '#f59e0b', '#ef4444'].map(color => (
                 <button key={color} className="w-10 h-10 border border-[var(--border-color)] hover:scale-110 transition-transform" style={{ backgroundColor: color }} />
               ))}
             </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Tags de Estilo</label>
            <div className="flex flex-wrap gap-2">
              {['Neutro', 'Corporativo', 'Sussurro', 'Rápido'].map(tag => (
                <span key={tag} className="px-3 py-1 border border-[var(--border-color)] text-xs uppercase hover:border-[var(--accent)] cursor-pointer transition-colors">
                  {tag}
                </span>
              ))}
              <button className="w-6 h-6 flex items-center justify-center border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
                <Plus size={14} />
              </button>
            </div>
          </div>
        </div>

        {/* Coluna Direita: F5-TTS Core */}
        <div className="lg:col-span-8 space-y-8">
          <div className="glass-panel p-8 border-[var(--accent)] border-l-4">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-bold text-xl flex items-center gap-2">
                <Volume2 className="text-[var(--accent)]" /> 
                Áudio de Referência (F5-TTS)
              </h3>
              <span className="text-xs font-mono text-[var(--text-secondary)]">WAV • 24kHz • Mono</span>
            </div>

            <div className="border border-dashed border-[var(--border-color)] p-12 flex flex-col items-center justify-center gap-4 hover:border-[var(--accent)] hover:bg-[var(--accent-glow)] transition-all cursor-pointer group mb-8">
              <div className="w-16 h-16 bg-[var(--bg-primary)] flex items-center justify-center group-hover:scale-110 transition-transform">
                <UploadCloud size={32} className="text-[var(--text-secondary)] group-hover:text-[var(--accent)]" />
              </div>
              <p className="text-sm uppercase tracking-widest font-bold">Arraste ou Clique</p>
              <p className="text-xs text-[var(--text-secondary)]">Recomendado: 6 a 10 segundos de fala limpa</p>
            </div>

            {/* Audio Player Simples */}
            <div className="bg-[var(--bg-primary)] p-4 flex items-center gap-4 border border-[var(--border-color)]">
              <button onClick={() => setIsPlaying(!isPlaying)} className="p-2 hover:text-[var(--accent)]">
                {isPlaying ? <Square size={16} fill="currentColor"/> : <Play size={16} fill="currentColor"/>}
              </button>
              <div className="flex-1 h-8 flex items-center gap-0.5">
                 {/* Visualizador de barras animado */}
                 {[...Array(60)].map((_, i) => (
                   <div 
                      key={i} 
                      className="w-1 bg-[var(--text-secondary)] transition-all duration-100"
                      style={{ 
                        height: isPlaying ? `${Math.random() * 100}%` : `${30 + Math.sin(i)*20}%`,
                        opacity: isPlaying ? 1 : 0.5
                      }} 
                   />
                 ))}
              </div>
              <span className="text-xs font-mono">00:06</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Transcrição (Reference Text)</label>
              <span className="text-xs text-[var(--accent)] font-bold">CRÍTICO PARA QUALIDADE</span>
            </div>
            <textarea 
              value={refText}
              onChange={(e) => setRefText(e.target.value)}
              className="tech-input h-32 resize-none leading-relaxed"
              placeholder="Digite exatamente o que é falado no áudio acima..."
            />
            <p className="text-[10px] text-[var(--text-secondary)] uppercase">
              * O F5-TTS usa este texto para alinhar os fonemas do áudio de referência. Erros aqui causam alucinações na voz gerada.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// --- MAIN AREA COMPONENT (DASHBOARD) ---
const DashboardArea = ({ theme, onLogout }) => {
  const [activeTab, setActiveTab] = useState('library');
  const [selectedVoice, setSelectedVoice] = useState(null); // Se null, mostra lista. Se obj, mostra editor.

  // Mock Data
  const voices = [
    { id: 1, name: 'João Paulo', initials: 'JP', lang: 'PT-BR', tags: ['Corporativo'], refText: 'Olá, este é um teste de voz corporativa.' },
    { id: 2, name: 'Maria Story', initials: 'MS', lang: 'PT-BR', tags: ['Narrativa'], refText: 'Era uma vez em uma terra distante...' },
    { id: 3, name: 'Alex Tech', initials: 'AT', lang: 'EN-US', tags: ['Rápido'], refText: 'System online, checking core modules.' },
    { id: 4, name: 'Sofia News', initials: 'SN', lang: 'ES', tags: ['Jornalismo'], refText: 'Noticias de ultima hora en directo.' },
  ];

  return (
    <div className="flex h-screen w-full bg-[var(--bg-primary)] text-[var(--text-primary)] relative z-20">
      <DashboardSidebar activeTab={activeTab} setActiveTab={setActiveTab} onLogout={onLogout} />
      
      {/* Background Sutil do Dashboard */}
      <SacredGeometry activeIndex={0} theme={theme} minimal={true} />

      <main className="flex-1 p-8 lg:p-12 overflow-hidden flex flex-col relative z-10">
        {/* Header da Área */}
        <header className="flex justify-between items-end mb-12 animate-fade-in-down">
          <div>
            <h1 className="text-5xl font-bold uppercase tracking-tighter mb-2">
              {activeTab === 'library' ? 'Biblioteca de Vozes' : activeTab === 'studio' ? 'Estúdio de Criação' : 'API Access'}
            </h1>
            <p className="text-[var(--text-secondary)] font-mono text-sm uppercase tracking-widest">
              F5-TTS Engine • ROCm 6.2 Active
            </p>
          </div>
          
          {activeTab === 'library' && !selectedVoice && (
            <button 
               onClick={() => setSelectedVoice({})} 
               className="hover-center-out px-8 py-4 border border-[var(--text-primary)] font-bold uppercase tracking-widest flex items-center gap-2"
            >
              <Plus size={18} /> Nova Voz
            </button>
          )}
        </header>

        {/* Content Switcher */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'library' && (
            selectedVoice ? (
              <VoiceEditor voice={selectedVoice.id ? selectedVoice : null} onClose={() => setSelectedVoice(null)} />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-fade-in-up h-full overflow-y-auto pb-20">
                {voices.map(voice => (
                  <VoiceCard key={voice.id} voice={voice} onClick={() => setSelectedVoice(voice)} />
                ))}
                
                {/* Empty State / Add Card */}
                <button 
                  onClick={() => setSelectedVoice({})}
                  className="group aspect-square border border-dashed border-[var(--border-color)] flex flex-col items-center justify-center hover:border-[var(--accent)] hover:bg-[var(--accent-glow)] transition-all duration-300"
                >
                   <Plus size={48} className="text-[var(--border-color)] group-hover:text-[var(--accent)] mb-4 transition-colors" />
                   <span className="uppercase font-bold text-sm tracking-widest text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">Criar Perfil</span>
                </button>
              </div>
            )
          )}

          {activeTab === 'studio' && (
             <div className="h-full flex items-center justify-center border border-[var(--border-color)] text-[var(--text-secondary)] uppercase tracking-widest">
                Módulo Estúdio em Desenvolvimento
             </div>
          )}
        </div>
      </main>
    </div>
  );
};

// --- APP PRINCIPAL (Gerenciador de Estado) ---

const App = () => {
  // Estados
  const [view, setView] = useState('landing'); // 'landing' | 'dashboard'
  const [activeIndex, setActiveIndex] = useState(0);
  const [theme, setTheme] = useState('dark');
  const scrollRef = useRef(null);

  // Scroll Handler (Landing)
  useEffect(() => {
    const container = scrollRef.current;
    if (!container || view === 'dashboard') return;

    const handleScroll = () => {
      const sectionHeight = window.innerHeight;
      const scrollPosition = container.scrollTop;
      const newIndex = Math.round(scrollPosition / sectionHeight);
      if (newIndex !== activeIndex) setActiveIndex(newIndex);
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [activeIndex, view]);

  const scrollTo = (index) => {
    scrollRef.current?.scrollTo({ top: index * window.innerHeight, behavior: 'smooth' });
  };

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  const handleLogin = () => setView('dashboard');
  const handleLogout = () => setView('landing');

  return (
    <>
      <GlobalStyles theme={theme} />
      
      {/* Renderização Condicional da View */}
      {view === 'landing' ? (
        <>
          <SacredGeometry activeIndex={activeIndex} theme={theme} />
          <NavigationDots total={5} active={activeIndex} scrollTo={scrollTo} />

          {/* Header Landing */}
          <div className="fixed top-0 left-0 w-full p-8 flex justify-between items-center z-50 pointer-events-none mix-blend-difference text-white">
            <div className="flex items-center gap-2 pointer-events-auto">
              <Box className="animate-pulse" size={24} strokeWidth={2} />
              <span className="font-bold tracking-widest text-lg">AETHER</span>
            </div>
            <div className="flex items-center gap-6 pointer-events-auto">
              <button onClick={toggleTheme} className="p-2 border border-white/20 hover:bg-white/10 transition-colors">
                {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
              </button>
              <button onClick={handleLogin} className="px-6 py-2 border border-white text-xs font-bold hover:bg-white hover:text-black transition-colors uppercase tracking-widest">
                Login
              </button>
            </div>
          </div>

          {/* Seções Landing */}
          <div ref={scrollRef} className="snap-container no-scrollbar relative z-10">
            <HeroSection active={activeIndex === 0} />
            <DemoSection active={activeIndex === 1} />
            <StackSection active={activeIndex === 2} />
            <PricingSection active={activeIndex === 3} />
            <FooterSection active={activeIndex === 4} theme={theme} />
          </div>
        </>
      ) : (
        /* View Dashboard */
        <DashboardArea theme={theme} onLogout={handleLogout} />
      )}
    </>
  );
};

export default App;