import { useState } from "react";
import { motion } from "framer-motion";

export default function OraculAi() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;
    const newMessages = [...messages, { role: "user", text: input }];
    setMessages(newMessages);
    setInput("");

    const res = await fetch("/api/gemini", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: input })
    });

    const data = await res.json();
    setMessages([...newMessages, { role: "assistant", text: data.reply }]);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg, i) => (
          <motion.div
            key={i}
            className={`my-2 p-3 rounded-lg ${
              msg.role === "user" ? "bg-blue-600 ml-auto" : "bg-gray-700"
            }`}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {msg.text}
          </motion.div>
        ))}
      </div>
      <div className="p-4 flex gap-2 bg-gray-800">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 p-2 rounded bg-gray-700 outline-none"
          placeholder="Напишите сообщение..."
        />
        <button
          onClick={sendMessage}
          className="bg-green-500 px-4 py-2 rounded"
        >
          Отправить
        </button>
      </div>
    </div>
  );
}
