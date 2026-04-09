import { gql } from "urql";

export const WORK_BLOCKS_QUERY = gql`
  query WorkBlocks($nameFilter: String, $limit: Int, $offset: Int, $latestOnly: Boolean) {
    workBlocks(nameFilter: $nameFilter, limit: $limit, offset: $offset, latestOnly: $latestOnly) {
      id
      version
      name
      description
      inputs {
        name
        description
        required
        schemaDef
      }
      outputs {
        name
        description
        required
        schemaDef
      }
      executionHints
      metadata
    }
  }
`;

export const WORK_BLOCK_QUERY = gql`
  query WorkBlock($id: UUID!, $version: Int) {
    workBlock(id: $id, version: $version) {
      id
      version
      name
      description
      inputs {
        name
        description
        required
        schemaDef
        metadata
      }
      outputs {
        name
        description
        required
        schemaDef
        metadata
      }
      executionHints
      metadata
    }
  }
`;

export const WORK_BLOCK_VERSIONS_QUERY = gql`
  query WorkBlockVersions($id: UUID!) {
    workBlockVersions(id: $id) {
      id
      version
      name
      description
    }
  }
`;

export const FLOWS_QUERY = gql`
  query Flows($nameFilter: String, $limit: Int, $offset: Int, $latestOnly: Boolean) {
    flows(nameFilter: $nameFilter, limit: $limit, offset: $offset, latestOnly: $latestOnly) {
      id
      version
      name
      description
      nodes {
        id
        targetId
        targetVersion
        alias
      }
      edges {
        sourceId
        targetId
        condition {
          description
        }
      }
      metadata
    }
  }
`;

export const FLOW_QUERY = gql`
  query Flow($id: UUID!, $version: Int) {
    flow(id: $id, version: $version) {
      id
      version
      name
      description
      nodes {
        id
        targetId
        targetVersion
        alias
        metadata
      }
      edges {
        sourceId
        targetId
        condition {
          description
          predicate
          metadata
        }
        portMappings {
          sourcePort
          targetPort
        }
      }
      expectedOutcome
      metadata
    }
  }
`;

export const CONTRACTS_QUERY = gql`
  query Contracts($nameFilter: String, $limit: Int, $offset: Int, $latestOnly: Boolean) {
    contracts(nameFilter: $nameFilter, limit: $limit, offset: $offset, latestOnly: $latestOnly) {
      id
      version
      name
      description
      workFlows {
        flowId
        flowVersion
        alias
      }
      subContracts {
        contractId
        contractVersion
        alias
      }
      requiredOutcomes {
        id
        name
        description
      }
      metadata
    }
  }
`;

export const CONTRACT_QUERY = gql`
  query Contract($id: UUID!, $version: Int) {
    contract(id: $id, version: $version) {
      id
      version
      name
      description
      workFlows {
        flowId
        flowVersion
        alias
        metadata
      }
      subContracts {
        contractId
        contractVersion
        alias
        metadata
      }
      requiredOutcomes {
        id
        name
        description
        metadata
      }
      assessmentBindings {
        requiredOutcomeId
        assessmentFlowId
        assessmentFlowVersion
        testFlowRefs {
          flowId
          flowVersion
          alias
        }
        metadata
      }
      metadata
    }
  }
`;
