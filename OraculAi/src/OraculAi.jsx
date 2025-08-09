import React, { useState, useEffect, useRef } from "react";

export default function OraculAi() {
  const [messages, setMessages] = useState([
    { id: "s1", role: "system", content: "Ты — OraculAi, умный помощник." }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text) return;

    const userMsg = { id: Date.now().toString(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("/api/gemini", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMsg]
        })
      });

      if (!res.ok) throw new Error(await res.text());

      const data = await res.json();
      const replyText = data.reply || "Нет ответа от OraculAi";

      const botMsg = {
        id: "b" + Date.now().toString(),
        role: "assistant",
        content: replyText
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { id: "e" + Date.now().toString(), role: "assistant", content: "Ошибка: " + err.message }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () =>
    setMessages([{ id: "s1", role: "system", content: "Ты — OraculAi, умный помощник." }]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-100 to-white p-6">
      <div className="w-full max-w-3xl bg-white shadow-2xl rounded-2xl overflow-hidden grid grid-rows-[auto,1fr,auto]">
        <header className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center text-white font-bold">
              OA
            </div>
            <div>
              <div className="font-semibold">OraculAi</div>
              <div className="text-xs text-gray-500">Ваш приватный AI-чат</div>
            </div>
          </div>
          <button
            onClick={clearChat}
            className="text-sm px-3 py-1 rounded-md hover:bg-gray-100"
          >
            Новый чат
          </button>
        </header>

        <main className="p-4 overflow-auto" style={{ height: "60vh" }}>
          <div className="space-y-4">
            {messages.map((m) => (
              <div
                key={m.id}
                className={
                  m.role === "user"
                    ? "flex justify-end"
                    : m.role === "system"
                    ? "flex justify-center"
                    : "flex justify-start"
                }
              >
                <div
                  className={`max-w-[75%] px-4 py-2 rounded-xl shadow-sm whitespace-pre-wrap ${
                    m.role === "user"
                      ? "bg-indigo-600 text-white rounded-tr-none"
                      : m.role === "assistant"
                      ? "bg-gray-100 text-gray-900 rounded-tl-none"
                      : "bg-yellow-50 text-gray-700"
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        </main>

        <footer className="p-4 border-t">
          <div className="flex gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={isLoading ? "Ожидание ответа..." : "Напишите сообщение и нажмите Enter"}
              disabled={isLoading}
              rows={1}
              className="flex-1 resize-none p-3 rounded-lg border focus:outline-none focus:ring"
            />
            <button
              onClick={sendMessage}
              disabled={isLoading}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white disabled:opacity-50"
            >
              {isLoading ? "Отправка..." : "Отправить"}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
      }
