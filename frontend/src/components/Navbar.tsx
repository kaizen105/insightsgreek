"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function Navbar({ title }: { title: string }) {
  const [username, setUsername] = useState("");
  const router = useRouter();

  useEffect(() => {
    const userStr = localStorage.getItem("user") || sessionStorage.getItem("user");
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        setUsername(user.username);
      } catch (e) {
        console.error("Failed to parse user", e);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.clear();
    sessionStorage.clear();
    router.push("/login");
  };

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center shadow-sm z-50 relative animate-slide-down">
      <h2 className="text-2xl font-bold bg-gradient-to-r from-[#667eea] to-[#764ba2] bg-clip-text text-transparent tracking-tight">
        {title}
      </h2>
      <div className="flex items-center gap-4">
        {username && <span className="text-gray-700 font-medium">{username}</span>}
        <button 
          onClick={handleLogout}
          className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded transition-colors text-sm font-medium"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}
