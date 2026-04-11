import { useCallback, useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Trash2 } from "lucide-react";

interface PortInput {
  name: string;
  description: string;
  required: boolean;
}

interface WorkBlockFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  submitLabel?: string;
  initialValue?: {
    name: string;
    description: string;
    inputs: PortInput[];
    outputs: PortInput[];
    executionHints: string[];
  };
  onSubmit: (input: {
    name: string;
    description: string;
    inputs: PortInput[];
    outputs: PortInput[];
    executionHints: string[];
  }) => Promise<void>;
}

export function WorkBlockFormDialog({
  open,
  onOpenChange,
  title = "Create Work Block",
  submitLabel = "Create",
  initialValue,
  onSubmit,
}: WorkBlockFormDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [inputs, setInputs] = useState<PortInput[]>([]);
  const [outputs, setOutputs] = useState<PortInput[]>([]);
  const [hints, setHints] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const applyInitialValue = useCallback(() => {
    setName(initialValue?.name ?? "");
    setDescription(initialValue?.description ?? "");
    setInputs(initialValue?.inputs ?? []);
    setOutputs(initialValue?.outputs ?? []);
    setHints(initialValue?.executionHints?.join(", ") ?? "");
  }, [initialValue]);

  const reset = () => {
    applyInitialValue();
  };

  useEffect(() => {
    if (open) {
      applyInitialValue();
      setError(null);
    }
  }, [applyInitialValue, open]);

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({
        name: name.trim(),
        description: description.trim(),
        inputs: inputs.filter((p) => p.name.trim()),
        outputs: outputs.filter((p) => p.name.trim()),
        executionHints: hints
          .split(",")
          .map((h) => h.trim())
          .filter(Boolean),
      });
      reset();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save work block");
    } finally {
      setSubmitting(false);
    }
  };

  const addPort = (type: "input" | "output") => {
    const port: PortInput = { name: "", description: "", required: false };
    if (type === "input") setInputs([...inputs, port]);
    else setOutputs([...outputs, port]);
  };

  const removePort = (type: "input" | "output", idx: number) => {
    if (type === "input") setInputs(inputs.filter((_, i) => i !== idx));
    else setOutputs(outputs.filter((_, i) => i !== idx));
  };

  const updatePort = (type: "input" | "output", idx: number, field: keyof PortInput, value: string | boolean) => {
    const setter = type === "input" ? setInputs : setOutputs;
    const arr = type === "input" ? inputs : outputs;
    const updated = [...arr];
    updated[idx] = { ...updated[idx], [field]: value };
    setter(updated);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label>Name *</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g., Data Validation" />
          </div>
          <div>
            <Label>Description</Label>
            <Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What does this block do?" rows={3} />
          </div>
          <div>
            <Label>Execution Hints (comma-separated)</Label>
            <Input value={hints} onChange={(e) => setHints(e.target.value)} placeholder="e.g., human, agent, system" />
          </div>

          {/* Inputs */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label>Inputs</Label>
              <Button variant="ghost" size="sm" onClick={() => addPort("input")} className="text-xs h-7">
                <Plus className="h-3 w-3 mr-1" /> Add Input
              </Button>
            </div>
            {inputs.map((port, i) => (
              <PortRow key={i} port={port} onChange={(f, v) => updatePort("input", i, f, v)} onRemove={() => removePort("input", i)} />
            ))}
          </div>

          {/* Outputs */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label>Outputs</Label>
              <Button variant="ghost" size="sm" onClick={() => addPort("output")} className="text-xs h-7">
                <Plus className="h-3 w-3 mr-1" /> Add Output
              </Button>
            </div>
            {outputs.map((port, i) => (
              <PortRow key={i} port={port} onChange={(f, v) => updatePort("output", i, f, v)} onRemove={() => removePort("output", i)} />
            ))}
          </div>
        </div>

        <DialogFooter>
          {error && <p className="w-full text-xs text-destructive">{error}</p>}
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={!name.trim() || submitting}>
            {submitting ? "Saving..." : submitLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function PortRow({
  port,
  onChange,
  onRemove,
}: {
  port: PortInput;
  onChange: (field: keyof PortInput, value: string | boolean) => void;
  onRemove: () => void;
}) {
  return (
    <div className="flex items-center gap-2 mb-2">
      <Input
        value={port.name}
        onChange={(e) => onChange("name", e.target.value)}
        placeholder="Port name"
        className="flex-1 h-8 text-xs"
      />
      <Input
        value={port.description}
        onChange={(e) => onChange("description", e.target.value)}
        placeholder="Description"
        className="flex-1 h-8 text-xs"
      />
      <label className="flex items-center gap-1 text-xs cursor-pointer whitespace-nowrap">
        <input
          type="checkbox"
          checked={port.required}
          onChange={(e) => onChange("required", e.target.checked)}
          className="rounded"
        />
        Req
      </label>
      <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={onRemove}>
        <Trash2 className="h-3 w-3 text-muted-foreground" />
      </Button>
    </div>
  );
}
