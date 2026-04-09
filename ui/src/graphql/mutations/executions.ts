import { gql } from "urql";

export const START_BLOCK_EXECUTION = gql`
  mutation StartBlockExecution($input: StartBlockExecutionInput!) {
    startBlockExecution(input: $input) {
      id
      nodeReferenceId
      workBlockId
      workBlockVersion
      state
    }
  }
`;

export const START_FLOW_EXECUTION = gql`
  mutation StartFlowExecution($input: StartFlowExecutionInput!) {
    startFlowExecution(input: $input) {
      id
      flowId
      flowVersion
      state
    }
  }
`;

export const START_CONTRACT_EXECUTION = gql`
  mutation StartContractExecution($input: StartContractExecutionInput!) {
    startContractExecution(input: $input) {
      id
      contractId
      contractVersion
      state
    }
  }
`;

export const EMIT_EXECUTION_EVENT = gql`
  mutation EmitExecutionEvent($input: EmitExecutionEventInput!) {
    emitExecutionEvent(input: $input) {
      id
      timestamp
      eventType
      payload
    }
  }
`;
