"use client";

import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import ChatWidget from "@/components/ChatWidget";

export default function SalespersonDashboard() {
  const [activeTab, setActiveTab] = useState<"feedback" | "leads">("feedback");
  
  // Feedback Tab State
  const [feedbackText, setFeedbackText] = useState("");
  const [feedbackGrammar, setFeedbackGrammar] = useState("");
  const [feedbackAiResult, setFeedbackAiResult] = useState<{label: string, score: number} | null>(null);
  
  // Lead Tab State
  const [leadText, setLeadText] = useState("");
  const [leadGrammar, setLeadGrammar] = useState("");
  const [leadAiResult, setLeadAiResult] = useState<{label: string, score: number, explanation?: string} | null>(null);

  const [statusMsg, setStatusMsg] = useState({ text: "", type: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const userStr = localStorage.getItem("user") || sessionStorage.getItem("user");
    if (!userStr) {
      window.location.href = "/login";
    }
  }, []);

  const secureFetch = async (url: string, options: any = {}) => {
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    const defaultHeaders = {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    };
    options.headers = { ...defaultHeaders, ...options.headers };
    const response = await fetch(url, options);
    if (response.status === 401) {
      localStorage.clear();
      sessionStorage.clear();
      window.location.href = "/login";
      throw new Error("Unauthorized");
    }
    return response;
  };

  const checkGrammar = async (type: "feedback" | "lead") => {
    const text = type === "feedback" ? feedbackText : leadText;
    if (!text) return;
    
    try {
      const res = await secureFetch("/api/grammar-check", {
        method: "POST",
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      if (res.ok) {
        if (type === "feedback") setFeedbackGrammar(data.corrected_text);
        else setLeadGrammar(data.corrected_text);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const submitData = async (type: "feedback" | "lead") => {
    const text = type === "feedback" ? feedbackText : leadText;
    if (!text.trim()) {
      setStatusMsg({ text: "Please enter some text first", type: "error" });
      return;
    }

    setIsSubmitting(true);
    setStatusMsg({ text: "", type: "" });
    const apiUrl = type === "lead" ? "/api/submit-lead" : "/api/analyze-feedback";

    try {
      const res = await secureFetch(apiUrl, {
        method: "POST",
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      
      if (res.ok) {
        setStatusMsg({ text: `${type === "lead" ? "Lead" : "Feedback"} submitted successfully!`, type: "success" });
        if (type === "feedback") {
          setFeedbackText("");
          setFeedbackGrammar("");
          setFeedbackAiResult({ label: data.sentiment_result.label, score: (data.sentiment_result.score * 100) });
        } else {
          setLeadText("");
          setLeadGrammar("");
          setLeadAiResult({ label: data.ml_result.label, score: (data.ml_result.score * 100), explanation: data.ml_result.explanation });
        }
      } else {
        throw new Error(data.error || "Submission failed");
      }
    } catch (e: any) {
      setStatusMsg({ text: e.message || "Error submitting data", type: "error" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#667eea] to-[#764ba2] text-gray-800 pb-10">
      <Navbar title="Salesperson Dashboard" />
      
      <div className="max-w-4xl mx-auto px-6 py-8">
        
        {/* Tab Navigation */}
        <div className="flex gap-4 mb-6">
          <button 
            onClick={() => setActiveTab("feedback")}
            className={`px-6 py-3 rounded-lg font-bold transition-all shadow-sm ${
              activeTab === "feedback" 
                ? "bg-white text-[#667eea]" 
                : "bg-white/20 text-white hover:bg-white/30"
            }`}
          >
            Customer Feedback
          </button>
          <button 
            onClick={() => setActiveTab("leads")}
            className={`px-6 py-3 rounded-lg font-bold transition-all shadow-sm ${
              activeTab === "leads" 
                ? "bg-white text-[#667eea]" 
                : "bg-white/20 text-white hover:bg-white/30"
            }`}
          >
            Submit Sales Lead
          </button>
        </div>

        {/* Content Area */}
        <div className="bg-white rounded-2xl p-8 shadow-xl animate-fade-in-up">
          
          {/* Status Message */}
          {statusMsg.text && (
            <div className={`mb-6 p-4 rounded-xl border ${
              statusMsg.type === "success" 
                ? "bg-green-50 border-green-200 text-green-700" 
                : "bg-red-50 border-red-200 text-red-700"
            }`}>
              {statusMsg.text}
            </div>
          )}

          {/* Feedback Tab */}
          {activeTab === "feedback" && (
            <div className="animate-fade-in-up">
              <h3 className="text-xl font-bold mb-6 text-[#667eea]">Customer Feedback Submission</h3>
              
              <div className="mb-6">
                <label className="block text-sm font-semibold mb-2 text-gray-700">Feedback Details:</label>
                <textarea
                  value={feedbackText}
                  onChange={e => setFeedbackText(e.target.value)}
                  className="w-full h-40 bg-gray-50 border border-gray-200 rounded-xl p-4 text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#667eea]"
                  placeholder="Enter general customer feedback, complaints, or suggestions..."
                />
              </div>

              <div className="bg-gray-50 border border-gray-100 p-4 rounded-xl mb-6">
                <button 
                  onClick={() => checkGrammar("feedback")}
                  className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded-lg font-medium transition-colors mb-3"
                >
                  Check Grammar
                </button>
                {feedbackGrammar && (
                  <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-lg text-sm text-indigo-800">
                    <span className="font-bold">Suggestion:</span> {feedbackGrammar}
                    <button 
                      onClick={() => { setFeedbackText(feedbackGrammar); setFeedbackGrammar(""); }}
                      className="ml-4 text-[#667eea] hover:underline font-semibold"
                    >
                      Apply
                    </button>
                  </div>
                )}
              </div>

              <div className="flex gap-4">
                <button 
                  onClick={() => submitData("feedback")}
                  disabled={isSubmitting}
                  className="flex-1 bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white font-bold py-3 rounded-xl hover:shadow-lg transition-all disabled:opacity-70"
                >
                  {isSubmitting ? "Submitting..." : "Submit Feedback"}
                </button>
                <button 
                  onClick={() => { setFeedbackText(""); setFeedbackGrammar(""); }}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 rounded-xl transition-colors"
                >
                  Reset
                </button>
              </div>

              {/* AI Result */}
              {feedbackAiResult && (
                <div className="mt-8 p-6 bg-gray-50 border border-gray-200 rounded-xl animate-fade-in-up">
                  <h4 className="text-lg font-bold mb-4 text-[#764ba2]">AI Analysis Result</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white p-4 rounded-lg border border-gray-100 shadow-sm text-center">
                      <div className="text-sm text-gray-500 mb-1">Sentiment</div>
                      <div className={`text-xl font-bold ${
                        feedbackAiResult.label === "Positive" ? "text-green-600" :
                        feedbackAiResult.label === "Neutral" ? "text-amber-600" : "text-red-600"
                      }`}>{feedbackAiResult.label}</div>
                    </div>
                    <div className="bg-white p-4 rounded-lg border border-gray-100 shadow-sm text-center">
                      <div className="text-sm text-gray-500 mb-1">Confidence Score</div>
                      <div className="text-xl font-bold text-[#667eea]">{feedbackAiResult.score.toFixed(1)}%</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Leads Tab */}
          {activeTab === "leads" && (
            <div className="animate-fade-in-up">
              <h3 className="text-xl font-bold mb-6 text-[#764ba2]">Sales Lead Submission</h3>
              
              <div className="mb-6">
                <label className="block text-sm font-semibold mb-2 text-gray-700">Lead Details:</label>
                <textarea
                  value={leadText}
                  onChange={e => setLeadText(e.target.value)}
                  className="w-full h-40 bg-gray-50 border border-gray-200 rounded-xl p-4 text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#764ba2]"
                  placeholder="Enter details about the potential sales lead..."
                />
              </div>

              <div className="bg-gray-50 border border-gray-100 p-4 rounded-xl mb-6">
                <button 
                  onClick={() => checkGrammar("lead")}
                  className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded-lg font-medium transition-colors mb-3"
                >
                  Check Grammar
                </button>
                {leadGrammar && (
                  <div className="p-3 bg-purple-50 border border-purple-100 rounded-lg text-sm text-purple-800">
                    <span className="font-bold">Suggestion:</span> {leadGrammar}
                    <button 
                      onClick={() => { setLeadText(leadGrammar); setLeadGrammar(""); }}
                      className="ml-4 text-[#764ba2] hover:underline font-semibold"
                    >
                      Apply
                    </button>
                  </div>
                )}
              </div>

              <div className="flex gap-4">
                <button 
                  onClick={() => submitData("lead")}
                  disabled={isSubmitting}
                  className="flex-1 bg-gradient-to-r from-[#764ba2] to-[#667eea] text-white font-bold py-3 rounded-xl hover:shadow-lg transition-all disabled:opacity-70"
                >
                  {isSubmitting ? "Submitting..." : "Submit Lead"}
                </button>
                <button 
                  onClick={() => { setLeadText(""); setLeadGrammar(""); }}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 rounded-xl transition-colors"
                >
                  Reset
                </button>
              </div>

              {/* AI Result */}
              {leadAiResult && (
                <div className="mt-8 p-6 bg-gray-50 border border-gray-200 rounded-xl animate-fade-in-up">
                  <h4 className="text-lg font-bold mb-4 text-[#667eea]">AI Lead Prediction</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white p-4 rounded-lg border border-gray-100 shadow-sm text-center">
                      <div className="text-sm text-gray-500 mb-1">Lead Quality</div>
                      <div className={`text-xl font-bold ${
                        leadAiResult.label === "High" ? "text-green-600" :
                        leadAiResult.label === "Medium" ? "text-amber-600" : "text-red-600"
                      }`}>{leadAiResult.label}</div>
                    </div>
                    <div className="bg-white p-4 rounded-lg border border-gray-100 shadow-sm text-center">
                      <div className="text-sm text-gray-500 mb-1">Confidence Score</div>
                      <div className="text-xl font-bold text-[#764ba2]">{leadAiResult.score.toFixed(1)}%</div>
                    </div>
                  </div>
                  {leadAiResult.explanation && (
                    <div className="mt-4 p-4 bg-indigo-50 border border-indigo-100 rounded-lg text-sm text-indigo-800 flex items-start gap-2">
                      <span className="text-xl">💡</span>
                      <div>
                        <span className="font-bold block mb-1">AI Reasoning</span>
                        {leadAiResult.explanation}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      {/* Floating Chat Widget */}
      <ChatWidget />
    </div>
  );
}
