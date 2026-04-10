/* ─── Domain types matching the GraphQL schema ─── */

export interface PortDescriptor {
  name: string;
  description: string;
  required: boolean;
  schemaDef: unknown | null;
  metadata: Record<string, unknown>;
}

export interface ExpectedOutcome {
  name: string;
  description: string;
  schemaDef: unknown | null;
  metadata: Record<string, unknown>;
}

export interface WorkBlock {
  id: string;
  version: number;
  createdAt: string;
  createdBy: string | null;
  name: string;
  description: string;
  inputs: PortDescriptor[];
  outputs: PortDescriptor[];
  executionHints: string[];
  expectedOutcome: ExpectedOutcome | null;
  metadata: Record<string, unknown>;
}

export interface WorkBlockSummary {
  id: string;
  version: number;
  name: string;
  description: string;
  executionHints: string[];
}

export interface Condition {
  description: string;
  predicate: unknown | null;
  metadata: Record<string, unknown>;
}

export interface PortMapping {
  sourcePort: string;
  targetPort: string;
}

export interface NodeReference {
  id: string;
  targetId: string;
  targetVersion: number;
  alias: string | null;
  metadata: Record<string, unknown>;
  workBlock?: WorkBlock | null;
}

export interface Edge {
  sourceId: string | null;
  targetId: string;
  condition: Condition | null;
  portMappings: PortMapping[];
}

export interface Flow {
  id: string;
  version: number;
  createdAt: string;
  createdBy: string | null;
  name: string;
  description: string;
  nodes: NodeReference[];
  edges: Edge[];
  expectedOutcome: ExpectedOutcome | null;
  metadata: Record<string, unknown>;
}

export interface FlowDraft {
  draftId: string;
  baseFlowId: string | null;
  baseFlowVersion: number | null;
  name: string;
  description: string;
  nodes: NodeReference[];
  edges: Edge[];
  expectedOutcome: ExpectedOutcome | null;
  metadata: Record<string, unknown>;
  nodePositions: NodePositionData[];
  edgeLayouts: EdgeLayoutData[];
  viewport: ViewportData;
  createdAt: string;
  updatedAt: string;
  createdBy: string | null;
}

export interface NodePositionData {
  nodeReferenceId: string;
  x: number;
  y: number;
  width?: number | null;
  height?: number | null;
  metadata?: Record<string, unknown>;
}

export interface EdgeLayoutData {
  sourceId: string | null;
  targetId: string;
  bendPoints: unknown[];
  labelPosition: unknown | null;
  metadata?: Record<string, unknown>;
}

export interface ViewportData {
  x: number;
  y: number;
  zoom: number;
}

export interface CanvasLayout {
  flowId: string;
  flowVersion: number;
  nodePositions: NodePositionData[];
  edgeLayouts: EdgeLayoutData[];
  viewport: ViewportData;
  updatedAt: string;
  updatedBy: string | null;
}

export interface Party {
  name: string;
  role: string;
  contact: string | null;
}

export interface FlowReference {
  flowId: string;
  flowVersion: number;
  alias: string | null;
  metadata: Record<string, unknown>;
}

export interface ContractReference {
  contractId: string;
  contractVersion: number;
  alias: string | null;
  metadata: Record<string, unknown>;
}

export interface RequiredOutcomeReference {
  requiredOutcomeId: string;
  requiredOutcomeVersion: number;
  alias: string | null;
  metadata: Record<string, unknown>;
}

export interface AssessmentBinding {
  assessmentFlow: FlowReference;
  testFlowRefs: FlowReference[];
  metadata: Record<string, unknown>;
}

export interface RequiredOutcome {
  id: string;
  version: number;
  createdAt: string;
  createdBy: string | null;
  name: string;
  description: string;
  assessmentBindings: AssessmentBinding[];
  metadata: Record<string, unknown>;
}

export interface Contract {
  id: string;
  version: number;
  createdAt: string;
  createdBy: string | null;
  name: string;
  description: string;
  owners: Party[];
  workFlows: FlowReference[];
  subContracts: ContractReference[];
  requiredOutcomes: RequiredOutcomeReference[];
  metadata: Record<string, unknown>;
}

export interface ExecutorInfo {
  type: string;
  identifier: string;
  metadata: Record<string, unknown>;
}

export interface ExecutionOutcome {
  value: unknown | null;
  metadata: Record<string, unknown>;
}

export interface ExecutionEvent {
  id: string;
  timestamp: string;
  executionId: string;
  eventType: string;
  executor: ExecutorInfo | null;
  outcome: ExecutionOutcome | null;
  metadata: Record<string, unknown>;
}

export interface BlockExecution {
  id: string;
  flowExecutionId: string | null;
  nodeReferenceId: string;
  workBlockId: string;
  workBlockVersion: number;
  state: string;
  createdAt: string;
}

export interface FlowExecution {
  id: string;
  contractExecutionId: string | null;
  flowId: string;
  flowVersion: number;
  blockExecutions: BlockExecution[];
  state: string;
  createdAt: string;
}

export interface ContractExecution {
  id: string;
  contractId: string;
  contractVersion: number;
  flowExecutions: FlowExecution[];
  subContractExecutions: ContractExecution[];
  state: string;
  createdAt: string;
}

export interface NodeExecutionState {
  nodeReferenceId: string;
  blockExecutionId: string | null;
  state: string | null;
  executor: ExecutorInfo | null;
  latestEvent: ExecutionEvent | null;
}

export interface FlowCanvasData {
  flow: Flow;
  layout: CanvasLayout | null;
  workBlockSummaries: WorkBlockSummary[];
}

export interface FlowExecutionCanvasData {
  flow: Flow;
  layout: CanvasLayout | null;
  execution: FlowExecution;
  nodeStates: NodeExecutionState[];
}

export interface PageInfo {
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
  endCursor: string | null;
}

export interface Connection<T> {
  edges: { node: T; cursor: string }[];
  pageInfo: PageInfo;
  totalCount: number;
}
