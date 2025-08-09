export default async function handler(req, res) {
  const { message } = req.body;

  const r = await fetch(
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + process.env.GEMINI_API_KEY,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{ role: "user", parts: [{ text: message }] }]
      })
    }
  );

  const data = await r.json();
  res.status(200).json(data);
}
