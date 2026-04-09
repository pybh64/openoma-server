import { useQuery } from "urql";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";
import { WORK_BLOCKS_QUERY } from "@/graphql/queries/entities";

interface WorkBlockPaletteProps {
  onDragStart: (event: React.DragEvent, workBlock: any) => void;
}

export function WorkBlockPalette({ onDragStart }: WorkBlockPaletteProps) {
  const [search, setSearch] = useState("");

  const [result] = useQuery({
    query: WORK_BLOCKS_QUERY,
    variables: { limit: 200, latestOnly: true },
  });

  const blocks = (result.data?.workBlocks ?? []).filter(
    (b: any) =>
      !search || b.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex h-full flex-col border-r border-border bg-background w-64">
      <div className="border-b border-border p-3">
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          Work Blocks
        </h3>
        <div className="relative">
          <Search className="absolute left-2 top-2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 pl-7 text-xs"
          />
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-1 p-2">
          {result.fetching ? (
            <p className="p-2 text-xs text-muted-foreground">Loading...</p>
          ) : blocks.length === 0 ? (
            <p className="p-2 text-xs text-muted-foreground">
              {search ? "No matches" : "No work blocks yet"}
            </p>
          ) : (
            blocks.map((block: any) => (
              <div
                key={block.id}
                draggable
                onDragStart={(e) => onDragStart(e, block)}
                className="cursor-grab rounded-md border border-border bg-card p-2 transition-colors hover:border-primary/50 hover:bg-accent active:cursor-grabbing"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium truncate">{block.name}</span>
                  <Badge variant="outline" className="text-[9px] font-mono ml-1 shrink-0">
                    v{block.version}
                  </Badge>
                </div>
                <div className="mt-1 flex gap-2 text-[10px] text-muted-foreground">
                  <span>{block.inputs?.length ?? 0} in</span>
                  <span>{block.outputs?.length ?? 0} out</span>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
