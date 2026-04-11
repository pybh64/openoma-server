import { useState } from "react";
import { useQuery, useMutation } from "urql";
import { Link, useNavigate } from "react-router-dom";
import { Plus, Search, FileText } from "lucide-react";
import { CONTRACTS_QUERY } from "@/graphql/queries/contracts";
import { CREATE_CONTRACT } from "@/graphql/mutations/contracts";
import { ContractFormDialog } from "@/components/contracts/ContractFormDialog";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingState, EmptyState } from "@/components/shared/StateDisplay";
import { shortId } from "@/lib/utils";

export function ContractsPage() {
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const navigate = useNavigate();
  const [{ data, fetching }] = useQuery({
    query: CONTRACTS_QUERY,
    variables: { name: search || undefined, limit: 50 },
  });
  const [, createContract] = useMutation(CREATE_CONTRACT);

  const contracts = data?.contracts ?? [];

  return (
    <div>
      <PageHeader
        title="Contracts"
        description="Operational agreements composing flows and sub-contracts"
        actions={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4" /> New Contract
          </Button>
        }
      />

      <div className="p-6 space-y-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search contracts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        {fetching ? (
          <LoadingState />
        ) : contracts.length === 0 ? (
          <EmptyState
            icon={<FileText className="h-10 w-10" />}
            title="No contracts found"
            description={search ? "Try a different search term" : "Create your first contract to get started"}
            action={!search && <Button onClick={() => setShowCreate(true)}><Plus className="h-4 w-4" /> Create Contract</Button>}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {contracts.map((c: { id: string; name: string; version: number; description: string; owners: { name: string; role: string }[]; workFlows: unknown[]; subContracts: unknown[]; requiredOutcomes: unknown[] }) => (
              <Link key={c.id} to={`/contracts/${c.id}`}>
                <Card className="hover:border-primary/30 hover:shadow-md transition-all h-full">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-sm">{c.name}</h3>
                      <Badge variant="outline" className="text-[10px] shrink-0">v{c.version}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                      {c.description || "No description"}
                    </p>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <span>{c.workFlows.length} flows</span>
                      <span>·</span>
                      <span>{c.subContracts.length} sub-contracts</span>
                      {c.owners.length > 0 && (
                        <>
                          <span>·</span>
                          <span>{c.owners.map((o) => o.name).join(", ")}</span>
                        </>
                      )}
                    </div>
                    <div className="text-[10px] text-muted-foreground/60 mt-2 font-mono">{shortId(c.id)}</div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>

      <ContractFormDialog
        open={showCreate}
        onOpenChange={setShowCreate}
        title="Create Contract"
        submitLabel="Create Contract"
        onSubmit={async (input) => {
          const result = await createContract({ input });
          if (result.data?.createContract) {
            navigate(`/contracts/${result.data.createContract.id}`);
          }
        }}
      />
    </div>
  );
}
