import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "urql";
import {
  ArrowLeft,
  Save,
  Plus,
  Link2,
  Trash2,
  X,
  ExternalLink,
} from "lucide-react";
import { v4 as uuid } from "uuid";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DAGCanvas, type DAGCanvasNode, type DAGCanvasEdge } from "@/components/canvas/FlowCanvas";
import { useCanvasStore } from "@/stores/canvas";
import { FLOW_QUERY, WORK_BLOCKS_QUERY, WORK_BLOCK_QUERY } from "@/graphql/queries/entities";
import { CREATE_FLOW, UPDATE_FLOW } from "@/graphql/mutations/entities";

interface FlowNode {
  id: string;
  workBlockId: string;
  workBlockName: string;
  workBlockVersion: number;
  alias: string;
}

interface FlowEdge {
  id: string;
  sourceId: string;
  targetId: string;
  condition: string;
}

export default function FlowEditor() {
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id && id !== "new";
  const navigate = useNavigate();

  const [flowName, setFlowName] = useState("");
  const [flowDescription, setFlowDescription] = useState("");
  const [flowNodes, setFlowNodes] = useState<FlowNode[]>([]);
  const [flowEdges, setFlowEdges] = useState<FlowEdge[]>([]);
  const [loaded, setLoaded] = useState(!isEdit);

  // Dialogs
  const [addNodeOpen, setAddNodeOpen] = useState(false);
  const [addEdgeOpen, setAddEdgeOpen] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [_selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);

  // Undo/redo via canvas store (reusing its snapshot logic)
  const store = useCanvasStore();

  // Queries
  const [flowResult] = useQuery({
    query: FLOW_QUERY,
    variables: { id },
    pause: !isEdit,
  });

  const [wbResult] = useQuery({
    query: WORK_BLOCKS_QUERY,
    variables: { limit: 200, latestOnly: true },
  });

  const workBlocks: any[] = wbResult.data?.workBlocks ?? [];

  // Load existing flow
  useEffect(() => {
    if (isEdit && flowResult.data?.flow && !loaded) {
      const flow = flowResult.data.flow;
      setFlowName(flow.name);
      setFlowDescription(flow.description ?? "");

      const nodes: FlowNode[] = (flow.nodes ?? []).map((n: any) => ({
        id: n.id,
        workBlockId: n.targetId,
        workBlockName: n.alias || n.targetId.slice(0, 8),
        workBlockVersion: n.targetVersion,
        alias: n.alias ?? "",
      }));

      const edges: FlowEdge[] = (flow.edges ?? [])
        .filter((e: any) => e.sourceId && e.targetId)
        .map((e: any) => ({
          id: `e-${uuid()}`,
          sourceId: e.sourceId,
          targetId: e.targetId,
          condition: e.condition?.description ?? "",
        }));

      setFlowNodes(nodes);
      setFlowEdges(edges);
      setLoaded(true);
    }
  }, [isEdit, flowResult.data, loaded]);

  // Reset on unmount
  useEffect(() => {
    store.reset();
    return () => store.reset();
  }, []);

  // Mutations
  const [, createMutation] = useMutation(CREATE_FLOW);
  const [, updateMutation] = useMutation(UPDATE_FLOW);

  // Build DAG data from our flowNodes/flowEdges
  const dagNodes: DAGCanvasNode[] = useMemo(
    () =>
      flowNodes.map((n) => {
        const wb = workBlocks.find((w: any) => w.id === n.workBlockId);
        return {
          id: n.id,
          label: n.alias || wb?.name || n.workBlockId.slice(0, 12),
          subtitle: `v${n.workBlockVersion}`,
        };
      }),
    [flowNodes, workBlocks]
  );

  const dagEdges: DAGCanvasEdge[] = useMemo(
    () =>
      flowEdges.map((e) => ({
        id: e.id,
        source: e.sourceId,
        target: e.targetId,
        condition: e.condition || undefined,
      })),
    [flowEdges]
  );

  // Add node
  const [newNodeWBId, setNewNodeWBId] = useState("");
  const [newNodeAlias, setNewNodeAlias] = useState("");

  const handleAddNode = useCallback(() => {
    if (!newNodeWBId) return;
    const wb = workBlocks.find((w: any) => w.id === newNodeWBId);
    if (!wb) return;

    setFlowNodes((prev) => [
      ...prev,
      {
        id: uuid(),
        workBlockId: wb.id,
        workBlockName: wb.name,
        workBlockVersion: wb.version,
        alias: newNodeAlias.trim() || wb.name,
      },
    ]);

    setNewNodeWBId("");
    setNewNodeAlias("");
    setAddNodeOpen(false);
  }, [newNodeWBId, newNodeAlias, workBlocks]);

  // Add edge
  const [newEdgeSource, setNewEdgeSource] = useState("");
  const [newEdgeTarget, setNewEdgeTarget] = useState("");
  const [newEdgeCondition, setNewEdgeCondition] = useState("");

  const handleAddEdge = useCallback(() => {
    if (!newEdgeSource || !newEdgeTarget) return;
    if (newEdgeSource === newEdgeTarget) {
      toast.error("Source and target must be different");
      return;
    }

    setFlowEdges((prev) => [
      ...prev,
      {
        id: `e-${uuid()}`,
        sourceId: newEdgeSource,
        targetId: newEdgeTarget,
        condition: newEdgeCondition.trim(),
      },
    ]);

    setNewEdgeSource("");
    setNewEdgeTarget("");
    setNewEdgeCondition("");
    setAddEdgeOpen(false);
  }, [newEdgeSource, newEdgeTarget, newEdgeCondition]);

  // Delete node
  const handleDeleteNode = useCallback(
    (nodeId: string) => {
      setFlowNodes((prev) => prev.filter((n) => n.id !== nodeId));
      setFlowEdges((prev) =>
        prev.filter((e) => e.sourceId !== nodeId && e.targetId !== nodeId)
      );
      setSelectedNodeId(null);
    },
    []
  );

  // Delete edge
  const handleDeleteEdge = useCallback((edgeId: string) => {
    setFlowEdges((prev) => prev.filter((e) => e.id !== edgeId));
  }, []);

  // Save
  const handleSave = useCallback(async () => {
    if (!flowName.trim()) {
      toast.error("Flow name is required");
      return;
    }

    const nodes = flowNodes.map((n) => ({
      id: n.id,
      targetId: n.workBlockId,
      targetVersion: n.workBlockVersion,
      alias: n.alias || null,
    }));

    const edges = flowEdges.map((e) => ({
      sourceId: e.sourceId,
      targetId: e.targetId,
      condition: e.condition ? { description: e.condition } : null,
      portMappings: [],
    }));

    const input: any = {
      name: flowName.trim(),
      description: flowDescription,
      nodes,
      edges,
    };

    let result;
    if (isEdit) {
      input.id = id;
      result = await updateMutation({ input });
    } else {
      result = await createMutation({ input });
    }

    if (result.error) {
      toast.error(result.error.message);
    } else {
      toast.success(isEdit ? "Flow updated" : "Flow created");
      const newId = isEdit ? id : result.data?.createFlow?.id;
      if (newId && !isEdit) navigate(`/flows/${newId}`, { replace: true });
    }
  }, [flowName, flowDescription, flowNodes, flowEdges, isEdit, id, createMutation, updateMutation, navigate]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        handleSave();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleSave]);

  const inspectedNode = selectedNodeId
    ? flowNodes.find((n) => n.id === selectedNodeId) ?? null
    : null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-background">
      {/* Toolbar */}
      <div className="flex h-12 items-center gap-2 border-b border-border px-4">
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <Separator orientation="vertical" className="h-6" />
        <Input
          value={flowName}
          onChange={(e) => setFlowName(e.target.value)}
          placeholder="Flow name"
          className="h-8 w-48 text-sm font-medium"
        />
        <Input
          value={flowDescription}
          onChange={(e) => setFlowDescription(e.target.value)}
          placeholder="Description..."
          className="h-8 w-64 text-sm text-muted-foreground"
        />
        <div className="ml-auto flex items-center gap-1">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="sm" className="h-8 gap-1.5" onClick={() => setAddNodeOpen(true)}>
                <Plus className="h-3.5 w-3.5" />
                Node
              </Button>
            </TooltipTrigger>
            <TooltipContent>Add a work block node</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="h-8 gap-1.5"
                onClick={() => setAddEdgeOpen(true)}
                disabled={flowNodes.length < 2}
              >
                <Link2 className="h-3.5 w-3.5" />
                Edge
              </Button>
            </TooltipTrigger>
            <TooltipContent>Connect two nodes</TooltipContent>
          </Tooltip>
          <Separator orientation="vertical" className="h-6 mx-1" />
          <Button size="sm" onClick={handleSave}>
            <Save className="mr-2 h-4 w-4" />
            Save
          </Button>
        </div>
      </div>

      {/* Main area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Canvas */}
        <div className="flex-1 relative">
          {flowNodes.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center space-y-3">
                <p className="text-muted-foreground text-sm">No nodes yet</p>
                <Button variant="outline" onClick={() => setAddNodeOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add First Node
                </Button>
              </div>
            </div>
          ) : (
            <DAGCanvas
              nodes={dagNodes}
              edges={dagEdges}
              onNodeClick={(id) => {
                setSelectedNodeId(id);
                setSelectedEdgeId(null);
              }}
              onEdgeClick={(id) => {
                setSelectedEdgeId(id);
                setSelectedNodeId(null);
              }}
              onConnect={(sourceId, targetId) => {
                if (sourceId === targetId) return;
                const exists = flowEdges.some(
                  (e) => e.sourceId === sourceId && e.targetId === targetId
                );
                if (exists) return;
                setFlowEdges((prev) => [
                  ...prev,
                  {
                    id: `e-${uuid()}`,
                    sourceId,
                    targetId,
                    condition: "",
                  },
                ]);
              }}
              interactive
            />
          )}
        </div>

        {/* Right panel — Inspector / Node list */}
        {inspectedNode ? (
          <NodeInspectorPanel
            node={inspectedNode}
            workBlocks={workBlocks}
            onClose={() => { setSelectedNodeId(null); setSelectedEdgeId(null); }}
            onDelete={() => handleDeleteNode(inspectedNode.id)}
            onNavigate={(wbId) => navigate(`/work-blocks/${wbId}`)}
          />
        ) : (
          <div className="w-64 border-l border-border bg-background flex flex-col">
            <div className="p-3 border-b border-border">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Nodes ({flowNodes.length})
              </h3>
            </div>
            <ScrollArea className="flex-1">
              <div className="p-2 space-y-1">
                {flowNodes.map((n) => {
                  const wb = workBlocks.find((w: any) => w.id === n.workBlockId);
                  return (
                    <div
                      key={n.id}
                      className="rounded-lg border border-border p-2 cursor-pointer transition-colors hover:bg-accent"
                      onClick={() => { setSelectedNodeId(n.id); setSelectedEdgeId(null); }}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium truncate flex-1">
                          {n.alias || wb?.name || n.workBlockId.slice(0, 12)}
                        </span>
                        <Badge variant="outline" className="text-[9px] font-mono shrink-0">
                          v{n.workBlockVersion}
                        </Badge>
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>

            {/* Edges section */}
            <div className="p-3 border-t border-border">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Edges ({flowEdges.length})
              </h3>
              <div className="space-y-1 max-h-40 overflow-auto">
                {flowEdges.map((e) => {
                  const src = flowNodes.find((n) => n.id === e.sourceId);
                  const tgt = flowNodes.find((n) => n.id === e.targetId);
                  return (
                    <div
                      key={e.id}
                      className="flex items-center gap-1 text-[11px] rounded border border-border px-2 py-1"
                    >
                      <span className="truncate">{src?.alias || "?"}</span>
                      <span className="text-muted-foreground shrink-0">→</span>
                      <span className="truncate">{tgt?.alias || "?"}</span>
                      {e.condition && (
                        <span className="text-muted-foreground truncate ml-1">({e.condition})</span>
                      )}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-4 w-4 ml-auto shrink-0"
                        onClick={() => handleDeleteEdge(e.id)}
                      >
                        <Trash2 className="h-2.5 w-2.5 text-muted-foreground" />
                      </Button>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add Node Dialog */}
      <Dialog open={addNodeOpen} onOpenChange={setAddNodeOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Node</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>Work Block</Label>
              <Select value={newNodeWBId} onValueChange={setNewNodeWBId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a work block..." />
                </SelectTrigger>
                <SelectContent>
                  {workBlocks.map((wb: any) => (
                    <SelectItem key={wb.id} value={wb.id}>
                      {wb.name} (v{wb.version})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Alias (optional)</Label>
              <Input
                value={newNodeAlias}
                onChange={(e) => setNewNodeAlias(e.target.value)}
                placeholder="Custom display name"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddNodeOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddNode} disabled={!newNodeWBId}>
              Add
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Edge Dialog */}
      <Dialog open={addEdgeOpen} onOpenChange={setAddEdgeOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Connect Nodes</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>From</Label>
              <Select value={newEdgeSource} onValueChange={setNewEdgeSource}>
                <SelectTrigger>
                  <SelectValue placeholder="Source node..." />
                </SelectTrigger>
                <SelectContent>
                  {flowNodes.map((n) => (
                    <SelectItem key={n.id} value={n.id}>
                      {n.alias || n.workBlockName}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>To</Label>
              <Select value={newEdgeTarget} onValueChange={setNewEdgeTarget}>
                <SelectTrigger>
                  <SelectValue placeholder="Target node..." />
                </SelectTrigger>
                <SelectContent>
                  {flowNodes
                    .filter((n) => n.id !== newEdgeSource)
                    .map((n) => (
                      <SelectItem key={n.id} value={n.id}>
                        {n.alias || n.workBlockName}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Condition (optional)</Label>
              <Input
                value={newEdgeCondition}
                onChange={(e) => setNewEdgeCondition(e.target.value)}
                placeholder="e.g. when approved"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddEdgeOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddEdge} disabled={!newEdgeSource || !newEdgeTarget}>
              Connect
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

/* ─── Node Inspector Panel ─── */

interface NodeInspectorProps {
  node: FlowNode;
  workBlocks: any[];
  onClose: () => void;
  onDelete: () => void;
  onNavigate: (workBlockId: string) => void;
}

function NodeInspectorPanel({ node, workBlocks, onClose, onDelete, onNavigate }: NodeInspectorProps) {
  const [wbResult] = useQuery({
    query: WORK_BLOCK_QUERY,
    variables: { id: node.workBlockId, version: node.workBlockVersion },
  });

  const wb = wbResult.data?.workBlock;
  const wbFromList = workBlocks.find((w: any) => w.id === node.workBlockId);

  return (
    <div className="w-80 border-l border-border bg-background flex flex-col animate-in slide-in-from-right-4 duration-200">
      {/* Header */}
      <div className="flex items-center gap-2 p-3 border-b border-border">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold truncate">{node.alias || wb?.name || wbFromList?.name || "Node"}</p>
          <p className="text-[11px] text-muted-foreground">Work Block · v{node.workBlockVersion}</p>
        </div>
        <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={onClose}>
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-3 space-y-4">
          {/* Description */}
          {wb?.description && (
            <div>
              <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Description</h4>
              <p className="text-xs text-foreground leading-relaxed">{wb.description}</p>
            </div>
          )}

          {/* Inputs */}
          {wb?.inputs && wb.inputs.length > 0 && (
            <div>
              <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                Inputs ({wb.inputs.length})
              </h4>
              <div className="space-y-1.5">
                {wb.inputs.map((port: any, i: number) => (
                  <div key={i} className="rounded-md border border-border p-2">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-medium">{port.name}</span>
                      {port.required && (
                        <Badge variant="destructive" className="text-[9px] h-4 px-1">req</Badge>
                      )}
                    </div>
                    {port.description && (
                      <p className="text-[11px] text-muted-foreground mt-0.5">{port.description}</p>
                    )}
                    {port.schemaDef && (
                      <pre className="text-[10px] text-muted-foreground bg-muted rounded px-1.5 py-0.5 mt-1 overflow-auto max-h-16">
                        {typeof port.schemaDef === "string" ? port.schemaDef : JSON.stringify(port.schemaDef, null, 1)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Outputs */}
          {wb?.outputs && wb.outputs.length > 0 && (
            <div>
              <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                Outputs ({wb.outputs.length})
              </h4>
              <div className="space-y-1.5">
                {wb.outputs.map((port: any, i: number) => (
                  <div key={i} className="rounded-md border border-border p-2">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-medium">{port.name}</span>
                      {port.required && (
                        <Badge variant="destructive" className="text-[9px] h-4 px-1">req</Badge>
                      )}
                    </div>
                    {port.description && (
                      <p className="text-[11px] text-muted-foreground mt-0.5">{port.description}</p>
                    )}
                    {port.schemaDef && (
                      <pre className="text-[10px] text-muted-foreground bg-muted rounded px-1.5 py-0.5 mt-1 overflow-auto max-h-16">
                        {typeof port.schemaDef === "string" ? port.schemaDef : JSON.stringify(port.schemaDef, null, 1)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Execution Hints */}
          {wb?.executionHints && (
            <div>
              <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Execution Hints</h4>
              <pre className="text-[10px] text-muted-foreground bg-muted rounded p-2 overflow-auto max-h-24">
                {typeof wb.executionHints === "string" ? wb.executionHints : JSON.stringify(wb.executionHints, null, 2)}
              </pre>
            </div>
          )}

          {/* Metadata */}
          {wb?.metadata && (
            <div>
              <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Metadata</h4>
              <pre className="text-[10px] text-muted-foreground bg-muted rounded p-2 overflow-auto max-h-24">
                {JSON.stringify(wb.metadata, null, 2)}
              </pre>
            </div>
          )}

          {/* Loading state */}
          {wbResult.fetching && !wb && (
            <div className="flex items-center justify-center py-8">
              <p className="text-xs text-muted-foreground">Loading work block data…</p>
            </div>
          )}

          {/* No data */}
          {!wbResult.fetching && !wb && (
            <div className="flex items-center justify-center py-8">
              <p className="text-xs text-muted-foreground">Work block not found</p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Footer actions */}
      <div className="p-3 border-t border-border flex gap-2">
        <Button
          variant="outline"
          size="sm"
          className="flex-1 text-xs h-8"
          onClick={() => onNavigate(node.workBlockId)}
        >
          <ExternalLink className="mr-1.5 h-3 w-3" />
          View Block
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="text-xs h-8 text-destructive hover:text-destructive"
          onClick={onDelete}
        >
          <Trash2 className="mr-1.5 h-3 w-3" />
          Remove
        </Button>
      </div>
    </div>
  );
}
