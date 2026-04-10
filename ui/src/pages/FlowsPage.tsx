import { useState } from "react";
import { useQuery, useMutation } from "urql";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Search, GitBranch } from "lucide-react";
import { FLOWS_QUERY } from "@/graphql/queries/flows";
import { CREATE_BLANK_FLOW_DRAFT } from "@/graphql/mutations/flowDrafts";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingState, EmptyState } from "@/components/shared/StateDisplay";
import { shortId } from "@/lib/utils";

export function FlowsPage() {
  const [search, setSearch] = useState("");
  const navigate = useNavigate();
  const [{ data, fetching }] = useQuery({
    query: FLOWS_QUERY,
    variables: { name: search || undefined, limit: 50 },
  });
  const [, createDraft] = useMutation(CREATE_BLANK_FLOW_DRAFT);

  const flows = data?.flows ?? [];

  const handleNewFlow = async () => {
    const name = prompt("Flow name:");
    if (!name) return;
    const result = await createDraft({ name });
    if (result.data?.createBlankFlowDraft) {
      navigate(`/drafts/${result.data.createBlankFlowDraft.draftId}`);
    }
  };

  return (
    <div>
      <PageHeader
        title="Flows"
        description="Directed acyclic graphs of connected work blocks"
        actions={
          <Button onClick={handleNewFlow}>
            <Plus className="h-4 w-4" /> New Flow
          </Button>
        }
      />

      <div className="p-6 space-y-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search flows..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        {fetching ? (
          <LoadingState />
        ) : flows.length === 0 ? (
          <EmptyState
            icon={<GitBranch className="h-10 w-10" />}
            title="No flows found"
            description={search ? "Try a different search term" : "Create your first flow to get started"}
            action={
              !search && (
                <Button onClick={handleNewFlow}>
                  <Plus className="h-4 w-4" /> Create Flow
                </Button>
              )
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {flows.map((f: { id: string; name: string; version: number; description: string; nodes: { id: string }[]; edges: { sourceId: string | null }[] }) => (
              <Link key={f.id} to={`/flows/${f.id}`}>
                <Card className="hover:border-primary/30 hover:shadow-md transition-all h-full">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-sm">{f.name}</h3>
                      <Badge variant="outline" className="text-[10px] shrink-0">
                        v{f.version}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                      {f.description || "No description"}
                    </p>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{f.nodes.length} nodes</span>
                      <span>·</span>
                      <span>{f.edges.length} edges</span>
                    </div>
                    <div className="text-[10px] text-muted-foreground/60 mt-2 font-mono">
                      {shortId(f.id)}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
