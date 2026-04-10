import { gql } from "urql";

const DRAFT_FIELDS = `
  draftId baseFlowId baseFlowVersion name description
  nodes {
    id targetId targetVersion alias metadata
    workBlock { id version name description executionHints inputs { name description required } outputs { name description required } }
  }
  edges {
    sourceId targetId
    condition { description predicate metadata }
    portMappings { sourcePort targetPort }
  }
  nodePositions edgeLayouts viewport
  createdAt updatedAt
`;

export const CREATE_FLOW_DRAFT = gql`
  mutation CreateFlowDraft($flowId: UUID!, $flowVersion: Int!) {
    createFlowDraft(flowId: $flowId, flowVersion: $flowVersion) { ${DRAFT_FIELDS} }
  }
`;

export const CREATE_BLANK_FLOW_DRAFT = gql`
  mutation CreateBlankFlowDraft($name: String!) {
    createBlankFlowDraft(name: $name) { ${DRAFT_FIELDS} }
  }
`;

export const PUBLISH_FLOW_DRAFT = gql`
  mutation PublishFlowDraft($draftId: UUID!) {
    publishFlowDraft(draftId: $draftId) {
      id version name description
      nodes { id targetId targetVersion alias }
      edges { sourceId targetId }
    }
  }
`;

export const DISCARD_FLOW_DRAFT = gql`
  mutation DiscardFlowDraft($draftId: UUID!) {
    discardFlowDraft(draftId: $draftId)
  }
`;

export const ADD_NODE_TO_DRAFT = gql`
  mutation AddNodeToDraft($draftId: UUID!, $node: NodeReferenceInput!, $position: NodePositionInput) {
    addNodeToDraft(draftId: $draftId, node: $node, position: $position) { ${DRAFT_FIELDS} }
  }
`;

export const REMOVE_NODE_FROM_DRAFT = gql`
  mutation RemoveNodeFromDraft($draftId: UUID!, $nodeReferenceId: UUID!) {
    removeNodeFromDraft(draftId: $draftId, nodeReferenceId: $nodeReferenceId) { ${DRAFT_FIELDS} }
  }
`;

export const ADD_EDGE_TO_DRAFT = gql`
  mutation AddEdgeToDraft($draftId: UUID!, $edge: EdgeInput!) {
    addEdgeToDraft(draftId: $draftId, edge: $edge) { ${DRAFT_FIELDS} }
  }
`;

export const REMOVE_EDGE_FROM_DRAFT = gql`
  mutation RemoveEdgeFromDraft($draftId: UUID!, $sourceId: UUID, $targetId: UUID!) {
    removeEdgeFromDraft(draftId: $draftId, sourceId: $sourceId, targetId: $targetId) { ${DRAFT_FIELDS} }
  }
`;

export const UPDATE_NODE_POSITIONS = gql`
  mutation UpdateNodePositions($draftId: UUID!, $positions: [NodePositionInput!]!) {
    updateNodePositions(draftId: $draftId, positions: $positions) { ${DRAFT_FIELDS} }
  }
`;

export const UPDATE_VIEWPORT = gql`
  mutation UpdateViewport($draftId: UUID!, $viewport: JSON!) {
    updateViewport(draftId: $draftId, viewport: $viewport) { ${DRAFT_FIELDS} }
  }
`;
