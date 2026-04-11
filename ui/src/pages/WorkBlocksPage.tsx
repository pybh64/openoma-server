import { useState } from "react";
import { useQuery, useMutation } from "urql";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Search, Blocks } from "lucide-react";
import { WORK_BLOCKS_QUERY } from "@/graphql/queries/workBlocks";
import { CREATE_WORK_BLOCK } from "@/graphql/mutations/workBlocks";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingState, EmptyState } from "@/components/shared/StateDisplay";
import { WorkBlockFormDialog } from "@/components/work-blocks/WorkBlockFormDialog";
import { shortId } from "@/lib/utils";

export function WorkBlocksPage() {
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const navigate = useNavigate();
  const [{ data, fetching }, reexecute] = useQuery({
    query: WORK_BLOCKS_QUERY,
    variables: { name: search || undefined, limit: 50 },
  });
  const [, createWorkBlock] = useMutation(CREATE_WORK_BLOCK);

  const workBlocks = data?.workBlocks ?? [];

  return (
    <div>
      <PageHeader
        title="Work Blocks"
        description="Reusable atomic units of work"
        actions={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4" /> New Work Block
          </Button>
        }
      />

      <div className="p-6 space-y-4">
        {/* Search bar */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search work blocks..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* List */}
        {fetching ? (
          <LoadingState />
        ) : workBlocks.length === 0 ? (
          <EmptyState
            icon={<Blocks className="h-10 w-10" />}
            title="No work blocks found"
            description={search ? "Try a different search term" : "Create your first work block to get started"}
            action={
              !search && (
                <Button onClick={() => setShowCreate(true)}>
                  <Plus className="h-4 w-4" /> Create Work Block
                </Button>
              )
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {workBlocks.map((wb: { id: string; name: string; version: number; description: string; inputs: unknown[]; outputs: unknown[]; executionHints: string[] }) => (
              <Link key={wb.id} to={`/work-blocks/${wb.id}`}>
                <Card className="hover:border-primary/30 hover:shadow-md transition-all h-full">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-sm">{wb.name}</h3>
                      <Badge variant="outline" className="text-[10px] shrink-0">
                        v{wb.version}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                      {wb.description}
                    </p>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{wb.inputs?.length ?? 0} inputs</span>
                      <span>·</span>
                      <span>{wb.outputs?.length ?? 0} outputs</span>
                      {wb.executionHints?.length > 0 && (
                        <>
                          <span>·</span>
                          <span>{wb.executionHints[0]}</span>
                        </>
                      )}
                    </div>
                    <div className="text-[10px] text-muted-foreground/60 mt-2 font-mono">
                      {shortId(wb.id)}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>

      <WorkBlockFormDialog
        open={showCreate}
        onOpenChange={setShowCreate}
        title="Create Work Block"
        submitLabel="Create Work Block"
        onSubmit={async (input) => {
          const result = await createWorkBlock({ input });
          if (result.data?.createWorkBlock) {
            reexecute({ requestPolicy: "network-only" });
            navigate(`/work-blocks/${result.data.createWorkBlock.id}`);
          }
        }}
      />
    </div>
  );
}
