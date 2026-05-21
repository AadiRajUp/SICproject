import { useEffect, useMemo, useState } from "react";
import { Line, Bar, Radar, Doughnut } from "react-chartjs-2";
import "chart.js/auto";
import "../styles/dashboard.css";
import "../styles/tables.css";
import { apiFetch } from "../api/client";
import { useNavigate } from "react-router-dom";

function Dashboard() {
  const [data, setData] = useState(null);
  const [insights, setInsights] = useState(null);
  const [days, setDays] = useState(7);
  const [sortKey, setSortKey] = useState("activity_date");
  const [sortDir, setSortDir] = useState("desc");

  const isLoading = data === null;
  const isUnauthorized = Boolean(data && data.error);
  const safeData = data && !data.error ? data : {};
  const navigate = useNavigate();
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const qs = days ? `?days=${days}` : "";
        const [dash, ins] = await Promise.all([
          apiFetch(`/api/dashboard${qs}`),
          apiFetch(`/api/insights${qs}`),
        ]);
        if (cancelled) return;
        setData(dash);
        console.log(dash);
        setInsights(ins);
        console.log(ins);
      } catch (e) {
        if (cancelled) return;
        if (e?.status === 401){ 
          
          setData({ error: "Unauthorized" });
          navigate("/login");
        }
        else setData({ error: e?.message || "Failed to load dashboard" });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [days]);

  // Theme Colors - Clean Light Theme
  const colors = {
    primary: "#000000", 
    primaryLight: "rgba(0, 0, 0, 0.05)",
    secondary: "#666666", 
    secondaryLight: "rgba(102, 102, 102, 0.1)",
    tertiary: "#0070f3", // Vercel Blue
    tertiaryLight: "rgba(0, 112, 243, 0.1)",
    quaternary: "#111111", 
    quaternaryLight: "rgba(17, 17, 17, 0.1)",
    text: "#666666",
    gridLines: "rgba(0, 0, 0, 0.06)"
  };

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: colors.text, font: { family: "'-apple-system', 'BlinkMacSystemFont', sans-serif" } } },
    },
    scales: {
      x: { ticks: { color: colors.text, font: { size: 11 } }, grid: { color: colors.gridLines } },
      y: { ticks: { color: colors.text, font: { size: 11 } }, grid: { color: colors.gridLines } }
    }
  };

  const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: colors.text } } },
    scales: {
      r: {
        angleLines: { color: colors.gridLines },
        grid: { color: colors.gridLines },
        pointLabels: { color: colors.text, font: { size: 11 } },
        ticks: { display: false }
      }
    }
  };

  // 1. Trend Line (Score evolution)
  const rollingAvg = useMemo(() => {
    const xs = safeData.scores || [];
    const window = xs.length >= 30 ? 7 : xs.length >= 14 ? 5 : 3;
    if (!xs.length) return [];
    const out = [];
    for (let i = 0; i < xs.length; i++) {
      const start = Math.max(0, i - window + 1);
      const slice = xs.slice(start, i + 1);
      const avg = slice.reduce((a, b) => a + b, 0) / slice.length;
      out.push(Number(avg.toFixed(2)));
    }
    return out;
  }, [safeData.scores]);

  const scoreTrendData = useMemo(() => {
    const labels = safeData.dates && safeData.dates.length > 0 ? safeData.dates : ["Day 1"];
    const values = safeData.scores && safeData.scores.length > 0 ? safeData.scores : [safeData.score || 0];
    return {
      labels,
      datasets: [
        {
          label: "Score",
          data: values,
          borderColor: colors.primary,
          backgroundColor: colors.primaryLight,
          fill: true,
          tension: 0.2,
          pointRadius: 2,
          pointBackgroundColor: colors.primary,
          borderWidth: 2,
        },
        {
          label: "Rolling Avg",
          data: rollingAvg,
          borderColor: colors.tertiary,
          backgroundColor: "rgba(0,0,0,0)",
          fill: false,
          tension: 0.2,
          pointRadius: 0,
          borderDash: [6, 6],
          borderWidth: 2,
        },
      ],
    };
  }, [safeData.dates, safeData.scores, safeData.score, rollingAvg, colors.primary, colors.primaryLight, colors.tertiary]);

  // 2. Metrics Comparison (Bar Chart)
  const metricsComparisonData = {
    labels: safeData.dates && safeData.dates.length > 0 ? safeData.dates : ['Day 1'],
    datasets: [
      {
        label: "Study Hours",
        data: safeData.study_hours || [0],
        backgroundColor: "#10b981", // SaaS Green
        borderRadius: 4,
        barPercentage: 0.6
      },
      {
        label: "Phone Usage",
        data: safeData.phone_usage_hours || [0],
        backgroundColor: "#ef4444", // SaaS Red
        borderRadius: 4,
        barPercentage: 0.6
      }
    ]
  };

  // 3. Balance Radar (Radar Chart for latest metrics)
  const latestIndex = safeData.dates ? Math.max(0, safeData.dates.length - 1) : 0;
  const latestStudy = safeData.study_hours ? safeData.study_hours[latestIndex] : 0;
  const latestFocus = safeData.focus_scores ? safeData.focus_scores[latestIndex] : 0;
  const latestSleep = safeData.sleep_hours ? safeData.sleep_hours[latestIndex] : 0;
  const latestPhone = safeData.phone_usage_hours ? safeData.phone_usage_hours[latestIndex] : 0;
  
  const balanceData = {
    labels: ["Study", "Focus (x10)", "Sleep", "Phone", "Score (x10)"],
    datasets: [
      {
        label: "Latest Day Balance",
        data: [latestStudy, latestFocus / 10, latestSleep, latestPhone, (safeData.score || 0) / 10], 
        backgroundColor: colors.primaryLight,
        borderColor: colors.primary,
        pointBackgroundColor: colors.primary,
        pointBorderColor: "#fff",
        borderWidth: 2
      }
    ]
  };

  // 4. Time Distribution (Doughnut)
  const distributionData = {
    labels: ["Study Hours", "Sleep Hours", "Phone Usage"],
    datasets: [
      {
        data: [latestStudy, latestSleep, latestPhone],
        backgroundColor: [
          "#10b981", // Green for Study
          "#3b82f6", // Blue for Sleep
          "#ef4444"  // Red for Phone
        ],
        borderColor: "#ffffff",
        borderWidth: 2,
        hoverOffset: 4
      }
    ]
  };
  
  const noDataOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: {color: colors.text, usePointStyle: true, boxWidth: 6} } }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "#10b981"; // SaaS Green
    if (score >= 50) return "#0070f3"; // SaaS Blue
    return "#ef4444"; // SaaS Red
  };

  const scoreThemeColor = getScoreColor(safeData.score || 0);

  const tableRows = useMemo(() => {
    const rows = (safeData.dates || []).map((d, i) => ({
      activity_date: d,
      study_hours: (safeData.study_hours || [])[i],
      focus_score: (safeData.focus_scores || [])[i],
      sleep_hours: (safeData.sleep_hours || [])[i],
      phone_usage_hours: (safeData.phone_usage_hours || [])[i],
      score: (safeData.scores || [])[i],
    }));

    const dir = sortDir === "asc" ? 1 : -1;
    return rows.sort((a, b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      if (sortKey === "activity_date") return dir * String(va).localeCompare(String(vb));
      return dir * ((Number(va) || 0) - (Number(vb) || 0));
    });
  }, [safeData.dates, safeData.study_hours, safeData.focus_scores, safeData.sleep_hours, safeData.phone_usage_hours, safeData.scores, sortKey, sortDir]);

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loader"></div>
        <p>Loading Dashboard...</p>
      </div>
    );
  }
  if (isUnauthorized) {
    return (
      <p style={{ padding: "30px", color: "white" }}>
        Please log in to view your dashboard.
      </p>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Productivity Analytics</h1>
        <p>Trends, stats, and personalized tips for your window.</p>
        <div style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button onClick={() => setDays(7)} style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid #eaeaea", background: days === 7 ? "#000" : "#fff", color: days === 7 ? "#fff" : "#000", cursor: "pointer" }}>7d</button>
          <button onClick={() => setDays(30)} style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid #eaeaea", background: days === 30 ? "#000" : "#fff", color: days === 30 ? "#fff" : "#000", cursor: "pointer" }}>30d</button>
          <button onClick={() => setDays(90)} style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid #eaeaea", background: days === 90 ? "#000" : "#fff", color: days === 90 ? "#fff" : "#000", cursor: "pointer" }}>90d</button>
          <button onClick={() => setDays(null)} style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid #eaeaea", background: days === null ? "#000" : "#fff", color: days === null ? "#fff" : "#000", cursor: "pointer" }}>All</button>
        </div>
      </div>

      <div className="dashboard-top-metrics">
        <div className="metric-card highlight" style={{ background: scoreThemeColor, borderColor: scoreThemeColor }}>
          <div className="metric-title" style={{ color: "rgba(255,255,255,0.8)" }}>Current Score</div>
            <div className="metric-value" style={{ color: "#fff" }}>{safeData.score}</div>
          <div className="metric-sub" style={{ color: "rgba(255,255,255,0.9)" }}>
            {insights?.streak_days ? `${insights.streak_days} day streak` : "No streak"}
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-title">Study Total</div>
          <div className="metric-value">{latestStudy}h</div>
          <div className="metric-sub">Latest day</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Focus Level</div>
          <div className="metric-value">{latestFocus}%</div>
          <div className="metric-sub">Latest day</div>
        </div>

        <div className="metric-card">
          <div className="metric-title">Avg Score</div>
          <div className="metric-value">{insights?.avg_score ?? 0}</div>
          <div className="metric-sub">
            {insights?.best_day ? `Best ${Number(insights.best_day.score).toFixed(1)} on ${insights.best_day.date}` : "—"}
          </div>
        </div>
      </div>

      {(insights?.recommendations?.length ?? 0) > 0 && (
        <section className="recommendations-section" aria-labelledby="rec-heading">
          <h2 id="rec-heading" className="recommendations-heading">
            Personal recommendations
          </h2>
          <p className="recommendations-lede">
            Based on your logged habits in this period (and your model when noted).
          </p>
          <ul className="recommendations-list">
            {(insights.recommendations || []).map((r) => (
              <li
                key={r.id}
                className={`recommendation-card recommendation-card--${r.priority || "medium"}`}
              >
                <div className="recommendation-meta">
                  <span className={`rec-priority rec-priority--${r.priority || "medium"}`}>
                    {(r.priority || "medium").replace(/^./, (c) => c.toUpperCase())}
                  </span>
                  {r.category ? (
                    <span className="rec-category">{String(r.category)}</span>
                  ) : null}
                </div>
                <h3 className="recommendation-title">{r.title}</h3>
                <p className="recommendation-detail">{r.detail}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="dashboard-grid">
        <div className="chart-card-full feature-chart">
          <h3>Productivity Trend (with Rolling Average)</h3>
          <div className="chart-wrapper">
            <Line data={scoreTrendData} options={commonOptions} />
          </div>
        </div>

        <div className="chart-card half-chart">
          <h3>Study vs Phone Usage</h3>
          <div className="chart-wrapper">
            <Bar data={metricsComparisonData} options={commonOptions} />
          </div>
        </div>

        <div className="chart-card half-chart">
          <h3>Activity Balance</h3>
          <div className="chart-wrapper">
            <Radar data={balanceData} options={radarOptions} />
          </div>
        </div>

        <div className="chart-card half-chart">
          <h3>Time Distribution</h3>
          <div className="chart-wrapper">
            <Doughnut data={distributionData} options={noDataOptions} />
          </div>
        </div>

        <div className="chart-card-full feature-chart table-card">
          <h3>Recent 5 Days</h3>
          <table>
            <thead>
              <tr>
                <th style={{ cursor: "pointer" }} onClick={() => toggleSort("activity_date")}>Date</th>
                <th style={{ cursor: "pointer" }} onClick={() => toggleSort("study_hours")}>Study (h)</th>
                <th style={{ cursor: "pointer" }} onClick={() => toggleSort("focus_score")}>Focus (%)</th>
                <th style={{ cursor: "pointer" }} onClick={() => toggleSort("sleep_hours")}>Sleep (h)</th>
                <th style={{ cursor: "pointer" }} onClick={() => toggleSort("phone_usage_hours")}>Phone (h)</th>
                <th style={{ cursor: "pointer" }} onClick={() => toggleSort("score")}>Score</th>
              </tr>
            </thead>
            <tbody>
              {tableRows.slice(0, 5).map((r) => (
                <tr key={r.activity_date}>
                  <td>{r.activity_date}</td>
                  <td>{Number(r.study_hours ?? 0).toFixed(1)}</td>
                  <td>{Number(r.focus_score ?? 0)}</td>
                  <td>{Number(r.sleep_hours ?? 0).toFixed(1)}</td>
                  <td>{Number(r.phone_usage_hours ?? 0).toFixed(1)}</td>
                  <td>{Number(r.score ?? 0).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;