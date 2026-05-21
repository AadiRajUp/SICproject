import { useEffect, useState } from "react";
import "../styles/form.css";
import { apiFetch } from "../api/client";
import { useNavigate } from "react-router-dom";

function TodayData() {
  const [studyHours, setStudyHours] = useState("");
  const [focusScore, setFocusScore] = useState("");
  const [sleepHours, setSleepHours] = useState("");
  const [phoneUsage, setPhoneUsage] = useState("");
  const navigate = useNavigate()
  const handleSubmit = async () => {
    // Basic validation
    if (!studyHours || !focusScore || !sleepHours || !phoneUsage) {
        alert("Please fill in all fields.");
        return;
    }
    try {
        await apiFetch("/api/today-data", {
          method: "POST",
          body: JSON.stringify({
            study_hours: parseFloat(studyHours),
            focus_score: parseInt(focusScore, 10),
            sleep_hours: parseFloat(sleepHours),
            phone_usage_hours: parseFloat(phoneUsage),
          }),
        });
        navigate("/");
        //alert("Data saved successfully!");
        setStudyHours("");
        setFocusScore("");
        setSleepHours("");
        setPhoneUsage("");
    } catch (err) {
        console.error("Fetch Error:", err);
        alert(err?.message || "Server error. Please try again.");
    }
  };

  return (
    <div style={{ padding: "48px 24px", background: "#fafafa", minHeight: "100vh" }}>
      <div className="form-card" style={{ maxWidth: "480px", margin: "0 auto", background: "#fff", padding: "32px", borderRadius: "8px", border: "1px solid #eaeaea", boxShadow: "0 1px 2px rgba(0,0,0,0.02)" }}>
        <h1 style={{ marginTop: 0, marginBottom: "32px", color: "#000", fontSize: "24px", fontWeight: "600", letterSpacing: "-0.02em" }}>Today's Data</h1>
        
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <div>
                <label style={{ color: "#666", display: "block", marginBottom: "8px", fontSize: "14px", fontWeight: "500" }}>Study Hours</label>
                <input type="number" step="0.1" value={studyHours} placeholder="e.g. 4.5" onChange={e => setStudyHours(e.target.value)} style={{ width: "100%", padding: "12px", borderRadius: "6px", border: "1px solid #eaeaea", background: "#fff", color: "#000", fontSize: "14px", outline: "none", transition: "border-color 0.2s" }} onFocus={e => e.target.style.borderColor = "#000"} onBlur={e => e.target.style.borderColor = "#eaeaea"} />
            </div>

            <div>
                <label style={{ color: "#666", display: "block", marginBottom: "8px", fontSize: "14px", fontWeight: "500" }}>Focus Score (1-100)</label>
                <input type="number" value={focusScore} placeholder="e.g. 85" onChange={e => setFocusScore(e.target.value)} style={{ width: "100%", padding: "12px", borderRadius: "6px", border: "1px solid #eaeaea", background: "#fff", color: "#000", fontSize: "14px", outline: "none", transition: "border-color 0.2s" }} onFocus={e => e.target.style.borderColor = "#000"} onBlur={e => e.target.style.borderColor = "#eaeaea"} />
            </div>

            <div>
                <label style={{ color: "#666", display: "block", marginBottom: "8px", fontSize: "14px", fontWeight: "500" }}>Sleep Hours</label>
                <input type="number" step="0.1" value={sleepHours} placeholder="e.g. 7.5" onChange={e => setSleepHours(e.target.value)} style={{ width: "100%", padding: "12px", borderRadius: "6px", border: "1px solid #eaeaea", background: "#fff", color: "#000", fontSize: "14px", outline: "none", transition: "border-color 0.2s" }} onFocus={e => e.target.style.borderColor = "#000"} onBlur={e => e.target.style.borderColor = "#eaeaea"} />
            </div>

            <div>
                <label style={{ color: "#666", display: "block", marginBottom: "8px", fontSize: "14px", fontWeight: "500" }}>Phone Usage (Hours)</label>
                <input type="number" step="0.1" value={phoneUsage} placeholder="e.g. 2.0" onChange={e => setPhoneUsage(e.target.value)} style={{ width: "100%", padding: "12px", borderRadius: "6px", border: "1px solid #eaeaea", background: "#fff", color: "#000", fontSize: "14px", outline: "none", transition: "border-color 0.2s" }} onFocus={e => e.target.style.borderColor = "#000"} onBlur={e => e.target.style.borderColor = "#eaeaea"} />
            </div>

            <button onClick={handleSubmit} style={{ marginTop: "16px", padding: "14px", background: "#000", color: "#fff", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "500", fontSize: "15px", transition: "background 0.2s" }} onMouseOver={e => e.target.style.background = "#333"} onMouseOut={e => e.target.style.background = "#000"}>Submit Data</button>
        </div>
      </div>
    </div>
  );
}

export default TodayData;