import { memo, useState } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { Box } from "lucide-react";

export interface DAGNodeData {
  label: string;
  subtitle?: string;
  status?: "idle" | "running" | "completed" | "failed" | "skipped";
  description?: string;
  inputCount?: number;
  outputCount?: number;
  inputs?: string[];
  outputs?: string[];
  [key: string]: unknown;
}

const statusColors: Record<string, string> = {
  idle: "border-border bg-card",
  running: "border-blue-500 bg-blue-500/5",
  completed: "border-green-500 bg-green-500/5",
  failed: "border-red-500 bg-red-500/5",
  skipped: "border-muted-foreground/40 bg-muted/30",
};

const statusDots: Record<string, string> = {
  idle: "bg-muted-foreground/40",
  running: "bg-blue-500 animate-pulse",
  completed: "bg-green-500",
  failed: "bg-red-500",
  skipped: "bg-muted-foreground/40",
};

const handleClass =
  "!w-2 !h-2 !bg-transparent !border-0 hover:!bg-primary/50 !rounded-full transition-colors";

function DAGNodeComponent({ data, selected }: NodeProps) {
  const d = data as unknown as DAGNodeData;
  const status = d.status ?? "idle";
  const [hovered, setHovered] = useState(false);

  return (
    <div
      className="relative"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div
        className={cn(
          "rounded-xl border-2 px-4 py-3 shadow-sm min-w-[180px] max-w-[240px] transition-all",
          statusColors[status],
          selected && "ring-2 ring-primary/30 border-primary"
        )}
      >
        <Handle type="target" position={Position.Left} className={cn(handleClass, "!-left-1")} />
        <Handle type="source" position={Position.Right} className={cn(handleClass, "!-right-1")} />
        <div className="flex items-center gap-2.5">
          <div
            className={cn(
              "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
              status === "idle" ? "bg-muted" : statusColors[status]
            )}
          >
            <Box className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium leading-tight truncate">{d.label}</p>
            {d.subtitle && (
              <p className="text-[11px] text-muted-foreground leading-tight truncate mt-0.5">
                {d.subtitle}
              </p>
            )}
          </div>
          <div className={cn("h-2.5 w-2.5 rounded-full shrink-0", statusDots[status])} />
        </div>
      </div>

      {/* Hover tooltip */}
      {hovered && (d.description || d.inputCount || d.outputCount) && (
        <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 z-50 pointer-events-none animate-in fade-in-0 zoom-in-95 duration-150">
          <div className="bg-popover border border-border rounded-lg shadow-lg p-3 min-w-[200px] max-w-[280px]">
            {d.description && (
              <p className="text-xs text-popover-foreground leading-relaxed mb-2 line-clamp-3">
                {d.description}
              </p>
            )}
            <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
              {d.inputCount != null && (
                <span className="flex items-center gap-1">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-500" />
                  {d.inputCount} input{d.inputCount !== 1 ? "s" : ""}
                </span>
              )}
              {d.outputCount != null && (
                <span className="flex items-center gap-1">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-green-500" />
                  {d.outputCount} output{d.outputCount !== 1 ? "s" : ""}
                </span>
              )}
            </div>
            {d.inputs && d.inputs.length > 0 && (
              <div className="mt-1.5 pt-1.5 border-t border-border">
                <p className="text-[10px] text-muted-foreground font-medium mb-0.5">Inputs</p>
                <p className="text-[10px] text-muted-foreground truncate">{d.inputs.join(", ")}</p>
              </div>
            )}
            {d.outputs && d.outputs.length > 0 && (
              <div className="mt-1 pt-1 border-t border-border">
                <p className="text-[10px] text-muted-foreground font-medium mb-0.5">Outputs</p>
                <p className="text-[10px] text-muted-foreground truncate">{d.outputs.join(", ")}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export const DAGNode = memo(DAGNodeComponent);
