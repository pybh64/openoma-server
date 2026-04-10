import { gql } from "urql";

export const FLOW_DRAFT_QUERY = gql`
  query FlowDraft($draftId: UUID!) {
    flowDraft(draftId: $draftId) {
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
      expectedOutcome { name description }
      metadata
      nodePositions edgeLayouts viewport
      createdAt updatedAt createdBy
    }
  }
`;

export const FLOW_DRAFTS_QUERY = gql`
  query FlowDrafts($baseFlowId: UUID, $limit: Int, $offset: Int) {
    flowDrafts(baseFlowId: $baseFlowId, limit: $limit, offset: $offset) {
      draftId baseFlowId baseFlowVersion name description
      nodes { id targetId targetVersion alias }
      edges { sourceId targetId }
      createdAt updatedAt
    }
  }
`;
