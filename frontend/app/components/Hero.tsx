"use client";

import { useRef, useState, useEffect } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from "framer-motion";

export default function Hero() {
  const detailsRef = useRef<HTMLDivElement>(null);
  const [showScrollTop, setShowScrollTop] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 500);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToDetails = () => {
    detailsRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <>
      <AnimatePresence>
        {showScrollTop && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={scrollToTop}
            className="fixed bottom-8 right-8 z-50 p-4 rounded-full bg-white/10 border border-white/20 backdrop-blur-md text-white hover:bg-white/20 transition-all shadow-2xl"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
            </svg>
          </motion.button>
        )}
      </AnimatePresence>

      <section className="relative flex flex-col items-center justify-center text-center px-6 py-44 overflow-hidden min-h-screen bg-black">
        <video
          autoPlay
          muted
          loop
          playsInline
          className="absolute inset-0 w-full h-full object-cover z-0 opacity-70"
        >
          <source src="/hero-bg.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-black/20 z-1" />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="relative z-10 max-w-4xl"
        >
          <h1 className="text-5xl md:text-7xl font-semibold tracking-tighter leading-[1.1] text-white">
            The Multi Agent approach to <br />
            <span className="italic font-light text-white/90">Code Synthesis</span>.
          </h1>

          <p className="mt-8 text-gray-400 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed font-light">
            MACE: A multi-agent framework using LangGraph that mimics a dev team Lead Developer, QA and Documentarian for iterative, self-improving code generation and documentation.
          </p>

          <div className="mt-12 flex justify-center gap-4">
            <Link href="/chat">
              <button className="bg-white text-black px-8 py-3 rounded-full font-bold hover:bg-gray-200 transition-all active:scale-95">
                Get started
              </button>
            </Link>
            <button 
              onClick={scrollToDetails}
              className="bg-[#111111] border border-white/10 px-8 py-3 rounded-full text-white text-sm font-medium hover:bg-white/5 transition-all active:scale-95"
            >
              Learn more
            </button>
          </div>
        </motion.div>
      </section>

      <section 
        ref={detailsRef}
        className="relative z-20 bg-black py-32 px-6 border-t border-white/5"
      >
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-light italic tracking-tighter text-white">
              The Agentic Workflow
            </h2>
            <p className="text-gray-500 mt-4 font-light">Three specialized agents, one unified goal.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { title: "Lead Dev", desc: "Architects the core logic and handles complex implementation.", icon: "💻" },
              { title: "QA Engineer", desc: "Performs automated testing and edge-case validation.", icon: "🛡️" },
              { title: "Documentarian", desc: "Ensures clear API docs and readable project guides.", icon: "📝" },
            ].map((agent, i) => (
              <motion.div 
                key={i}
                whileHover={{ y: -5 }}
                className="p-8 bg-[#0A0A0A] border border-white/5 rounded-3xl hover:border-white/20 transition-all group"
              >
                <div className="text-3xl mb-4 group-hover:scale-110 transition-transform">{agent.icon}</div>
                <h3 className="text-xl font-semibold text-white mb-2">{agent.title}</h3>
                <p className="text-gray-500 text-sm font-light leading-relaxed">{agent.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}