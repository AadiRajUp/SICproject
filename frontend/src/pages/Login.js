import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/auth.css";
import { apiFetch } from "../api/client";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async () => {
    try {
      await apiFetch("/api/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      onLogin({ authenticated: true});
      navigate("/");
    } catch (e) {
      alert(e?.message || "Login failed");
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">Login</h1>
        <p className="auth-sub">Welcome back</p>
        <input placeholder="Email" onChange={e => setEmail(e.target.value)} />
        <input placeholder="Password" type="password" onChange={e => setPassword(e.target.value)} />
        <button onClick={handleSubmit}>Login</button>
        <Link to="/signup">signup?</Link>
      </div>
    </div>
  );
}

export default Login;