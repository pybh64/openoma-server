import { X, Blocks, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { NodeReference, Edge } from "@/types";

interface NodeDetailPanelProps {
  node: NodeReference;
  edges: Edge[];
  allNodes: NodeReference[];
  onClose: () => void;
  onRemoveNode?: (nodeRefId: string) => void;
}

export function NodeDetailPanel({ node, edges, allNodes, onClose, onRemoveNode }: NodeDetailPanelProps) {
  const wb = node.workBlock;
  const incomingEdges = edges.filter((e) => e.targetId === node.id);
  const outgoingEdges = edges.filter((e) => e.sourceId === node.id);

  const getNodeName = (refId: string) => {
    const n = allNodes.find((n) => n.id === refId);
    return n?.alias || n?.workBlock?.name || "Entry";
  };

  return (
    <div className="w-80 border-l border-border bg-card flex flex-col h-full">
      <div className="p-3 border-b border-border flex items-center justify-between">
        <h3 className="text-sm font-semibold truncate flex items-center gap-2">
          <Blocks className="h-4 w-4 text-primary" />
          {node.alias || wb?.name || "Unknown Block"}
        </h3>
        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-3 space-y-4">
          {/* Basic Info */}
          <div>
            {node.alias && wb?.name && (
              <div className="text-xs text-muted-foreground mb-1">Work Block: {wb.name}</div>
            )}
            <p className="text-xs text-muted-foreground">{wb?.description || "No description"}</p>
            <div className="flex gap-2 mt-2">
              <Badge variant="outline" className="text-[10px]">v{node.targetVersion}</Badge>
              {wb?.executionHints?.map((h: string) => (
                <Badge key={h} variant="secondary" className="text-[10px]">{h}</Badge>
              ))}
            </div>
          </div>

          <Separator />

          {/* Inputs */}
          {wb?.inputs && wb.inputs.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold mb-2">Inputs ({wb.inputs.length})</h4>
              <div className="space-y-1.5">
                {wb.inputs.map((p: { name: string; description: string; required: boolean }, i: number) => (
                  <div key={i} className="text-[11px] p-1.5 rounded bg-muted/50">
                    <span className="font-medium">{p.name}</span>
                    {p.required && <span className="text-destructive ml-1">*</span>}
                    {p.description && <div className="text-muted-foreground">{p.description}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Outputs */}
          {wb?.outputs && wb.outputs.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold mb-2">Outputs ({wb.outputs.length})</h4>
              <div className="space-y-1.5">
                {wb.outputs.map((p: { name: string; description: string; required: boolean }, i: number) => (
                  <div key={i} className="text-[11px] p-1.5 rounded bg-muted/50">
                    <span className="font-medium">{p.name}</span>
                    {p.description && <div className="text-muted-foreground">{p.description}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}

          <Separator />

          {/* Connections */}
          <div>
            <h4 className="text-xs font-semibold mb-2">Connections</h4>
            {incomingEdges.length > 0 && (
              <div className="mb-2">
                <div className="text-[10px] text-muted-foreground mb-1">Incoming ({incomingEdges.length})</div>
                {incomingEdges.map((e, i) => (
                  <div key={i} className="text-[11px] flex items-center gap-1 py-0.5">
                    <span className="font-medium">{e.sourceId ? getNodeName(e.sourceId) : "Entry"}</span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                    <span>this</span>
                    {e.condition && (
                      <span className="text-muted-foreground ml-1">({e.condition.description})</span>
                    )}
                  </div>
                ))}
              </div>
            )}
            {outgoingEdges.length > 0 && (
              <div>
                <div className="text-[10px] text-muted-foreground mb-1">Outgoing ({outgoingEdges.length})</div>
                {outgoingEdges.map((e, i) => (
                  <div key={i} className="text-[11px] flex items-center gap-1 py-0.5">
                    <span>this</span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                    <span className="font-medium">{getNodeName(e.targetId)}</span>
                    {e.condition && (
                      <span className="text-muted-foreground ml-1">({e.condition.description})</span>
                    )}
                  </div>
                ))}
              </div>
            )}
            {incomingEdges.length === 0 && outgoingEdges.length === 0 && (
              <p className="text-[11px] text-muted-foreground">No connections</p>
            )}
          </div>

          <Separator />

          {/* Actions */}
          <div className="space-y-2">
            <Link to={`/work-blocks/${node.targetId}`}>
              <Button variant="outline" size="sm" className="w-full text-xs">
                View Work Block Details
              </Button>
            </Link>
            {onRemoveNode && (
              <Button
                variant="destructive"
                size="sm"
                className="w-full text-xs"
                onClick={() => onRemoveNode(node.id)}
              >
                Remove from Flow
              </Button>
            )}
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
