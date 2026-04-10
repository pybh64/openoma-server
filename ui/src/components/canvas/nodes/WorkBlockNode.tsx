import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface WorkBlockNodeData {
  label: string;
  description: string;
  executionHints: string[];
  inputCount: number;
  outputCount: number;
  workBlockId: string;
  workBlockVersion: number;
  alias: string | null;
  nodeReferenceId: string;
  executionState?: string | null;
}

export const WorkBlockNode = memo(function WorkBlockNode({
  data,
  selected,
}: NodeProps & { data: WorkBlockNodeData }) {
  const stateColor = data.executionState ? getStateColor(data.executionState) : null;

  return (
    <div
      className={cn(
        "rounded-lg border-2 bg-card shadow-sm min-w-[180px] max-w-[260px] transition-all",
        selected ? "border-primary shadow-md ring-2 ring-primary/20" : "border-node-wb-border",
        stateColor && `ring-2 ${stateColor}`
      )}
    >
      {/* Header */}
      <div className="px-3 py-2 bg-node-wb rounded-t-[6px] border-b border-node-wb-border/30">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-semibold text-foreground truncate">
            {data.alias || data.label}
          </span>
          {data.executionState && (
            <span className={cn("text-[10px] px-1.5 py-0.5 rounded-full font-medium shrink-0", getStateBadge(data.executionState))}>
              {data.executionState}
            </span>
          )}
        </div>
        {data.alias && data.alias !== data.label && (
          <div className="text-[10px] text-muted-foreground truncate">{data.label}</div>
        )}
      </div>

      {/* Body */}
      <div className="px-3 py-2">
        <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
          {data.description || "No description"}
        </p>

        <div className="flex items-center gap-2 mt-2 text-[10px] text-muted-foreground">
          {data.inputCount > 0 && (
            <span className="flex items-center gap-0.5">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-400" />
              {data.inputCount} in
            </span>
          )}
          {data.outputCount > 0 && (
            <span className="flex items-center gap-0.5">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400" />
              {data.outputCount} out
            </span>
          )}
          {data.executionHints.length > 0 && (
            <span className="ml-auto bg-muted px-1 py-0.5 rounded text-[9px]">
              {data.executionHints[0]}
            </span>
          )}
        </div>
      </div>

      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-2.5 !h-2.5 !bg-blue-500 !border-2 !border-card"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!w-2.5 !h-2.5 !bg-emerald-500 !border-2 !border-card"
      />
    </div>
  );
});

function getStateColor(state: string): string {
  switch (state) {
    case "in_progress": return "ring-amber-400/50";
    case "completed": return "ring-emerald-400/50";
    case "failed": return "ring-red-400/50";
    case "assigned": return "ring-blue-400/50";
    default: return "ring-gray-300/50";
  }
}

function getStateBadge(state: string): string {
  switch (state) {
    case "in_progress": return "bg-amber-100 text-amber-700";
    case "completed": return "bg-emerald-100 text-emerald-700";
    case "failed": return "bg-red-100 text-red-700";
    case "assigned": return "bg-blue-100 text-blue-700";
    case "created": return "bg-slate-100 text-slate-600";
    default: return "bg-gray-100 text-gray-600";
  }
}
