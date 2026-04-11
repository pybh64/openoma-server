import { useEffect, useState, useCallback } from "react";
import { X, Blocks, ArrowRight, Clock3, ChevronDown, ChevronRight, Target } from "lucide-react";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { NodeReference, Edge, PortDescriptor, ExpectedOutcome } from "@/types";

interface NodeDetailPanelProps {
  node: NodeReference;
  edges: Edge[];
  allNodes: NodeReference[];
  onClose: () => void;
  onRemoveNode?: (nodeRefId: string) => Promise<void> | void;
  onReplaceWorkBlock?: (nodeRefId: string) => void;
  onEditWorkBlockVersion?: (node: NodeReference) => void;
  onUpdateNode?: (
    nodeRefId: string,
    input: {
      alias?: string | null;
      executionSchedule?: string | null;
      targetId?: string;
      targetVersion?: number;
    }
  ) => Promise<void>;
}

function SchemaView({ schema }: { schema: unknown }) {
  const [open, setOpen] = useState(false);
  const text = JSON.stringify(schema, null, 2);
  return (
    <div className="mt-1">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
      >
        {open ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        Schema
      </button>
      {open && (
        <pre className="mt-1 text-[10px] font-mono bg-muted/70 rounded p-2 overflow-auto max-h-40 whitespace-pre-wrap break-all">
          {text}
        </pre>
      )}
    </div>
  );
}

function PortList({ ports, label }: { ports: PortDescriptor[]; label: string }) {
  if (ports.length === 0) return null;
  return (
    <div>
      <h4 className="text-xs font-semibold mb-2">
        {label} ({ports.length})
      </h4>
      <div className="space-y-2">
        {ports.map((p, i) => (
          <div key={i} className="text-[11px] p-2 rounded bg-muted/50">
            <div className="flex items-center gap-1">
              <span className="font-medium">{p.name}</span>
              {p.required && (
                <span className="text-destructive text-[10px] font-semibold">required</span>
              )}
            </div>
            {p.description && (
              <div className="text-muted-foreground mt-0.5">{p.description}</div>
            )}
            {p.schema != null && <SchemaView schema={p.schema} />}
          </div>
        ))}
      </div>
    </div>
  );
}

function ExpectedOutcomeSection({ outcome }: { outcome: ExpectedOutcome }) {
  return (
    <div className="rounded-md bg-muted/50 p-2.5 text-[11px]">
      <div className="mb-1 flex items-center gap-1.5 font-semibold">
        <Target className="h-3.5 w-3.5 text-primary" />
        Expected Outcome: {outcome.name}
      </div>
      {outcome.description && (
        <div className="text-muted-foreground">{outcome.description}</div>
      )}
      {outcome.schema != null && <SchemaView schema={outcome.schema} />}
    </div>
  );
}

export function NodeDetailPanel({
  node,
  edges,
  allNodes,
  onClose,
  onRemoveNode,
  onReplaceWorkBlock,
  onEditWorkBlockVersion,
  onUpdateNode,
}: NodeDetailPanelProps) {
  const wb = node.workBlock;
  const incomingEdges = edges.filter((e) => e.targetId === node.id);
  const outgoingEdges = edges.filter((e) => e.sourceId === node.id);
  const [alias, setAlias] = useState(node.alias || "");
  const [executionSchedule, setExecutionSchedule] = useState(node.executionSchedule || "");
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setAlias(node.alias || "");
    setExecutionSchedule(node.executionSchedule || "");
    setError(null);
  }, [node.id, node.alias, node.executionSchedule]);

  const getNodeName = useCallback(
    (refId: string) => {
      const n = allNodes.find((n) => n.id === refId);
      return n?.alias || n?.workBlock?.name || "Entry";
    },
    [allNodes],
  );

  return (
    <div className="w-80 border-l border-border bg-card flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-border flex items-center justify-between shrink-0">
        <h3 className="text-sm font-semibold truncate flex items-center gap-2">
          <Blocks className="h-4 w-4 text-primary shrink-0" />
          {node.alias || wb?.name || "Unknown Block"}
        </h3>
        <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={onClose}>
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-3 space-y-4">

          {/* Basic Info */}
          <div>
            {node.alias && wb?.name && (
              <div className="text-xs text-muted-foreground mb-1">
                Work Block: <span className="font-medium text-foreground">{wb.name}</span>
              </div>
            )}
            <p className="text-xs text-muted-foreground leading-relaxed">
              {wb?.description || "No description"}
            </p>
            <div className="flex flex-wrap gap-1.5 mt-2">
              <Badge variant="outline" className="text-[10px]">v{node.targetVersion}</Badge>
              {wb?.executionHints?.map((h: string) => (
                <Badge key={h} variant="secondary" className="text-[10px]">{h}</Badge>
              ))}
            </div>
          </div>

          {/* Expected Outcome */}
          {wb?.expectedOutcome && (
            <>
              <Separator />
              <ExpectedOutcomeSection outcome={wb.expectedOutcome} />
            </>
          )}

          {/* Execution Schedule */}
          {node.executionSchedule && (
            <div className="rounded-md bg-muted/50 p-2 text-[11px]">
              <div className="mb-1 flex items-center gap-1 font-medium">
                <Clock3 className="h-3 w-3" /> Execution Schedule
              </div>
              <div className="text-muted-foreground font-mono">{node.executionSchedule}</div>
            </div>
          )}

          <Separator />

          {/* Node Settings (editable) */}
          {onUpdateNode && (
            <>
              <div className="space-y-3">
                <h4 className="text-xs font-semibold">Node Settings</h4>
                <div>
                  <Label className="text-xs">Alias</Label>
                  <Input
                    value={alias}
                    onChange={(e) => setAlias(e.target.value)}
                    placeholder="Optional node alias"
                    className="mt-1 h-8 text-xs"
                  />
                </div>
                <div>
                  <Label className="text-xs">Execution Schedule</Label>
                  <Input
                    value={executionSchedule}
                    onChange={(e) => setExecutionSchedule(e.target.value)}
                    placeholder='e.g. cron: 0 9 * * 1-5'
                    className="mt-1 h-8 text-xs"
                  />
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full text-xs"
                  disabled={saving}
                  onClick={async () => {
                    setSaving(true);
                    setError(null);
                    try {
                      await onUpdateNode(node.id, {
                        alias: alias.trim() || null,
                        executionSchedule: executionSchedule.trim() || null,
                      });
                    } catch (err) {
                      setError(err instanceof Error ? err.message : "Unable to save node settings");
                    } finally {
                      setSaving(false);
                    }
                  }}
                >
                  {saving ? "Saving…" : "Save Node Settings"}
                </Button>
              </div>
              {error && <p className="text-[11px] text-destructive">{error}</p>}
              <Separator />
            </>
          )}

          {/* Inputs */}
          {wb?.inputs && wb.inputs.length > 0 && (
            <PortList ports={wb.inputs as PortDescriptor[]} label="Inputs" />
          )}

          {/* Outputs */}
          {wb?.outputs && wb.outputs.length > 0 && (
            <PortList ports={wb.outputs as PortDescriptor[]} label="Outputs" />
          )}

          {((wb?.inputs?.length ?? 0) > 0 || (wb?.outputs?.length ?? 0) > 0) && <Separator />}

          {/* Connections */}
          <div>
            <h4 className="text-xs font-semibold mb-2">Connections</h4>
            {incomingEdges.length > 0 && (
              <div className="mb-2">
                <div className="text-[10px] text-muted-foreground mb-1 uppercase tracking-wide">
                  Incoming ({incomingEdges.length})
                </div>
                {incomingEdges.map((e, i) => (
                  <div key={i} className="text-[11px] flex items-center gap-1 py-0.5">
                    <span className="font-medium truncate max-w-[90px]">
                      {e.sourceId ? getNodeName(e.sourceId) : "Entry"}
                    </span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
                    <span>this</span>
                    {e.condition && (
                      <span className="text-muted-foreground ml-1 truncate">
                        ({e.condition.description})
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
            {outgoingEdges.length > 0 && (
              <div>
                <div className="text-[10px] text-muted-foreground mb-1 uppercase tracking-wide">
                  Outgoing ({outgoingEdges.length})
                </div>
                {outgoingEdges.map((e, i) => (
                  <div key={i} className="text-[11px] flex items-center gap-1 py-0.5">
                    <span>this</span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
                    <span className="font-medium truncate max-w-[90px]">
                      {getNodeName(e.targetId)}
                    </span>
                    {e.condition && (
                      <span className="text-muted-foreground ml-1 truncate">
                        ({e.condition.description})
                      </span>
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
            {onReplaceWorkBlock && (
              <Button
                variant="secondary"
                size="sm"
                className="w-full text-xs"
                onClick={() => onReplaceWorkBlock(node.id)}
              >
                Replace Work Block
              </Button>
            )}
            {onEditWorkBlockVersion && wb && (
              <Button
                variant="secondary"
                size="sm"
                className="w-full text-xs"
                onClick={() => onEditWorkBlockVersion(node)}
              >
                Edit as New Work Block Version
              </Button>
            )}
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
                disabled={removing}
                onClick={async () => {
                  setRemoving(true);
                  setError(null);
                  try {
                    await onRemoveNode(node.id);
                  } catch (err) {
                    setError(err instanceof Error ? err.message : "Unable to remove node");
                  } finally {
                    setRemoving(false);
                  }
                }}
              >
                {removing ? "Removing…" : "Remove from Flow"}
              </Button>
            )}
            {error && <p className="text-[11px] text-destructive">{error}</p>}
          </div>

        </div>
      </ScrollArea>
    </div>
  );
}


