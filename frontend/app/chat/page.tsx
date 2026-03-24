"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";

export default function ChatPage() {
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<{ role: string; content: any }[]>([]);
  const [copied, setCopied] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);

  // 1. Create a ref for the bottom of the chat
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadingMessages = [
    "Lead Developer is architecting logic...",
    "QA Engineer is scanning for vulnerabilities...",
    "Documentarian is generating specifications...",
    "Orchestrator is finalizing the build..."
  ];

  // 2. Function to scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // 3. Trigger scroll whenever messages or loading state changes
  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, loadingStep]);

  useEffect(() => {
    let interval: any;
    if (isLoading) {
      interval = setInterval(() => {
        setLoadingStep((prev) => (prev + 1) % loadingMessages.length);
      }, 2000);
    } else {
      setLoadingStep(0);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSend = () => {
    if (!prompt.trim() || isLoading) return;
    
    const newMessages = [...messages, { role: "user", content: prompt }];
    setMessages(newMessages);
    setPrompt("");
    setIsLoading(true);

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "MACE",
          content: {
            code: "def main():\n    # MACE Generated Logic\n    print('System initialized')\n    return True",
            feedback: "All systems green. Optimization score: 98%.",
            document: "Build Version: 1.0.4\nEnvironment: Production-ready"
          }
        }
      ]);
      setIsLoading(false);
    }, 6000); 
  };

  return (
    <main className="flex flex-col h-screen bg-black text-white selection:bg-white/20">
      <header className="p-4 border-b border-white/5 flex justify-between items-center bg-black sticky top-0 z-10">
        <Link href="/" className="text-xs text-gray-500 hover:text-white transition-colors tracking-widest uppercase font-medium">
          ← Back
        </Link>
        <h1 className="text-xl font-light italic tracking-tighter uppercase">MACE</h1>
        <div className="w-10"></div>
      </header>

      <div className="flex-1 overflow-y-auto p-4 md:p-10 space-y-12 custom-scrollbar">
        <AnimatePresence>
          {messages.map((msg, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`max-w-4xl mx-auto flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
            >
              {msg.role === "user" ? (
                <div className="flex flex-col items-end gap-3">
                  <span className="text-[10px] text-white/30 uppercase tracking-[0.3em] font-bold">YOU</span>
                  <div className="bg-[#111] border border-white/10 p-5 rounded-3xl rounded-tr-none text-gray-300 font-light max-w-md shadow-xl">
                    {msg.content}
                  </div>
                </div>
              ) : (
                <div className="w-full flex flex-col gap-6">
                  <span className="text-[10px] text-white/30 uppercase tracking-[0.3em] font-bold ml-1">MACE Analysis</span>
                  
                  <div className="bg-[#0A0A0A] border border-white/10 p-7 rounded-3xl relative overflow-hidden group">
                    <div className="absolute top-0 left-0 w-1.5 h-full bg-blue-500/40" />
                    <div className="flex justify-between items-start mb-4">
                      <h4 className="text-[10px] font-bold uppercase text-blue-400 tracking-widest">Code Implementation</h4>
                      <button 
                        onClick={() => handleCopy(msg.content.code)}
                        className="text-[10px] uppercase tracking-widest bg-white/5 border border-white/10 px-3 py-1 rounded-full hover:bg-white/10 transition-all text-gray-400 hover:text-white"
                      >
                        {copied ? "Copied!" : "Copy"}
                      </button>
                    </div>
                    <pre className="text-sm text-gray-400 font-mono whitespace-pre-wrap leading-relaxed bg-black/40 p-4 rounded-xl border border-white/5">
                      {msg.content.code}
                    </pre>
                  </div>

                  <div className="bg-[#0A0A0A] border border-white/10 p-7 rounded-3xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1.5 h-full bg-emerald-500/40" />
                    <h4 className="text-[10px] font-bold uppercase text-emerald-400 mb-4 tracking-widest">Agent Feedback</h4>
                    <p className="text-sm text-gray-400 font-light leading-relaxed italic px-2">
                      {msg.content.feedback}
                    </p>
                  </div>

                  <div className="bg-[#0A0A0A] border border-white/10 p-7 rounded-3xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1.5 h-full bg-purple-500/40" />
                    <h4 className="text-[10px] font-bold uppercase text-purple-400 mb-4 tracking-widest">Documentation</h4>
                    <p className="text-sm text-gray-400 font-light leading-relaxed px-2">
                      {msg.content.document}
                    </p>
                  </div>
                </div>
              )}
            </motion.div>
          ))}

          {isLoading && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="max-w-4xl mx-auto w-full"
            >
              <div className="flex flex-col items-start gap-4">
                <span className="text-[10px] text-white/30 uppercase tracking-[0.3em] font-bold ml-1 italic animate-pulse">
                  Agent processing...
                </span>
                <div className="bg-[#0A0A0A] border border-white/5 p-6 rounded-3xl w-full flex items-center gap-4">
                  <div className="flex gap-1">
                    <div className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce [animation-delay:-0.3s]" />
                    <div className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce [animation-delay:-0.15s]" />
                    <div className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce" />
                  </div>
                  <p className="text-sm text-gray-500 font-light italic">
                    {loadingMessages[loadingStep]}
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 4. The Scroll Anchor */}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-8 bg-black">
        <div className="max-w-3xl mx-auto">
          <div className="relative flex items-center bg-[#0D0D0D] border border-white/10 rounded-full px-7 py-2.5 shadow-2xl focus-within:border-white/20 transition-all group">
            <input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder={isLoading ? "Agents at work..." : "Message MACE..."}
              disabled={isLoading}
              className="w-full bg-transparent border-none outline-none py-3 text-white placeholder:text-gray-700 font-light text-sm disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!prompt.trim() || isLoading}
              className="ml-3 bg-white text-black p-2.5 rounded-full hover:bg-gray-200 transition-all active:scale-95 disabled:opacity-5 disabled:grayscale"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                <path d="M3.105 2.289a.75.75 0 0 0-.826.95l1.414 4.925A1.5 1.5 0 0 0 5.135 9.25h6.115a.75.75 0 0 1 0 1.5H5.135a1.5 1.5 0 0 0-1.442 1.086l-1.414 4.926a.75.75 0 0 0 .826.95 28.896 28.896 0 0 0 15.293-7.154.75.75 0 0 0 0-1.115A28.897 28.897 0 0 0 3.105 2.289Z" />
              </svg>
            </button>
          </div>
          <p className="text-center text-[9px] text-gray-800 mt-5 tracking-[0.3em] uppercase font-bold">
            MACE AGENT FRAMEWORK 2026
          </p>
        </div>
      </div>
    </main>
  );
}