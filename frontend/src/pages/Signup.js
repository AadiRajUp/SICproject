import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/auth.css";
import { apiFetch } from "../api/client";

function Signup() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async () => {
    try {
      await apiFetch("/api/signup", {
        method: "POST",
        body: JSON.stringify({ full_name: fullName, email, password }),
      });
      alert("Signup successful! Please log in.");
      navigate("/login");
    } catch (e) {
      alert(e?.message || "Signup failed");
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">Signup</h1>
        <p className="auth-sub">Create your account</p>
        <input placeholder="Full Name" onChange={e => setFullName(e.target.value)} />
        <input placeholder="Email" onChange={e => setEmail(e.target.value)} />
        <input placeholder="Password" type="password" onChange={e => setPassword(e.target.value)} />
        <button onClick={handleSubmit}>Signup</button>
      </div>
    </div>
  );
}

export default Signup;