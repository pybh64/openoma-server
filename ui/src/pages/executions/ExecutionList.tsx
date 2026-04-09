import { useNavigate } from "react-router-dom";
import { useQuery } from "urql";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { BLOCK_EXECUTIONS_QUERY } from "@/graphql/queries/executions";

interface BlockExecutionSummary {
  executionId: string;
  id?: string;
  nodeReferenceId: string;
  workBlockId: string;
  workBlockVersion: number;
  flowExecutionId: string | null;
  createdAt: string | null;
}

const blockColumns: Column<BlockExecutionSummary>[] = [
  {
    header: "Execution ID",
    accessor: (row) => (
      <span className="font-mono text-xs">{row.executionId.slice(0, 8)}…</span>
    ),
  },
  {
    header: "Work Block",
    accessor: (row) => (
      <span className="font-mono text-xs">{row.workBlockId.slice(0, 8)}…</span>
    ),
  },
  {
    header: "Version",
    accessor: (row) => <span className="text-xs">v{row.workBlockVersion}</span>,
    className: "w-20",
  },
  {
    header: "Created",
    accessor: (row) =>
      row.createdAt ? new Date(row.createdAt).toLocaleString() : "—",
  },
];

export default function ExecutionList() {
  const navigate = useNavigate();

  const [blockResult] = useQuery({
    query: BLOCK_EXECUTIONS_QUERY,
    variables: { limit: 50, offset: 0 },
  });

  const blockData: BlockExecutionSummary[] =
    blockResult.data?.blockExecutions ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Executions</h1>
        <p className="text-sm text-muted-foreground">
          Monitor running processes and event history
        </p>
      </div>

      <Tabs defaultValue="blocks">
        <TabsList>
          <TabsTrigger value="blocks">Block Executions</TabsTrigger>
          <TabsTrigger value="flows">Flow Executions</TabsTrigger>
          <TabsTrigger value="contracts">Contract Executions</TabsTrigger>
        </TabsList>

        <TabsContent value="blocks" className="mt-4">
          <DataTable
            columns={blockColumns}
            data={blockData.map((d) => ({ ...d, id: d.executionId }))}
            loading={blockResult.fetching}
            emptyMessage="No block executions yet"
            onRowClick={(row) => navigate(`/executions/block/${row.executionId}`)}
          />
        </TabsContent>

        <TabsContent value="flows" className="mt-4">
          <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
            Flow execution list — coming with full execution detail views
          </div>
        </TabsContent>

        <TabsContent value="contracts" className="mt-4">
          <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
            Contract execution list — coming with full execution detail views
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
