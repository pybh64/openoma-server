import { memo } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from "@xyflow/react";
import { Badge } from "@/components/ui/badge";

function ConditionalEdgeComponent({
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
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
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
            ? "hsl(var(--primary))"
            : hasCondition
            ? "#f59e0b"
            : "hsl(var(--muted-foreground))",
          strokeWidth: selected ? 2 : 1.5,
          strokeDasharray: hasCondition ? "6 3" : undefined,
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
            <Badge
              variant="outline"
              className="bg-background text-[10px] border-yellow-500/50 text-yellow-500 cursor-pointer"
            >
              {condition.description}
            </Badge>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export const ConditionalEdge = memo(ConditionalEdgeComponent);
