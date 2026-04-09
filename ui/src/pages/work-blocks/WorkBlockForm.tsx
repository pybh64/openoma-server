import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery } from "urql";
import { ArrowLeft, Plus, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { WORK_BLOCK_QUERY } from "@/graphql/queries/entities";
import { CREATE_WORK_BLOCK, UPDATE_WORK_BLOCK } from "@/graphql/mutations/entities";

interface PortForm {
  name: string;
  description: string;
  required: boolean;
  schemaDef: string;
}

const emptyPort = (): PortForm => ({
  name: "",
  description: "",
  required: true,
  schemaDef: "",
});

export default function WorkBlockForm() {
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [inputs, setInputs] = useState<PortForm[]>([]);
  const [outputs, setOutputs] = useState<PortForm[]>([]);
  const [hints, setHints] = useState("");
  const [loaded, setLoaded] = useState(!isEdit);

  const [_queryResult] = useQuery({
    query: WORK_BLOCK_QUERY,
    variables: { id },
    pause: !isEdit,
  });

  // Populate form on load for edit mode
  if (isEdit && _queryResult.data?.workBlock && !loaded) {
    const wb = _queryResult.data.workBlock;
    setName(wb.name);
    setDescription(wb.description ?? "");
    setInputs(
      (wb.inputs ?? []).map((p: any) => ({
        name: p.name,
        description: p.description ?? "",
        required: p.required ?? true,
        schemaDef: p.schemaDef ? JSON.stringify(p.schemaDef) : "",
      }))
    );
    setOutputs(
      (wb.outputs ?? []).map((p: any) => ({
        name: p.name,
        description: p.description ?? "",
        required: p.required ?? true,
        schemaDef: p.schemaDef ? JSON.stringify(p.schemaDef) : "",
      }))
    );
    setHints((wb.executionHints ?? []).join(", "));
    setLoaded(true);
  }

  const [, createMutation] = useMutation(CREATE_WORK_BLOCK);
  const [, updateMutation] = useMutation(UPDATE_WORK_BLOCK);

  const buildPorts = (ports: PortForm[]) =>
    ports
      .filter((p) => p.name.trim())
      .map((p) => ({
        name: p.name.trim(),
        description: p.description,
        required: p.required,
        schemaDef: p.schemaDef ? JSON.parse(p.schemaDef) : null,
      }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const input: any = {
      name: name.trim(),
      description,
      inputs: buildPorts(inputs),
      outputs: buildPorts(outputs),
      executionHints: hints
        .split(",")
        .map((h) => h.trim())
        .filter(Boolean),
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
      toast.success(isEdit ? "Work block updated" : "Work block created");
      const newId = isEdit
        ? id
        : result.data?.createWorkBlock?.id;
      navigate(newId ? `/work-blocks/${newId}` : "/work-blocks");
    }
  };

  const updatePort = (
    list: PortForm[],
    setList: (p: PortForm[]) => void,
    index: number,
    field: keyof PortForm,
    value: string | boolean
  ) => {
    const updated = [...list];
    (updated[index] as any)[field] = value;
    setList(updated);
  };

  const renderPortSection = (
    title: string,
    ports: PortForm[],
    setPorts: (p: PortForm[]) => void
  ) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm">{title}</CardTitle>
        <Button type="button" variant="outline" size="sm" onClick={() => setPorts([...ports, emptyPort()])}>
          <Plus className="mr-1 h-3 w-3" />
          Add
        </Button>
      </CardHeader>
      <CardContent>
        {ports.length === 0 ? (
          <p className="text-sm text-muted-foreground">No ports defined</p>
        ) : (
          <div className="space-y-4">
            {ports.map((port, i) => (
              <div key={i} className="rounded-md border p-3 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Port {i + 1}</span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => setPorts(ports.filter((_, j) => j !== i))}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <Label className="text-xs">Name</Label>
                    <Input
                      value={port.name}
                      onChange={(e) => updatePort(ports, setPorts, i, "name", e.target.value)}
                      placeholder="port_name"
                      className="h-8 font-mono text-sm"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Description</Label>
                    <Input
                      value={port.description}
                      onChange={(e) => updatePort(ports, setPorts, i, "description", e.target.value)}
                      placeholder="What this port does"
                      className="h-8 text-sm"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    checked={port.required}
                    onCheckedChange={(v) => updatePort(ports, setPorts, i, "required", v)}
                  />
                  <Label className="text-xs">Required</Label>
                </div>
                <div>
                  <Label className="text-xs">JSON Schema (optional)</Label>
                  <Input
                    value={port.schemaDef}
                    onChange={(e) => updatePort(ports, setPorts, i, "schemaDef", e.target.value)}
                    placeholder='{"type": "string"}'
                    className="h-8 font-mono text-xs"
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">
          {isEdit ? "Edit Work Block" : "New Work Block"}
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardContent className="pt-6 space-y-4">
            <div>
              <Label>Name</Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Work Block"
                required
              />
            </div>
            <div>
              <Label>Description</Label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What this work block does"
              />
            </div>
            <div>
              <Label>Execution Hints (comma-separated)</Label>
              <Input
                value={hints}
                onChange={(e) => setHints(e.target.value)}
                placeholder="parallel, idempotent, retry-safe"
              />
            </div>
          </CardContent>
        </Card>

        {renderPortSection("Input Ports", inputs, setInputs)}
        {renderPortSection("Output Ports", outputs, setOutputs)}

        <Separator />

        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => navigate(-1)}>
            Cancel
          </Button>
          <Button type="submit">{isEdit ? "Update" : "Create"}</Button>
        </div>
      </form>
    </div>
  );
}
