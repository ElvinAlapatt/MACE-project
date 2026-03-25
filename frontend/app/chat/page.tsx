"use client";
import ReactMarkdown from "react-markdown";
import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import remarkGfm from "remark-gfm";

export default function ChatPage() {
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<{ role: string; content: any }[]>([]);
  const [copied, setCopied] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadingMessages = [
    "Lead Developer is architecting logic...",
    "QA Engineer is scanning for vulnerabilities...",
    "Documentarian is generating specifications...",
    "Orchestrator is finalizing the build..."
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

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

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  const handleSend = async () => {
    if (!prompt.trim() || isLoading) return;

    const userPrompt = prompt;
    setMessages(prev => [...prev, { role: "user", content: userPrompt }]);
    setPrompt("");
    setIsLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: userPrompt, max_retries: 3 })
      });

      const data = await response.json();

      setMessages(prev => [...prev, {
        role: "MACE",
        content: {
          code: data.generated_code,
          feedback: data.qa_feedback,
          document: data.documentation,
          status: data.status,
          retry_count: data.retry_count,
          time_taken: data.time_taken,
          memory_used: data.memory_used,
          lessons_count: data.lessons_count
        }
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: "MACE",
        content: {
          code: "Error connecting to MACE backend.",
          feedback: "Could not reach the API.",
          document: "",
          status: "error",
          retry_count: 0,
          time_taken: 0,
          memory_used: false,
          lessons_count: 0
        }
      }]);
    } finally {
      setIsLoading(false);
    }
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

                  {/* Code Block */}
                  <div className="bg-[#0A0A0A] border border-white/10 p-7 rounded-3xl relative overflow-hidden group">
                    <div className="absolute top-0 left-0 w-1.5 h-full bg-blue-500/40" />
                    <div className="flex justify-between items-start mb-4">
                      <h4 className="text-[10px] font-bold uppercase text-blue-400 tracking-widest">
                        Code Implementation - [qwen/qwen3-32b]
                      </h4>
                      <button
                        onClick={() => handleCopy(msg.content.code, `code-${index}`)}
                        className="text-[10px] uppercase tracking-widest bg-white/5 border border-white/10 px-3 py-1 rounded-full hover:bg-white/10 transition-all text-gray-400 hover:text-white"
                      >
                        {copied === `code-${index}` ? "Copied!" : "Copy"}
                      </button>
                    </div>
                    <pre className="text-sm text-gray-400 font-mono whitespace-pre-wrap leading-relaxed bg-black/40 p-4 rounded-xl border border-white/5">
                      {msg.content.code}
                    </pre>
                  </div>

                  {/* Feedback Block */}
                  <div className="bg-[#0A0A0A] border border-white/10 p-7 rounded-3xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1.5 h-full bg-emerald-500/40" />
                    <h4 className="text-[10px] font-bold uppercase text-emerald-400 mb-4 tracking-widest">
                      Agent Feedbacks - [llama-3.3-70b-versatile]
                    </h4>
                    <p className="text-sm text-gray-400 font-light leading-relaxed italic px-2">
                      {msg.content.feedback}
                    </p>
                  </div>

                  {/* Documentation Block */}
                  <div className="bg-[#0A0A0A] border border-white/10 p-7 rounded-3xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1.5 h-full bg-purple-500/40" />
                    <div className="flex justify-between items-start mb-4">
                      <h4 className="text-[10px] font-bold uppercase text-purple-400 tracking-widest">
                        Documentation - [llama-3.3-70b-versatile]
                      </h4>
                      <button
                        onClick={() => handleCopy(msg.content.document, `doc-${index}`)}
                        className="text-[10px] uppercase tracking-widest bg-white/5 border border-white/10 px-3 py-1 rounded-full hover:bg-white/10 transition-all text-gray-400 hover:text-white"
                      >
                        {copied === `doc-${index}` ? "Copied!" : "Copy"}
                      </button>
                    </div>
                    <div className="px-2 text-sm text-gray-400 font-light leading-relaxed
    [&_h1]:text-purple-300 [&_h1]:text-lg [&_h1]:font-semibold [&_h1]:mb-3 [&_h1]:mt-0
    [&_h2]:text-purple-300 [&_h2]:text-base [&_h2]:font-semibold [&_h2]:mt-5 [&_h2]:mb-2
    [&_h3]:text-purple-200 [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:mt-4 [&_h3]:mb-1
    [&_p]:mb-3 [&_p]:text-gray-400
    [&_code]:text-blue-300 [&_code]:bg-black/40 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-xs
    [&_pre]:bg-black/40 [&_pre]:border [&_pre]:border-white/5 [&_pre]:p-4 [&_pre]:rounded-xl [&_pre]:mb-3 [&_pre]:overflow-x-auto
    [&_pre_code]:bg-transparent [&_pre_code]:p-0
    [&_table]:w-full [&_table]:border-collapse [&_table]:mb-3 [&_table]:text-xs
    [&_th]:text-purple-300 [&_th]:text-left [&_th]:border [&_th]:border-white/10 [&_th]:p-2 [&_th]:bg-white/5
    [&_td]:text-gray-400 [&_td]:border [&_td]:border-white/10 [&_td]:p-2
    [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:mb-3
    [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:mb-3
    [&_li]:mb-1 [&_li]:text-gray-400
    [&_strong]:text-gray-300 [&_strong]:font-semibold
    [&_hr]:border-white/10 [&_hr]:my-4">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content.document}</ReactMarkdown>
                    </div>
                  </div>

                  {/* Metadata Strip */}
                  <div className="flex flex-wrap items-center gap-6 px-2">
                    <span className="text-[10px] text-white/50 uppercase tracking-widest font-bold">
                      {msg.content.status === "pass" ? "✅ Pass" : "❌ Failed"}
                    </span>
                    <span className="text-[10px] text-white/50 uppercase tracking-widest font-bold">
                      ⏱ {msg.content.time_taken}s
                    </span>
                    <span className="text-[10px] text-white/50 uppercase tracking-widest font-bold">
                      🔄 {msg.content.retry_count === 0 ? "1st Try" : `${msg.content.retry_count + 1} Attempts`}
                    </span>
                    <span className="text-[10px] text-white/50 uppercase tracking-widest font-bold">
                      🧠 {msg.content.memory_used ? "Memory Used" : "Fresh Start"}
                    </span>
                    <span className="text-[10px] text-white/50 uppercase tracking-widest font-bold">
                      📚 {msg.content.lessons_count} Lessons Stored
                    </span>
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