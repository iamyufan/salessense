"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface QueryInputProps {
  onSubmit: (question: string) => void;
  isLoading: boolean;
}

export function QueryInput({ onSubmit, isLoading }: QueryInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Listen for suggestion events from the empty state
  useEffect(() => {
    const handler = (e: Event) => {
      const suggestion = (e as CustomEvent<string>).detail;
      setValue(suggestion);
      textareaRef.current?.focus();
    };
    window.addEventListener("salessense:suggestion", handler);
    return () => window.removeEventListener("salessense:suggestion", handler);
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSubmit(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-zinc-800 bg-zinc-950/80 backdrop-blur-sm px-4 py-4">
      <div className="max-w-3xl mx-auto">
        <div className="relative flex items-end gap-2 bg-zinc-800/60 border border-zinc-700/60 rounded-xl px-4 py-3 focus-within:border-indigo-500/50 focus-within:bg-zinc-800/80 transition-all">
          <Textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your sales data... (Enter to submit, Shift+Enter for newline)"
            disabled={isLoading}
            rows={1}
            className="flex-1 resize-none bg-transparent border-0 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 text-sm text-zinc-100 placeholder:text-zinc-500 min-h-[24px] max-h-[160px] py-0 px-0"
          />
          <Button
            onClick={handleSubmit}
            disabled={!value.trim() || isLoading}
            size="icon"
            className="shrink-0 h-8 w-8 bg-indigo-600 hover:bg-indigo-500 disabled:bg-zinc-700 disabled:text-zinc-500 rounded-lg transition-colors"
          >
            {isLoading ? (
              <div className="w-3.5 h-3.5 border-2 border-zinc-400 border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
          </Button>
        </div>
        <p className="text-[10px] text-zinc-600 text-center mt-2">
          Powered by Gemini 2.5 Flash · Weaviate hybrid search · Cohere rerank
        </p>
      </div>
    </div>
  );
}
