import { memo } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  type EdgeProps,
} from "@xyflow/react";
import { cn } from "@/lib/utils";

interface FlowEdgeData {
  conditionDescription?: string;
  portMappings?: { sourcePort: string; targetPort: string }[];
}

export const FlowEdge = memo(function FlowEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  data,
  selected,
}: EdgeProps & { data?: FlowEdgeData }) {
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 14,
  });

  const mappingCount = data?.portMappings?.length ?? 0;
  const hasLabel = Boolean(data?.conditionDescription || mappingCount > 0);

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        interactionWidth={24}
        style={{
          stroke: selected ? "var(--color-primary)" : "var(--color-muted-foreground)",
          strokeWidth: selected ? 3 : 2.25,
        }}
      />
      {hasLabel && (
        <EdgeLabelRenderer>
          <div
            className={cn(
              "pointer-events-auto absolute max-w-[240px] rounded-lg border bg-card/95 px-2.5 py-1.5 text-left shadow-sm backdrop-blur-sm",
              selected ? "border-primary shadow-md" : "border-border",
            )}
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            }}
          >
            {data?.conditionDescription && (
              <div className="text-[11px] font-medium leading-tight text-foreground">
                {data.conditionDescription}
              </div>
            )}
            {mappingCount > 0 && (
              <div className="mt-1 text-[10px] text-muted-foreground">
                {mappingCount} port mapping{mappingCount === 1 ? "" : "s"}
              </div>
            )}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});
