import { gql } from "urql";

export const WORK_BLOCKS_QUERY = gql`
  query WorkBlocks($name: String, $limit: Int, $offset: Int) {
    workBlocks(name: $name, limit: $limit, offset: $offset) {
      id version createdAt name description
      inputs { name description required }
      outputs { name description required }
      executionHints
      expectedOutcome { name description }
      metadata
    }
  }
`;

export const WORK_BLOCK_QUERY = gql`
  query WorkBlock($id: UUID!, $version: Int) {
    workBlock(id: $id, version: $version) {
      id version createdAt createdBy name description
      inputs { name description required schemaDef metadata }
      outputs { name description required schemaDef metadata }
      executionHints
      expectedOutcome { name description schemaDef metadata }
      metadata
    }
  }
`;

export const WORK_BLOCKS_CONNECTION = gql`
  query WorkBlocksConnection($first: Int, $after: String, $filter: WorkBlockFilter, $orderBy: WorkBlockOrderBy, $orderDirection: OrderDirection) {
    workBlocksConnection(first: $first, after: $after, filter: $filter, orderBy: $orderBy, orderDirection: $orderDirection) {
      edges { node { id version name description executionHints createdAt } cursor }
      pageInfo { hasNextPage hasPreviousPage startCursor endCursor }
      totalCount
    }
  }
`;

export const WORK_BLOCK_SEARCH = gql`
  query WorkBlockSearch($name: String, $limit: Int) {
    workBlocks(name: $name, limit: $limit) {
      id version name description executionHints
      inputs { name description required }
      outputs { name description required }
    }
  }
`;
