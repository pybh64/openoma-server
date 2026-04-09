import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useSubscription } from "urql";
import { ArrowLeft, Radio } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { StateBadge } from "@/components/shared/Badges";
import { BLOCK_EXECUTION_QUERY } from "@/graphql/queries/executions";
import { EXECUTION_EVENTS_SUBSCRIPTION } from "@/graphql/subscriptions/executions";

const eventTypeColors: Record<string, string> = {
  CREATED: "bg-blue-500",
  EXECUTOR_ASSIGNED: "bg-purple-500",
  EXECUTOR_RELEASED: "bg-purple-400",
  STARTED: "bg-cyan-500",
  PROGRESS: "bg-yellow-500",
  OUTCOME_PRODUCED: "bg-green-400",
  COMPLETED: "bg-green-500",
  FAILED: "bg-red-500",
  SKIPPED: "bg-gray-500",
  CANCELLED: "bg-orange-500",
};

export default function ExecutionDetail() {
  const { type, id } = useParams<{ type: string; id: string }>();
  const navigate = useNavigate();
  const [live, setLive] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  const [result] = useQuery({
    query: BLOCK_EXECUTION_QUERY,
    variables: { executionId: id },
    pause: !id || type !== "block",
  });

  const [subResult] = useSubscription(
    {
      query: EXECUTION_EVENTS_SUBSCRIPTION,
      variables: { executionId: id },
      pause: !live || !id,
    },
  );

  const execution = result.data?.blockExecution;
  const events = execution?.events ?? [];
  const liveEvents = subResult.data ? [subResult.data.executionEvents] : [];
  const allEvents = [...events, ...liveEvents];

  // Auto-scroll on new events
  useEffect(() => {
    if (live && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [allEvents.length, live]);

  if (result.fetching) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!execution && type === "block") {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-muted-foreground">Execution not found</p>
        <Button variant="outline" onClick={() => navigate("/executions")}>
          Back to list
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate("/executions")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">
              {type === "block" ? "Block" : type === "flow" ? "Flow" : "Contract"} Execution
            </h1>
            {execution?.state && <StateBadge state={execution.state} />}
          </div>
          <p className="text-sm text-muted-foreground font-mono">{id}</p>
        </div>
        <Button
          variant={live ? "default" : "outline"}
          size="sm"
          onClick={() => setLive(!live)}
        >
          <Radio className={`mr-2 h-4 w-4 ${live ? "animate-pulse" : ""}`} />
          {live ? "Live" : "Paused"}
        </Button>
      </div>

      {execution && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-muted-foreground">Work Block</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-mono text-xs">{execution.workBlockId?.slice(0, 16)}…</p>
              <p className="text-xs text-muted-foreground">v{execution.workBlockVersion}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-muted-foreground">Node Reference</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-mono text-xs">{execution.nodeReferenceId?.slice(0, 16)}…</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-muted-foreground">Events</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{allEvents.length}</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-sm">Event Timeline</CardTitle>
          {live && (
            <Badge variant="outline" className="text-[10px] text-green-500 border-green-500/30">
              <span className="mr-1 h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse inline-block" />
              Streaming
            </Badge>
          )}
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]" ref={scrollRef}>
            {allEvents.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No events recorded yet
              </p>
            ) : (
              <div className="relative ml-4 border-l border-border pl-6 space-y-4">
                {allEvents.map((event: any, i: number) => (
                  <div key={event.id ?? i} className="relative">
                    <div
                      className={`absolute -left-[31px] h-3 w-3 rounded-full border-2 border-background ${
                        eventTypeColors[event.eventType] ?? "bg-gray-500"
                      }`}
                    />
                    <div className="rounded-md border p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="secondary" className="text-[10px]">
                          {event.eventType}
                        </Badge>
                        <span className="text-[10px] text-muted-foreground">
                          {new Date(event.timestamp).toLocaleString()}
                        </span>
                        {event.executor && (
                          <span className="text-[10px] text-muted-foreground ml-auto">
                            {event.executor.type}: {event.executor.identifier}
                          </span>
                        )}
                      </div>
                      {event.payload && (
                        <pre className="mt-2 rounded bg-muted p-2 text-[10px] overflow-auto">
                          {JSON.stringify(event.payload, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
