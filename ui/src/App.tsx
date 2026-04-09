import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Provider as UrqlProvider } from "urql";
import { TooltipProvider } from "@/components/ui/tooltip";
import { graphqlClient } from "@/graphql/client";
import { AppShell } from "@/components/layout/AppShell";
import { Skeleton } from "@/components/ui/skeleton";

const Dashboard = lazy(() => import("@/pages/Dashboard"));
const WorkBlockList = lazy(() => import("@/pages/work-blocks/WorkBlockList"));
const WorkBlockDetail = lazy(() => import("@/pages/work-blocks/WorkBlockDetail"));
const WorkBlockForm = lazy(() => import("@/pages/work-blocks/WorkBlockForm"));
const FlowList = lazy(() => import("@/pages/flows/FlowList"));
const FlowDetail = lazy(() => import("@/pages/flows/FlowDetail"));
const FlowEditor = lazy(() => import("@/pages/flows/FlowEditor"));
const ContractList = lazy(() => import("@/pages/contracts/ContractList"));
const ContractDetail = lazy(() => import("@/pages/contracts/ContractDetail"));
const ContractForm = lazy(() => import("@/pages/contracts/ContractForm"));
const ExecutionList = lazy(() => import("@/pages/executions/ExecutionList"));
const ExecutionDetail = lazy(() => import("@/pages/executions/ExecutionDetail"));

function PageLoader() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-4 w-96" />
      <div className="mt-6 space-y-3">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    </div>
  );
}

function P({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>;
}

export default function App() {
  return (
    <UrqlProvider value={graphqlClient}>
      <TooltipProvider delayDuration={200}>
        <BrowserRouter>
          <Routes>
            {/* Flow editor is full-screen, outside the shell */}
            <Route path="flows/new" element={<P><FlowEditor /></P>} />
            <Route path="flows/:id/edit" element={<P><FlowEditor /></P>} />

            <Route element={<AppShell />}>
              <Route index element={<P><Dashboard /></P>} />

              <Route path="work-blocks" element={<P><WorkBlockList /></P>} />
              <Route path="work-blocks/new" element={<P><WorkBlockForm /></P>} />
              <Route path="work-blocks/:id" element={<P><WorkBlockDetail /></P>} />
              <Route path="work-blocks/:id/edit" element={<P><WorkBlockForm /></P>} />

              <Route path="flows" element={<P><FlowList /></P>} />
              <Route path="flows/:id" element={<P><FlowDetail /></P>} />

              <Route path="contracts" element={<P><ContractList /></P>} />
              <Route path="contracts/new" element={<P><ContractForm /></P>} />
              <Route path="contracts/:id" element={<P><ContractDetail /></P>} />
              <Route path="contracts/:id/edit" element={<P><ContractForm /></P>} />

              <Route path="executions" element={<P><ExecutionList /></P>} />
              <Route path="executions/:type/:id" element={<P><ExecutionDetail /></P>} />
            </Route>
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </UrqlProvider>
  );
}
