import { gql } from "urql";

export const BLOCK_EXECUTION_QUERY = gql`
  query BlockExecution($executionId: UUID!) {
    blockExecution(executionId: $executionId) {
      id
      nodeReferenceId
      workBlockId
      workBlockVersion
      state
      events {
        id
        timestamp
        eventType
        executor {
          type
          identifier
        }
        payload
        metadata
      }
    }
  }
`;

export const FLOW_EXECUTION_QUERY = gql`
  query FlowExecution($executionId: UUID!) {
    flowExecution(executionId: $executionId) {
      id
      flowId
      flowVersion
      blockExecutionIds
      state
      events {
        id
        timestamp
        eventType
        executor {
          type
          identifier
        }
        payload
        metadata
      }
    }
  }
`;

export const BLOCK_EXECUTIONS_QUERY = gql`
  query BlockExecutions($flowExecutionId: UUID, $limit: Int, $offset: Int) {
    blockExecutions(flowExecutionId: $flowExecutionId, limit: $limit, offset: $offset) {
      executionId
      nodeReferenceId
      workBlockId
      workBlockVersion
      flowExecutionId
      createdAt
    }
  }
`;

export const EXECUTION_EVENTS_QUERY = gql`
  query ExecutionEvents($executionId: UUID!, $after: DateTime) {
    executionEvents(executionId: $executionId, after: $after) {
      id
      timestamp
      executionId
      eventType
      executor {
        type
        identifier
      }
      payload
      metadata
    }
  }
`;
