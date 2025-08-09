export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const GEMINI_API_KEY = process.env.GEMINI_API_KEY; // Храним в переменных окружения Vercel
  const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent";

  try {
    const { messages } = req.body;

    const payload = {
      contents: [
        {
          parts: messages.map((m) => ({ text: m.content }))
        }
      ]
    };

    const response = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    res.status(200).json({ reply: data.candidates?.[0]?.content?.parts?.[0]?.text || "Нет ответа" });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
  }
