import { useLocation, Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { Fragment } from "react";

const labels: Record<string, string> = {
  "work-blocks": "Work Blocks",
  flows: "Flows",
  contracts: "Contracts",
  executions: "Executions",
  new: "New",
  edit: "Edit",
};

export function Breadcrumbs() {
  const { pathname } = useLocation();
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length === 0) return null;

  return (
    <nav className="mb-4 flex items-center gap-1 text-sm text-muted-foreground">
      <Link to="/" className="hover:text-foreground transition-colors">
        Home
      </Link>
      {segments.map((seg, i) => {
        const path = "/" + segments.slice(0, i + 1).join("/");
        const label = labels[seg] ?? seg;
        const isLast = i === segments.length - 1;
        return (
          <Fragment key={path}>
            <ChevronRight className="h-3 w-3" />
            {isLast ? (
              <span className="text-foreground font-medium">{label}</span>
            ) : (
              <Link to={path} className="hover:text-foreground transition-colors">
                {label}
              </Link>
            )}
          </Fragment>
        );
      })}
    </nav>
  );
}
