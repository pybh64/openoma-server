import { useEffect, useState } from "react";
import { ArrowRight, Link2, Plus, Trash2, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { formatJson } from "@/lib/utils";
import type { Edge, NodeReference } from "@/types";

interface EdgeDetailPanelProps {
  edge: Edge;
  allNodes: NodeReference[];
  onClose: () => void;
  onUpdateEdge?: (
    edge: Edge,
    input: {
      condition: {
        description: string;
        predicate: unknown | null;
        metadata: Record<string, unknown>;
      } | null;
      portMappings: { sourcePort: string; targetPort: string }[];
    }
  ) => Promise<void>;
  onRemoveEdge?: (edge: Edge) => Promise<void>;
}

export function EdgeDetailPanel({
  edge,
  allNodes,
  onClose,
  onUpdateEdge,
  onRemoveEdge,
}: EdgeDetailPanelProps) {
  const getNodeName = (nodeId: string | null) => {
    if (!nodeId) return "Entry";
    const node = allNodes.find((candidate) => candidate.id === nodeId);
    return node?.alias || node?.workBlock?.name || "Unknown Node";
  };

  const hasConditionMetadata = Boolean(
    edge.condition?.metadata && Object.keys(edge.condition.metadata).length > 0,
  );
  const [description, setDescription] = useState(edge.condition?.description ?? "");
  const [predicateText, setPredicateText] = useState(
    edge.condition?.predicate !== null && edge.condition?.predicate !== undefined
      ? formatJson(edge.condition.predicate)
      : "",
  );
  const [metadataText, setMetadataText] = useState(
    hasConditionMetadata ? formatJson(edge.condition?.metadata) : "",
  );
  const [portMappings, setPortMappings] = useState(edge.portMappings);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setDescription(edge.condition?.description ?? "");
    setPredicateText(
      edge.condition?.predicate !== null && edge.condition?.predicate !== undefined
        ? formatJson(edge.condition.predicate)
        : "",
    );
    setMetadataText(
      edge.condition?.metadata && Object.keys(edge.condition.metadata).length > 0
        ? formatJson(edge.condition.metadata)
        : "",
    );
    setPortMappings(edge.portMappings);
    setError(null);
  }, [edge]);

  const parseJsonField = (value: string, fieldName: string): unknown | null => {
    if (!value.trim()) {
      return null;
    }
    try {
      return JSON.parse(value);
    } catch {
      throw new Error(`${fieldName} must be valid JSON`);
    }
  };

  const addPortMapping = () => {
    setPortMappings([...portMappings, { sourcePort: "", targetPort: "" }]);
  };

  const updatePortMapping = (
    index: number,
    field: "sourcePort" | "targetPort",
    value: string,
  ) => {
    const updated = [...portMappings];
    updated[index] = { ...updated[index], [field]: value };
    setPortMappings(updated);
  };

  const removePortMapping = (index: number) => {
    setPortMappings(portMappings.filter((_, currentIndex) => currentIndex !== index));
  };

  const handleSave = async () => {
    if (!onUpdateEdge) return;
    setSaving(true);
    setError(null);
    try {
      const predicate = parseJsonField(predicateText, "Predicate");
      const metadata = parseJsonField(metadataText, "Condition metadata");
      const condition = description.trim()
        ? {
            description: description.trim(),
            predicate,
            metadata: (metadata as Record<string, unknown> | null) ?? {},
          }
        : null;
      await onUpdateEdge(edge, {
        condition,
        portMappings: portMappings.filter(
          (mapping) => mapping.sourcePort.trim() || mapping.targetPort.trim(),
        ),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save edge");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="w-80 border-l border-border bg-card flex flex-col h-full">
      <div className="p-3 border-b border-border flex items-center justify-between">
        <h3 className="text-sm font-semibold truncate flex items-center gap-2">
          <Link2 className="h-4 w-4 text-primary" />
          Connection
        </h3>
        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-3 space-y-4">
          <div className="rounded-lg border border-border bg-muted/30 p-3">
            <div className="flex items-center gap-2 text-sm">
              <span className="font-medium">{getNodeName(edge.sourceId)}</span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="font-medium">{getNodeName(edge.targetId)}</span>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              <Badge variant="outline" className="text-[10px]">
                {edge.sourceId ? "Node transition" : "Entry transition"}
              </Badge>
              <Badge variant="secondary" className="text-[10px]">
                {edge.portMappings.length} port mapping{edge.portMappings.length === 1 ? "" : "s"}
              </Badge>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold mb-2">Condition</h4>
            {onUpdateEdge ? (
              <div className="space-y-2">
                <div>
                  <Label className="text-xs">Condition description</Label>
                  <Input
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                    placeholder="Leave blank for unconditional routing"
                    className="mt-1 h-8 text-xs"
                  />
                </div>
                <div>
                  <Label className="text-xs">Predicate JSON</Label>
                  <Textarea
                    value={predicateText}
                    onChange={(event) => setPredicateText(event.target.value)}
                    placeholder='e.g. {"approved": true}'
                    rows={4}
                    className="mt-1 text-xs"
                  />
                </div>
                <div>
                  <Label className="text-xs">Condition metadata JSON</Label>
                  <Textarea
                    value={metadataText}
                    onChange={(event) => setMetadataText(event.target.value)}
                    placeholder='e.g. {"reviewer": "qa"}'
                    rows={3}
                    className="mt-1 text-xs"
                  />
                </div>
              </div>
            ) : edge.condition ? (
              <div className="space-y-2">
                <div className="rounded-md bg-muted/50 p-2 text-[11px]">
                  <div className="font-medium text-foreground">{edge.condition.description}</div>
                </div>
                {edge.condition.predicate !== null && (
                  <div>
                    <div className="text-[10px] text-muted-foreground mb-1">Predicate</div>
                    <pre className="overflow-x-auto rounded-md bg-muted p-2 text-[10px]">
                      {formatJson(edge.condition.predicate)}
                    </pre>
                  </div>
                )}
                {hasConditionMetadata && (
                  <div>
                    <div className="text-[10px] text-muted-foreground mb-1">Condition metadata</div>
                    <pre className="overflow-x-auto rounded-md bg-muted p-2 text-[10px]">
                      {formatJson(edge.condition?.metadata)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-[11px] text-muted-foreground">
                This link is unconditional and will route directly to the target.
              </p>
            )}
          </div>

          <Separator />

          <div>
            <h4 className="text-xs font-semibold mb-2">Port mappings</h4>
            {onUpdateEdge ? (
              <div className="space-y-2">
                {portMappings.map((mapping, index) => (
                  <div
                    key={`${mapping.sourcePort}-${mapping.targetPort}-${index}`}
                    className="rounded-md bg-muted/50 p-2"
                  >
                    <div className="flex items-center gap-2">
                      <Input
                        value={mapping.sourcePort}
                        onChange={(event) =>
                          updatePortMapping(index, "sourcePort", event.target.value)
                        }
                        placeholder="Source port"
                        className="h-8 text-xs"
                      />
                      <ArrowRight className="h-3 w-3 text-muted-foreground" />
                      <Input
                        value={mapping.targetPort}
                        onChange={(event) =>
                          updatePortMapping(index, "targetPort", event.target.value)
                        }
                        placeholder="Target port"
                        className="h-8 text-xs"
                      />
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 shrink-0"
                        onClick={() => removePortMapping(index)}
                      >
                        <Trash2 className="h-3.5 w-3.5 text-muted-foreground" />
                      </Button>
                    </div>
                  </div>
                ))}
                <Button variant="outline" size="sm" className="w-full text-xs" onClick={addPortMapping}>
                  <Plus className="h-3.5 w-3.5 mr-1" /> Add Port Mapping
                </Button>
              </div>
            ) : edge.portMappings.length > 0 ? (
              <div className="space-y-2">
                {edge.portMappings.map((mapping, index) => (
                  <div
                    key={`${mapping.sourcePort}-${mapping.targetPort}-${index}`}
                    className="rounded-md bg-muted/50 p-2 text-[11px]"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{mapping.sourcePort}</span>
                      <ArrowRight className="h-3 w-3 text-muted-foreground" />
                      <span className="font-medium">{mapping.targetPort}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[11px] text-muted-foreground">
                No explicit port mappings are defined on this link.
              </p>
            )}
          </div>

          {error && <p className="text-[11px] text-destructive">{error}</p>}

          {(onUpdateEdge || onRemoveEdge) && <Separator />}

          {(onUpdateEdge || onRemoveEdge) && (
            <div className="space-y-2">
              {onUpdateEdge && (
                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full text-xs"
                  disabled={saving}
                  onClick={handleSave}
                >
                  {saving ? "Saving..." : "Save Connection Settings"}
                </Button>
              )}
              {onRemoveEdge && (
                <Button
                  variant="destructive"
                  size="sm"
                  className="w-full text-xs"
                  onClick={() => onRemoveEdge(edge)}
                >
                  Remove Connection
                </Button>
              )}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
