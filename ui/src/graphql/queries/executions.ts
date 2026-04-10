import { gql } from "urql";

export const FLOW_EXECUTIONS_QUERY = gql`
  query FlowExecutions($flowId: UUID, $state: String, $limit: Int, $offset: Int) {
    flowExecutions(flowId: $flowId, state: $state, limit: $limit, offset: $offset) {
      id flowId flowVersion state createdAt contractExecutionId
      blockExecutions { id nodeReferenceId workBlockId workBlockVersion state createdAt }
    }
  }
`;

export const FLOW_EXECUTION_QUERY = gql`
  query FlowExecution($id: UUID!) {
    flowExecution(id: $id) {
      id flowId flowVersion state createdAt contractExecutionId
      blockExecutions { id nodeReferenceId workBlockId workBlockVersion state createdAt }
    }
  }
`;

export const CONTRACT_EXECUTIONS_QUERY = gql`
  query ContractExecutions($contractId: UUID, $state: String, $limit: Int) {
    contractExecutions(contractId: $contractId, state: $state, limit: $limit) {
      id contractId contractVersion state createdAt
      flowExecutions { id flowId flowVersion state }
    }
  }
`;

export const EXECUTION_EVENTS_QUERY = gql`
  query ExecutionEvents($executionId: UUID!) {
    executionEvents(executionId: $executionId) {
      id timestamp executionId eventType
      executor { type identifier metadata }
      outcome { value metadata }
      metadata
    }
  }
`;
