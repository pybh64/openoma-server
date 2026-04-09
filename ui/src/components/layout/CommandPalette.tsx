import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Box, GitBranch, FileText, Play, LayoutDashboard } from "lucide-react";

const staticRoutes = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Work Blocks", path: "/work-blocks", icon: Box },
  { label: "Flows", path: "/flows", icon: GitBranch },
  { label: "Contracts", path: "/contracts", icon: FileText },
  { label: "Executions", path: "/executions", icon: Play },
];

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [_search, setSearch] = useState("");

  const handleSelect = useCallback(
    (path: string) => {
      navigate(path);
      onOpenChange(false);
    },
    [navigate, onOpenChange]
  );

  useEffect(() => {
    if (!open) setSearch("");
  }, [open]);

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput
        placeholder="Search entities, navigate..."
        onValueChange={setSearch}
      />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Navigation">
          {staticRoutes.map(({ label, path, icon: Icon }) => (
            <CommandItem key={path} onSelect={() => handleSelect(path)}>
              <Icon className="mr-2 h-4 w-4" />
              {label}
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
