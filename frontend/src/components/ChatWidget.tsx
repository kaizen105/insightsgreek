"use client";

import { useState, useRef, useEffect } from "react";

type Message = {
  role: "user" | "bot";
  content: string;
};

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: "bot", content: "Hello! I can help you refine your pitch, analyze this lead, or suggest next steps based on what you're typing." }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const toggleChat = () => setIsOpen(!isOpen);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const token = localStorage.getItem("token") || sessionStorage.getItem("token");
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ message: userMessage })
      });

      if (!res.ok) {
        if (res.status === 401) {
          window.location.href = "/login";
          return;
        }
        throw new Error("Chat request failed");
      }

      const data = await res.json();
      setMessages((prev) => [...prev, { role: "bot", content: data.reply || "No response received" }]);
    } catch (err: any) {
      setMessages((prev) => [...prev, { role: "bot", content: "Sorry, I encountered an error. Please try again." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {isOpen && (
        <div className="mb-4 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden flex flex-col h-[400px] transition-all transform origin-bottom-right">
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-4 text-white flex justify-between items-center shadow-md">
            <div className="font-bold flex items-center gap-2">
              <span>🤖</span> AI Assistant
            </div>
            <button 
              onClick={toggleChat}
              className="text-white/80 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.map((msg, i) => (
              <div 
                key={i} 
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div 
                  className={`max-w-[80%] rounded-2xl px-4 py-2 shadow-sm text-sm ${
                    msg.role === "user" 
                      ? "bg-indigo-600 text-white rounded-tr-sm" 
                      : "bg-white text-gray-800 border border-gray-100 rounded-tl-sm"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-100 text-gray-400 rounded-2xl rounded-tl-sm px-4 py-2 shadow-sm text-sm flex gap-1">
                  <span className="animate-bounce">.</span><span className="animate-bounce delay-100">.</span><span className="animate-bounce delay-200">.</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-3 bg-white border-t border-gray-100 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Ask AI..."
              className="flex-1 bg-gray-100 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-gray-800"
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !input.trim()}
              className="bg-indigo-600 text-white rounded-full p-2 w-10 h-10 flex items-center justify-center hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              ↗
            </button>
          </div>
        </div>
      )}
      
      {!isOpen && (
        <button
          onClick={toggleChat}
          className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-full w-14 h-14 flex items-center justify-center shadow-xl hover:shadow-indigo-500/30 hover:-translate-y-1 transition-all"
        >
          <span className="text-2xl">🤖</span>
        </button>
      )}
    </div>
  );
}
