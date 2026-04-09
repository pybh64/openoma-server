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
import { WORK_BLOCKS_QUERY } from "@/graphql/queries/entities";
import { DELETE_WORK_BLOCK } from "@/graphql/mutations/entities";

interface WorkBlock {
  id: string;
  version: number;
  name: string;
  description: string;
  inputs: { name: string }[];
  outputs: { name: string }[];
  executionHints: string[];
}

const columns: Column<WorkBlock>[] = [
  { header: "Name", accessor: "name" },
  {
    header: "Version",
    accessor: (row) => <VersionBadge version={row.version} />,
    className: "w-24",
  },
  {
    header: "Ports",
    accessor: (row) => (
      <span className="text-muted-foreground text-xs">
        {row.inputs?.length ?? 0} in / {row.outputs?.length ?? 0} out
      </span>
    ),
    className: "w-32",
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

export default function WorkBlockList() {
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
  } = useEntityList<WorkBlock>({
    query: WORK_BLOCKS_QUERY,
    queryKey: "workBlocks",
  });

  const { deleteEntity } = useDeleteEntity({
    mutation: DELETE_WORK_BLOCK,
    onSuccess: () => {
      toast.success("Work block deleted");
      refresh();
    },
  });

  const [deleteTarget, setDeleteTarget] = useState<WorkBlock | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Work Blocks</h1>
          <p className="text-sm text-muted-foreground">
            Atomic units of work with typed input/output ports
          </p>
        </div>
        <Link to="/work-blocks/new">
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" />
            New Work Block
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
        emptyMessage="No work blocks yet. Create your first one!"
        onRowClick={(row) => navigate(`/work-blocks/${row.id}`)}
        actions={(row) => (
          <RowActions
            onView={() => navigate(`/work-blocks/${row.id}`)}
            onEdit={() => navigate(`/work-blocks/${row.id}/edit`)}
            onDelete={() => setDeleteTarget(row)}
          />
        )}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Work Block"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This will remove all versions.`}
        confirmLabel="Delete"
        destructive
        onConfirm={() => deleteTarget && deleteEntity(deleteTarget.id)}
      />
    </div>
  );
}
