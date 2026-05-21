import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import TodayData from "./pages/TodayData";
import "./styles/global.css";
import "./styles/navbar.css";
import { apiFetch } from "./api/client";

function App() {
  const [me, setMe] = useState({ authenticated: false });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await apiFetch("/api/me");
        if (!cancelled) setMe(res || { authenticated: false });
      } catch {
        if (!cancelled) setMe({ authenticated: false });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleLogout = async () => {
    try {
      await apiFetch("/api/logout", { method: "POST" });
    } finally {
      setMe({ authenticated: false });
      window.location.href = "/login";
    }
  };

  return (
    <Router>
      <nav className="navbar">
        <div className="brand">Productivity Challenge</div>
        <div className="nav-center">
          <div className="nav-links">
            <Link to="/">Dashboard</Link>
            
            {me.authenticated ? (
              <>
            <Link to="/today">Today Data</Link>
            <a onClick={handleLogout} style={{cursor: "pointer"}}>Logout</a>
            </>
          ):
          (
            <Link to="/login">Login</Link>
          )
          }
          </div>
        </div>
        <div className="nav-right">
          
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/login" element={<Login onLogin={setMe} />} />
        <Route path="/signup" element={<Signup onLogin={setMe} />} />
        <Route path="/today" element={<TodayData />} />
      </Routes>
    </Router>
  );
}

export default App;