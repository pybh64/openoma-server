import { gql } from "urql";

export const CREATE_WORK_BLOCK = gql`
  mutation CreateWorkBlock($input: CreateWorkBlockInput!) {
    createWorkBlock(input: $input) {
      id version name description
      inputs { name description required schemaDef metadata }
      outputs { name description required schemaDef metadata }
      executionHints
      expectedOutcome { name description }
      metadata
    }
  }
`;

export const UPDATE_WORK_BLOCK = gql`
  mutation UpdateWorkBlock($id: UUID!, $input: UpdateWorkBlockInput!) {
    updateWorkBlock(id: $id, input: $input) {
      id version name description
      inputs { name description required }
      outputs { name description required }
      executionHints
    }
  }
`;
