import { Moon, Sun, Search, LogOut, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useUIStore } from "@/stores/ui";
import { useAuthStore } from "@/stores/auth";

interface HeaderProps {
  onOpenCommandPalette: () => void;
}

export function Header({ onOpenCommandPalette }: HeaderProps) {
  const theme = useUIStore((s) => s.theme);
  const toggleTheme = useUIStore((s) => s.toggleTheme);
  const { userId, tenantId, roles, isAuthenticated, clearAuth } = useAuthStore();

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-background px-6">
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="sm"
          className="h-8 w-64 justify-start gap-2 text-muted-foreground"
          onClick={onOpenCommandPalette}
        >
          <Search className="h-3.5 w-3.5" />
          <span className="text-xs">Search entities...</span>
          <kbd className="ml-auto rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
            ⌘K
          </kbd>
        </Button>
      </div>

      <div className="flex items-center gap-2">
        {isAuthenticated && (
          <div className="flex items-center gap-2 mr-2">
            <User className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">{userId}</span>
            {tenantId && (
              <Badge variant="outline" className="text-[9px] h-5">
                {tenantId}
              </Badge>
            )}
            {roles.includes("admin") && (
              <Badge variant="secondary" className="text-[9px] h-5">
                admin
              </Badge>
            )}
          </div>
        )}

        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={toggleTheme}
        >
          {theme === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>

        {isAuthenticated && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={clearAuth}
          >
            <LogOut className="h-4 w-4" />
          </Button>
        )}
      </div>
    </header>
  );
}
