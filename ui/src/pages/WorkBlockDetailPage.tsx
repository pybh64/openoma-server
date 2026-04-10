import { useParams } from "react-router-dom";
import { useQuery } from "urql";
import { WORK_BLOCK_QUERY } from "@/graphql/queries/workBlocks";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LoadingState, ErrorState } from "@/components/shared/StateDisplay";
import { formatDate } from "@/lib/utils";
import type { PortDescriptor } from "@/types";

export function WorkBlockDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [{ data, fetching, error }] = useQuery({
    query: WORK_BLOCK_QUERY,
    variables: { id },
    pause: !id,
  });

  if (fetching) return <LoadingState />;
  if (error) return <ErrorState message={error.message} />;

  const wb = data?.workBlock;
  if (!wb) return <ErrorState message="Work block not found" />;

  return (
    <div>
      <PageHeader
        breadcrumbs={[
          { label: "Work Blocks", href: "/work-blocks" },
          { label: wb.name },
        ]}
        title={wb.name}
        description={wb.description}
        actions={
          <Badge variant="outline">v{wb.version}</Badge>
        }
      />

      <div className="p-6 space-y-6">
        {/* Metadata */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <InfoItem label="Version" value={`v${wb.version}`} />
          <InfoItem label="Created" value={formatDate(wb.createdAt)} />
          <InfoItem label="Created by" value={wb.createdBy || "—"} />
          <InfoItem label="Execution hints" value={wb.executionHints?.join(", ") || "—"} />
        </div>

        {/* Inputs */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Inputs ({wb.inputs?.length ?? 0})</CardTitle>
          </CardHeader>
          <CardContent>
            {wb.inputs?.length > 0 ? (
              <div className="space-y-3">
                {wb.inputs.map((port: PortDescriptor, i: number) => (
                  <PortItem key={i} port={port} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No inputs defined</p>
            )}
          </CardContent>
        </Card>

        {/* Outputs */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Outputs ({wb.outputs?.length ?? 0})</CardTitle>
          </CardHeader>
          <CardContent>
            {wb.outputs?.length > 0 ? (
              <div className="space-y-3">
                {wb.outputs.map((port: PortDescriptor, i: number) => (
                  <PortItem key={i} port={port} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No outputs defined</p>
            )}
          </CardContent>
        </Card>

        {/* Expected Outcome */}
        {wb.expectedOutcome && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Expected Outcome</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-medium text-sm">{wb.expectedOutcome.name}</p>
              <p className="text-sm text-muted-foreground">{wb.expectedOutcome.description}</p>
            </CardContent>
          </Card>
        )}

        {/* Metadata */}
        {wb.metadata && Object.keys(wb.metadata).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Metadata</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto">
                {JSON.stringify(wb.metadata, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}

function PortItem({ port }: { port: PortDescriptor }) {
  return (
    <div className="flex items-start gap-3 p-2 rounded-md bg-muted/50">
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{port.name}</span>
          {port.required && <Badge variant="secondary" className="text-[10px]">required</Badge>}
        </div>
        <p className="text-xs text-muted-foreground">{port.description}</p>
      </div>
    </div>
  );
}
