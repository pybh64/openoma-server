import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { DataTable, type Column } from "@/components/shared/DataTable";
import { VersionBadge } from "@/components/shared/Badges";
import { RowActions } from "@/components/shared/RowActions";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { useEntityList, useDeleteEntity } from "@/hooks/useEntity";
import { FLOWS_QUERY } from "@/graphql/queries/entities";
import { DELETE_FLOW } from "@/graphql/mutations/entities";

interface FlowNode {
  id: string;
  alias: string | null;
}

interface FlowEdge {
  sourceId: string | null;
  targetId: string;
}

interface Flow {
  id: string;
  version: number;
  name: string;
  description: string;
  nodes: FlowNode[];
  edges: FlowEdge[];
}

const columns: Column<Flow>[] = [
  { header: "Name", accessor: "name" },
  {
    header: "Version",
    accessor: (row) => <VersionBadge version={row.version} />,
    className: "w-24",
  },
  {
    header: "Graph",
    accessor: (row) => (
      <span className="text-muted-foreground text-xs">
        {row.nodes?.length ?? 0} nodes / {row.edges?.length ?? 0} edges
      </span>
    ),
    className: "w-36",
  },
  {
    header: "Description",
    accessor: (row) => (
      <span className="text-muted-foreground line-clamp-1 max-w-md">
        {row.description || "—"}
      </span>
    ),
  },
];

export default function FlowList() {
  const navigate = useNavigate();
  const {
    data,
    loading,
    hasMore,
    offset,
    limit,
    setOffset,
    setNameFilter,
    refresh,
  } = useEntityList<Flow>({
    query: FLOWS_QUERY,
    queryKey: "flows",
  });

  const { deleteEntity } = useDeleteEntity({
    mutation: DELETE_FLOW,
    onSuccess: () => {
      toast.success("Flow deleted");
      refresh();
    },
  });

  const [deleteTarget, setDeleteTarget] = useState<Flow | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Flows</h1>
          <p className="text-sm text-muted-foreground">
            Directed graphs connecting work blocks into workflows
          </p>
        </div>
        <Link to="/flows/new">
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" />
            New Flow
          </Button>
        </Link>
      </div>

      <DataTable
        columns={columns}
        data={data}
        loading={loading}
        searchPlaceholder="Filter by name..."
        onSearch={setNameFilter}
        onRefresh={refresh}
        limit={limit}
        offset={offset}
        onPageChange={setOffset}
        hasMore={hasMore}
        emptyMessage="No flows yet. Create your first one!"
        onRowClick={(row) => navigate(`/flows/${row.id}`)}
        actions={(row) => (
          <RowActions
            onView={() => navigate(`/flows/${row.id}`)}
            onEdit={() => navigate(`/flows/${row.id}/edit`)}
            onDelete={() => setDeleteTarget(row)}
          />
        )}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Flow"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This will remove all versions.`}
        confirmLabel="Delete"
        destructive
        onConfirm={() => deleteTarget && deleteEntity(deleteTarget.id)}
      />
    </div>
  );
}
