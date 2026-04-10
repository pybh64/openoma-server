import { useState, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation } from "urql";
import { Edit3, Eye } from "lucide-react";
import { FLOW_CANVAS_QUERY } from "@/graphql/queries/flows";
import { CREATE_FLOW_DRAFT } from "@/graphql/mutations/flowDrafts";
import { FlowCanvas } from "@/components/canvas/FlowCanvas";
import { NodeDetailPanel } from "@/components/canvas/panels/NodeDetailPanel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingState, ErrorState } from "@/components/shared/StateDisplay";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { NodeReference } from "@/types";

export function FlowCanvasPage() {
  const { id, version } = useParams<{ id: string; version?: string }>();
  const navigate = useNavigate();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const [{ data, fetching, error }] = useQuery({
    query: FLOW_CANVAS_QUERY,
    variables: { flowId: id, flowVersion: version ? parseInt(version) : undefined },
    pause: !id,
  });

  const [, createDraft] = useMutation(CREATE_FLOW_DRAFT);

  const handleEdit = useCallback(async () => {
    if (!data?.flowCanvas?.flow) return;
    const f = data.flowCanvas.flow;
    const result = await createDraft({ flowId: f.id, flowVersion: f.version });
    if (result.data?.createFlowDraft) {
      navigate(`/drafts/${result.data.createFlowDraft.draftId}`);
    }
  }, [data, createDraft, navigate]);

  if (fetching) return <LoadingState message="Loading flow canvas..." />;
  if (error) return <ErrorState message={error.message} />;
  if (!data?.flowCanvas) return <ErrorState message="Flow not found" />;

  const { flow, layout, workBlockSummaries } = data.flowCanvas;
  const selectedNode = selectedNodeId
    ? flow.nodes.find((n: NodeReference) => n.id === selectedNodeId) ?? null
    : null;

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-4 py-2.5 border-b border-border bg-card">
        <Link to="/flows" className="text-xs text-muted-foreground hover:text-foreground">
          ← Flows
        </Link>
        <div className="h-4 w-px bg-border" />
        <span className="text-sm font-semibold">{flow.name}</span>
        <Badge variant="outline" className="text-[10px]">v{flow.version}</Badge>
        <Badge variant="secondary" className="text-[10px]">
          <Eye className="h-3 w-3 mr-1" /> Read-only
        </Badge>
        <div className="text-xs text-muted-foreground">
          {flow.nodes.length} nodes · {flow.edges.length} edges
        </div>
        <div className="flex-1" />
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline" size="sm" onClick={handleEdit}>
              <Edit3 className="h-3.5 w-3.5 mr-1" /> Edit as Draft
            </Button>
          </TooltipTrigger>
          <TooltipContent>Create a mutable draft from this version</TooltipContent>
        </Tooltip>
      </div>

      {/* Canvas + panels */}
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1">
          <FlowCanvas
            flow={flow}
            layout={layout}
            workBlockSummaries={workBlockSummaries}
            onNodeSelect={setSelectedNodeId}
          />
        </div>

        {selectedNode && (
          <NodeDetailPanel
            node={selectedNode}
            edges={flow.edges}
            allNodes={flow.nodes}
            onClose={() => setSelectedNodeId(null)}
          />
        )}
      </div>
    </div>
  );
}
