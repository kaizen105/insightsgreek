"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [role, setRole] = useState("salesperson");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg("");

    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role, username, password }),
      });
      
      let data;
      try {
        data = await response.json();
      } catch (parseError) {
        throw new Error("Server error (non-JSON response). Please try again.");
      }

      if (response.ok) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("user", JSON.stringify(data.user));
        sessionStorage.setItem("token", data.token);
        sessionStorage.setItem("user", JSON.stringify(data.user));

        if (data.user.role === "salesperson") router.push("/salesperson");
        else if (data.user.role === "manager") router.push("/manager");
        else if (data.user.role === "dev") router.push("/dev");
      } else {
        throw new Error(data.error || "Login failed");
      }
    } catch (error: any) {
      setErrorMsg(error.message || "Connection error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#667eea] to-[#764ba2] flex flex-col items-center justify-center p-6 text-gray-800">
      <h1 className="text-4xl font-bold text-white mb-8">Welcome Back</h1>
      <div className="w-full max-w-[400px] bg-white rounded-xl shadow-2xl p-8">
        
        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-sm font-medium mb-1.5 text-gray-700">Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              required
              className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2.5 text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#667eea] focus:border-transparent"
            >
              <option value="salesperson">Salesperson</option>
              <option value="manager">Manager</option>
              <option value="dev">Developer</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5 text-gray-700">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2.5 text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#667eea] focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5 text-gray-700">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2.5 text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#667eea] focus:border-transparent"
            />
          </div>

          {errorMsg && (
            <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg text-sm border border-red-200">
              {errorMsg}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white py-3 rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-70 mt-4"
          >
            {isLoading ? "Logging in..." : "Login"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          Need an account?{" "}
          <Link href="/register" className="text-[#764ba2] font-medium hover:underline">
            Register here
          </Link>
        </div>
      </div>
    </div>
  );
}
