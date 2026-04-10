import { useState } from "react";
import { useQuery } from "urql";
import { Search, Plus, Blocks } from "lucide-react";
import { WORK_BLOCK_SEARCH } from "@/graphql/queries/workBlocks";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";

interface WorkBlockSearchPanelProps {
  onAddBlock: (block: {
    id: string;
    version: number;
    name: string;
    description: string;
    executionHints: string[];
    inputs: { name: string; description: string; required: boolean }[];
    outputs: { name: string; description: string; required: boolean }[];
  }) => void;
}

export function WorkBlockSearchPanel({ onAddBlock }: WorkBlockSearchPanelProps) {
  const [search, setSearch] = useState("");
  const [{ data, fetching }] = useQuery({
    query: WORK_BLOCK_SEARCH,
    variables: { name: search || undefined, limit: 20 },
  });

  const blocks = data?.workBlocks ?? [];

  return (
    <div className="w-72 border-l border-border bg-card flex flex-col h-full">
      <div className="p-3 border-b border-border">
        <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
          <Blocks className="h-4 w-4" /> Add Work Block
        </h3>
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
              {search ? "No blocks found" : "Type to search work blocks"}
            </div>
          ) : (
            blocks.map((block: {
              id: string;
              version: number;
              name: string;
              description: string;
              executionHints: string[];
              inputs: { name: string; description: string; required: boolean }[];
              outputs: { name: string; description: string; required: boolean }[];
            }) => (
              <button
                key={block.id}
                onClick={() => onAddBlock(block)}
                className="w-full text-left p-2.5 rounded-md hover:bg-muted transition-colors group"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-xs font-medium truncate">{block.name}</div>
                    <div className="text-[10px] text-muted-foreground line-clamp-2 mt-0.5">
                      {block.description}
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-[10px] text-muted-foreground">
                      <span>{block.inputs?.length ?? 0} in</span>
                      <span>·</span>
                      <span>{block.outputs?.length ?? 0} out</span>
                    </div>
                  </div>
                  <Plus className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity mt-0.5 shrink-0" />
                </div>
              </button>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
