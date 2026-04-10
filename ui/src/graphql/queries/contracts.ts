import { gql } from "urql";

export const CONTRACTS_QUERY = gql`
  query Contracts($name: String, $limit: Int, $offset: Int) {
    contracts(name: $name, limit: $limit, offset: $offset) {
      id version createdAt name description
      owners { name role contact }
      workFlows { flowId flowVersion alias }
      subContracts { contractId contractVersion alias }
      requiredOutcomes { requiredOutcomeId requiredOutcomeVersion alias }
      metadata
    }
  }
`;

export const CONTRACT_QUERY = gql`
  query Contract($id: UUID!, $version: Int) {
    contract(id: $id, version: $version) {
      id version createdAt createdBy name description
      owners { name role contact }
      workFlows { flowId flowVersion alias metadata }
      subContracts { contractId contractVersion alias metadata }
      requiredOutcomes { requiredOutcomeId requiredOutcomeVersion alias metadata }
      metadata
    }
  }
`;

export const CONTRACTS_CONNECTION = gql`
  query ContractsConnection($first: Int, $after: String, $filter: ContractFilter, $orderBy: ContractOrderBy, $orderDirection: OrderDirection) {
    contractsConnection(first: $first, after: $after, filter: $filter, orderBy: $orderBy, orderDirection: $orderDirection) {
      edges {
        node {
          id version name description createdAt
          owners { name role }
          workFlows { flowId flowVersion alias }
          subContracts { contractId contractVersion alias }
        }
        cursor
      }
      pageInfo { hasNextPage hasPreviousPage startCursor endCursor }
      totalCount
    }
  }
`;

export const REQUIRED_OUTCOMES_QUERY = gql`
  query RequiredOutcomes($name: String, $limit: Int, $offset: Int) {
    requiredOutcomes(name: $name, limit: $limit, offset: $offset) {
      id version createdAt name description
      assessmentBindings { assessmentFlow { flowId flowVersion alias } testFlowRefs { flowId flowVersion alias } }
      metadata
    }
  }
`;
