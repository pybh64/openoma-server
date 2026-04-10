import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "urql";
import { FLOW_EXECUTION_CANVAS_QUERY } from "@/graphql/queries/flows";
import { EXECUTION_EVENTS_QUERY } from "@/graphql/queries/executions";
import { FlowCanvas } from "@/components/canvas/FlowCanvas";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { LoadingState, ErrorState } from "@/components/shared/StateDisplay";
import { formatDate, executionStateColor } from "@/lib/utils";
import type { NodeReference, ExecutionEvent, NodeExecutionState } from "@/types";

export function FlowExecutionPage() {
  const { id } = useParams<{ id: string }>();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const [{ data, fetching, error }] = useQuery({
    query: FLOW_EXECUTION_CANVAS_QUERY,
    variables: { flowExecutionId: id },
    pause: !id,
  });

  const [{ data: eventsData }] = useQuery({
    query: EXECUTION_EVENTS_QUERY,
    variables: { executionId: id },
    pause: !id,
  });

  if (fetching) return <LoadingState message="Loading execution..." />;
  if (error) return <ErrorState message={error.message} />;
  if (!data?.flowExecutionCanvas) return <ErrorState message="Execution not found" />;

  const { flow, layout, execution, nodeStates } = data.flowExecutionCanvas;
  const events: ExecutionEvent[] = eventsData?.executionEvents ?? [];

  const selectedNode = selectedNodeId
    ? flow.nodes.find((n: NodeReference) => n.id === selectedNodeId) ?? null
    : null;
  const selectedNodeState = selectedNodeId
    ? nodeStates.find((ns: NodeExecutionState) => ns.nodeReferenceId === selectedNodeId)
    : null;

  return (
    <div className="flex flex-col h-full">
      {/* Header bar */}
      <div className="flex items-center gap-3 px-4 py-2.5 border-b border-border bg-card">
        <Link to="/executions" className="text-xs text-muted-foreground hover:text-foreground">
          ← Executions
        </Link>
        <div className="h-4 w-px bg-border" />
        <span className="text-sm font-semibold">{flow.name}</span>
        <Badge variant="outline" className="text-[10px]">v{execution.flowVersion}</Badge>
        <Badge className={executionStateColor(execution.state) + " border-0 text-[11px]"}>
          {execution.state}
        </Badge>
        <div className="text-xs text-muted-foreground">
          {nodeStates.filter((ns: NodeExecutionState) => ns.state === "completed").length}/{nodeStates.length} completed
        </div>
        <div className="flex-1" />
        <span className="text-xs text-muted-foreground">Started {formatDate(execution.createdAt)}</span>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Canvas */}
        <div className="flex-1">
          <FlowCanvas
            flow={flow}
            layout={layout}
            nodeStates={nodeStates}
            onNodeSelect={setSelectedNodeId}
          />
        </div>

        {/* Side panel */}
        <div className="w-80 border-l border-border bg-card flex flex-col overflow-hidden">
          {selectedNode ? (
            <div className="flex flex-col h-full">
              <div className="p-3 border-b border-border">
                <h3 className="text-sm font-semibold">{selectedNode.alias || selectedNode.workBlock?.name || "Node"}</h3>
                {selectedNodeState && (
                  <Badge className={executionStateColor(selectedNodeState.state || "created") + " border-0 text-[10px] mt-1"}>
                    {selectedNodeState.state || "pending"}
                  </Badge>
                )}
                {selectedNodeState?.executor && (
                  <div className="text-xs text-muted-foreground mt-1">
                    Executor: {selectedNodeState.executor.identifier} ({selectedNodeState.executor.type})
                  </div>
                )}
              </div>
              <ScrollArea className="flex-1 p-3">
                <div className="space-y-2">
                  {events
                    .filter((e) => e.executionId === selectedNodeState?.blockExecutionId)
                    .map((event) => (
                      <EventCard key={event.id} event={event} />
                    ))}
                </div>
              </ScrollArea>
            </div>
          ) : (
            <div className="flex flex-col h-full">
              <div className="p-3 border-b border-border">
                <h3 className="text-sm font-semibold">Event Timeline</h3>
                <p className="text-xs text-muted-foreground">{events.length} events</p>
              </div>
              <ScrollArea className="flex-1 p-3">
                <div className="space-y-2">
                  {events.map((event: ExecutionEvent) => (
                    <EventCard key={event.id} event={event} />
                  ))}
                  {events.length === 0 && (
                    <p className="text-xs text-muted-foreground text-center py-4">No events yet</p>
                  )}
                </div>
              </ScrollArea>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function EventCard({ event }: { event: ExecutionEvent }) {
  return (
    <Card className="shadow-none">
      <CardContent className="p-2.5">
        <div className="flex items-center justify-between gap-2">
          <Badge className={executionStateColor(event.eventType) + " border-0 text-[10px]"}>
            {event.eventType}
          </Badge>
          <span className="text-[10px] text-muted-foreground">{formatDate(event.timestamp)}</span>
        </div>
        {event.executor && (
          <div className="text-[11px] text-muted-foreground mt-1">
            {event.executor.identifier} ({event.executor.type})
          </div>
        )}
      </CardContent>
    </Card>
  );
}
