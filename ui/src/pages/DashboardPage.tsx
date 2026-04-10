import { useQuery } from "urql";
import { Link } from "react-router-dom";
import { Blocks, GitBranch, FileText, Activity, ArrowRight } from "lucide-react";
import { gql } from "urql";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/PageHeader";
import { LoadingState } from "@/components/shared/StateDisplay";

const DASHBOARD_QUERY = gql`
  query Dashboard {
    workBlocks(limit: 5) { id name version description }
    flows(limit: 5) { id name version description nodes { id } edges { sourceId } }
    contracts(limit: 5) { id name version description workFlows { flowId } subContracts { contractId } }
  }
`;

export function DashboardPage() {
  const [{ data, fetching }] = useQuery({ query: DASHBOARD_QUERY });

  if (fetching) return <LoadingState />;

  const workBlocks = data?.workBlocks ?? [];
  const flows = data?.flows ?? [];
  const contracts = data?.contracts ?? [];

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of your OpenOMA operational model"
      />

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard icon={<Blocks className="h-5 w-5" />} label="Work Blocks" count={workBlocks.length} href="/work-blocks" />
          <StatCard icon={<GitBranch className="h-5 w-5" />} label="Flows" count={flows.length} href="/flows" />
          <StatCard icon={<FileText className="h-5 w-5" />} label="Contracts" count={contracts.length} href="/contracts" />
          <StatCard icon={<Activity className="h-5 w-5" />} label="Executions" count={0} href="/executions" />
        </div>

        {/* Recent items */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <RecentList
            title="Recent Work Blocks"
            items={workBlocks}
            href="/work-blocks"
            renderItem={(wb: { id: string; name: string; description: string }) => (
              <Link to={`/work-blocks/${wb.id}`} className="block p-3 rounded-md hover:bg-muted transition-colors">
                <div className="font-medium text-sm">{wb.name}</div>
                <div className="text-xs text-muted-foreground truncate">{wb.description}</div>
              </Link>
            )}
          />
          <RecentList
            title="Recent Flows"
            items={flows}
            href="/flows"
            renderItem={(f: { id: string; name: string; nodes: unknown[]; edges: unknown[] }) => (
              <Link to={`/flows/${f.id}`} className="block p-3 rounded-md hover:bg-muted transition-colors">
                <div className="font-medium text-sm">{f.name}</div>
                <div className="text-xs text-muted-foreground">
                  {f.nodes.length} nodes · {f.edges.length} edges
                </div>
              </Link>
            )}
          />
          <RecentList
            title="Recent Contracts"
            items={contracts}
            href="/contracts"
            renderItem={(c: { id: string; name: string; workFlows: unknown[]; subContracts: unknown[] }) => (
              <Link to={`/contracts/${c.id}`} className="block p-3 rounded-md hover:bg-muted transition-colors">
                <div className="font-medium text-sm">{c.name}</div>
                <div className="text-xs text-muted-foreground">
                  {c.workFlows.length} flows · {c.subContracts.length} sub-contracts
                </div>
              </Link>
            )}
          />
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, count, href }: { icon: React.ReactNode; label: string; count: number; href: string }) {
  return (
    <Link to={href}>
      <Card className="hover:border-primary/30 transition-colors">
        <CardContent className="flex items-center gap-4 p-4">
          <div className="rounded-lg bg-primary/10 p-2.5 text-primary">{icon}</div>
          <div>
            <div className="text-2xl font-bold">{count}</div>
            <div className="text-sm text-muted-foreground">{label}</div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function RecentList<T extends { id: string }>({
  title,
  items,
  href,
  renderItem,
}: {
  title: string;
  items: T[];
  href: string;
  renderItem: (item: T) => React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{title}</CardTitle>
          <Link to={href} className="text-xs text-primary flex items-center gap-1 hover:underline">
            View all <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      </CardHeader>
      <CardContent className="space-y-1">
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">No items yet</p>
        ) : (
          items.map((item) => <div key={item.id}>{renderItem(item)}</div>)
        )}
      </CardContent>
    </Card>
  );
}
