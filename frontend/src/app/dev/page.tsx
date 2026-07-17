"use client";

import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";

type Product = { id: number; name: string; description: string; details: string };
type User = { id: number; username: string; role: string };
type Log = { id: number; timestamp: string; action: string; details: string; user: string };

export default function DevDashboard() {
  const [activeTab, setActiveTab] = useState<"products" | "users" | "logs">("products");
  
  const [products, setProducts] = useState<Product[]>([]);
  const [showAddProduct, setShowAddProduct] = useState(false);
  const [newProduct, setNewProduct] = useState({ name: "", description: "", details: "" });

  const [users, setUsers] = useState<User[]>([]);
  const [showAddUser, setShowAddUser] = useState(false);
  const [newUser, setNewUser] = useState({ username: "", password: "", role: "salesperson" });

  const [logs, setLogs] = useState<Log[]>([]);
  const [logFilter, setLogFilter] = useState("all");

  const secureFetch = async (url: string, options: any = {}) => {
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    const defaultHeaders = {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    };
    options.headers = { ...defaultHeaders, ...options.headers };
    const response = await fetch(url, options);
    if (response.status === 401) {
      window.location.href = "/login";
      throw new Error("Unauthorized");
    }
    return response;
  };

  const loadData = async () => {
    try {
      const [resProducts, resUsers, resLogs] = await Promise.all([
        secureFetch("/api/products"),
        secureFetch("/api/users"),
        secureFetch("/api/logs")
      ]);
      const [dataProducts, dataUsers, dataLogs] = await Promise.all([
        resProducts.json(), resUsers.json(), resLogs.json()
      ]);
      setProducts(dataProducts.products || []);
      setUsers(dataUsers.users || []);
      setLogs(dataLogs.logs || []);
    } catch (e) {
      console.error("Failed to load dev data", e);
    }
  };

  useEffect(() => {
    const userStr = localStorage.getItem("user") || sessionStorage.getItem("user");
    if (!userStr || JSON.parse(userStr).role !== "dev") {
      window.location.href = "/login";
      return;
    }
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleAddProduct = async () => {
    if (!newProduct.name || !newProduct.description) return alert("Missing required fields");
    try {
      const res = await secureFetch("/api/products", { method: "POST", body: JSON.stringify(newProduct) });
      if (res.ok) {
        setShowAddProduct(false);
        setNewProduct({ name: "", description: "", details: "" });
        loadData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteProduct = async (id: number) => {
    if (!confirm("Are you sure?")) return;
    try {
      const res = await secureFetch(`/api/products/${id}`, { method: "DELETE" });
      if (res.ok) loadData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddUser = async () => {
    if (!newUser.username || !newUser.password) return alert("Missing required fields");
    try {
      const res = await secureFetch("/api/users", { method: "POST", body: JSON.stringify(newUser) });
      if (res.ok) {
        setShowAddUser(false);
        setNewUser({ username: "", password: "", role: "salesperson" });
        loadData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteUser = async (id: number) => {
    if (!confirm("Are you sure?")) return;
    try {
      const res = await secureFetch(`/api/users/${id}`, { method: "DELETE" });
      if (res.ok) loadData();
    } catch (e) {
      console.error(e);
    }
  };

  const filteredLogs = logFilter === "all" ? logs : logs.filter(l => l.action.toLowerCase() === logFilter.toLowerCase());

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#667eea] to-[#764ba2] text-gray-800 pb-10">
      <Navbar title="Developer Admin Panel" />
      
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Tab Navigation */}
        <div className="flex gap-4 mb-6">
          {(["products", "users", "logs"] as const).map(tab => (
            <button 
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 rounded-lg font-bold transition-all capitalize shadow-sm ${
                activeTab === tab 
                  ? "bg-white text-[#667eea]" 
                  : "bg-white/20 text-white hover:bg-white/30"
              }`}
            >
              {tab === "logs" ? "Activity Logs" : tab}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="bg-white rounded-2xl p-8 shadow-xl animate-fade-in-up">
          
          {/* Products Tab */}
          {activeTab === "products" && (
            <div className="animate-fade-in-up">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-[#667eea]">Product Management</h3>
                <button 
                  onClick={() => setShowAddProduct(!showAddProduct)}
                  className="px-4 py-2 bg-gradient-to-r from-[#667eea] to-[#764ba2] hover:shadow-lg text-white rounded-lg text-sm font-semibold transition-all"
                >
                  {showAddProduct ? "Cancel" : "Add Product"}
                </button>
              </div>

              {showAddProduct && (
                <div className="bg-gray-50 p-6 rounded-xl border border-gray-200 mb-8 animate-fade-in-up">
                  <h4 className="font-bold mb-4 text-gray-800">Add New Product</h4>
                  <div className="space-y-4">
                    <input 
                      type="text" placeholder="Product Name" value={newProduct.name} onChange={e => setNewProduct({...newProduct, name: e.target.value})}
                      className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#667eea]"
                    />
                    <textarea 
                      placeholder="Description" value={newProduct.description} onChange={e => setNewProduct({...newProduct, description: e.target.value})} rows={3}
                      className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#667eea]"
                    />
                    <textarea 
                      placeholder="Details" value={newProduct.details} onChange={e => setNewProduct({...newProduct, details: e.target.value})} rows={3}
                      className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#667eea]"
                    />
                    <button onClick={handleAddProduct} className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg text-sm">Save Product</button>
                  </div>
                </div>
              )}

              <div className="space-y-4">
                {products.map(p => (
                  <div key={p.id} className="bg-white border border-gray-200 shadow-sm p-6 rounded-xl flex justify-between items-center hover:shadow-md transition-shadow">
                    <div>
                      <h4 className="text-lg font-bold text-[#764ba2]">{p.name}</h4>
                      <p className="text-gray-600 text-sm mt-1 font-medium">{p.description}</p>
                      <p className="text-gray-400 text-xs mt-1">{p.details}</p>
                    </div>
                    <button onClick={() => handleDeleteProduct(p.id)} className="px-4 py-2 bg-red-50 hover:bg-red-600 border border-red-200 rounded-lg text-sm font-semibold transition-colors text-red-600 hover:text-white">Delete</button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Users Tab */}
          {activeTab === "users" && (
            <div className="animate-fade-in-up">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-[#667eea]">User Management</h3>
                <button 
                  onClick={() => setShowAddUser(!showAddUser)}
                  className="px-4 py-2 bg-gradient-to-r from-[#667eea] to-[#764ba2] hover:shadow-lg text-white rounded-lg text-sm font-semibold transition-all"
                >
                  {showAddUser ? "Cancel" : "Add User"}
                </button>
              </div>

              {showAddUser && (
                <div className="bg-gray-50 p-6 rounded-xl border border-gray-200 mb-8 animate-fade-in-up">
                  <h4 className="font-bold mb-4 text-gray-800">Add New User</h4>
                  <div className="space-y-4">
                    <input 
                      type="text" placeholder="Username" value={newUser.username} onChange={e => setNewUser({...newUser, username: e.target.value})}
                      className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#667eea]"
                    />
                    <input 
                      type="password" placeholder="Password" value={newUser.password} onChange={e => setNewUser({...newUser, password: e.target.value})}
                      className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#667eea]"
                    />
                    <select 
                      value={newUser.role} onChange={e => setNewUser({...newUser, role: e.target.value})}
                      className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#667eea]"
                    >
                      <option value="salesperson">Salesperson</option>
                      <option value="manager">Manager</option>
                      <option value="dev">Developer</option>
                    </select>
                    <button onClick={handleAddUser} className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg text-sm">Save User</button>
                  </div>
                </div>
              )}

              <div className="space-y-4">
                {users.map(u => (
                  <div key={u.id} className="bg-white border border-gray-200 shadow-sm p-6 rounded-xl flex justify-between items-center hover:shadow-md transition-shadow">
                    <div>
                      <h4 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                        {u.username}
                        <span className="text-xs px-2 py-1 bg-indigo-50 border border-indigo-100 rounded text-indigo-700 capitalize">{u.role}</span>
                      </h4>
                    </div>
                    <button onClick={() => handleDeleteUser(u.id)} className="px-4 py-2 bg-red-50 hover:bg-red-600 border border-red-200 rounded-lg text-sm font-semibold transition-colors text-red-600 hover:text-white">Delete</button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Logs Tab */}
          {activeTab === "logs" && (
            <div className="animate-fade-in-up">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-[#667eea]">Activity Logs</h3>
                <select 
                  value={logFilter} onChange={e => setLogFilter(e.target.value)}
                  className="bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-800 focus:outline-none focus:ring-2 focus:ring-[#667eea] font-medium"
                >
                  <option value="all">All Activities</option>
                  <option value="login">Logins</option>
                  <option value="feedback">Feedbacks</option>
                  <option value="product">Product Changes</option>
                  <option value="user">User Changes</option>
                </select>
              </div>

              <div className="space-y-3">
                {filteredLogs.map(log => (
                  <div key={log.id} className="bg-white border border-gray-100 p-4 rounded-xl flex flex-col sm:flex-row justify-between sm:items-center gap-2 hover:bg-gray-50 transition-colors shadow-sm">
                    <div className="flex items-start gap-4">
                      <span className="px-2 py-1 bg-[#667eea]/10 text-[#667eea] border border-[#667eea]/20 text-xs rounded uppercase font-bold mt-0.5">{log.action}</span>
                      <div>
                        <p className="text-gray-800 font-medium text-sm">{log.details}</p>
                        <p className="text-gray-500 text-xs mt-1">User: <span className="font-semibold text-gray-700">{log.user}</span></p>
                      </div>
                    </div>
                    <span className="text-gray-400 font-medium text-xs whitespace-nowrap">{log.timestamp}</span>
                  </div>
                ))}
                {filteredLogs.length === 0 && <div className="text-center text-gray-400 py-8">No logs found.</div>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
