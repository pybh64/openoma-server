import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "urql";
import { ArrowLeft, Save, Undo2, Redo2, LayoutGrid } from "lucide-react";
import { v4 as uuid } from "uuid";
import { toast } from "sonner";
import ELK from "elkjs/lib/elk.bundled.js";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { FlowCanvas } from "@/components/canvas/FlowCanvas";
import { WorkBlockPalette } from "@/components/canvas/panels/WorkBlockPalette";
import { NodeInspector, EdgeInspector } from "@/components/canvas/panels/Inspectors";
import { useCanvasStore } from "@/stores/canvas";
import { FLOW_QUERY } from "@/graphql/queries/entities";
import { CREATE_FLOW, UPDATE_FLOW } from "@/graphql/mutations/entities";
import type { Node, Edge } from "@xyflow/react";

const elk = new ELK();

export default function FlowEditor() {
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id && id !== "new";
  const navigate = useNavigate();

  const [flowName, setFlowName] = useState("");
  const [flowDescription, setFlowDescription] = useState("");
  const [loaded, setLoaded] = useState(!isEdit);

  const store = useCanvasStore();

  const [queryResult] = useQuery({
    query: FLOW_QUERY,
    variables: { id },
    pause: !isEdit,
  });

  // Load existing flow into canvas
  useEffect(() => {
    if (isEdit && queryResult.data?.flow && !loaded) {
      const flow = queryResult.data.flow;
      setFlowName(flow.name);
      setFlowDescription(flow.description ?? "");

      const nodes: Node[] = (flow.nodes ?? []).map((n: any, i: number) => ({
        id: n.id,
        type: "workBlock",
        position: { x: i * 250, y: 100 },
        data: {
          label: n.alias || `Node ${i + 1}`,
          alias: n.alias ?? "",
          workBlockId: n.targetId,
          workBlockVersion: n.targetVersion,
          inputs: [],
          outputs: [],
        },
      }));

      const edges: Edge[] = (flow.edges ?? [])
        .filter((e: any) => e.sourceId)
        .map((e: any) => ({
          id: `e-${uuid()}`,
          source: e.sourceId,
          target: e.targetId,
          sourceHandle: e.portMappings?.[0]?.sourcePort ?? undefined,
          targetHandle: e.portMappings?.[0]?.targetPort ?? undefined,
          type: "conditional",
          data: {
            condition: e.condition ?? null,
            portMappings: e.portMappings ?? [],
          },
        }));

      store.setNodes(nodes);
      store.setEdges(edges);
      setLoaded(true);
    }
  }, [isEdit, queryResult.data, loaded, store]);

  // Reset canvas on unmount
  useEffect(() => {
    if (!isEdit) {
      store.reset();
    }
    return () => store.reset();
  }, []);

  const [, createMutation] = useMutation(CREATE_FLOW);
  const [, updateMutation] = useMutation(UPDATE_FLOW);

  const handleDragStart = useCallback((event: React.DragEvent, workBlock: any) => {
    event.dataTransfer.setData(
      "application/openoma-workblock",
      JSON.stringify(workBlock)
    );
    event.dataTransfer.effectAllowed = "move";
  }, []);

  const handleSave = useCallback(async () => {
    if (!flowName.trim()) {
      toast.error("Flow name is required");
      return;
    }

    const nodes = store.nodes.map((n) => ({
      id: n.id,
      targetId: (n.data as any).workBlockId,
      targetVersion: (n.data as any).workBlockVersion,
      alias: (n.data as any).alias || null,
    }));

    const edges = store.edges.map((e) => {
      const data = (e.data ?? {}) as any;
      return {
        sourceId: e.source,
        targetId: e.target,
        condition: data.condition?.description
          ? { description: data.condition.description }
          : null,
        portMappings:
          e.sourceHandle && e.targetHandle
            ? [{ sourcePort: e.sourceHandle, targetPort: e.targetHandle }]
            : data.portMappings ?? [],
      };
    });

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
  }, [
    flowName,
    flowDescription,
    store.nodes,
    store.edges,
    isEdit,
    id,
    createMutation,
    updateMutation,
    navigate,
  ]);

  const handleAutoLayout = useCallback(async () => {
    const graph = {
      id: "root",
      layoutOptions: {
        "elk.algorithm": "layered",
        "elk.direction": "RIGHT",
        "elk.spacing.nodeNode": "60",
        "elk.layered.spacing.nodeNodeBetweenLayers": "80",
      },
      children: store.nodes.map((n) => ({
        id: n.id,
        width: 200,
        height: 80 + Math.max((n.data as any).inputs?.length ?? 0, (n.data as any).outputs?.length ?? 0) * 20,
      })),
      edges: store.edges.map((e) => ({
        id: e.id,
        sources: [e.source],
        targets: [e.target],
      })),
    };

    try {
      const layout = await elk.layout(graph);
      store.pushSnapshot();
      store.setNodes(
        store.nodes.map((n) => {
          const layoutNode = layout.children?.find((c) => c.id === n.id);
          return layoutNode
            ? { ...n, position: { x: layoutNode.x ?? 0, y: layoutNode.y ?? 0 } }
            : n;
        })
      );
      toast.success("Layout applied");
    } catch {
      toast.error("Auto-layout failed");
    }
  }, [store]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "z" && !e.shiftKey) {
        e.preventDefault();
        store.undo();
      }
      if ((e.metaKey || e.ctrlKey) && (e.key === "y" || (e.key === "z" && e.shiftKey))) {
        e.preventDefault();
        store.redo();
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        handleSave();
      }
    },
    [store, handleSave]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  const showNodeInspector = store.selectedNodeId !== null;
  const showEdgeInspector = store.selectedEdgeId !== null;

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
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={store.undo}>
                <Undo2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Undo (⌘Z)</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={store.redo}>
                <Redo2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Redo (⌘⇧Z)</TooltipContent>
          </Tooltip>
          <Separator orientation="vertical" className="h-6" />
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleAutoLayout}>
                <LayoutGrid className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Auto Layout</TooltipContent>
          </Tooltip>
          <Separator orientation="vertical" className="h-6" />
          <Button size="sm" onClick={handleSave}>
            <Save className="mr-2 h-4 w-4" />
            Save
          </Button>
        </div>
      </div>

      {/* Canvas area */}
      <div className="flex flex-1 overflow-hidden">
        <WorkBlockPalette onDragStart={handleDragStart} />
        <div className="flex-1">
          <FlowCanvas />
        </div>
        {showNodeInspector && <NodeInspector />}
        {showEdgeInspector && <EdgeInspector />}
      </div>
    </div>
  );
}
