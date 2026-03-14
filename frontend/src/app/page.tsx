"use client";

import { useState, useCallback } from "react";
import { Activity } from "lucide-react";
import { ChatThread } from "@/components/ChatThread";
import { QueryInput } from "@/components/QueryInput";
import { Message } from "@/components/MessageBubble";
import { queryAPI } from "@/lib/api";

function generateId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = useCallback(async (question: string) => {
    const messageId = generateId();

    // Add optimistic loading message
    const loadingMessage: Message = {
      id: messageId,
      question,
      isLoading: true,
    };
    setMessages((prev) => [...prev, loadingMessage]);
    setIsLoading(true);

    try {
      const response = await queryAPI(question);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? { ...msg, isLoading: false, response }
            : msg
        )
      );
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Something went wrong";
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? { ...msg, isLoading: false, error: errorMessage }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <header className="shrink-0 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur-sm px-4 py-3">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
              <span className="text-sm font-bold text-indigo-400">S</span>
            </div>
            <div>
              <h1 className="text-sm font-semibold text-zinc-100 leading-none">
                SalesSense
              </h1>
              <p className="text-[10px] text-zinc-500 leading-none mt-0.5">
                Sales Intelligence Platform
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-zinc-500">
            <Activity className="w-3 h-3 text-green-400" />
            <span>~8k docs indexed</span>
          </div>
        </div>
      </header>

      {/* Chat thread */}
      <ChatThread messages={messages} />

      {/* Query input */}
      <QueryInput onSubmit={handleSubmit} isLoading={isLoading} />
    </div>
  );
}
