import { gql } from "urql";

export const CREATE_CONTRACT = gql`
  mutation CreateContract($input: CreateContractInput!) {
    createContract(input: $input) {
      id version name description
      owners { name role contact }
      workFlows { flowId flowVersion alias }
      subContracts { contractId contractVersion alias }
      requiredOutcomes { requiredOutcomeId requiredOutcomeVersion alias }
    }
  }
`;

export const UPDATE_CONTRACT = gql`
  mutation UpdateContract($id: UUID!, $input: UpdateContractInput!) {
    updateContract(id: $id, input: $input) {
      id version name description
      owners { name role contact }
      workFlows { flowId flowVersion alias }
      subContracts { contractId contractVersion alias }
      requiredOutcomes { requiredOutcomeId requiredOutcomeVersion alias }
    }
  }
`;
