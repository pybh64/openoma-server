import { gql } from "urql";

export const FLOWS_QUERY = gql`
  query Flows($name: String, $limit: Int, $offset: Int) {
    flows(name: $name, limit: $limit, offset: $offset) {
      id version createdAt name description
      nodes { id targetId targetVersion alias }
      edges { sourceId targetId }
      metadata
    }
  }
`;

export const FLOW_QUERY = gql`
  query Flow($id: UUID!, $version: Int) {
    flow(id: $id, version: $version) {
      id version createdAt createdBy name description
      nodes {
        id targetId targetVersion alias metadata
        workBlock { id version name description executionHints inputs { name description required } outputs { name description required } }
      }
      edges {
        sourceId targetId
        condition { description predicate metadata }
        portMappings { sourcePort targetPort }
      }
      expectedOutcome { name description }
      metadata
    }
  }
`;

export const FLOWS_CONNECTION = gql`
  query FlowsConnection($first: Int, $after: String, $filter: FlowFilter, $orderBy: FlowOrderBy, $orderDirection: OrderDirection) {
    flowsConnection(first: $first, after: $after, filter: $filter, orderBy: $orderBy, orderDirection: $orderDirection) {
      edges { node { id version name description createdAt nodes { id targetId } edges { sourceId targetId } } cursor }
      pageInfo { hasNextPage hasPreviousPage startCursor endCursor }
      totalCount
    }
  }
`;

export const FLOW_CANVAS_QUERY = gql`
  query FlowCanvas($flowId: UUID!, $flowVersion: Int) {
    flowCanvas(flowId: $flowId, flowVersion: $flowVersion) {
      flow {
        id version name description createdAt
        nodes {
          id targetId targetVersion alias metadata
          workBlock { id version name description executionHints inputs { name description required } outputs { name description required } }
        }
        edges {
          sourceId targetId
          condition { description predicate metadata }
          portMappings { sourcePort targetPort }
        }
        expectedOutcome { name description }
        metadata
      }
      layout {
        flowId flowVersion
        nodePositions { nodeReferenceId x y width height metadata }
        edgeLayouts { sourceId targetId bendPoints labelPosition metadata }
        viewport
        updatedAt
      }
      workBlockSummaries {
        id version name description executionHints
      }
    }
  }
`;

export const FLOW_EXECUTION_CANVAS_QUERY = gql`
  query FlowExecutionCanvas($flowExecutionId: UUID!) {
    flowExecutionCanvas(flowExecutionId: $flowExecutionId) {
      flow {
        id version name description
        nodes { id targetId targetVersion alias metadata workBlock { id version name description } }
        edges { sourceId targetId condition { description } }
      }
      layout {
        nodePositions { nodeReferenceId x y width height }
        edgeLayouts { sourceId targetId bendPoints }
        viewport
      }
      execution { id flowId flowVersion state createdAt }
      nodeStates {
        nodeReferenceId blockExecutionId state
        executor { type identifier }
        latestEvent { id timestamp eventType }
      }
    }
  }
`;
