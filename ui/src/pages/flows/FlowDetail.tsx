import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "urql";
import { ArrowLeft, Trash2, Play } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { VersionBadge } from "@/components/shared/Badges";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { DAGCanvas, type DAGCanvasNode, type DAGCanvasEdge } from "@/components/canvas/FlowCanvas";
import { useDeleteEntity } from "@/hooks/useEntity";
import { FLOW_QUERY, WORK_BLOCKS_QUERY } from "@/graphql/queries/entities";
import { DELETE_FLOW } from "@/graphql/mutations/entities";

export default function FlowDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [showDelete, setShowDelete] = useState(false);

  const [result] = useQuery({
    query: FLOW_QUERY,
    variables: { id },
    pause: !id,
  });

  const [wbResult] = useQuery({ query: WORK_BLOCKS_QUERY });

  const { deleteEntity } = useDeleteEntity({
    mutation: DELETE_FLOW,
    onSuccess: () => {
      toast.success("Flow deleted");
      navigate("/flows");
    },
  });

  const flow = result.data?.flow;
  const workBlocks: any[] = wbResult.data?.workBlocks ?? [];

  const dagNodes: DAGCanvasNode[] = useMemo(
    () =>
      (flow?.nodes ?? []).map((n: any) => {
        const wb = workBlocks.find((w: any) => w.id === n.targetId);
        return {
          id: n.id,
          label: n.alias || wb?.name || n.targetId.slice(0, 12),
          subtitle: `v${n.targetVersion}`,
          description: wb?.description,
          inputCount: wb?.inputs?.length,
          outputCount: wb?.outputs?.length,
          inputs: wb?.inputs?.map((p: any) => p.name),
          outputs: wb?.outputs?.map((p: any) => p.name),
          meta: { workBlockId: n.targetId },
        };
      }),
    [flow?.nodes, workBlocks]
  );

  const dagEdges: DAGCanvasEdge[] = useMemo(
    () =>
      (flow?.edges ?? [])
        .filter((e: any) => e.sourceId && e.targetId)
        .map((e: any, i: number) => ({
          id: `e-${i}`,
          source: e.sourceId,
          target: e.targetId,
          condition: e.condition?.description,
        })),
    [flow?.edges]
  );

  if (result.fetching) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!flow) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-muted-foreground">Flow not found</p>
        <Button variant="outline" onClick={() => navigate("/flows")}>
          Back to list
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate("/flows")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">{flow.name}</h1>
            <VersionBadge version={flow.version} />
          </div>
          <p className="text-sm text-muted-foreground">{flow.description || "No description"}</p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" onClick={() => navigate(`/flows/${id}/edit`)}>
            <Play className="mr-2 h-4 w-4" />
            Open Editor
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowDelete(true)}>
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      {/* DAG Canvas — primary view */}
      {dagNodes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">
              Flow Graph — {dagNodes.length} nodes, {dagEdges.length} edges
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="h-[400px] rounded-b-lg overflow-hidden">
              <DAGCanvas
                nodes={dagNodes}
                edges={dagEdges}
                interactive={false}
                onNodeClick={(nodeId) => {
                  const node = dagNodes.find((n) => n.id === nodeId);
                  const wbId = (node?.meta as any)?.workBlockId;
                  if (wbId) navigate(`/work-blocks/${wbId}`);
                }}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {flow.expectedOutcome && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Expected Outcome</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="rounded bg-muted p-3 text-xs overflow-auto">
              {JSON.stringify(flow.expectedOutcome, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {flow.metadata && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Metadata</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="rounded bg-muted p-3 text-xs overflow-auto">
              {JSON.stringify(flow.metadata, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      <ConfirmDialog
        open={showDelete}
        onOpenChange={setShowDelete}
        title="Delete Flow"
        description={`Are you sure you want to delete "${flow.name}"? This will remove all versions.`}
        confirmLabel="Delete"
        destructive
        onConfirm={() => deleteEntity(id!)}
      />
    </div>
  );
}
