import {
  Box,
  GitBranch,
  FileText,
  Play,
  ArrowRight,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const sections = [
  {
    title: "Work Blocks",
    description: "Atomic units of work with typed input/output ports",
    icon: Box,
    to: "/work-blocks",
    color: "text-blue-400",
  },
  {
    title: "Flows",
    description: "Directed graphs connecting work blocks into workflows",
    icon: GitBranch,
    to: "/flows",
    color: "text-green-400",
  },
  {
    title: "Contracts",
    description: "Composable contracts with outcomes and assessments",
    icon: FileText,
    to: "/contracts",
    color: "text-purple-400",
  },
  {
    title: "Executions",
    description: "Monitor running processes and event history",
    icon: Play,
    to: "/executions",
    color: "text-orange-400",
  },
];

export default function Dashboard() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome to OpenOMA — the operational process framework
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {sections.map(({ title, description, icon: Icon, to, color }) => (
          <Link key={to} to={to}>
            <Card className="group transition-colors hover:border-primary/50">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">{title}</CardTitle>
                <Icon className={`h-5 w-5 ${color}`} />
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">{description}</p>
                <div className="mt-3 flex items-center gap-1 text-xs text-muted-foreground group-hover:text-primary">
                  <span>Browse</span>
                  <ArrowRight className="h-3 w-3" />
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
