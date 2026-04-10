import { useState, useCallback, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "urql";
import { v4 as uuidv4 } from "uuid";
import { FLOW_DRAFT_QUERY } from "@/graphql/queries/flowDrafts";
import {
  PUBLISH_FLOW_DRAFT,
  DISCARD_FLOW_DRAFT,
  ADD_NODE_TO_DRAFT,
  REMOVE_NODE_FROM_DRAFT,
  ADD_EDGE_TO_DRAFT,
  UPDATE_NODE_POSITIONS,
} from "@/graphql/mutations/flowDrafts";
import { DraftCanvas } from "@/components/canvas/DraftCanvas";
import { DraftToolbar } from "@/components/canvas/panels/DraftToolbar";
import { WorkBlockSearchPanel } from "@/components/canvas/panels/WorkBlockSearchPanel";
import { NodeDetailPanel } from "@/components/canvas/panels/NodeDetailPanel";
import { useDraftStore } from "@/stores/draftStore";
import { useCanvasStore } from "@/stores/canvasStore";
import { LoadingState, ErrorState } from "@/components/shared/StateDisplay";
import type { NodePositionData, NodeReference } from "@/types";

export function FlowDraftCanvasPage() {
  const { draftId } = useParams<{ draftId: string }>();
  const navigate = useNavigate();
  const { draft, setDraft, isDirty, selectedNodeId, selectNode } = useDraftStore();
  const { searchPanelOpen } = useCanvasStore();

  const [{ data, fetching, error }] = useQuery({
    query: FLOW_DRAFT_QUERY,
    variables: { draftId },
    pause: !draftId,
  });

  const [, publishDraft] = useMutation(PUBLISH_FLOW_DRAFT);
  const [, discardDraft] = useMutation(DISCARD_FLOW_DRAFT);
  const [, addNode] = useMutation(ADD_NODE_TO_DRAFT);
  const [, removeNode] = useMutation(REMOVE_NODE_FROM_DRAFT);
  const [, addEdge] = useMutation(ADD_EDGE_TO_DRAFT);
  const [, updatePositions] = useMutation(UPDATE_NODE_POSITIONS);
  const [publishing, setPublishing] = useState(false);

  // Sync server data to store
  useEffect(() => {
    if (data?.flowDraft) {
      setDraft(data.flowDraft);
    }
  }, [data?.flowDraft, setDraft]);

  const handleAddBlock = useCallback(
    async (block: { id: string; version: number; name: string }) => {
      if (!draftId) return;
      const nodeRefId = uuidv4();
      const result = await addNode({
        draftId,
        node: {
          id: nodeRefId,
          targetId: block.id,
          targetVersion: block.version,
          alias: null,
          metadata: {},
        },
        position: {
          nodeReferenceId: nodeRefId,
          x: 300 + Math.random() * 200,
          y: 150 + Math.random() * 200,
        },
      });
      if (result.data?.addNodeToDraft) {
        setDraft(result.data.addNodeToDraft);
      }
    },
    [draftId, addNode, setDraft]
  );

  const handleRemoveNode = useCallback(
    async (nodeReferenceId: string) => {
      if (!draftId) return;
      const result = await removeNode({ draftId, nodeReferenceId });
      if (result.data?.removeNodeFromDraft) {
        setDraft(result.data.removeNodeFromDraft);
        selectNode(null);
      }
    },
    [draftId, removeNode, setDraft, selectNode]
  );

  const handleConnect = useCallback(
    async (source: string, target: string) => {
      if (!draftId) return;
      const result = await addEdge({
        draftId,
        edge: {
          sourceId: source || null,
          targetId: target,
          portMappings: [],
        },
      });
      if (result.data?.addEdgeToDraft) {
        setDraft(result.data.addEdgeToDraft);
      }
    },
    [draftId, addEdge, setDraft]
  );

  const handleSavePositions = useCallback(async () => {
    if (!draftId || !draft) return;
    const result = await updatePositions({
      draftId,
      positions: draft.nodePositions.map((p) => ({
        nodeReferenceId: (p as any).nodeReferenceId ?? (p as any).node_reference_id,
        x: p.x,
        y: p.y,
      })),
    });
    if (result.data?.updateNodePositions) {
      setDraft(result.data.updateNodePositions);
    }
  }, [draftId, draft, updatePositions, setDraft]);

  const handlePositionChange = useCallback(
    (positions: NodePositionData[]) => {
      useDraftStore.getState().updatePositions(positions);
    },
    []
  );

  const handlePublish = useCallback(async () => {
    if (!draftId) return;
    setPublishing(true);
    try {
      const result = await publishDraft({ draftId });
      if (result.data?.publishFlowDraft) {
        const flow = result.data.publishFlowDraft;
        navigate(`/flows/${flow.id}`);
      } else if (result.error) {
        alert(`Publish failed: ${result.error.message}`);
      }
    } finally {
      setPublishing(false);
    }
  }, [draftId, publishDraft, navigate]);

  const handleDiscard = useCallback(async () => {
    if (!draftId) return;
    if (!confirm("Discard this draft? This cannot be undone.")) return;
    await discardDraft({ draftId });
    navigate("/flows");
  }, [draftId, discardDraft, navigate]);

  if (fetching) return <LoadingState message="Loading draft..." />;
  if (error) return <ErrorState message={error.message} />;
  if (!draft) return <ErrorState message="Draft not found" />;

  const selectedNode = selectedNodeId
    ? draft.nodes.find((n: NodeReference) => n.id === selectedNodeId) ?? null
    : null;

  return (
    <div className="flex flex-col h-full">
      <DraftToolbar
        draftName={draft.name}
        isDirty={isDirty}
        nodeCount={draft.nodes.length}
        edgeCount={draft.edges.length}
        onPublish={handlePublish}
        onDiscard={handleDiscard}
        onSavePositions={handleSavePositions}
        publishing={publishing}
      />

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1">
          <DraftCanvas
            draft={draft}
            onConnect={handleConnect}
            onNodeSelect={selectNode}
            onNodesPositionChange={handlePositionChange}
          />
        </div>

        {searchPanelOpen && <WorkBlockSearchPanel onAddBlock={handleAddBlock} />}

        {selectedNode && !searchPanelOpen && (
          <NodeDetailPanel
            node={selectedNode}
            edges={draft.edges}
            allNodes={draft.nodes}
            onClose={() => selectNode(null)}
            onRemoveNode={handleRemoveNode}
          />
        )}
      </div>
    </div>
  );
}
