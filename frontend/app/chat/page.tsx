"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";

export default function ChatPage() {
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);

  const handleSend = () => {
    if (!prompt.trim()) return;
    
    // Add the typed prompt to the message history
    setMessages([...messages, { role: "user", content: prompt }]);
    setPrompt(""); // Clear the input box
  };

  return (
    <main className="flex flex-col h-screen bg-black text-white">
      {/* Header */}
      <header className="p-4 border-b border-white/10 flex justify-between items-center bg-black/50 backdrop-blur-md sticky top-0 z-10">
        <Link href="/" className="text-sm text-gray-400 hover:text-white transition-colors">
          ← Back
        </Link>
        <h1 className="text-xl font-light italic tracking-tighter">MACE <span className="text-white/40"></span></h1>
        <div className="w-10"></div> {/* Spacer for symmetry */}
      </header>

      {/* 1. THE ABOVE BOX: Display area for messages */}
      <div className="flex-1 overflow-y-auto p-4 md:p-10 space-y-6 custom-scrollbar">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <p className="text-gray-600 font-light italic text-lg">Start by typing your requirements below...</p>
          </div>
        ) : (
          <AnimatePresence>
            {messages.map((msg, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-2xl mx-auto flex flex-col items-end"
              >
                <div className="bg-[#111] border border-white/10 p-4 rounded-2xl rounded-tr-none text-gray-200 font-light leading-relaxed">
                  {msg.content}
                </div>
                <span className="text-[10px] text-gray-600 mt-2 uppercase tracking-widest">You</span>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* 2. THE BELOW BOX: Where you type (ChatGPT/Gemini style) */}
      <div className="p-4 md:p-8 bg-gradient-to-t from-black via-black to-transparent">
        <div className="max-w-3xl mx-auto relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-white/10 to-white/5 rounded-2xl blur opacity-30 group-focus-within:opacity-50 transition duration-1000"></div>
          
          <div className="relative flex items-end gap-2 bg-[#0A0A0A] border border-white/10 rounded-2xl p-2 pl-4">
            <textarea
              rows={1}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Message MACE..."
              className="w-full bg-transparent border-none outline-none py-3 resize-none text-white placeholder:text-gray-600 font-light"
              style={{ maxHeight: '200px' }}
            />
            
            <button
              onClick={handleSend}
              disabled={!prompt.trim()}
              className="bg-white text-black p-2.5 rounded-xl hover:bg-gray-200 transition-all disabled:opacity-20 disabled:grayscale"
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 24 24" 
                fill="currentColor" 
                className="w-5 h-5"
              >
                <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
              </svg>
            </button>
          </div>
          <p className="text-center text-[10px] text-gray-600 mt-3 uppercase tracking-tighter">
            MACE can make mistakes. 
          </p>
        </div>
      </div>
    </main>
  );
}