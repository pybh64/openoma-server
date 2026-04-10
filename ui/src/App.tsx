import { Routes, Route, Navigate } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppLayout } from "@/components/layout/AppLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { WorkBlocksPage } from "@/pages/WorkBlocksPage";
import { WorkBlockDetailPage } from "@/pages/WorkBlockDetailPage";
import { FlowsPage } from "@/pages/FlowsPage";
import { FlowCanvasPage } from "@/pages/FlowCanvasPage";
import { FlowDraftCanvasPage } from "@/pages/FlowDraftCanvasPage";
import { ContractsPage } from "@/pages/ContractsPage";
import { ContractDetailPage } from "@/pages/ContractDetailPage";
import { ExecutionsPage } from "@/pages/ExecutionsPage";
import { FlowExecutionPage } from "@/pages/FlowExecutionPage";

export function App() {
  return (
    <TooltipProvider delayDuration={300}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/work-blocks" element={<WorkBlocksPage />} />
          <Route path="/work-blocks/:id" element={<WorkBlockDetailPage />} />
          <Route path="/flows" element={<FlowsPage />} />
          <Route path="/flows/:id" element={<FlowCanvasPage />} />
          <Route path="/flows/:id/v/:version" element={<FlowCanvasPage />} />
          <Route path="/drafts/:draftId" element={<FlowDraftCanvasPage />} />
          <Route path="/contracts" element={<ContractsPage />} />
          <Route path="/contracts/:id" element={<ContractDetailPage />} />
          <Route path="/executions" element={<ExecutionsPage />} />
          <Route path="/executions/flow/:id" element={<FlowExecutionPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </TooltipProvider>
  );
}
