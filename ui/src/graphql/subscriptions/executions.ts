import { gql } from "urql";

export const EXECUTION_EVENTS_SUBSCRIPTION = gql`
  subscription ExecutionEvents($executionId: UUID) {
    executionEvents(executionId: $executionId) {
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
