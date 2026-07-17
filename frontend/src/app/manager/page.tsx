"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

type DashboardData = {
  stats: { 
    total: number; 
    week: number; 
    active_sales: number;
    leads: { high: number; medium: number; low: number };
  };
  trends: { date: string; leads: number; avgLeadScore: number; feedback: number; avgSentiment: number }[];
  wordcloud_data: [string, number][];
  recent: any[];
};

export default function ManagerDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const token = localStorage.getItem("token") || sessionStorage.getItem("token");
      const res = await fetch("/api/dashboard", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.status === 401) {
        window.location.href = "/login";
        return;
      }
      const json = await res.json();
      if (res.ok) {
        setData(json);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const downloadReport = async () => {
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    window.location.href = `/api/download-report?token=${token}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0f0f23] text-white flex items-center justify-center">
        <div className="animate-pulse text-xl text-indigo-400 font-bold flex items-center gap-2">
          <span>Loading Dashboard...</span>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const pieData = [
    { name: "High Quality", value: data.stats.leads.high, color: "#059669" },
    { name: "Medium Quality", value: data.stats.leads.medium, color: "#d97706" },
    { name: "Low Quality", value: data.stats.leads.low, color: "#dc2626" },
  ].filter(d => d.value > 0);

  const lineData = data.trends; // Now an array of objects

  // Simple Word Cloud implementation using flex
  // Find max value to scale font sizes
  const maxWordValue = Math.max(...(data.wordcloud_data?.map(d => d[1]) || [1]), 1);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#667eea] to-[#764ba2] text-gray-800">
      <Navbar title="Manager Dashboard" />
      
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex justify-end mb-8">
          <button 
            onClick={downloadReport}
            className="px-6 py-2 bg-white text-[#764ba2] rounded-lg font-bold hover:shadow-lg transition-all flex items-center gap-2 shadow"
          >
            <span>📥</span> Download Report
          </button>
        </div>

        {/* Top Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {[
            { label: "Total Feedbacks", value: data.stats?.total || 0, icon: "📊" },
            { label: "This Week", value: data.stats?.week || 0, icon: "📈" },
            { label: "Active Salespeople", value: data.stats?.active_sales || 0, icon: "👥" },
          ].map((stat, i) => (
            <div key={i} className="bg-white rounded-2xl p-6 shadow-xl animate-fade-in-up" style={{ animationDelay: `${i * 100}ms` }}>
              <div className="text-3xl mb-2">{stat.icon}</div>
              <h4 className="text-gray-500 text-sm font-medium mb-1">{stat.label}</h4>
              <p className="text-4xl font-bold text-gray-800">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* AI Lead Score */}
          <div className="bg-white rounded-2xl p-6 shadow-xl col-span-1 flex flex-col animate-fade-in-up delay-300">
            <h3 className="text-xl font-bold mb-6 text-[#764ba2]">AI Lead Scores</h3>
            <div className="flex-1 min-h-[300px]">
              {pieData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value">
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'white', borderColor: '#e5e7eb', borderRadius: '8px', color: '#1f2937' }}
                      itemStyle={{ color: '#1f2937' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-gray-400">No lead data yet</div>
              )}
            </div>
            <div className="flex justify-center gap-4 mt-4 flex-wrap text-sm text-gray-600">
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-[#059669]"></div>High</div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-[#d97706]"></div>Med</div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-[#dc2626]"></div>Low</div>
            </div>
          </div>

          {/* Trends Chart */}
          <div className="bg-white rounded-2xl p-6 shadow-xl col-span-1 lg:col-span-2 flex flex-col animate-fade-in-up delay-300">
            <h3 className="text-xl font-bold mb-6 text-[#667eea]">Advanced BI: Average Sentiment vs AI Lead Scores</h3>
            <div className="flex-1 min-h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lineData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis dataKey="date" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" domain={[0, 1]} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'white', borderColor: '#e5e7eb', borderRadius: '8px', color: '#1f2937' }}
                  />
                  <Line type="monotone" name="Avg Lead Score" dataKey="avgLeadScore" stroke="#059669" strokeWidth={3} activeDot={{ r: 8 }} />
                  <Line type="monotone" name="Avg Sentiment Score" dataKey="avgSentiment" stroke="#8b5cf6" strokeWidth={3} activeDot={{ r: 8 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Word Cloud & Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl p-6 shadow-xl animate-fade-in-up delay-400">
            <h3 className="text-xl font-bold mb-6 text-[#764ba2]">High-Value Keywords</h3>
            <div className="flex flex-wrap gap-4 items-center justify-center p-4 min-h-[250px]">
              {data.wordcloud_data.map(([word, value], i) => (
                <span 
                  key={word} 
                  className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#667eea] to-[#764ba2] transition-all hover:scale-110 cursor-default"
                  style={{ fontSize: `${Math.max(14, (value / maxWordValue) * 40)}px` }}
                >
                  {word}
                </span>
              ))}
              {data.wordcloud_data.length === 0 && (
                <div className="text-gray-400">No keywords available</div>
              )}
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-xl animate-fade-in-up delay-400">
            <h3 className="text-xl font-bold mb-6 text-[#667eea]">Recent Activity</h3>
            <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
              {data.recent.map((item, i) => (
                <div key={i} className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-medium px-2 py-1 bg-white border border-gray-200 rounded-md text-gray-600">
                      {item.type === 'lead' ? '🎯 Lead' : '💬 Feedback'}
                    </span>
                    <span className="text-xs text-gray-400">{item.time}</span>
                  </div>
                  <p className="text-gray-800 text-sm mb-2">{item.text}</p>
                  <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-200">
                    <span className="text-xs text-gray-500">User: <span className="font-semibold text-gray-700">{item.salesperson}</span></span>
                    <span className={`text-xs font-bold px-2 py-1 rounded-md ${
                      (item.label?.includes('High') || item.label?.includes('Positive')) ? 'bg-green-100 text-green-700' :
                      (item.label?.includes('Medium') || item.label?.includes('Neutral')) ? 'bg-amber-100 text-amber-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {item.label || "Unknown"} ({(item.score * 100).toFixed(0)}%)
                    </span>
                  </div>
                </div>
              ))}
              {data.recent.length === 0 && (
                <div className="text-gray-400 text-center py-8">No recent activity</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
