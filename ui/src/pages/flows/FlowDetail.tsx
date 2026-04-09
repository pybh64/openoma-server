import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "urql";
import { ArrowLeft, Trash2, Play } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { VersionBadge } from "@/components/shared/Badges";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { useDeleteEntity } from "@/hooks/useEntity";
import { FLOW_QUERY } from "@/graphql/queries/entities";
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

  const { deleteEntity } = useDeleteEntity({
    mutation: DELETE_FLOW,
    onSuccess: () => {
      toast.success("Flow deleted");
      navigate("/flows");
    },
  });

  const flow = result.data?.flow;

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

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">
              Nodes ({flow.nodes?.length ?? 0})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {flow.nodes?.length > 0 ? (
              <div className="space-y-2">
                {flow.nodes.map((node: any) => (
                  <div key={node.id} className="flex items-center gap-2 rounded-md border p-2">
                    <Badge variant="outline" className="font-mono text-[10px]">
                      {node.id.slice(0, 8)}…
                    </Badge>
                    <span className="text-sm">{node.alias || "Unnamed"}</span>
                    <span className="ml-auto text-xs text-muted-foreground">
                      → {node.targetId.slice(0, 8)}… v{node.targetVersion}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No nodes</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">
              Edges ({flow.edges?.length ?? 0})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {flow.edges?.length > 0 ? (
              <div className="space-y-2">
                {flow.edges.map((edge: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 rounded-md border p-2 text-xs">
                    <span className="font-mono">
                      {edge.sourceId ? edge.sourceId.slice(0, 8) + "…" : "entry"}
                    </span>
                    <span className="text-muted-foreground">→</span>
                    <span className="font-mono">{edge.targetId.slice(0, 8)}…</span>
                    {edge.condition && (
                      <Badge variant="secondary" className="text-[10px]">
                        {edge.condition.description}
                      </Badge>
                    )}
                    {edge.portMappings?.length > 0 && (
                      <span className="text-muted-foreground">
                        ({edge.portMappings.length} mappings)
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No edges</p>
            )}
          </CardContent>
        </Card>
      </div>

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
