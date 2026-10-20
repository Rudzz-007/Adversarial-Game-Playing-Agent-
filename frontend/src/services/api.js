// frontend/src/services/api.js
const API_URL = "http://localhost:8000";

export async function fetchAIMove(board, depth = 4) {
  try {
    const response = await fetch(`${API_URL}/api/ai-move`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ board, depth }),
    });

    if (!response.ok) {
      throw new Error("Failed to fetch AI move from backend");
    }

    return await response.json();
  } catch (error) {
    console.error("API Error:", error);
    return null;
  }
}