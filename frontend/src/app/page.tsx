import Link from "next/link";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Home - InsightGreek-Brain",
  description: "Transform customer interactions and leads into actionable insights with real-time AI lead scoring and analytics.",
};

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0f0f23] text-white selection:bg-indigo-500/30 overflow-hidden relative">
      {/* Background elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-gradient-to-br from-indigo-500 to-purple-700 blur-[120px] pointer-events-none animate-float opacity-30" />
      <div className="absolute bottom-[-15%] right-[-15%] w-[50%] h-[50%] rounded-full bg-gradient-to-br from-pink-500 to-rose-500 blur-[120px] pointer-events-none animate-float delay-300 opacity-20" />
      <div className="absolute top-[50%] left-[50%] w-[350px] h-[350px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 blur-[120px] pointer-events-none animate-float delay-500 opacity-20" />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0f0f23]/90 backdrop-blur-md border-b border-white/10 animate-slide-down">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-500 bg-clip-text text-transparent flex items-center gap-2">
            <span>📊</span> InsightGreek-Brain
          </div>
          <div className="flex items-center gap-6">
            <Link 
              href="/login" 
              className="text-white/80 hover:text-white transition-colors font-medium"
            >
              Login
            </Link>
            <Link 
              href="/register" 
              className="px-6 py-2.5 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium shadow-[0_4px_15px_rgba(102,126,234,0.3)] hover:shadow-[0_6px_20px_rgba(102,126,234,0.5)] transition-all hover:-translate-y-0.5"
            >
              Create Account
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 px-6 flex flex-col items-center justify-center min-h-[80vh] text-center z-10">
        <div className="inline-flex items-center gap-2 px-5 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-sm font-semibold mb-8 animate-pulse-glow">
          ✨ Powered by AI
        </div>
        
        <h1 className="text-5xl lg:text-7xl font-bold tracking-tight mb-6 bg-gradient-to-b from-white to-indigo-200 bg-clip-text text-transparent animate-fade-in-up delay-100">
          The InsightGreek Platform
        </h1>
        
        <p className="text-lg lg:text-xl text-white/70 max-w-2xl mb-10 leading-relaxed animate-fade-in-up delay-200">
          Transform customer interactions and leads into actionable insights with real-time AI lead scoring and analytics.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center gap-5 animate-fade-in-up delay-300">
          <Link 
            href="/register" 
            className="w-full sm:w-auto px-10 py-4 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold shadow-[0_10px_30px_rgba(102,126,234,0.4)] hover:shadow-[0_15px_40px_rgba(102,126,234,0.6)] transition-all hover:-translate-y-1"
          >
            Get Started Free
          </Link>
          <Link 
            href="/login" 
            className="w-full sm:w-auto px-10 py-4 rounded-full bg-transparent border-2 border-white/30 text-white font-semibold hover:bg-white/10 hover:border-white transition-all"
          >
            Sign In &rarr;
          </Link>
        </div>
      </main>

      {/* Features Section */}
      <section className="relative z-10 py-20 px-6 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: "🎯",
              title: "AI Lead Scoring",
              desc: "Automatically score leads with 90% accuracy using machine learning models fine-tuned on sales data.",
              delay: "delay-100"
            },
            {
              icon: "📈",
              title: "Real-time Analytics",
              desc: "Get instant insights with word clouds, sentiment analysis, and conversion trends across your team.",
              delay: "delay-200"
            },
            {
              icon: "🤝",
              title: "Team Collaboration",
              desc: "Empower salespeople, managers, and developers with role-based dashboards tailored to their needs.",
              delay: "delay-300"
            },
          ].map((feature, i) => (
            <div 
              key={i}
              className={`p-8 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition-colors animate-fade-in-up ${feature.delay}`}
            >
              <div className="text-4xl mb-6">{feature.icon}</div>
              <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
              <p className="text-white/60 leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Stats Section */}
      <section className="relative z-10 py-20 px-6 bg-gradient-to-b from-transparent to-black/30 border-t border-white/5">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-3 gap-8 text-center">
          <div>
            <div className="text-5xl font-bold text-indigo-400 mb-2">90%</div>
            <div className="text-white/60 font-medium">Lead Accuracy</div>
          </div>
          <div>
            <div className="text-5xl font-bold text-purple-400 mb-2">Real-time</div>
            <div className="text-white/60 font-medium">Insights</div>
          </div>
          <div className="col-span-2 md:col-span-1">
            <div className="text-5xl font-bold text-blue-400 mb-2">3</div>
            <div className="text-white/60 font-medium">Role Dashboards</div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 py-8 text-center text-white/40 text-sm border-t border-white/10">
        <p>&copy; {new Date().getFullYear()} Sales Feedback Intelligence. Built with AI & ❤️</p>
      </footer>
    </div>
  );
}
