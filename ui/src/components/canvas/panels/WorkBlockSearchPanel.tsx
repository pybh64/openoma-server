import { useState } from "react";
import { useQuery } from "urql";
import { Search, Plus, Blocks, X } from "lucide-react";
import { WORK_BLOCK_SEARCH } from "@/graphql/queries/workBlocks";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";

interface WorkBlockSearchResult {
  id: string;
  version: number;
  name: string;
  description: string;
  executionHints: string[];
  inputs: { name: string; description: string; required: boolean }[];
  outputs: { name: string; description: string; required: boolean }[];
}

interface WorkBlockSearchPanelProps {
  mode?: "add" | "replace";
  selectedBlockId?: string | null;
  selectedBlockVersion?: number | null;
  onSelectBlock: (block: WorkBlockSearchResult) => void;
  onClose: () => void;
}

export function WorkBlockSearchPanel({
  mode = "add",
  selectedBlockId,
  selectedBlockVersion,
  onSelectBlock,
  onClose,
}: WorkBlockSearchPanelProps) {
  const [search, setSearch] = useState("");
  const [{ data, fetching }] = useQuery({
    query: WORK_BLOCK_SEARCH,
    variables: { name: search || undefined, limit: 20 },
  });

  const blocks: WorkBlockSearchResult[] = data?.workBlocks ?? [];
  const actionLabel = mode === "replace" ? "Replace with this version" : "Add to draft";
  const title = mode === "replace" ? "Replace Work Block" : "Add Work Block";
  const subtitle =
    mode === "replace"
      ? "Pick the version you want this node to reference."
      : "Pick a work block to add as a new node in this draft.";

  return (
    <div className="w-72 border-l border-border bg-card flex flex-col h-full">
      <div className="p-3 border-b border-border">
        <div className="mb-2 flex items-start justify-between gap-2">
          <div>
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Blocks className="h-4 w-4" /> {title}
            </h3>
            <p className="mt-1 text-[11px] text-muted-foreground">{subtitle}</p>
          </div>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search blocks..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 h-8 text-xs"
            autoFocus
          />
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {fetching ? (
            <div className="text-xs text-muted-foreground text-center py-4">Searching...</div>
          ) : blocks.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-4">
              {search ? "No blocks found" : "No work blocks available yet"}
            </div>
          ) : (
            blocks.map((block) => {
              const isCurrent =
                selectedBlockId === block.id && selectedBlockVersion === block.version;
              return (
              <button
                key={block.id}
                onClick={() => onSelectBlock(block)}
                className="w-full rounded-md border border-transparent p-2.5 text-left transition-colors hover:border-border hover:bg-muted group"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <div className="text-xs font-medium truncate">{block.name}</div>
                      <Badge variant="outline" className="text-[10px]">
                        v{block.version}
                      </Badge>
                      {isCurrent && (
                        <Badge variant="secondary" className="text-[10px]">
                          Current
                        </Badge>
                      )}
                    </div>
                    <div className="text-[10px] text-muted-foreground line-clamp-2 mt-0.5">
                      {block.description}
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-[10px] text-muted-foreground">
                      <span>{block.inputs?.length ?? 0} in</span>
                      <span>·</span>
                      <span>{block.outputs?.length ?? 0} out</span>
                    </div>
                    <div className="mt-2 text-[10px] font-medium text-primary">
                      {actionLabel}
                    </div>
                  </div>
                  <Plus className="h-3.5 w-3.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 mt-0.5 shrink-0" />
                </div>
              </button>
              );
            })
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
