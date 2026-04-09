import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useCanvasStore } from "@/stores/canvas";

export function NodeInspector() {
  const selectedNodeId = useCanvasStore((s) => s.selectedNodeId);
  const nodes = useCanvasStore((s) => s.nodes);
  const setNodes = useCanvasStore((s) => s.setNodes);
  const pushSnapshot = useCanvasStore((s) => s.pushSnapshot);

  const node = nodes.find((n) => n.id === selectedNodeId);

  if (!node) return null;

  const data = node.data as any;

  const updateAlias = (alias: string) => {
    pushSnapshot();
    setNodes(
      nodes.map((n) =>
        n.id === selectedNodeId
          ? { ...n, data: { ...n.data, alias } }
          : n
      )
    );
  };

  return (
    <div className="w-72 border-l border-border bg-background overflow-auto">
      <div className="p-3 border-b border-border">
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Node Inspector
        </h3>
      </div>
      <div className="p-3 space-y-4">
        <div>
          <Label className="text-xs">Alias</Label>
          <Input
            value={data.alias ?? ""}
            onChange={(e) => updateAlias(e.target.value)}
            placeholder={data.label}
            className="h-8 text-sm"
          />
        </div>

        <div>
          <Label className="text-xs">Work Block</Label>
          <p className="text-sm font-medium">{data.label}</p>
          <p className="text-xs text-muted-foreground font-mono">{data.workBlockId?.slice(0, 16)}…</p>
        </div>

        <Separator />

        <div>
          <Label className="text-xs">Input Ports</Label>
          <div className="mt-1 space-y-1">
            {data.inputs?.map((p: any) => (
              <div key={p.name} className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-blue-500" />
                <span className="text-xs font-mono">{p.name}</span>
                {p.required && (
                  <Badge variant="secondary" className="text-[8px] h-3 px-1">req</Badge>
                )}
              </div>
            ))}
          </div>
        </div>

        <div>
          <Label className="text-xs">Output Ports</Label>
          <div className="mt-1 space-y-1">
            {data.outputs?.map((p: any) => (
              <div key={p.name} className="flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-xs font-mono">{p.name}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <Label className="text-xs">Node ID</Label>
          <p className="text-[10px] text-muted-foreground font-mono break-all">{node.id}</p>
        </div>
      </div>
    </div>
  );
}

export function EdgeInspector() {
  const selectedEdgeId = useCanvasStore((s) => s.selectedEdgeId);
  const edges = useCanvasStore((s) => s.edges);
  const setEdges = useCanvasStore((s) => s.setEdges);
  const pushSnapshot = useCanvasStore((s) => s.pushSnapshot);

  const edge = edges.find((e) => e.id === selectedEdgeId);

  if (!edge) return null;

  const data = (edge.data ?? {}) as any;

  const updateConditionDescription = (desc: string) => {
    pushSnapshot();
    setEdges(
      edges.map((e) =>
        e.id === selectedEdgeId
          ? {
              ...e,
              data: {
                ...e.data,
                condition: { ...(data.condition ?? {}), description: desc },
              },
            }
          : e
      )
    );
  };

  return (
    <div className="w-72 border-l border-border bg-background overflow-auto">
      <div className="p-3 border-b border-border">
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Edge Inspector
        </h3>
      </div>
      <div className="p-3 space-y-4">
        <div>
          <Label className="text-xs">Source</Label>
          <p className="text-xs font-mono">{edge.source}</p>
          {edge.sourceHandle && (
            <p className="text-[10px] text-muted-foreground">port: {edge.sourceHandle}</p>
          )}
        </div>
        <div>
          <Label className="text-xs">Target</Label>
          <p className="text-xs font-mono">{edge.target}</p>
          {edge.targetHandle && (
            <p className="text-[10px] text-muted-foreground">port: {edge.targetHandle}</p>
          )}
        </div>

        <Separator />

        <div>
          <Label className="text-xs">Condition (optional)</Label>
          <Input
            value={data.condition?.description ?? ""}
            onChange={(e) => updateConditionDescription(e.target.value)}
            placeholder="e.g. when status == approved"
            className="h-8 text-sm"
          />
        </div>

        <div>
          <Label className="text-xs">Edge ID</Label>
          <p className="text-[10px] text-muted-foreground font-mono break-all">{edge.id}</p>
        </div>
      </div>
    </div>
  );
}
