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
import { CONTRACTS_QUERY } from "@/graphql/queries/entities";
import { DELETE_CONTRACT } from "@/graphql/mutations/entities";

interface Contract {
  id: string;
  version: number;
  name: string;
  description: string;
  workFlows: { flowId: string }[];
  subContracts: { contractId: string }[];
  requiredOutcomes: { id: string; name: string }[];
}

const columns: Column<Contract>[] = [
  { header: "Name", accessor: "name" },
  {
    header: "Version",
    accessor: (row) => <VersionBadge version={row.version} />,
    className: "w-24",
  },
  {
    header: "Composition",
    accessor: (row) => (
      <span className="text-muted-foreground text-xs">
        {row.workFlows?.length ?? 0} flows / {row.subContracts?.length ?? 0} sub-contracts
      </span>
    ),
    className: "w-48",
  },
  {
    header: "Outcomes",
    accessor: (row) => (
      <span className="text-muted-foreground text-xs">
        {row.requiredOutcomes?.length ?? 0}
      </span>
    ),
    className: "w-24",
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

export default function ContractList() {
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
  } = useEntityList<Contract>({
    query: CONTRACTS_QUERY,
    queryKey: "contracts",
  });

  const { deleteEntity } = useDeleteEntity({
    mutation: DELETE_CONTRACT,
    onSuccess: () => {
      toast.success("Contract deleted");
      refresh();
    },
  });

  const [deleteTarget, setDeleteTarget] = useState<Contract | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Contracts</h1>
          <p className="text-sm text-muted-foreground">
            Composable contracts with outcomes and assessments
          </p>
        </div>
        <Link to="/contracts/new">
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" />
            New Contract
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
        emptyMessage="No contracts yet. Create your first one!"
        onRowClick={(row) => navigate(`/contracts/${row.id}`)}
        actions={(row) => (
          <RowActions
            onView={() => navigate(`/contracts/${row.id}`)}
            onEdit={() => navigate(`/contracts/${row.id}/edit`)}
            onDelete={() => setDeleteTarget(row)}
          />
        )}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Contract"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This will remove all versions.`}
        confirmLabel="Delete"
        destructive
        onConfirm={() => deleteTarget && deleteEntity(deleteTarget.id)}
      />
    </div>
  );
}
