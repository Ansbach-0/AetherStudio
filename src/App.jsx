import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Mic, 
  Play, 
  Cpu, 
  Zap, 
  Globe, 
  ArrowDown,
  Hexagon,
  ChevronRight,
  ChevronDown,
  Activity,
  LogOut,
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
  X,
  Loader2,
  AlertCircle,
  CheckCircle,
  LogIn,
  Check,
  Key,
  Code,
  Terminal,
  Book,
  Copy,
  ExternalLink,
  Shield,
  Users,
  Heart,
  Rocket,
  FileCode
} from 'lucide-react';
import { useApi } from './context';

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
    .animate-fade-in-down {
      animation: fadeInDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }
    @keyframes fadeInDown {
      from { opacity: 0; transform: translateY(-20px); }
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

// --- COMPONENTE DROPDOWN CUSTOMIZADO ---
// Dropdown 100% customizado que substitui o <select> nativo
// Mantém mesma funcionalidade com visual consistente ao design do site
const CustomDropdown = ({ 
  value,           // Valor selecionado atual
  onChange,        // Callback ao selecionar opção
  options,         // Array de opções: { value: string, label: string }
  placeholder,     // Texto quando nenhuma opção selecionada
  disabled = false // Desabilitar interação
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const dropdownRef = useRef(null);
  const listRef = useRef(null);

  // Encontra a opção selecionada para exibir no trigger
  const selectedOption = options.find(opt => opt.value === value);

  // Fecha o dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
        setFocusedIndex(-1);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Navegação por teclado para acessibilidade
  const handleKeyDown = (e) => {
    if (disabled) return;

    switch (e.key) {
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(options.findIndex(opt => opt.value === value) || 0);
        } else if (focusedIndex >= 0) {
          handleSelect(options[focusedIndex].value);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setFocusedIndex(-1);
        break;
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(0);
        } else {
          setFocusedIndex(prev => 
            prev < options.length - 1 ? prev + 1 : prev
          );
        }
        break;
      case 'ArrowUp':
        e.preventDefault();
        if (isOpen) {
          setFocusedIndex(prev => prev > 0 ? prev - 1 : 0);
        }
        break;
      case 'Tab':
        setIsOpen(false);
        setFocusedIndex(-1);
        break;
      default:
        break;
    }
  };

  // Handler de seleção de opção
  const handleSelect = (optionValue) => {
    onChange({ target: { value: optionValue } }); // Mantém compatibilidade com onChange do select nativo
    setIsOpen(false);
    setFocusedIndex(-1);
  };

  // Scroll automático para item focado
  useEffect(() => {
    if (isOpen && focusedIndex >= 0 && listRef.current) {
      const focusedElement = listRef.current.children[focusedIndex];
      if (focusedElement) {
        focusedElement.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [focusedIndex, isOpen]);

  return (
    <div 
      ref={dropdownRef}
      className="relative w-full"
    >
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-labelledby="dropdown-label"
        className={`
          w-full flex items-center justify-between gap-2
          px-4 py-4 
          bg-transparent 
          border border-[var(--border-color)] 
          text-[var(--text-primary)] 
          font-['Space_Grotesk',sans-serif]
          text-left
          outline-none
          transition-all duration-300
          ${isOpen ? 'border-[var(--accent)] shadow-[0_0_15px_var(--accent-glow)]' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-[var(--accent)]/50'}
        `}
      >
        <span className={selectedOption ? '' : 'text-[var(--text-secondary)]'}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDown 
          size={18} 
          className={`
            text-[var(--text-secondary)] 
            transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]
            ${isOpen ? 'rotate-180' : 'rotate-0'}
          `}
        />
      </button>

      {/* Lista de Opções */}
      <div
        className={`
          absolute top-full left-0 right-0 z-50
          mt-1
          bg-[var(--bg-primary)] 
          border border-[var(--border-color)]
          shadow-lg shadow-black/20
          max-h-60 overflow-y-auto
          origin-top
          transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]
          ${isOpen 
            ? 'opacity-100 scale-y-100 translate-y-0' 
            : 'opacity-0 scale-y-95 -translate-y-2 pointer-events-none'
          }
        `}
        role="listbox"
        ref={listRef}
      >
        {options.map((option, index) => (
          <div
            key={option.value}
            role="option"
            aria-selected={value === option.value}
            onClick={() => handleSelect(option.value)}
            className={`
              px-4 py-3
              cursor-pointer
              transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]
              ${value === option.value 
                ? 'bg-[var(--accent)] text-white' 
                : 'hover:bg-[var(--accent)]/30 hover:pl-5 text-[var(--text-primary)]'
              }
              ${focusedIndex === index && value !== option.value
                ? 'bg-[var(--accent)]/15 pl-5' 
                : ''
              }
            `}
          >
            {option.label}
          </div>
        ))}
      </div>
    </div>
  );
};

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
        <span className="w-2 h-2 animate-pulse" style={{ backgroundColor: '#22c55e' }} />
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
                <div className="w-4 h-4 bg-[var(--text-primary)] text-[var(--bg-primary)] flex items-center justify-center">
                  <Check size={10} strokeWidth={3} />
                </div>
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

      {/* Botão de logout/sair da conta */}
      <button 
        onClick={onLogout} 
        className="mt-auto text-[var(--text-secondary)] hover:text-red-500 p-4"
        title="Sair"
        aria-label="Sair da conta"
      >
        <LogOut size={20} />
      </button>
    </div>
  );
};

const VoiceCard = ({ voice, onClick }) => {
  const displayTags = voice.tags ? voice.tags.split(',').map(t => t.trim()).filter(Boolean) : [];
  const avatarColor = voice.color || '#7c3aed';
  
  return (
    <div 
      onClick={onClick}
      className="group relative aspect-square glass-panel p-6 flex flex-col justify-between cursor-pointer hover:border-[var(--accent)] transition-all duration-500"
    >
      <div className="flex justify-between items-start">
        <div 
          className="w-10 h-10 flex items-center justify-center font-bold text-lg text-white"
          style={{ backgroundColor: avatarColor }}
        >
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
              className="w-1 opacity-50 group-hover:opacity-100 transition-all"
              style={{ 
                height: `${Math.random() * 100}%`,
                transitionDelay: `${i * 50}ms`,
                backgroundColor: avatarColor,
              }} 
            />
          ))}
        </div>
        <h3 className="font-bold text-xl uppercase tracking-tight">{voice.name}</h3>
        <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-secondary)]">
          <span>{voice.lang}</span>
          {displayTags.length > 0 && (
            <>
              <span>•</span>
              <span>{displayTags[0]}</span>
              {displayTags.length > 1 && <span className="opacity-60">+{displayTags.length - 1}</span>}
            </>
          )}
        </div>
      </div>

      {/* Hover Effect Background uses avatar color */}
      <div 
        className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-500 pointer-events-none" 
        style={{ backgroundColor: avatarColor }}
      />
    </div>
  );
};

const VoiceEditor = ({ voice, onClose }) => {
  const { voiceProfiles } = useApi();
  const [name, setName] = useState(voice?.name || '');
  const [refText, setRefText] = useState(voice?.refText || '');
  const [description, setDescription] = useState(voice?.description || '');
  const [color, setColor] = useState(voice?.color || '#7c3aed');
  const [tags, setTags] = useState(voice?.tags ? voice.tags.split(',').map(t => t.trim()).filter(Boolean) : []);
  const [customTag, setCustomTag] = useState('');
  const [showTagInput, setShowTagInput] = useState(false);
  const [audioFile, setAudioFile] = useState(null);
  const [audioPreview, setAudioPreview] = useState(voice?.referenceAudio || null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const fileInputRef = useRef(null);
  const tagInputRef = useRef(null);

  // Preset tags available for selection
  const presetTags = ['Neutro', 'Corporativo', 'Sussurro', 'Rápido', 'Calmo', 'Energético', 'Formal', 'Casual'];
  const availableColors = ['#7c3aed', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#ec4899'];

  const toggleTag = (tag) => {
    setTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag) 
        : [...prev, tag]
    );
  };

  const addCustomTag = () => {
    const trimmed = customTag.trim();
    if (trimmed && !tags.includes(trimmed)) {
      setTags(prev => [...prev, trimmed]);
    }
    setCustomTag('');
    setShowTagInput(false);
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setAudioFile(file);
      setAudioPreview(URL.createObjectURL(file));
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('audio/')) {
      setAudioFile(file);
      setAudioPreview(URL.createObjectURL(file));
    }
  };

  const handleSave = async () => {
    if (!name.trim()) return;
    
    setSaving(true);
    try {
      const tagsString = tags.join(',');
      if (voice?.id) {
        // Update existing profile
        await voiceProfiles.updateProfile(voice.id, {
          name: name.trim(),
          reference_text: refText.trim(),
          description: description.trim(),
          color: color,
          tags: tagsString,
        });
      } else {
        // Create new profile
        if (!audioFile) {
          alert('Por favor, adicione um áudio de referência');
          setSaving(false);
          return;
        }
        await voiceProfiles.createProfile({
          name: name.trim(),
          referenceAudio: audioFile,
          referenceText: refText.trim(),
          description: description.trim(),
          color: color,
          tags: tagsString,
        });
      }
      onClose();
    } catch {
      // Error handled by context
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!voice?.id) return;
    if (!confirm('Tem certeza que deseja excluir este perfil?')) return;
    
    setDeleting(true);
    try {
      await voiceProfiles.deleteProfile(voice.id);
      onClose();
    } catch {
      // Error handled by context
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="h-full flex flex-col animate-fade-in">
      <div className="flex justify-between items-center mb-8 pb-4 border-b border-[var(--border-color)]">
        <h2 className="text-3xl font-bold uppercase flex items-center gap-4">
          <button onClick={onClose} className="hover:text-[var(--accent)] transition-colors">
            <ChevronRight className="rotate-180" size={32} />
          </button>
          Editor de Voz <span className="text-[var(--text-secondary)] text-sm ml-2 font-mono">{voice?.id ? 'EDIT MODE' : 'CREATE MODE'}</span>
        </h2>
        <div className="flex gap-4">
          {voice?.id && (
            <button 
              onClick={handleDelete}
              disabled={deleting}
              className="px-6 py-3 border border-red-500/30 text-red-500 hover:bg-red-500 hover:text-white transition-colors uppercase font-bold text-xs tracking-wider flex items-center gap-2 disabled:opacity-50"
            >
              {deleting ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />} Excluir
            </button>
          )}
          <button 
            onClick={handleSave}
            disabled={saving || !name.trim()}
            className="px-6 py-3 bg-[var(--text-primary)] text-[var(--bg-primary)] hover:bg-[var(--accent)] hover:text-white transition-colors uppercase font-bold text-xs tracking-wider flex items-center gap-2 disabled:opacity-50"
          >
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />} Salvar Perfil
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 h-full overflow-y-auto">
        {/* Coluna Esquerda: Dados Básicos */}
        <div className="lg:col-span-4 space-y-8">
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Nome da Voz *</label>
            <input 
              type="text" 
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="tech-input" 
              placeholder="Ex: Narrador Corporativo" 
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Descrição</label>
            <textarea 
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="tech-input h-24 resize-none"
              placeholder="Descreva o perfil de voz..."
            />
          </div>

          {/* Botões de seleção de cor - apenas glow, sem aumento de tamanho */}
          <div className="space-y-2">
             <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Avatar / Cor</label>
             <div className="flex gap-4">
               {availableColors.map(c => (
                 <button 
                   key={c} 
                   onClick={() => setColor(c)}
                   className={`w-10 h-10 border-2 transition-shadow ${
                     color === c ? 'border-white ring-2 ring-[var(--accent)] shadow-[0_0_12px_var(--accent-glow)]' : 'border-[var(--border-color)] hover:ring-2 hover:ring-[var(--accent)]/50 hover:shadow-[0_0_8px_var(--accent-glow)]'
                   }`} 
                   style={{ backgroundColor: c }} 
                 />
               ))}
             </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Tags de Estilo</label>
            <div className="flex flex-wrap gap-2">
              {presetTags.map(tag => (
                <span 
                  key={tag} 
                  onClick={() => toggleTag(tag)}
                  className={`px-3 py-1 border text-xs uppercase cursor-pointer transition-colors ${
                    tags.includes(tag) 
                      ? 'border-[var(--accent)] bg-[var(--accent-glow)] text-[var(--accent)]' 
                      : 'border-[var(--border-color)] hover:border-[var(--accent)]'
                  }`}
                >
                  {tag}
                </span>
              ))}
              {/* Custom tags */}
              {tags.filter(t => !presetTags.includes(t)).map(tag => (
                <span 
                  key={tag} 
                  onClick={() => toggleTag(tag)}
                  className="px-3 py-1 border border-[var(--accent)] bg-[var(--accent-glow)] text-[var(--accent)] text-xs uppercase cursor-pointer transition-colors flex items-center gap-1"
                >
                  {tag}
                  <X size={12} className="opacity-60 hover:opacity-100" />
                </span>
              ))}
              {showTagInput ? (
                <div className="flex items-center gap-1">
                  <input
                    ref={tagInputRef}
                    type="text"
                    value={customTag}
                    onChange={(e) => setCustomTag(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addCustomTag()}
                    onBlur={() => { if (!customTag.trim()) setShowTagInput(false); }}
                    className="w-24 px-2 py-1 border border-[var(--accent)] bg-transparent text-xs"
                    placeholder="Nova tag..."
                    autoFocus
                  />
                  <button onClick={addCustomTag} className="text-[var(--accent)]">
                    <Check size={14} />
                  </button>
                </div>
              ) : (
                <button 
                  onClick={() => setShowTagInput(true)}
                  className="w-6 h-6 flex items-center justify-center border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--accent)]"
                >
                  <Plus size={14} />
                </button>
              )}
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

            <input 
              type="file" 
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="audio/*"
              className="hidden"
            />

            <div 
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              className="border border-dashed border-[var(--border-color)] p-12 flex flex-col items-center justify-center gap-4 hover:border-[var(--accent)] hover:bg-[var(--accent-glow)] transition-all cursor-pointer group mb-8"
            >
              <div className="w-16 h-16 bg-[var(--bg-primary)] flex items-center justify-center group-hover:scale-110 transition-transform">
                <UploadCloud size={32} className="text-[var(--text-secondary)] group-hover:text-[var(--accent)]" />
              </div>
              <p className="text-sm uppercase tracking-widest font-bold">
                {audioFile ? audioFile.name : 'Arraste ou Clique'}
              </p>
              <p className="text-xs text-[var(--text-secondary)]">Recomendado: 6 a 10 segundos de fala limpa</p>
            </div>

            {/* Audio Player */}
            {audioPreview && (
              <div className="bg-[var(--bg-primary)] p-4 flex items-center gap-4 border border-[var(--border-color)]">
                <button onClick={() => setIsPlaying(!isPlaying)} className="p-2 hover:text-[var(--accent)]">
                  {isPlaying ? <Square size={16} fill="currentColor"/> : <Play size={16} fill="currentColor"/>}
                </button>
                <audio 
                  src={audioPreview} 
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onEnded={() => setIsPlaying(false)}
                  controls 
                  className="flex-1"
                />
              </div>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Transcrição (Reference Text) *</label>
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
  const { auth, voiceProfiles, credits, systemStatus, globalError, clearErrors, retryConnection } = useApi();
  const [activeTab, setActiveTab] = useState('library');
  const [selectedVoice, setSelectedVoice] = useState(null);

  // API base URL for audio files
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Transform API profiles to display format
  const voices = voiceProfiles.profiles.map(profile => ({
    id: profile.id,
    name: profile.name,
    initials: profile.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase(),
    lang: profile.language?.toUpperCase() || 'AUTO',
    tags: profile.tags || '',
    color: profile.color || '#7c3aed',
    refText: profile.reference_text || '',
    referenceAudio: profile.reference_audio_url ? `${API_BASE_URL}${profile.reference_audio_url}` : null,
    description: profile.description,
  }));

  return (
    <div className="flex h-screen w-full bg-[var(--bg-primary)] text-[var(--text-primary)] relative z-20">
      <DashboardSidebar activeTab={activeTab} setActiveTab={setActiveTab} onLogout={onLogout} />
      
      {/* Background Sutil do Dashboard */}
      <SacredGeometry activeIndex={0} theme={theme} minimal={true} />

      {/* Global Error Toast */}
      {globalError && (
        <div className="fixed top-4 right-4 z-50 bg-red-500/90 text-white px-6 py-3 flex items-center gap-3 animate-fade-in-down">
          <AlertCircle size={20} />
          <span className="font-medium">{globalError}</span>
          <button onClick={clearErrors} className="ml-2 hover:opacity-70">
            <X size={18} />
          </button>
        </div>
      )}

      {/* System Status Badge removido - info de status disponível no header */}

      <main className="flex-1 p-8 lg:p-12 overflow-hidden flex flex-col relative z-10">
        {/* Header da Área */}
        <header className="flex justify-between items-end mb-12 animate-fade-in-down">
          <div>
            <h1 className="text-5xl font-bold uppercase tracking-tighter mb-2">
              {activeTab === 'library' ? 'Biblioteca de Vozes' : activeTab === 'studio' ? 'Estúdio de Criação' : 'API Access'}
            </h1>
            <p className="text-[var(--text-secondary)] font-mono text-sm uppercase tracking-widest flex items-center gap-4">
              <span className="flex items-center gap-2">
                F5-TTS Engine • 
                <span className={systemStatus.gpuAvailable ? 'text-green-500' : 'text-[var(--accent)]'}>
                  {systemStatus.gpuAvailable ? (systemStatus.gpuName || 'GPU Ativo') : 'Modo CPU'}
                </span>
              </span>
              {auth.user && (
                <span className="text-[var(--accent)]">• {credits.credits} créditos</span>
              )}
            </p>
          </div>
          
          {activeTab === 'library' && !selectedVoice && (
            <button 
               onClick={() => setSelectedVoice({})} 
               className="hover-center-out px-8 py-4 border border-[var(--text-primary)] font-bold uppercase tracking-widest flex items-center gap-2"
               disabled={voiceProfiles.loading}
            >
              {voiceProfiles.loading ? <Loader2 size={18} className="animate-spin" /> : <Plus size={18} />} Nova Voz
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
                {voiceProfiles.loading ? (
                  <div className="col-span-full flex items-center justify-center h-64">
                    <Loader2 size={48} className="animate-spin text-[var(--accent)]" />
                  </div>
                ) : voices.length === 0 ? (
                  <div className="col-span-full flex flex-col items-center justify-center h-64 text-[var(--text-secondary)]">
                    <Mic size={48} className="mb-4 opacity-50" />
                    <p className="uppercase tracking-widest text-sm">Nenhuma voz criada</p>
                    <p className="text-xs mt-2">Clique em "Nova Voz" para começar</p>
                  </div>
                ) : (
                  voices.map(voice => (
                    <VoiceCard key={voice.id} voice={voice} onClick={() => setSelectedVoice(voice)} />
                  ))
                )}
                
                {/* Empty State / Add Card */}
                {!voiceProfiles.loading && (
                  <button 
                    onClick={() => setSelectedVoice({})}
                    className="group aspect-square border border-dashed border-[var(--border-color)] flex flex-col items-center justify-center hover:border-[var(--accent)] hover:bg-[var(--accent-glow)] transition-all duration-300"
                  >
                     <Plus size={48} className="text-[var(--border-color)] group-hover:text-[var(--accent)] mb-4 transition-colors" />
                     <span className="uppercase font-bold text-sm tracking-widest text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">Criar Perfil</span>
                  </button>
                )}
              </div>
            )
          )}

          {activeTab === 'studio' && (
             <StudioArea />
          )}

          {activeTab === 'api' && (
             <ApiAccessArea />
          )}
        </div>
      </main>
    </div>
  );
};

// --- STUDIO AREA COMPONENT ---
const StudioArea = () => {
  const { voiceProfiles, synthesis } = useApi();
  const [selectedProfileId, setSelectedProfileId] = useState('');
  const [text, setText] = useState('');
  const [referenceText, setReferenceText] = useState('');  // Texto de referência do perfil selecionado
  const [emotion, setEmotion] = useState('neutral');

  // Pré-preenche o texto de referência quando seleciona um perfil
  const handleProfileSelect = (profileId) => {
    setSelectedProfileId(profileId);
    const profile = voiceProfiles.profiles.find(p => p.id === parseInt(profileId) || p.id === profileId);
    if (profile?.reference_text) {
      setReferenceText(profile.reference_text);
    } else {
      setReferenceText('');
    }
  };

  const handleGenerate = async () => {
    if (!selectedProfileId || !text.trim()) return;
    
    try {
      await synthesis.generate({
        profileId: selectedProfileId,
        text: text.trim(),
        emotion,
      });
    } catch {
      // Error handled by context
    }
  };

  return (
    <div className="h-full flex flex-col gap-8 animate-fade-in">
      <div className="glass-panel p-8">
        <h3 className="font-bold text-xl mb-6 uppercase tracking-wider">Síntese de Voz</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Perfil de Voz</label>
            <CustomDropdown
              value={selectedProfileId}
              onChange={(e) => handleProfileSelect(e.target.value)}
              placeholder="Selecione uma voz..."
              options={voiceProfiles.profiles.map(p => ({ value: p.id, label: p.name }))}
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Emoção</label>
            <CustomDropdown
              value={emotion}
              onChange={(e) => setEmotion(e.target.value)}
              placeholder="Selecione uma emoção..."
              options={['neutral', 'happy', 'sad', 'angry', 'fearful', 'surprised', 'calm', 'whisper'].map(e => ({
                value: e,
                label: e.charAt(0).toUpperCase() + e.slice(1)
              }))}
            />
          </div>
        </div>
        
        {/* Campo de Texto de Referência - pré-preenchido pelo perfil selecionado */}
        {referenceText && (
          <div className="space-y-2 mb-6">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Texto de Referência (do Perfil)</label>
            <textarea 
              value={referenceText}
              onChange={(e) => setReferenceText(e.target.value)}
              className="tech-input h-20 resize-none bg-[var(--accent)]/5 border-[var(--accent)]/30"
              placeholder="Transcrição do áudio de referência..."
            />
            <p className="text-[10px] text-[var(--text-secondary)] uppercase">
              * Este texto foi salvo junto com o perfil de voz. Ele ajuda o F5-TTS a alinhar os fonemas corretamente.
            </p>
          </div>
        )}

        <div className="space-y-2 mb-6">
          <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Texto para Síntese</label>
          <textarea 
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="tech-input h-32 resize-none"
            placeholder="Digite o texto que deseja sintetizar..."
          />
        </div>

        <div className="flex items-center gap-4">
          <button 
            onClick={handleGenerate}
            disabled={synthesis.generating || !selectedProfileId || !text.trim()}
            className="px-8 py-4 bg-[var(--accent)] text-white font-bold uppercase tracking-widest flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[var(--accent)]/80 transition-colors"
          >
            {synthesis.generating ? (
              <>
                <Loader2 size={18} className="animate-spin" /> Gerando... {synthesis.progress}%
              </>
            ) : (
              <>
                <Zap size={18} /> Gerar Áudio
              </>
            )}
          </button>

          {synthesis.audioUrl && (
            <div className="flex-1 flex items-center gap-4">
              <audio controls src={synthesis.audioUrl} className="flex-1" />
              <a 
                href={synthesis.audioUrl} 
                download="synthesized.wav"
                className="px-4 py-2 border border-[var(--border-color)] text-xs uppercase tracking-wider hover:bg-[var(--accent)] hover:text-white hover:border-[var(--accent)] transition-colors"
              >
                Download
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// --- API ACCESS AREA COMPONENT ---
// Componente de documentação de API profissional inspirado em Stripe/OpenAI
const ApiAccessArea = () => {
  const { auth, systemStatus } = useApi();
  const [copiedId, setCopiedId] = useState(null); // ID do item copiado
  const [generating, setGenerating] = useState(false);
  const [newApiKey, setNewApiKey] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [codeLanguage, setCodeLanguage] = useState('curl'); // Tab de linguagem selecionada
  const [expandedEndpoints, setExpandedEndpoints] = useState({}); // Endpoints expandidos
  
  const apiKey = newApiKey || auth.user?.api_key || null;
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Função de copiar com feedback visual por ID
  const copyToClipboard = (text, id = 'default') => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Toggle de endpoint expandido
  const toggleEndpoint = (id) => {
    setExpandedEndpoints(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleGenerateKey = async () => {
    if (!confirm('Isso irá substituir sua API Key atual. Deseja continuar?')) return;
    
    setGenerating(true);
    try {
      const response = await fetch(`${baseUrl}/api/v1/users/api-key/generate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) throw new Error('Falha ao gerar API Key');
      
      const data = await response.json();
      setNewApiKey(data.api_key);
      alert('API Key gerada com sucesso! Copie e guarde em local seguro.');
    } catch (error) {
      alert('Erro ao gerar API Key: ' + error.message);
    } finally {
      setGenerating(false);
    }
  };

  // Exemplos de código por linguagem
  const codeExamples = {
    curl: `curl -X POST "${baseUrl}/api/v1/voice/pipeline?user_id=${auth.user?.id || 'USER_ID'}" \\
  -H "Authorization: Bearer ${apiKey || 'YOUR_API_KEY'}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "profile_id": 1,
    "text": "Olá, este é um teste de síntese de voz.",
    "emotion": "neutral",
    "language": "pt-BR"
  }'`,
    python: `import requests

API_KEY = "${apiKey || 'YOUR_API_KEY'}"
BASE_URL = "${baseUrl}"

# Sintetizar voz com o pipeline completo
response = requests.post(
    f"{BASE_URL}/api/v1/voice/pipeline",
    params={"user_id": ${auth.user?.id || 'USER_ID'}},
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "profile_id": 1,
        "text": "Olá, este é um teste.",
        "emotion": "neutral"
    }
)

if response.ok:
    result = response.json()
    print(f"Áudio gerado: {result['audio_url']}")
else:
    print(f"Erro: {response.status_code}")`,
    javascript: `const API_KEY = '${apiKey || 'YOUR_API_KEY'}';
const BASE_URL = '${baseUrl}';

// Sintetizar voz com o pipeline completo
async function synthesize(text, profileId) {
  const response = await fetch(
    \`\${BASE_URL}/api/v1/voice/pipeline?user_id=${auth.user?.id || 'USER_ID'}\`,
    {
      method: 'POST',
      headers: {
        'Authorization': \`Bearer \${API_KEY}\`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        profile_id: profileId,
        text: text,
        emotion: 'neutral',
      }),
    }
  );
  
  return response.json();
}

// Uso
synthesize('Olá mundo!', 1).then(console.log);`,
  };

  // Configuração das tabs de navegação principal
  const navTabs = [
    { id: 'overview', label: 'Visão Geral', icon: Book },
    { id: 'auth', label: 'Autenticação', icon: Key },
    { id: 'examples', label: 'Exemplos', icon: Code },
    { id: 'endpoints', label: 'Endpoints', icon: Terminal },
  ];

  // Configuração das tabs de linguagem
  const languageTabs = [
    { id: 'curl', label: 'cURL', icon: Terminal },
    { id: 'python', label: 'Python', icon: FileCode },
    { id: 'javascript', label: 'JavaScript', icon: Code },
  ];

  // Endpoints agrupados por categoria
  const endpointGroups = [
    {
      category: 'Health',
      icon: Heart,
      description: 'Monitore o status e saúde da API',
      endpoints: [
        { 
          method: 'GET', 
          path: '/health', 
          desc: 'Status da API',
          details: 'Retorna o status básico da API. Útil para health checks.',
          auth: false,
          response: '{ "status": "healthy", "timestamp": "..." }'
        },
        { 
          method: 'GET', 
          path: '/health/detailed', 
          desc: 'Status detalhado',
          details: 'Retorna informações detalhadas incluindo GPU, memória e modelos carregados.',
          auth: false,
          response: '{ "status": "healthy", "gpu_available": true, "models": [...] }'
        },
      ]
    },
    {
      category: 'Voice',
      icon: Mic,
      description: 'Endpoints de clonagem e síntese de voz',
      endpoints: [
        { 
          method: 'POST', 
          path: '/voice/pipeline', 
          desc: 'Pipeline completo TTS + RVC',
          details: 'Executa o pipeline completo: Text-to-Speech seguido de conversão RVC para clonagem de voz.',
          auth: true,
          response: '{ "audio_url": "...", "duration": 3.5, "credits_used": 1 }'
        },
        { 
          method: 'POST', 
          path: '/voice/clone', 
          desc: 'Clonagem de voz (TTS)',
          details: 'Gera áudio usando apenas Text-to-Speech sem conversão RVC.',
          auth: true,
          response: '{ "audio_url": "...", "duration": 2.1 }'
        },
        { 
          method: 'GET', 
          path: '/voice/profiles', 
          desc: 'Listar perfis',
          details: 'Retorna todos os perfis de voz do usuário autenticado.',
          auth: true,
          response: '[{ "id": 1, "name": "...", "created_at": "..." }]'
        },
        { 
          method: 'POST', 
          path: '/voice/profiles', 
          desc: 'Criar perfil',
          details: 'Cria um novo perfil de voz com arquivos de áudio de referência.',
          auth: true,
          response: '{ "id": 2, "name": "...", "status": "created" }'
        },
        { 
          method: 'DELETE', 
          path: '/voice/profiles/{id}', 
          desc: 'Excluir perfil',
          details: 'Remove permanentemente um perfil de voz e seus arquivos associados.',
          auth: true,
          response: '{ "message": "Profile deleted" }'
        },
      ]
    },
    {
      category: 'Users',
      icon: Users,
      description: 'Gerenciamento de usuários e créditos',
      endpoints: [
        { 
          method: 'GET', 
          path: '/users/me', 
          desc: 'Dados do usuário',
          details: 'Retorna informações do usuário autenticado incluindo email, nome e configurações.',
          auth: true,
          response: '{ "id": 1, "email": "...", "name": "...", "credits": 100 }'
        },
        { 
          method: 'GET', 
          path: '/users/credits', 
          desc: 'Saldo de créditos',
          details: 'Retorna o saldo atual de créditos do usuário.',
          auth: true,
          response: '{ "credits": 100, "plan": "pro" }'
        },
      ]
    },
  ];

  // Componente de bloco de código com botão de copiar
  const CodeBlock = ({ code, id, language }) => (
    <div className="relative group">
      <pre className="p-4 bg-[var(--bg-primary)] border border-[var(--border-color)] font-mono text-xs overflow-x-auto rounded-lg">
        <code className="text-[var(--text-secondary)]">{code}</code>
      </pre>
      <button
        onClick={() => copyToClipboard(code, id)}
        className="absolute top-3 right-3 p-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded opacity-0 group-hover:opacity-100 transition-all hover:bg-[var(--accent)] hover:border-[var(--accent)] hover:text-white"
        title="Copiar código"
      >
        {copiedId === id ? <Check size={14} /> : <Copy size={14} />}
      </button>
    </div>
  );

  // Componente de card de status com hover
  const StatusCard = ({ icon: Icon, value, label, accent = false }) => (
    <div className="group p-5 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg transition-all duration-300 hover:border-[var(--accent)] hover:shadow-lg hover:shadow-[var(--accent)]/10 hover:-translate-y-1">
      <div className="flex items-center gap-3 mb-2">
        <div className={`p-2 rounded-lg ${accent ? 'bg-[var(--accent)]/20 text-[var(--accent)]' : 'bg-[var(--border-color)]'}`}>
          <Icon size={20} />
        </div>
        <div className={`text-2xl font-bold ${accent ? 'text-[var(--accent)]' : ''}`}>{value}</div>
      </div>
      <div className="text-xs text-[var(--text-secondary)] uppercase tracking-wider">{label}</div>
    </div>
  );

  return (
    <div className="h-full flex flex-col gap-6 animate-fade-in overflow-y-auto pb-20">
      {/* Hero Banner com gradiente */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-[var(--accent)]/20 via-[var(--depth-color)]/10 to-transparent border border-[var(--accent)]/30 p-8">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--accent)]/10 rounded-full blur-3xl" />
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-[var(--accent)] rounded-lg">
              <Cpu size={24} className="text-white" />
            </div>
            <h2 className="text-2xl font-bold uppercase tracking-wider">Aether Voice API</h2>
          </div>
          <p className="text-[var(--text-secondary)] max-w-2xl">
            Integre clonagem e síntese de voz de alta qualidade em suas aplicações. 
            Nossa API oferece processamento em tempo real com suporte a GPU para máxima performance.
          </p>
          <div className="flex gap-3 mt-4">
            <span className="px-3 py-1 text-xs font-bold uppercase bg-green-500/20 text-green-400 rounded-full flex items-center gap-1">
              <Activity size={12} /> v1.0
            </span>
            <span className="px-3 py-1 text-xs font-bold uppercase bg-[var(--accent)]/20 text-[var(--accent)] rounded-full">
              REST API
            </span>
          </div>
        </div>
      </div>

      {/* Tabs de navegação principal */}
      <div className="flex gap-1 p-1 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg">
        {navTabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 px-4 py-3 text-sm font-bold uppercase tracking-wider rounded-md transition-all flex items-center justify-center gap-2 ${
                activeTab === tab.id
                  ? 'bg-[var(--accent)] text-white shadow-lg shadow-[var(--accent)]/30'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--border-color)]/50'
              }`}
            >
              <Icon size={16} />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* ========== SEÇÃO VISÃO GERAL ========== */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Cards de Status */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatusCard 
              icon={Zap} 
              value={auth.user?.credits?.toFixed(0) || 0} 
              label="Créditos Disponíveis" 
              accent 
            />
            <StatusCard 
              icon={Activity} 
              value={systemStatus.online ? 'Online' : 'Offline'} 
              label="Status da API" 
            />
            <StatusCard 
              icon={Cpu} 
              value={systemStatus.gpuAvailable ? 'GPU' : 'CPU'} 
              label="Modo de Processamento" 
            />
          </div>

          {/* Quick Start - 3 passos */}
          <div className="glass-panel p-8">
            <h3 className="font-bold text-lg mb-6 uppercase tracking-wider flex items-center gap-2">
              <Rocket size={20} className="text-[var(--accent)]" /> Quick Start
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { step: 1, title: 'Gere sua API Key', desc: 'Vá até a aba Autenticação e gere sua chave de acesso única.', icon: Key },
                { step: 2, title: 'Crie um Perfil', desc: 'Faça upload de amostras de áudio para criar um perfil de voz.', icon: Mic },
                { step: 3, title: 'Sintetize', desc: 'Use o endpoint /voice/pipeline para gerar áudios clonados.', icon: Play },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.step} className="relative pl-12">
                    <div className="absolute left-0 top-0 w-8 h-8 rounded-full bg-[var(--accent)] text-white flex items-center justify-center font-bold text-sm">
                      {item.step}
                    </div>
                    <h4 className="font-bold mb-1 flex items-center gap-2">
                      <Icon size={16} className="text-[var(--accent)]" />
                      {item.title}
                    </h4>
                    <p className="text-sm text-[var(--text-secondary)]">{item.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Base URL */}
          <div className="glass-panel p-6">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)] mb-3 block flex items-center gap-2">
              <Globe size={14} /> Base URL
            </label>
            <div className="flex gap-2">
              <code className="flex-1 p-4 bg-[var(--bg-primary)] border border-[var(--border-color)] font-mono text-sm rounded-lg flex items-center">
                <span className="text-[var(--accent)]">{baseUrl}</span>
                <span className="text-[var(--text-secondary)]">/api/v1</span>
              </code>
              <button 
                onClick={() => copyToClipboard(`${baseUrl}/api/v1`, 'baseUrl')}
                className="px-4 py-2 border border-[var(--border-color)] text-xs uppercase tracking-wider hover:bg-[var(--accent)] hover:text-white hover:border-[var(--accent)] transition-all rounded-lg flex items-center gap-2"
              >
                {copiedId === 'baseUrl' ? <Check size={14} /> : <Copy size={14} />}
                <span className="hidden sm:inline">Copiar</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========== SEÇÃO AUTENTICAÇÃO ========== */}
      {activeTab === 'auth' && (
        <div className="space-y-6">
          <div className="glass-panel p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-[var(--accent)]/20 rounded-lg">
                <Key size={24} className="text-[var(--accent)]" />
              </div>
              <div>
                <h3 className="font-bold text-xl uppercase tracking-wider">Sua API Key</h3>
                <p className="text-sm text-[var(--text-secondary)]">Chave de autenticação para acessar a API</p>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <input 
                    type="text" 
                    readOnly 
                    value={apiKey || 'Nenhuma API Key gerada'}
                    className="tech-input w-full font-mono text-sm pr-12"
                  />
                  {apiKey && (
                    <button 
                      onClick={() => copyToClipboard(apiKey, 'apiKey')}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-2 hover:bg-[var(--accent)]/20 rounded transition-colors"
                      title="Copiar API Key"
                    >
                      {copiedId === 'apiKey' ? <Check size={16} className="text-green-500" /> : <Copy size={16} />}
                    </button>
                  )}
                </div>
              </div>
              
              <button
                onClick={handleGenerateKey}
                disabled={generating}
                className="px-6 py-3 bg-[var(--accent)] text-white font-bold uppercase tracking-wider flex items-center gap-2 hover:opacity-90 transition-all disabled:opacity-50 rounded-lg shadow-lg shadow-[var(--accent)]/30"
              >
                {generating ? <Loader2 size={18} className="animate-spin" /> : <Zap size={18} />}
                {apiKey ? 'Regenerar API Key' : 'Gerar API Key'}
              </button>
              
              <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg flex items-start gap-3">
                <AlertCircle size={18} className="text-yellow-500 mt-0.5 flex-shrink-0" />
                <div className="text-sm">
                  <p className="font-bold text-yellow-500">Importante</p>
                  <p className="text-[var(--text-secondary)]">A API Key é exibida apenas uma vez após geração. Guarde-a em local seguro.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="glass-panel p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-[var(--accent)]/20 rounded-lg">
                <Shield size={24} className="text-[var(--accent)]" />
              </div>
              <div>
                <h3 className="font-bold text-lg uppercase tracking-wider">Como Autenticar</h3>
                <p className="text-sm text-[var(--text-secondary)]">Adicione o header em todas as requisições</p>
              </div>
            </div>
            
            <CodeBlock 
              code={`Authorization: Bearer ${apiKey || 'YOUR_API_KEY'}`} 
              id="authHeader" 
            />

            <div className="mt-4 p-4 bg-[var(--accent)]/5 border border-[var(--accent)]/20 rounded-lg">
              <p className="text-sm text-[var(--text-secondary)]">
                <span className="text-[var(--accent)] font-bold">Dica:</span> Endpoints marcados com 
                <span className="mx-1 px-2 py-0.5 bg-[var(--accent)]/20 text-[var(--accent)] text-xs rounded">Auth</span> 
                requerem autenticação.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ========== SEÇÃO EXEMPLOS ========== */}
      {activeTab === 'examples' && (
        <div className="space-y-6">
          <div className="glass-panel p-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[var(--accent)]/20 rounded-lg">
                  <Code size={24} className="text-[var(--accent)]" />
                </div>
                <div>
                  <h3 className="font-bold text-xl uppercase tracking-wider">Exemplos de Código</h3>
                  <p className="text-sm text-[var(--text-secondary)]">Pipeline de síntese de voz</p>
                </div>
              </div>
            </div>
            
            {/* Tabs de linguagem */}
            <div className="flex gap-1 p-1 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg mb-4">
              {languageTabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setCodeLanguage(tab.id)}
                    className={`flex-1 px-4 py-2 text-sm font-bold uppercase tracking-wider rounded-md transition-all flex items-center justify-center gap-2 ${
                      codeLanguage === tab.id
                        ? 'bg-[var(--accent)] text-white'
                        : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--border-color)]/50'
                    }`}
                  >
                    <Icon size={14} />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* Bloco de código da linguagem selecionada */}
            <CodeBlock 
              code={codeExamples[codeLanguage]} 
              id={`code-${codeLanguage}`} 
              language={codeLanguage}
            />

            <div className="mt-4 p-4 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg">
              <p className="text-sm text-[var(--text-secondary)]">
                <span className="text-[var(--accent)] font-bold">Parâmetros:</span>
              </p>
              <ul className="mt-2 space-y-1 text-sm text-[var(--text-secondary)]">
                <li>• <code className="text-[var(--text-primary)]">profile_id</code> - ID do perfil de voz</li>
                <li>• <code className="text-[var(--text-primary)]">text</code> - Texto para sintetizar</li>
                <li>• <code className="text-[var(--text-primary)]">emotion</code> - Emoção (neutral, happy, sad, angry)</li>
                <li>• <code className="text-[var(--text-primary)]">language</code> - Idioma (pt-BR, en-US, etc)</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* ========== SEÇÃO ENDPOINTS ========== */}
      {activeTab === 'endpoints' && (
        <div className="space-y-6">
          {endpointGroups.map((group) => {
            const GroupIcon = group.icon;
            return (
              <div key={group.category} className="glass-panel p-6">
                {/* Header do grupo */}
                <div className="flex items-center gap-3 mb-4 pb-4 border-b border-[var(--border-color)]">
                  <div className="p-2 bg-[var(--accent)]/20 rounded-lg">
                    <GroupIcon size={20} className="text-[var(--accent)]" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg uppercase tracking-wider">{group.category}</h3>
                    <p className="text-sm text-[var(--text-secondary)]">{group.description}</p>
                  </div>
                </div>
                
                {/* Lista de endpoints */}
                <div className="space-y-2">
                  {group.endpoints.map((endpoint, i) => {
                    const endpointId = `${group.category}-${i}`;
                    const isExpanded = expandedEndpoints[endpointId];
                    
                    return (
                      <div key={i} className="border border-[var(--border-color)] rounded-lg overflow-hidden transition-all hover:border-[var(--accent)]/50">
                        {/* Linha principal do endpoint */}
                        <button
                          onClick={() => toggleEndpoint(endpointId)}
                          className="w-full flex items-center gap-4 p-4 bg-[var(--bg-primary)] hover:bg-[var(--bg-primary)]/80 transition-colors text-left"
                        >
                          <span className={`px-2 py-1 text-xs font-bold uppercase rounded ${
                            endpoint.method === 'GET' ? 'bg-green-500/20 text-green-400' :
                            endpoint.method === 'POST' ? 'bg-blue-500/20 text-blue-400' :
                            'bg-red-500/20 text-red-400'
                          }`}>
                            {endpoint.method}
                          </span>
                          <code className="font-mono text-sm flex-1">/api/v1{endpoint.path}</code>
                          <span className="text-xs text-[var(--text-secondary)] hidden sm:block">{endpoint.desc}</span>
                          {endpoint.auth && (
                            <span className="px-2 py-0.5 text-xs bg-[var(--accent)]/20 text-[var(--accent)] rounded flex items-center gap-1">
                              <Key size={10} /> Auth
                            </span>
                          )}
                          <ChevronDown 
                            size={16} 
                            className={`text-[var(--text-secondary)] transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
                          />
                        </button>
                        
                        {/* Detalhes expandidos */}
                        {isExpanded && (
                          <div className="p-4 bg-[var(--bg-secondary)] border-t border-[var(--border-color)] space-y-3 animate-fade-in">
                            <p className="text-sm text-[var(--text-secondary)]">{endpoint.details}</p>
                            <div>
                              <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] block mb-2">Resposta de exemplo:</span>
                              <CodeBlock code={endpoint.response} id={`response-${endpointId}`} />
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
            
          {/* Link para documentação completa */}
          <div className="glass-panel p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Book size={20} className="text-[var(--accent)]" />
                <div>
                  <p className="font-bold">Documentação Completa</p>
                  <p className="text-sm text-[var(--text-secondary)]">Swagger UI com todos os endpoints e schemas</p>
                </div>
              </div>
              <a 
                href={`${baseUrl}/docs`} 
                target="_blank" 
                rel="noopener noreferrer"
                className="px-4 py-2 bg-[var(--accent)] text-white font-bold uppercase tracking-wider text-sm rounded-lg flex items-center gap-2 hover:opacity-90 transition-opacity"
              >
                Abrir Docs <ExternalLink size={14} />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// --- LOGIN MODAL COMPONENT ---
const LoginModal = ({ onClose, onSuccess }) => {
  const { auth } = useApi();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      if (isRegister) {
        await auth.register(email, password, name);
      } else {
        await auth.login(email, password);
      }
      onSuccess();
    } catch (err) {
      setError(err.message || 'Falha na autenticação');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="glass-panel p-8 w-full max-w-md relative">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
        >
          <X size={24} />
        </button>
        
        <div className="text-center mb-8">
          <Box className="mx-auto mb-4 text-[var(--accent)]" size={48} />
          <h2 className="text-2xl font-bold uppercase tracking-wider">
            {isRegister ? 'Criar Conta' : 'Entrar'}
          </h2>
          <p className="text-[var(--text-secondary)] text-sm mt-2">
            {isRegister ? 'Comece a clonar vozes agora' : 'Acesse sua conta'}
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 text-red-500 text-sm flex items-center gap-2">
            <AlertCircle size={18} />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {isRegister && (
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Nome</label>
              <input 
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="tech-input"
                placeholder="Seu nome"
              />
            </div>
          )}
          
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Email</label>
            <input 
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="tech-input"
              placeholder="seu@email.com"
              required
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">Senha</label>
            <input 
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="tech-input"
              placeholder="••••••••"
              required
              minLength={6}
            />
          </div>

          <button 
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-[var(--text-primary)] text-[var(--bg-primary)] font-bold uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-[var(--accent)] hover:text-white transition-colors disabled:opacity-50"
          >
            {loading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <>
                <LogIn size={18} />
                {isRegister ? 'Criar Conta' : 'Entrar'}
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button 
            onClick={() => setIsRegister(!isRegister)}
            className="text-sm text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors"
          >
            {isRegister ? 'Já tem conta? Faça login' : 'Não tem conta? Registre-se'}
          </button>
        </div>
      </div>
    </div>
  );
};

// --- APP PRINCIPAL (Gerenciador de Estado) ---

const App = () => {
  const { auth, systemStatus } = useApi();
  
  // Estados
  const [view, setView] = useState('landing'); // 'landing' | 'dashboard'
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [theme, setTheme] = useState('dark');
  const scrollRef = useRef(null);

  // Auto-redirect if already authenticated (com proteção contra re-execução)
  useEffect(() => {
    if (auth.isAuthenticated && !auth.loading && view !== 'dashboard') {
      setView('dashboard');
    }
  }, [auth.isAuthenticated, auth.loading, view]);

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
  
  const handleLoginClick = () => {
    setShowLoginModal(true);
  };
  
  const handleLoginSuccess = () => {
    setShowLoginModal(false);
    setView('dashboard');
  };
  
  const handleLogout = () => {
    auth.logout();
    setView('landing');
  };

  // Não bloquear UI durante verificação de auth - renderizar landing imediatamente
  return (
    <>
      <GlobalStyles theme={theme} />
      
      {/* Login Modal */}
      {showLoginModal && (
        <LoginModal 
          onClose={() => setShowLoginModal(false)} 
          onSuccess={handleLoginSuccess}
        />
      )}
      
      {/* Renderização Condicional da View */}
      {view === 'landing' ? (
        <>
          <SacredGeometry activeIndex={activeIndex} theme={theme} />
          <NavigationDots total={5} active={activeIndex} scrollTo={scrollTo} />

          {/* Header Landing - mix-blend-difference inverte cores, então status fica separado */}
          <div className="fixed top-0 left-0 w-full p-8 flex justify-between items-center z-50 pointer-events-none">
            {/* Logo com mix-blend-difference */}
            <div className="flex items-center gap-2 pointer-events-auto mix-blend-difference text-white">
              <Box className="animate-pulse" size={24} strokeWidth={2} />
              <span className="font-bold tracking-widest text-lg">AETHER</span>
            </div>
            <div className="flex items-center gap-6 pointer-events-auto">
              {/* System Status Indicator - SEM mix-blend para manter cor verde correta */}
              <div className="flex items-center gap-2 text-xs">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: systemStatus.online ? '#22c55e' : '#ef4444' }} />
                <span style={{ color: systemStatus.online ? '#22c55e' : '#ef4444' }}>
                  {systemStatus.online ? 'Online' : 'Offline'}
                </span>
              </div>
              {/* Botões com mix-blend-difference */}
              <div className="flex items-center gap-4 mix-blend-difference text-white">
                <button onClick={toggleTheme} className="p-2 border border-white/20 hover:bg-white/10 transition-colors">
                  {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                </button>
                <button onClick={handleLoginClick} className="px-6 py-2 border border-white text-xs font-bold hover:bg-white hover:text-black transition-colors uppercase tracking-widest">
                  Login
                </button>
              </div>
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