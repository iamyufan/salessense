"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Source } from "@/lib/api";

const DOC_TYPE_COLORS: Record<Source["doc_type"], string> = {
  deal_note: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  transcript: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  battlecard: "bg-orange-500/20 text-orange-300 border-orange-500/30",
  playbook: "bg-green-500/20 text-green-300 border-green-500/30",
};

const DOC_TYPE_LABELS: Record<Source["doc_type"], string> = {
  deal_note: "Deal Note",
  transcript: "Transcript",
  battlecard: "Battlecard",
  playbook: "Playbook",
};

interface SourceCardProps {
  source: Source;
  index: number;
}

export function SourceCard({ source, index }: SourceCardProps) {
  const scorePercent = Math.round(source.score * 100);

  return (
    <Card className="bg-zinc-800/60 border-zinc-700/50 hover:border-zinc-600/70 transition-colors">
      <CardContent className="p-4 space-y-3">
        {/* Header row: index + doc_type badge + score */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="text-xs text-zinc-500 font-mono">#{index + 1}</span>
            <span
              className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${DOC_TYPE_COLORS[source.doc_type]}`}
            >
              {DOC_TYPE_LABELS[source.doc_type]}
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <span className="font-mono">{scorePercent}%</span>
            <div className="w-16 h-1.5 bg-zinc-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-500 rounded-full transition-all"
                style={{ width: `${scorePercent}%` }}
              />
            </div>
          </div>
        </div>

        {/* Tags: industry + icp */}
        <div className="flex flex-wrap gap-1.5">
          {source.industry && (
            <Badge
              variant="outline"
              className="text-xs border-zinc-600 text-zinc-400 bg-zinc-800/40"
            >
              {source.industry}
            </Badge>
          )}
          {source.icp && (
            <Badge
              variant="outline"
              className="text-xs border-zinc-600 text-zinc-400 bg-zinc-800/40"
            >
              {source.icp}
            </Badge>
          )}
          {source.source_id && (
            <Badge
              variant="outline"
              className="text-xs border-zinc-700 text-zinc-500 bg-zinc-800/20 font-mono max-w-[160px] truncate"
            >
              {source.source_id}
            </Badge>
          )}
        </div>

        {/* Snippet */}
        {source.snippet && (
          <p className="text-xs text-zinc-400 leading-relaxed line-clamp-3 border-l-2 border-zinc-700 pl-3">
            {source.snippet}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
