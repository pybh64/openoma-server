import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface EntryNodeData {
  label: string;
}

export const EntryNode = memo(function EntryNode({
  data,
  selected,
}: NodeProps & { data: EntryNodeData }) {
  return (
    <div
      className={cn(
        "rounded-full border-2 bg-node-entry px-4 py-2 shadow-sm transition-all",
        selected ? "border-primary shadow-md" : "border-node-entry-border"
      )}
    >
      <span className="text-xs font-semibold text-foreground">{data.label}</span>
      <Handle
        type="source"
        position={Position.Right}
        className="!w-2.5 !h-2.5 !bg-emerald-500 !border-2 !border-card"
      />
    </div>
  );
});
