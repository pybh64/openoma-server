import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

export interface WorkBlockNodeData {
  label: string;
  alias: string;
  workBlockId: string;
  workBlockVersion: number;
  inputs: { name: string; required: boolean }[];
  outputs: { name: string; required: boolean }[];
  [key: string]: unknown;
}

function WorkBlockNodeComponent({ data, selected }: NodeProps) {
  const d = data as unknown as WorkBlockNodeData;
  return (
    <div
      className={cn(
        "rounded-lg border bg-card shadow-md min-w-[180px] transition-all",
        selected ? "border-primary ring-2 ring-primary/20" : "border-border"
      )}
    >
      <div className="flex items-center gap-2 border-b border-border bg-muted/30 px-3 py-2 rounded-t-lg">
        <span className="text-sm font-medium truncate">{d.alias || d.label}</span>
        <Badge variant="outline" className="ml-auto text-[10px] font-mono shrink-0">
          v{d.workBlockVersion}
        </Badge>
      </div>

      <div className="flex">
        {/* Input ports */}
        <div className="flex-1 border-r border-border/50 py-2 px-1 min-w-[80px]">
          {d.inputs?.map((port) => (
            <div key={port.name} className="relative flex items-center py-0.5 pl-3 pr-1">
              <Handle
                type="target"
                position={Position.Left}
                id={port.name}
                className="!bg-blue-500 !border-blue-600 !w-2.5 !h-2.5"
                style={{ top: "auto" }}
              />
              <span className="text-[10px] text-muted-foreground truncate">
                {port.name}
                {port.required && <span className="text-destructive-foreground">*</span>}
              </span>
            </div>
          ))}
          {(!d.inputs || d.inputs.length === 0) && (
            <div className="relative py-0.5 pl-3">
              <Handle
                type="target"
                position={Position.Left}
                id="__default_in"
                className="!bg-blue-500/50 !border-blue-600/50 !w-2 !h-2"
              />
              <span className="text-[10px] text-muted-foreground/50 italic">in</span>
            </div>
          )}
        </div>

        {/* Output ports */}
        <div className="flex-1 py-2 px-1 min-w-[80px]">
          {d.outputs?.map((port) => (
            <div key={port.name} className="relative flex items-center justify-end py-0.5 pl-1 pr-3">
              <span className="text-[10px] text-muted-foreground truncate">
                {port.name}
              </span>
              <Handle
                type="source"
                position={Position.Right}
                id={port.name}
                className="!bg-green-500 !border-green-600 !w-2.5 !h-2.5"
                style={{ top: "auto" }}
              />
            </div>
          ))}
          {(!d.outputs || d.outputs.length === 0) && (
            <div className="relative flex justify-end py-0.5 pr-3">
              <span className="text-[10px] text-muted-foreground/50 italic">out</span>
              <Handle
                type="source"
                position={Position.Right}
                id="__default_out"
                className="!bg-green-500/50 !border-green-600/50 !w-2 !h-2"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export const WorkBlockNode = memo(WorkBlockNodeComponent);
