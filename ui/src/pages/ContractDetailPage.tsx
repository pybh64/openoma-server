import { useParams, Link } from "react-router-dom";
import { useQuery } from "urql";
import { ArrowRight, GitBranch, FileText, Target } from "lucide-react";
import { CONTRACT_QUERY } from "@/graphql/queries/contracts";
import { FLOW_QUERY } from "@/graphql/queries/flows";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingState, ErrorState } from "@/components/shared/StateDisplay";
import { formatDate, shortId } from "@/lib/utils";
import type { FlowReference, ContractReference, RequiredOutcomeReference, Party } from "@/types";

export function ContractDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [{ data, fetching, error }] = useQuery({
    query: CONTRACT_QUERY,
    variables: { id },
    pause: !id,
  });

  if (fetching) return <LoadingState />;
  if (error) return <ErrorState message={error.message} />;

  const contract = data?.contract;
  if (!contract) return <ErrorState message="Contract not found" />;

  return (
    <div>
      <PageHeader
        breadcrumbs={[
          { label: "Contracts", href: "/contracts" },
          { label: contract.name },
        ]}
        title={contract.name}
        description={contract.description}
        actions={<Badge variant="outline">v{contract.version}</Badge>}
      />

      <div className="p-6 space-y-6">
        {/* Info */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><div className="text-xs text-muted-foreground">Version</div><div className="font-medium">v{contract.version}</div></div>
          <div><div className="text-xs text-muted-foreground">Created</div><div className="font-medium">{formatDate(contract.createdAt)}</div></div>
          <div><div className="text-xs text-muted-foreground">Flows</div><div className="font-medium">{contract.workFlows.length}</div></div>
          <div><div className="text-xs text-muted-foreground">Sub-contracts</div><div className="font-medium">{contract.subContracts.length}</div></div>
        </div>

        {/* Owners */}
        {contract.owners.length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-base">Parties</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2">
                {contract.owners.map((p: Party, i: number) => (
                  <div key={i} className="flex items-center gap-3 p-2 rounded-md bg-muted/50">
                    <div className="h-8 w-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">
                      {p.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="text-sm font-medium">{p.name}</div>
                      <div className="text-xs text-muted-foreground">{p.role}{p.contact ? ` · ${p.contact}` : ""}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Flows */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <GitBranch className="h-4 w-4" /> Flows ({contract.workFlows.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {contract.workFlows.length === 0 ? (
              <p className="text-sm text-muted-foreground">No flows attached</p>
            ) : (
              <div className="space-y-2">
                {contract.workFlows.map((ref: FlowReference, i: number) => (
                  <FlowRefCard key={i} ref_={ref} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sub-contracts */}
        {contract.subContracts.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="h-4 w-4" /> Sub-contracts ({contract.subContracts.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {contract.subContracts.map((ref: ContractReference, i: number) => (
                  <Link
                    key={i}
                    to={`/contracts/${ref.contractId}`}
                    className="flex items-center justify-between p-3 rounded-md bg-muted/50 hover:bg-muted transition-colors"
                  >
                    <div>
                      <div className="text-sm font-medium">{ref.alias || `Contract ${shortId(ref.contractId)}`}</div>
                      <div className="text-xs text-muted-foreground">v{ref.contractVersion}</div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Required Outcomes */}
        {contract.requiredOutcomes.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Target className="h-4 w-4" /> Required Outcomes ({contract.requiredOutcomes.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {contract.requiredOutcomes.map((ref: RequiredOutcomeReference, i: number) => (
                  <div key={i} className="p-3 rounded-md bg-muted/50">
                    <div className="text-sm font-medium">{ref.alias || `Outcome ${shortId(ref.requiredOutcomeId)}`}</div>
                    <div className="text-xs text-muted-foreground">v{ref.requiredOutcomeVersion}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function FlowRefCard({ ref_ }: { ref_: FlowReference }) {
  const [{ data }] = useQuery({ query: FLOW_QUERY, variables: { id: ref_.flowId, version: ref_.flowVersion } });
  const flow = data?.flow;
  return (
    <Link
      to={`/flows/${ref_.flowId}/v/${ref_.flowVersion}`}
      className="flex items-center justify-between p-3 rounded-md bg-muted/50 hover:bg-muted transition-colors"
    >
      <div>
        <div className="text-sm font-medium">{flow?.name || ref_.alias || `Flow ${shortId(ref_.flowId)}`}</div>
        <div className="text-xs text-muted-foreground">
          v{ref_.flowVersion}
          {flow && ` · ${flow.nodes.length} nodes`}
        </div>
      </div>
      <ArrowRight className="h-4 w-4 text-muted-foreground" />
    </Link>
  );
}
