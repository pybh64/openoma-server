import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery } from "urql";
import { ArrowLeft, Plus, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { CONTRACT_QUERY } from "@/graphql/queries/entities";
import { CREATE_CONTRACT, UPDATE_CONTRACT } from "@/graphql/mutations/entities";

interface FlowRef {
  flowId: string;
  flowVersion: string;
  alias: string;
}

interface OutcomeForm {
  name: string;
  description: string;
}

export default function ContractForm() {
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id && id !== "new";
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [workflows, setWorkflows] = useState<FlowRef[]>([]);
  const [outcomes, setOutcomes] = useState<OutcomeForm[]>([]);
  const [loaded, setLoaded] = useState(!isEdit);

  const [queryResult] = useQuery({
    query: CONTRACT_QUERY,
    variables: { id },
    pause: !isEdit,
  });

  useEffect(() => {
    if (isEdit && queryResult.data?.contract && !loaded) {
      const c = queryResult.data.contract;
      setName(c.name);
      setDescription(c.description ?? "");
      setWorkflows(
        (c.workFlows ?? []).map((w: any) => ({
          flowId: w.flowId,
          flowVersion: String(w.flowVersion),
          alias: w.alias ?? "",
        }))
      );
      setOutcomes(
        (c.requiredOutcomes ?? []).map((o: any) => ({
          name: o.name,
          description: o.description ?? "",
        }))
      );
      setLoaded(true);
    }
  }, [isEdit, queryResult.data, loaded]);

  const [, createMutation] = useMutation(CREATE_CONTRACT);
  const [, updateMutation] = useMutation(UPDATE_CONTRACT);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const input: any = {
      name: name.trim(),
      description,
      workFlows: workflows
        .filter((w) => w.flowId.trim())
        .map((w) => ({
          flowId: w.flowId.trim(),
          flowVersion: parseInt(w.flowVersion) || 1,
          alias: w.alias || null,
        })),
      requiredOutcomes: outcomes
        .filter((o) => o.name.trim())
        .map((o) => ({
          name: o.name.trim(),
          description: o.description,
        })),
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
      toast.success(isEdit ? "Contract updated" : "Contract created");
      const newId = isEdit ? id : result.data?.createContract?.id;
      navigate(newId ? `/contracts/${newId}` : "/contracts");
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">
          {isEdit ? "Edit Contract" : "New Contract"}
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
                placeholder="My Contract"
                required
              />
            </div>
            <div>
              <Label>Description</Label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What this contract represents"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Workflow References</CardTitle>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setWorkflows([...workflows, { flowId: "", flowVersion: "1", alias: "" }])}
            >
              <Plus className="mr-1 h-3 w-3" />
              Add
            </Button>
          </CardHeader>
          <CardContent>
            {workflows.length === 0 ? (
              <p className="text-sm text-muted-foreground">No workflows assigned</p>
            ) : (
              <div className="space-y-3">
                {workflows.map((wf, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <Input
                      value={wf.flowId}
                      onChange={(e) => {
                        const u = [...workflows];
                        u[i] = { ...u[i], flowId: e.target.value };
                        setWorkflows(u);
                      }}
                      placeholder="Flow ID (UUID)"
                      className="h-8 font-mono text-xs flex-1"
                    />
                    <Input
                      value={wf.flowVersion}
                      onChange={(e) => {
                        const u = [...workflows];
                        u[i] = { ...u[i], flowVersion: e.target.value };
                        setWorkflows(u);
                      }}
                      placeholder="v"
                      className="h-8 w-16 text-xs"
                      type="number"
                    />
                    <Input
                      value={wf.alias}
                      onChange={(e) => {
                        const u = [...workflows];
                        u[i] = { ...u[i], alias: e.target.value };
                        setWorkflows(u);
                      }}
                      placeholder="Alias"
                      className="h-8 w-28 text-xs"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 shrink-0"
                      onClick={() => setWorkflows(workflows.filter((_, j) => j !== i))}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">Required Outcomes</CardTitle>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setOutcomes([...outcomes, { name: "", description: "" }])}
            >
              <Plus className="mr-1 h-3 w-3" />
              Add
            </Button>
          </CardHeader>
          <CardContent>
            {outcomes.length === 0 ? (
              <p className="text-sm text-muted-foreground">No outcomes defined</p>
            ) : (
              <div className="space-y-3">
                {outcomes.map((o, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <Input
                      value={o.name}
                      onChange={(e) => {
                        const u = [...outcomes];
                        u[i] = { ...u[i], name: e.target.value };
                        setOutcomes(u);
                      }}
                      placeholder="Outcome name"
                      className="h-8 text-sm"
                    />
                    <Input
                      value={o.description}
                      onChange={(e) => {
                        const u = [...outcomes];
                        u[i] = { ...u[i], description: e.target.value };
                        setOutcomes(u);
                      }}
                      placeholder="Description"
                      className="h-8 text-sm flex-1"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 shrink-0"
                      onClick={() => setOutcomes(outcomes.filter((_, j) => j !== i))}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

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
