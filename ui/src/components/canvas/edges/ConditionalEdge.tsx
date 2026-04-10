import { memo } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from "@xyflow/react";

interface ConditionalEdgeData {
  conditionDescription?: string;
}

export const ConditionalEdge = memo(function ConditionalEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}: EdgeProps & { data?: ConditionalEdgeData }) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: selected ? "var(--color-primary)" : "var(--color-muted-foreground)",
          strokeWidth: selected ? 3 : 2,
        }}
      />
      {data?.conditionDescription && (
        <EdgeLabelRenderer>
          <div
            className="absolute text-[10px] bg-card border border-border rounded px-1.5 py-0.5 shadow-sm text-muted-foreground pointer-events-all"
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            }}
          >
            {data.conditionDescription}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});
