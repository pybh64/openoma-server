import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "urql";
import { ArrowLeft, Pencil, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { v4 as uuidv4 } from "uuid";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { VersionBadge } from "@/components/shared/Badges";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { DAGCanvas, type DAGCanvasNode, type DAGCanvasEdge } from "@/components/canvas/FlowCanvas";
import { useDeleteEntity } from "@/hooks/useEntity";
import { CONTRACT_QUERY } from "@/graphql/queries/entities";
import { DELETE_CONTRACT } from "@/graphql/mutations/entities";

export default function ContractDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [showDelete, setShowDelete] = useState(false);

  const [result] = useQuery({
    query: CONTRACT_QUERY,
    variables: { id },
    pause: !id,
  });

  const { deleteEntity } = useDeleteEntity({
    mutation: DELETE_CONTRACT,
    onSuccess: () => {
      toast.success("Contract deleted");
      navigate("/contracts");
    },
  });

  const contract = result.data?.contract;

  // Build DAG: contract → workflows + sub-contracts as a relationship graph
  const { dagNodes, dagEdges } = useMemo(() => {
    if (!contract) return { dagNodes: [] as DAGCanvasNode[], dagEdges: [] as DAGCanvasEdge[] };

    const nodes: DAGCanvasNode[] = [];
    const edges: DAGCanvasEdge[] = [];
    const contractNodeId = "contract-root";

    nodes.push({
      id: contractNodeId,
      label: contract.name,
      subtitle: `Contract v${contract.version}`,
    });

    for (const ref of contract.workFlows ?? []) {
      const nodeId = `wf-${ref.flowId}`;
      nodes.push({
        id: nodeId,
        label: ref.alias || ref.flowId.slice(0, 12),
        subtitle: `Flow v${ref.flowVersion}`,
      });
      edges.push({
        id: `e-${uuidv4()}`,
        source: contractNodeId,
        target: nodeId,
      });
    }

    for (const ref of contract.subContracts ?? []) {
      const nodeId = `sc-${ref.contractId}`;
      nodes.push({
        id: nodeId,
        label: ref.alias || ref.contractId.slice(0, 12),
        subtitle: `Sub-contract v${ref.contractVersion}`,
      });
      edges.push({
        id: `e-${uuidv4()}`,
        source: contractNodeId,
        target: nodeId,
      });
    }

    return { dagNodes: nodes, dagEdges: edges };
  }, [contract]);

  if (result.fetching) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-muted-foreground">Contract not found</p>
        <Button variant="outline" onClick={() => navigate("/contracts")}>
          Back to list
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate("/contracts")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">{contract.name}</h1>
            <VersionBadge version={contract.version} />
          </div>
          <p className="text-sm text-muted-foreground">
            {contract.description || "No description"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => navigate(`/contracts/${id}/edit`)}>
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowDelete(true)}>
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      {/* DAG Canvas — primary view showing contract → workflow/sub-contract relationships */}
      {dagNodes.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">
              Contract Graph — {(contract.workFlows?.length ?? 0)} workflows, {(contract.subContracts?.length ?? 0)} sub-contracts
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="h-[350px] rounded-b-lg overflow-hidden">
              <DAGCanvas
                nodes={dagNodes}
                edges={dagEdges}
                interactive={false}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {contract.requiredOutcomes?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">
              Required Outcomes ({contract.requiredOutcomes.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {contract.requiredOutcomes.map((outcome: any) => (
                <div key={outcome.id} className="rounded-md border p-3">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="font-mono text-[10px]">
                      {outcome.id.slice(0, 8)}…
                    </Badge>
                    <span className="text-sm font-medium">{outcome.name}</span>
                  </div>
                  {outcome.description && (
                    <p className="mt-1 text-xs text-muted-foreground">{outcome.description}</p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {contract.assessmentBindings?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">
              Assessment Bindings ({contract.assessmentBindings.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {contract.assessmentBindings.map((binding: any, i: number) => (
                <div key={i} className="rounded-md border p-3 space-y-1">
                  <div className="text-xs">
                    <span className="text-muted-foreground">Outcome: </span>
                    <span className="font-mono">{binding.requiredOutcomeId.slice(0, 8)}…</span>
                  </div>
                  <div className="text-xs">
                    <span className="text-muted-foreground">Assessment Flow: </span>
                    <span
                      className="font-mono cursor-pointer hover:underline"
                      onClick={() => navigate(`/flows/${binding.assessmentFlowId}`)}
                    >
                      {binding.assessmentFlowId.slice(0, 8)}… v{binding.assessmentFlowVersion}
                    </span>
                  </div>
                  {binding.testFlowRefs?.length > 0 && (
                    <div className="text-xs">
                      <span className="text-muted-foreground">
                        Test Flows: {binding.testFlowRefs.length}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {contract.metadata && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Metadata</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="rounded bg-muted p-3 text-xs overflow-auto">
              {JSON.stringify(contract.metadata, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      <ConfirmDialog
        open={showDelete}
        onOpenChange={setShowDelete}
        title="Delete Contract"
        description={`Are you sure you want to delete "${contract.name}"? This will remove all versions.`}
        confirmLabel="Delete"
        destructive
        onConfirm={() => deleteEntity(id!)}
      />
    </div>
  );
}
