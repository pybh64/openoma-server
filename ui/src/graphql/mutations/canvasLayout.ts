import { gql } from "urql";

export const SAVE_CANVAS_LAYOUT = gql`
  mutation SaveCanvasLayout($flowId: UUID!, $flowVersion: Int!, $input: SaveCanvasLayoutInput!) {
    saveCanvasLayout(flowId: $flowId, flowVersion: $flowVersion, input: $input) {
      flowId flowVersion
      nodePositions { nodeReferenceId x y width height }
      edgeLayouts { sourceId targetId bendPoints }
      viewport
      updatedAt
    }
  }
`;
