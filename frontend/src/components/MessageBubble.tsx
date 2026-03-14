"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { SourceCard } from "@/components/SourceCard";
import { QueryResponse } from "@/lib/api";

export interface Message {
  id: string;
  question: string;
  response?: QueryResponse;
  isLoading: boolean;
  error?: string;
}

interface MessageBubbleProps {
  message: Message;
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3 py-2">
      <Skeleton className="h-4 w-3/4 bg-zinc-700" />
      <Skeleton className="h-4 w-full bg-zinc-700" />
      <Skeleton className="h-4 w-5/6 bg-zinc-700" />
      <Skeleton className="h-4 w-2/3 bg-zinc-700" />
    </div>
  );
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [sourcesOpen, setSourcesOpen] = useState(false);

  return (
    <div className="space-y-4">
      {/* Question bubble */}
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-indigo-600/30 border border-indigo-500/30 rounded-2xl rounded-tr-sm px-4 py-3">
          <p className="text-sm text-zinc-100 leading-relaxed">
            {message.question}
          </p>
        </div>
      </div>

      {/* Answer bubble */}
      <div className="flex justify-start">
        <div className="max-w-[90%] w-full space-y-3">
          {/* Answer card */}
          <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-2xl rounded-tl-sm px-4 py-3 space-y-3">
            {/* Header with logo mark + cached badge */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                <span className="w-4 h-4 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
                  <span className="text-[8px] text-indigo-400 font-bold">S</span>
                </span>
                <span>SalesSense</span>
              </div>
              {message.response?.cached && (
                <Badge
                  variant="outline"
                  className="text-[10px] border-amber-500/40 text-amber-400 bg-amber-500/10 flex items-center gap-1"
                >
                  <Zap className="w-2.5 h-2.5" />
                  Cached
                </Badge>
              )}
            </div>

            {/* Answer content */}
            {message.isLoading ? (
              <LoadingSkeleton />
            ) : message.error ? (
              <p className="text-sm text-red-400">{message.error}</p>
            ) : (
              <p className="text-sm text-zinc-200 leading-relaxed whitespace-pre-wrap">
                {message.response?.answer}
              </p>
            )}

            {/* Sources toggle */}
            {!message.isLoading &&
              !message.error &&
              message.response?.sources &&
              message.response.sources.length > 0 && (
                <div className="pt-1 border-t border-zinc-700/50">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSourcesOpen(!sourcesOpen)}
                    className="h-7 px-2 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700/50 -ml-1 gap-1"
                  >
                    {sourcesOpen ? (
                      <ChevronUp className="w-3 h-3" />
                    ) : (
                      <ChevronDown className="w-3 h-3" />
                    )}
                    {sourcesOpen ? "Hide" : "Show"} sources (
                    {message.response.sources.length})
                    {message.response.num_retrieved && (
                      <span className="text-zinc-600 ml-1">
                        · {message.response.num_retrieved} retrieved
                      </span>
                    )}
                  </Button>
                </div>
              )}
          </div>

          {/* Collapsible sources */}
          {sourcesOpen &&
            message.response?.sources &&
            message.response.sources.length > 0 && (
              <div className="space-y-2 pl-2">
                {message.response.sources.map((source, idx) => (
                  <SourceCard key={`${source.source_id}-${idx}`} source={source} index={idx} />
                ))}
              </div>
            )}
        </div>
      </div>
    </div>
  );
}
