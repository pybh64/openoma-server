import { useEffect, useState } from "react";
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
import { formatJson } from "@/lib/utils";
import type {
  ContractReference,
  FlowReference,
  Party,
  RequiredOutcomeReference,
} from "@/types";

interface ContractFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  submitLabel?: string;
  initialValue?: {
    name: string;
    description: string;
    owners: Party[];
    workFlows: FlowReference[];
    subContracts: ContractReference[];
    requiredOutcomes: RequiredOutcomeReference[];
    metadata: Record<string, unknown>;
  };
  onSubmit: (input: {
    name: string;
    description: string;
    owners: Party[];
    workFlows: FlowReference[];
    subContracts: ContractReference[];
    requiredOutcomes: RequiredOutcomeReference[];
    metadata: Record<string, unknown>;
  }) => Promise<void>;
}

export function ContractFormDialog({
  open,
  onOpenChange,
  title = "Create Contract",
  submitLabel = "Create Contract",
  initialValue,
  onSubmit,
}: ContractFormDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [ownersJson, setOwnersJson] = useState("[]");
  const [flowsJson, setFlowsJson] = useState("[]");
  const [subContractsJson, setSubContractsJson] = useState("[]");
  const [outcomesJson, setOutcomesJson] = useState("[]");
  const [metadataJson, setMetadataJson] = useState("{}");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    setName(initialValue?.name ?? "");
    setDescription(initialValue?.description ?? "");
    setOwnersJson(formatJson(initialValue?.owners ?? []));
    setFlowsJson(formatJson(initialValue?.workFlows ?? []));
    setSubContractsJson(formatJson(initialValue?.subContracts ?? []));
    setOutcomesJson(formatJson(initialValue?.requiredOutcomes ?? []));
    setMetadataJson(formatJson(initialValue?.metadata ?? {}));
  }, [initialValue, open]);

  const parseJson = <T,>(label: string, value: string): T => {
    try {
      return JSON.parse(value) as T;
    } catch {
      throw new Error(`${label} must be valid JSON`);
    }
  };

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      await onSubmit({
        name: name.trim(),
        description: description.trim(),
        owners: parseJson<Party[]>("Owners", ownersJson),
        workFlows: parseJson<FlowReference[]>("Work flows", flowsJson),
        subContracts: parseJson<ContractReference[]>("Sub-contracts", subContractsJson),
        requiredOutcomes: parseJson<RequiredOutcomeReference[]>(
          "Required outcomes",
          outcomesJson
        ),
        metadata: parseJson<Record<string, unknown>>("Metadata", metadataJson),
      });
      onOpenChange(false);
    } catch (error) {
      window.alert(error instanceof Error ? error.message : "Unable to save contract");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] max-w-3xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Name *</Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Q3 Product Launch"
              />
            </div>
            <div>
              <Label>Description</Label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What this contract coordinates"
              />
            </div>
          </div>

          <JsonField
            label="Owners"
            value={ownersJson}
            onChange={setOwnersJson}
            placeholder='[{"name":"Alice","role":"lead","contact":"alice@example.com"}]'
          />
          <JsonField
            label="Work Flows"
            value={flowsJson}
            onChange={setFlowsJson}
            placeholder='[{"flowId":"...","flowVersion":1,"alias":"main"}]'
          />
          <JsonField
            label="Sub-contracts"
            value={subContractsJson}
            onChange={setSubContractsJson}
            placeholder='[{"contractId":"...","contractVersion":1,"alias":"infra"}]'
          />
          <JsonField
            label="Required Outcomes"
            value={outcomesJson}
            onChange={setOutcomesJson}
            placeholder='[{"requiredOutcomeId":"...","requiredOutcomeVersion":1,"alias":"shipped"}]'
          />
          <JsonField
            label="Metadata"
            value={metadataJson}
            onChange={setMetadataJson}
            placeholder='{"priority":"high"}'
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!name.trim() || submitting}>
            {submitting ? "Saving..." : submitLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function JsonField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <div>
      <Label>{label}</Label>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={4}
        className="mt-1 font-mono text-xs"
      />
    </div>
  );
}
