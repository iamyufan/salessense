"use client";

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble, Message } from "@/components/MessageBubble";

interface ChatThreadProps {
  messages: Message[];
}

export function ChatThread({ messages }: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-4">
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
          <span className="text-3xl font-bold text-indigo-400">S</span>
        </div>
        <div className="space-y-1">
          <h2 className="text-lg font-semibold text-zinc-200">
            Ask SalesSense
          </h2>
          <p className="text-sm text-zinc-500 max-w-sm">
            Query your sales transcripts, deal notes, battlecards, and playbooks
            using natural language.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2 max-w-lg w-full">
          {[
            "What objections come up most in enterprise deals?",
            "Summarize key themes from FinTech transcripts",
            "What does the MEDDIC playbook say about champion building?",
            "Which SMB deals closed fastest and why?",
          ].map((suggestion) => (
            <button
              key={suggestion}
              className="text-left text-xs text-zinc-400 border border-zinc-700/60 rounded-lg px-3 py-2.5 hover:border-zinc-600 hover:text-zinc-300 hover:bg-zinc-800/40 transition-all"
              onClick={() => {
                // Dispatch a custom event to pre-fill the input
                window.dispatchEvent(
                  new CustomEvent("salessense:suggestion", {
                    detail: suggestion,
                  })
                );
              }}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 px-4">
      <div className="max-w-3xl mx-auto py-6 space-y-8">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
