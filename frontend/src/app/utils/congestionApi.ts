import type { PortData } from "../data/ports";

export function scoreToLevel(score: number): PortData["congestion"]["level"] {
  if (score >= 0.85) return "critical";
  if (score >= 0.65) return "high";
  if (score >= 0.45) return "moderate";
  return "low";
}

export async function fetchCongestionScore(portName: string): Promise<number> {
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/predict/${encodeURIComponent(portName)}`
    );

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }

    const data = await response.json();

    console.log("Congestion API response:", data);

    return data.congestion_score;
  } catch (error) {
    console.error("Error fetching congestion score:", error);
    return 0.5;
  }
}