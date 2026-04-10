import { gql } from "urql";

export const CREATE_FLOW = gql`
  mutation CreateFlow($input: CreateFlowInput!) {
    createFlow(input: $input) {
      id version name description
      nodes { id targetId targetVersion alias }
      edges { sourceId targetId }
    }
  }
`;

export const UPDATE_FLOW = gql`
  mutation UpdateFlow($id: UUID!, $input: UpdateFlowInput!) {
    updateFlow(id: $id, input: $input) {
      id version name description
      nodes { id targetId targetVersion alias }
      edges { sourceId targetId }
    }
  }
`;
