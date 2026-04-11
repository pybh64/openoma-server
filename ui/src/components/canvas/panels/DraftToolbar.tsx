import {
  Plus,
  Save,
  Trash2,
  Upload,
  Search,
  Grid3X3,
  Map,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import { useCanvasStore } from "@/stores/canvasStore";

interface DraftToolbarProps {
  draftName: string;
  isDirty: boolean;
  nodeCount: number;
  edgeCount: number;
  onPublish: () => void;
  onDiscard: () => void;
  onSavePositions: () => void;
  onOpenBlockLibrary: () => void;
  publishing?: boolean;
}

export function DraftToolbar({
  draftName,
  isDirty,
  nodeCount,
  edgeCount,
  onPublish,
  onDiscard,
  onSavePositions,
  onOpenBlockLibrary,
  publishing,
}: DraftToolbarProps) {
  const {
    showMinimap,
    showGrid,
    searchPanelOpen,
    toggleMinimap,
    toggleGrid,
  } = useCanvasStore();

  return (
    <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-card">
      {/* Draft info */}
      <div className="flex items-center gap-2 mr-4">
        <span className="text-sm font-semibold truncate max-w-[200px]">{draftName}</span>
        <Badge variant="secondary" className="text-[10px]">Draft</Badge>
        {isDirty && <Badge variant="outline" className="text-[10px] text-amber-600">Unsaved</Badge>}
      </div>

      <div className="text-xs text-muted-foreground">
        {nodeCount} nodes · {edgeCount} edges
      </div>

      <div className="flex-1" />

      {/* Canvas tools */}
      <Button
        variant={searchPanelOpen ? "secondary" : "outline"}
        size="sm"
        onClick={onOpenBlockLibrary}
      >
        <Plus className="h-3.5 w-3.5 mr-1" /> Add Block
      </Button>
      <ToolButton icon={Search} label="Block Library" active={searchPanelOpen} onClick={onOpenBlockLibrary} />
      <ToolButton icon={Grid3X3} label="Toggle Grid" active={showGrid} onClick={toggleGrid} />
      <ToolButton icon={Map} label="Toggle Minimap" active={showMinimap} onClick={toggleMinimap} />

      <Separator orientation="vertical" className="h-6 mx-1" />

      {/* Draft actions */}
      <Button variant="outline" size="sm" onClick={onSavePositions} disabled={!isDirty}>
        <Save className="h-3.5 w-3.5 mr-1" /> Save Layout
      </Button>
      <Button variant="default" size="sm" onClick={onPublish} disabled={publishing}>
        <Upload className="h-3.5 w-3.5 mr-1" /> {publishing ? "Publishing..." : "Publish"}
      </Button>
      <Button variant="ghost" size="sm" onClick={onDiscard} className="text-destructive hover:text-destructive">
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}

function ToolButton({
  icon: Icon,
  label,
  active,
  onClick,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  active?: boolean;
  onClick: () => void;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant={active ? "secondary" : "ghost"}
          size="icon"
          className="h-8 w-8"
          onClick={onClick}
        >
          <Icon className="h-3.5 w-3.5" />
        </Button>
      </TooltipTrigger>
      <TooltipContent side="bottom">{label}</TooltipContent>
    </Tooltip>
  );
}
