import { gql } from "urql";

export const CREATE_FLOW_EXECUTION = gql`
  mutation CreateFlowExecution($input: CreateFlowExecutionInput!) {
    createFlowExecution(input: $input) {
      id flowId flowVersion state createdAt
    }
  }
`;

export const CREATE_BLOCK_EXECUTION = gql`
  mutation CreateBlockExecution($input: CreateBlockExecutionInput!) {
    createBlockExecution(input: $input) {
      id workBlockId workBlockVersion nodeReferenceId state createdAt
    }
  }
`;

export const ASSIGN_EXECUTOR = gql`
  mutation AssignExecutor($executionId: UUID!, $executor: ExecutorInfoInput!) {
    assignExecutorToBlock(executionId: $executionId, executor: $executor) {
      id state
    }
  }
`;

export const START_BLOCK_EXECUTION = gql`
  mutation StartBlockExecution($executionId: UUID!) {
    startBlockExecution(executionId: $executionId) { id state }
  }
`;

export const COMPLETE_BLOCK_EXECUTION = gql`
  mutation CompleteBlockExecution($executionId: UUID!) {
    completeBlockExecution(executionId: $executionId) { id state }
  }
`;

export const FAIL_BLOCK_EXECUTION = gql`
  mutation FailBlockExecution($executionId: UUID!, $metadata: JSON) {
    failBlockExecution(executionId: $executionId, metadata: $metadata) { id state }
  }
`;

export const ADD_BLOCK_TO_FLOW_EXECUTION = gql`
  mutation AddBlockToFlowExecution($flowExecutionId: UUID!, $blockExecutionId: UUID!) {
    addBlockToFlowExecution(flowExecutionId: $flowExecutionId, blockExecutionId: $blockExecutionId) {
      id state blockExecutions { id nodeReferenceId state }
    }
  }
`;

export const REFRESH_FLOW_STATE = gql`
  mutation RefreshFlowState($flowExecutionId: UUID!) {
    refreshFlowState(flowExecutionId: $flowExecutionId) {
      id state blockExecutions { id nodeReferenceId state }
    }
  }
`;
