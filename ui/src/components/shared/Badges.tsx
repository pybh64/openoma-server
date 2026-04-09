import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface VersionBadgeProps {
  version: number;
  className?: string;
}

export function VersionBadge({ version, className }: VersionBadgeProps) {
  return (
    <Badge variant="outline" className={cn("font-mono text-xs", className)}>
      v{version}
    </Badge>
  );
}

interface StateBadgeProps {
  state: string;
  className?: string;
}

const stateColors: Record<string, string> = {
  PENDING: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
  IN_PROGRESS: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  COMPLETED: "bg-green-500/10 text-green-500 border-green-500/20",
  FAILED: "bg-red-500/10 text-red-500 border-red-500/20",
  SKIPPED: "bg-gray-500/10 text-gray-500 border-gray-500/20",
  CANCELLED: "bg-orange-500/10 text-orange-500 border-orange-500/20",
};

export function StateBadge({ state, className }: StateBadgeProps) {
  const colors = stateColors[state] ?? stateColors.PENDING;
  return (
    <Badge variant="outline" className={cn("text-xs", colors, className)}>
      {state.replace("_", " ")}
    </Badge>
  );
}
