import { memo } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  type EdgeProps,
} from "@xyflow/react";

function DAGEdgeComponent({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
  markerEnd,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 12,
  });

  const condition = (data as any)?.condition;
  const hasCondition = !!condition?.description;

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          stroke: selected
            ? "var(--color-primary)"
            : "var(--color-muted-foreground)",
          strokeWidth: selected ? 2.5 : 1.5,
          opacity: selected ? 1 : 0.6,
        }}
      />
      {hasCondition && (
        <EdgeLabelRenderer>
          <div
            className="nodrag nopan absolute"
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: "all",
            }}
          >
            <div className="rounded-full bg-background border border-border px-2 py-0.5 text-[10px] text-muted-foreground shadow-sm">
              {condition.description}
            </div>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export const DAGEdge = memo(DAGEdgeComponent);
