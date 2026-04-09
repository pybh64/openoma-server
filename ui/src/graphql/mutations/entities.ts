import { gql } from "urql";

export const CREATE_WORK_BLOCK = gql`
  mutation CreateWorkBlock($input: CreateWorkBlockInput!) {
    createWorkBlock(input: $input) {
      id
      version
      name
      description
    }
  }
`;

export const UPDATE_WORK_BLOCK = gql`
  mutation UpdateWorkBlock($input: UpdateWorkBlockInput!) {
    updateWorkBlock(input: $input) {
      id
      version
      name
      description
    }
  }
`;

export const DELETE_WORK_BLOCK = gql`
  mutation DeleteWorkBlock($id: UUID!, $version: Int) {
    deleteWorkBlock(id: $id, version: $version)
  }
`;

export const CREATE_FLOW = gql`
  mutation CreateFlow($input: CreateFlowInput!) {
    createFlow(input: $input) {
      id
      version
      name
      description
    }
  }
`;

export const UPDATE_FLOW = gql`
  mutation UpdateFlow($input: UpdateFlowInput!) {
    updateFlow(input: $input) {
      id
      version
      name
      description
    }
  }
`;

export const DELETE_FLOW = gql`
  mutation DeleteFlow($id: UUID!, $version: Int) {
    deleteFlow(id: $id, version: $version)
  }
`;

export const CREATE_CONTRACT = gql`
  mutation CreateContract($input: CreateContractInput!) {
    createContract(input: $input) {
      id
      version
      name
      description
    }
  }
`;

export const UPDATE_CONTRACT = gql`
  mutation UpdateContract($input: UpdateContractInput!) {
    updateContract(input: $input) {
      id
      version
      name
      description
    }
  }
`;

export const DELETE_CONTRACT = gql`
  mutation DeleteContract($id: UUID!, $version: Int) {
    deleteContract(id: $id, version: $version)
  }
`;
