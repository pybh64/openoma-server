import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "urql";
import { ArrowLeft, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { VersionBadge } from "@/components/shared/Badges";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { useDeleteEntity } from "@/hooks/useEntity";
import { WORK_BLOCK_QUERY, WORK_BLOCK_VERSIONS_QUERY } from "@/graphql/queries/entities";
import { DELETE_WORK_BLOCK } from "@/graphql/mutations/entities";

export default function WorkBlockDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [showDelete, setShowDelete] = useState(false);

  const [result] = useQuery({
    query: WORK_BLOCK_QUERY,
    variables: { id },
    pause: !id,
  });

  const [versionsResult] = useQuery({
    query: WORK_BLOCK_VERSIONS_QUERY,
    variables: { id },
    pause: !id,
  });

  const { deleteEntity } = useDeleteEntity({
    mutation: DELETE_WORK_BLOCK,
    onSuccess: () => {
      toast.success("Work block deleted");
      navigate("/work-blocks");
    },
  });

  const wb = result.data?.workBlock;
  const versions = versionsResult.data?.workBlockVersions ?? [];

  if (result.fetching) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!wb) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-muted-foreground">Work block not found</p>
        <Button variant="outline" onClick={() => navigate("/work-blocks")}>
          Back to list
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate("/work-blocks")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">{wb.name}</h1>
            <VersionBadge version={wb.version} />
          </div>
          <p className="text-sm text-muted-foreground">{wb.description || "No description"}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => navigate(`/work-blocks/${id}/edit`)}>
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowDelete(true)}>
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Input Ports</CardTitle>
          </CardHeader>
          <CardContent>
            {wb.inputs?.length > 0 ? (
              <div className="space-y-3">
                {wb.inputs.map((port: any, i: number) => (
                  <div key={i} className="rounded-md border p-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">{port.name}</span>
                      {port.required && (
                        <Badge variant="secondary" className="text-[10px]">required</Badge>
                      )}
                    </div>
                    {port.description && (
                      <p className="mt-1 text-xs text-muted-foreground">{port.description}</p>
                    )}
                    {port.schemaDef && (
                      <pre className="mt-2 rounded bg-muted p-2 text-[10px] overflow-auto">
                        {JSON.stringify(port.schemaDef, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No input ports</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Output Ports</CardTitle>
          </CardHeader>
          <CardContent>
            {wb.outputs?.length > 0 ? (
              <div className="space-y-3">
                {wb.outputs.map((port: any, i: number) => (
                  <div key={i} className="rounded-md border p-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">{port.name}</span>
                      {port.required && (
                        <Badge variant="secondary" className="text-[10px]">required</Badge>
                      )}
                    </div>
                    {port.description && (
                      <p className="mt-1 text-xs text-muted-foreground">{port.description}</p>
                    )}
                    {port.schemaDef && (
                      <pre className="mt-2 rounded bg-muted p-2 text-[10px] overflow-auto">
                        {JSON.stringify(port.schemaDef, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No output ports</p>
            )}
          </CardContent>
        </Card>
      </div>

      {wb.executionHints?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Execution Hints</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {wb.executionHints.map((hint: string, i: number) => (
                <Badge key={i} variant="outline">{hint}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {wb.metadata && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Metadata</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="rounded bg-muted p-3 text-xs overflow-auto">
              {JSON.stringify(wb.metadata, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {versions.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Version History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {versions.map((v: any) => (
                <button
                  key={v.version}
                  onClick={() => navigate(`/work-blocks/${id}?version=${v.version}`)}
                  className={`flex w-full items-center gap-3 rounded-md border p-2 text-left text-sm transition-colors hover:bg-accent ${
                    v.version === wb.version ? "border-primary bg-accent" : ""
                  }`}
                >
                  <VersionBadge version={v.version} />
                  <span>{v.name}</span>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <ConfirmDialog
        open={showDelete}
        onOpenChange={setShowDelete}
        title="Delete Work Block"
        description={`Are you sure you want to delete "${wb.name}"? This will remove all versions.`}
        confirmLabel="Delete"
        destructive
        onConfirm={() => deleteEntity(id!)}
      />
    </div>
  );
}
