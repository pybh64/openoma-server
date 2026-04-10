import { useState } from "react";
import { useQuery } from "urql";
import { Link } from "react-router-dom";
import { Activity, GitBranch, FileText } from "lucide-react";
import { FLOW_EXECUTIONS_QUERY, CONTRACT_EXECUTIONS_QUERY } from "@/graphql/queries/executions";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LoadingState, EmptyState } from "@/components/shared/StateDisplay";
import { formatDate, shortId, executionStateColor } from "@/lib/utils";

export function ExecutionsPage() {
  const [tab, setTab] = useState("flows");
  const [{ data: flowData, fetching: flowFetching }] = useQuery({
    query: FLOW_EXECUTIONS_QUERY,
    variables: { limit: 50 },
  });
  const [{ data: contractData, fetching: contractFetching }] = useQuery({
    query: CONTRACT_EXECUTIONS_QUERY,
    variables: { limit: 50 },
  });

  const flowExecs = flowData?.flowExecutions ?? [];
  const contractExecs = contractData?.contractExecutions ?? [];

  return (
    <div>
      <PageHeader
        title="Executions"
        description="Monitor and track execution progress"
      />

      <div className="p-6">
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="flows" className="gap-1.5">
              <GitBranch className="h-3.5 w-3.5" /> Flow Executions
              {flowExecs.length > 0 && (
                <Badge variant="secondary" className="text-[10px] ml-1">{flowExecs.length}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="contracts" className="gap-1.5">
              <FileText className="h-3.5 w-3.5" /> Contract Executions
              {contractExecs.length > 0 && (
                <Badge variant="secondary" className="text-[10px] ml-1">{contractExecs.length}</Badge>
              )}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="flows" className="mt-4">
            {flowFetching ? (
              <LoadingState />
            ) : flowExecs.length === 0 ? (
              <EmptyState
                icon={<Activity className="h-10 w-10" />}
                title="No flow executions"
                description="Execute a flow to see its progress here"
              />
            ) : (
              <div className="space-y-2">
                {flowExecs.map((exec: { id: string; flowId: string; flowVersion: number; state: string; createdAt: string; blockExecutions: { id: string; state: string }[] }) => (
                  <Link key={exec.id} to={`/executions/flow/${exec.id}`}>
                    <Card className="hover:border-primary/30 transition-colors">
                      <CardContent className="flex items-center gap-4 p-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium">Flow {shortId(exec.flowId)}</span>
                            <Badge variant="outline" className="text-[10px]">v{exec.flowVersion}</Badge>
                          </div>
                          <div className="text-xs text-muted-foreground mt-0.5">
                            {formatDate(exec.createdAt)} · {exec.blockExecutions?.length ?? 0} blocks
                          </div>
                        </div>
                        <Badge className={executionStateColor(exec.state) + " border-0 text-[11px]"}>
                          {exec.state}
                        </Badge>
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="contracts" className="mt-4">
            {contractFetching ? (
              <LoadingState />
            ) : contractExecs.length === 0 ? (
              <EmptyState
                icon={<Activity className="h-10 w-10" />}
                title="No contract executions"
                description="Execute a contract to see its progress here"
              />
            ) : (
              <div className="space-y-2">
                {contractExecs.map((exec: { id: string; contractId: string; contractVersion: number; state: string; createdAt: string; flowExecutions: unknown[] }) => (
                  <Card key={exec.id} className="hover:border-primary/30 transition-colors">
                    <CardContent className="flex items-center gap-4 p-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">Contract {shortId(exec.contractId)}</span>
                          <Badge variant="outline" className="text-[10px]">v{exec.contractVersion}</Badge>
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {formatDate(exec.createdAt)} · {exec.flowExecutions?.length ?? 0} flows
                        </div>
                      </div>
                      <Badge className={executionStateColor(exec.state) + " border-0 text-[11px]"}>
                        {exec.state}
                      </Badge>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
