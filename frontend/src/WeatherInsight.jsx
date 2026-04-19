/**
 * WeatherInsight.jsx
 * 
 * React component that calls the FastAPI backend and displays
 * today's Chicago weather insight with historical comparison.
 * 
 * Usage:
 *   npm create vite@latest my-app -- --template react
 *   cd my-app && npm install
 *   # Copy this file to src/WeatherInsight.jsx
 *   # In src/App.jsx: import WeatherInsight from './WeatherInsight'
 *   npm run dev
 */

import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// ──────────────────────────────────────────────
// CONSTANTS
// ──────────────────────────────────────────────
const MARK_CONFIG = {
  0: { label: "clear",         symbol: "○", colorClass: "good" },
  1: { label: "extreme temp",  symbol: "◈", colorClass: "warm" },
  2: { label: "rain",          symbol: "◑", colorClass: "rain" },
  3: { label: "snow",          symbol: "◆", colorClass: "snow" },
};

const SEASON_SYMBOL = { winter: "❄", spring: "◌", summer: "○", fall: "◧" };

// ──────────────────────────────────────────────
// HELPERS
// ──────────────────────────────────────────────
function fmt(n, decimals = 0) {
  if (n == null || isNaN(n)) return "-";
  return Number(n).toLocaleString("en-US", {
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
  });
}

function deltaSign(v) { return v > 0 ? "+" : ""; }

// ──────────────────────────────────────────────
// HOOKS
// ──────────────────────────────────────────────
function useInsight() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`${API_BASE}/api/insight`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e) => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return { data, loading, error };
}

// ──────────────────────────────────────────────
// SUB-COMPONENTS
// ──────────────────────────────────────────────
function WeatherStrip({ weather }) {
  const mc = MARK_CONFIG[weather.weather_mark] ?? MARK_CONFIG[0];
  const si = SEASON_SYMBOL[weather.season] ?? "○";
  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long", month: "long", day: "numeric",
  });

  return (
    <div style={styles.weatherStrip}>
      <span style={styles.weatherPill}>{si} {weather.season}</span>
      <span style={styles.weatherPill}>⊙ {weather.day_time}</span>
      <span style={styles.weatherPill}>⊕ {weather.temperature_c}°C</span>
      {weather.precipitation_mm > 0 && (
        <span style={styles.weatherPill}>◑ {weather.precipitation_mm}mm</span>
      )}
      {weather.snowfall_cm > 0 && (
        <span style={styles.weatherPill}>◆ {weather.snowfall_cm}cm snow</span>
      )}
      <span style={{ ...styles.markBadge, ...styles[`mark_${mc.colorClass}`] }}>
        {mc.symbol} {mc.label}
      </span>
    </div>
  );
}

function MetricsGrid({ data }) {
  const { city_avg_trips, city_avg_fare,
          good_weather_avg_trips, good_weather_avg_fare,
          delta_trips_pct, delta_fare_pct } = data;

  return (
    <div style={styles.metricsGrid}>
      <MetricCard
        label="trips today (hist.)"
        value={fmt(city_avg_trips)}
        delta={`${deltaSign(delta_trips_pct)}${delta_trips_pct}% vs clear`}
        deltaPositive={delta_trips_pct >= 0}
      />
      <MetricCard
        label="avg fare"
        value={`$${fmt(city_avg_fare, 2)}`}
        delta={`${deltaSign(delta_fare_pct)}${delta_fare_pct}% vs clear`}
        deltaPositive={delta_fare_pct >= 0}
      />
      <MetricCard
        label="clear-day baseline"
        value={fmt(good_weather_avg_trips)}
        delta={`$${fmt(good_weather_avg_fare, 2)} avg fare`}
        deltaNeutral
      />
    </div>
  );
}

function MetricCard({ label, value, delta, deltaPositive, deltaNeutral }) {
  const deltaColor = deltaNeutral
    ? "var(--color-text-tertiary)"
    : deltaPositive ? "#3B6D11" : "#A32D2D";

  return (
    <div style={styles.metricCard}>
      <div style={styles.metricLabel}>{label}</div>
      <div style={styles.metricValue}>{value}</div>
      <div style={{ ...styles.metricDelta, color: deltaColor }}>{delta}</div>
    </div>
  );
}

function AreaList({ areas }) {
  const maxTrips = Math.max(...areas.map((a) => a.avg_trips), 1);

  return (
    <div style={styles.areaList}>
      {areas.map((area, i) => {
        const barW = Math.round((area.avg_trips / maxTrips) * 100);
        return (
          <div key={area.area} style={styles.areaRow}>
            <span style={styles.areaRank}>{String(i + 1).padStart(2, "0")}</span>
            <span style={styles.areaName}>Area {area.area}</span>
            <div style={styles.areaBarWrap}>
              <div style={{ ...styles.areaBar, width: `${barW}%` }} />
            </div>
            <span style={styles.areaTrips}>{fmt(area.avg_trips)} trips</span>
            <span style={styles.areaFare}>${fmt(area.avg_fare, 2)}</span>
          </div>
        );
      })}
    </div>
  );
}

function Skeleton() {
  return (
    <div style={styles.loadingState}>
      {[120, "80%", 44, 60, 120].map((w, i) => (
        <div
          key={i}
          style={{ ...styles.skeleton, width: w, height: typeof w === "number" ? 16 : 44 }}
        />
      ))}
    </div>
  );
}

function ErrorCard({ message }) {
  return (
    <div style={styles.errorCard}>
      <div style={{ fontSize: 20, marginBottom: 8 }}>○</div>
      <div>{message}</div>
      <div style={{ marginTop: 8, color: "var(--color-text-tertiary)", fontSize: 12 }}>
        Make sure the FastAPI server is running on {API_BASE}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// MAIN COMPONENT
// ──────────────────────────────────────────────
export default function WeatherInsight() {
  const { data, loading, error } = useInsight();

  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long", month: "long", day: "numeric",
  });

  if (loading) return <Skeleton />;
  if (error || !data) return <ErrorCard message={error ?? "No data available"} />;

  const { weather, headline, reasoning, top_areas } = data;
  const season   = weather?.season   ?? "";
  const day_time = weather?.day_time ?? "";

  return (
    <div style={styles.root}>
      <div style={styles.eyebrow}>
        {today} · Chicago · {season} {day_time}
      </div>

      <h1 style={styles.headline}>{headline}</h1>

      <WeatherStrip weather={weather} />

      <p style={styles.reasoning}>{reasoning}</p>

      <hr style={styles.divider} />

      <MetricsGrid data={data} />

      <div style={styles.sectionLabel}>top pickup areas under these conditions</div>
      <AreaList areas={top_areas} />

      <div style={styles.footerNote}>
        based on 2018–2025 TNP trip records · weather via open-meteo
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// STYLES
// ──────────────────────────────────────────────
const styles = {
  root: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 14,
    color: "var(--color-text-primary)",
    padding: "2rem 0 3rem",
    maxWidth: 680,
  },
  eyebrow: {
    fontFamily: "'DM Mono', monospace",
    fontSize: 11,
    letterSpacing: "0.12em",
    textTransform: "uppercase",
    color: "var(--color-text-tertiary)",
    marginBottom: "0.5rem",
  },
  headline: {
    fontFamily: "'Instrument Serif', serif",
    fontSize: 28,
    fontWeight: 400,
    lineHeight: 1.25,
    margin: "0 0 1.5rem",
    color: "var(--color-text-primary)",
  },
  weatherStrip: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "10px 14px",
    borderRadius: "var(--border-radius-md)",
    border: "0.5px solid var(--color-border-tertiary)",
    background: "var(--color-background-secondary)",
    marginBottom: "1.5rem",
    flexWrap: "wrap",
  },
  weatherPill: {
    display: "inline-flex",
    alignItems: "center",
    gap: 5,
    fontSize: 12,
    fontFamily: "'DM Mono', monospace",
    color: "var(--color-text-secondary)",
    padding: "3px 8px",
    borderRadius: 100,
    border: "0.5px solid var(--color-border-tertiary)",
    background: "var(--color-background-primary)",
  },
  markBadge: {
    display: "inline-flex",
    alignItems: "center",
    gap: 5,
    fontSize: 11,
    fontFamily: "'DM Mono', monospace",
    fontWeight: 500,
    padding: "3px 10px",
    borderRadius: 100,
    marginLeft: "auto",
  },
  mark_good: { background: "#EAF3DE", color: "#3B6D11", border: "0.5px solid #C0DD97" },
  mark_warm: { background: "#FAEEDA", color: "#854F0B", border: "0.5px solid #FAC775" },
  mark_rain: { background: "#E6F1FB", color: "#185FA5", border: "0.5px solid #B5D4F4" },
  mark_snow: { background: "#EEEDFE", color: "#534AB7", border: "0.5px solid #CECBF6" },
  divider: {
    border: "none",
    borderTop: "0.5px solid var(--color-border-tertiary)",
    margin: "1.5rem 0",
  },
  reasoning: {
    fontSize: 14,
    lineHeight: 1.7,
    color: "var(--color-text-secondary)",
    margin: "0 0 1.5rem",
  },
  metricsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
    gap: 10,
    marginBottom: "1.5rem",
  },
  metricCard: {
    background: "var(--color-background-secondary)",
    borderRadius: "var(--border-radius-md)",
    padding: "14px 16px",
  },
  metricLabel: {
    fontSize: 11,
    fontFamily: "'DM Mono', monospace",
    color: "var(--color-text-tertiary)",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    marginBottom: 6,
  },
  metricValue: {
    fontSize: 22,
    fontWeight: 500,
    lineHeight: 1,
    color: "var(--color-text-primary)",
  },
  metricDelta: {
    fontSize: 11,
    fontFamily: "'DM Mono', monospace",
    marginTop: 4,
  },
  sectionLabel: {
    fontSize: 11,
    fontFamily: "'DM Mono', monospace",
    textTransform: "uppercase",
    letterSpacing: "0.1em",
    color: "var(--color-text-tertiary)",
    marginBottom: 10,
  },
  areaList: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
  },
  areaRow: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "10px 14px",
    borderRadius: "var(--border-radius-md)",
    border: "0.5px solid var(--color-border-tertiary)",
    background: "var(--color-background-primary)",
  },
  areaRank: {
    fontFamily: "'DM Mono', monospace",
    fontSize: 11,
    color: "var(--color-text-tertiary)",
    width: 16,
    flexShrink: 0,
  },
  areaName: { fontSize: 13, fontWeight: 500, flex: 1, color: "var(--color-text-primary)" },
  areaBarWrap: {
    flex: 2,
    height: 4,
    background: "var(--color-border-tertiary)",
    borderRadius: 2,
    overflow: "hidden",
  },
  areaBar: {
    height: "100%",
    borderRadius: 2,
    background: "var(--color-text-secondary)",
    opacity: 0.5,
  },
  areaTrips: {
    fontFamily: "'DM Mono', monospace",
    fontSize: 12,
    color: "var(--color-text-secondary)",
    width: 72,
    textAlign: "right",
    flexShrink: 0,
  },
  areaFare: {
    fontFamily: "'DM Mono', monospace",
    fontSize: 12,
    color: "var(--color-text-tertiary)",
    width: 52,
    textAlign: "right",
    flexShrink: 0,
  },
  loadingState: { display: "flex", flexDirection: "column", gap: 12, padding: "2rem 0" },
  skeleton: {
    background: "var(--color-background-secondary)",
    borderRadius: "var(--border-radius-md)",
    animation: "pulse 1.4s ease-in-out infinite",
  },
  errorCard: {
    padding: 20,
    borderRadius: "var(--border-radius-lg)",
    border: "0.5px solid var(--color-border-tertiary)",
    background: "var(--color-background-secondary)",
    textAlign: "center",
    color: "var(--color-text-secondary)",
    fontSize: 13,
    lineHeight: 1.6,
  },
  footerNote: {
    fontSize: 11,
    fontFamily: "'DM Mono', monospace",
    color: "var(--color-text-tertiary)",
    marginTop: "1.5rem",
    textAlign: "right",
  },
};
