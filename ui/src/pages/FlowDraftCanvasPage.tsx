import { useState, useCallback, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "urql";
import { v4 as uuidv4 } from "uuid";
import { FLOW_DRAFT_QUERY } from "@/graphql/queries/flowDrafts";
import { UPDATE_WORK_BLOCK } from "@/graphql/mutations/workBlocks";
import {
  PUBLISH_FLOW_DRAFT,
  DISCARD_FLOW_DRAFT,
  ADD_NODE_TO_DRAFT,
  REMOVE_NODE_FROM_DRAFT,
  ADD_EDGE_TO_DRAFT,
  REMOVE_EDGE_FROM_DRAFT,
  UPDATE_EDGE_IN_DRAFT,
  UPDATE_NODE_POSITIONS,
  UPDATE_NODE_IN_DRAFT,
} from "@/graphql/mutations/flowDrafts";
import { DraftCanvas } from "@/components/canvas/DraftCanvas";
import { EdgeDetailPanel } from "@/components/canvas/panels/EdgeDetailPanel";
import { DraftToolbar } from "@/components/canvas/panels/DraftToolbar";
import { WorkBlockSearchPanel } from "@/components/canvas/panels/WorkBlockSearchPanel";
import { NodeDetailPanel } from "@/components/canvas/panels/NodeDetailPanel";
import { WorkBlockFormDialog } from "@/components/work-blocks/WorkBlockFormDialog";
import { useDraftStore } from "@/stores/draftStore";
import { useCanvasStore } from "@/stores/canvasStore";
import { LoadingState, ErrorState } from "@/components/shared/StateDisplay";
import type { NodePositionData, NodeReference } from "@/types";

function getNodePositionId(position: NodePositionData & { node_reference_id?: string }): string {
  return position.nodeReferenceId ?? position.node_reference_id ?? "";
}

export function FlowDraftCanvasPage() {
  const { draftId } = useParams<{ draftId: string }>();
  const navigate = useNavigate();
  const {
    draft,
    setDraft,
    isDirty,
    selectedNodeId,
    selectedEdge,
    selectNode,
    selectEdge,
  } = useDraftStore();
  const { searchPanelOpen, setSearchPanelOpen } = useCanvasStore();

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
  const [, removeEdge] = useMutation(REMOVE_EDGE_FROM_DRAFT);
  const [, updateEdge] = useMutation(UPDATE_EDGE_IN_DRAFT);
  const [, updatePositions] = useMutation(UPDATE_NODE_POSITIONS);
  const [, updateNode] = useMutation(UPDATE_NODE_IN_DRAFT);
  const [, updateWorkBlock] = useMutation(UPDATE_WORK_BLOCK);
  const [publishing, setPublishing] = useState(false);
  const [searchMode, setSearchMode] = useState<"add" | "replace">("add");
  const [replaceNodeId, setReplaceNodeId] = useState<string | null>(null);
  const [editingBlockNode, setEditingBlockNode] = useState<NodeReference | null>(null);
  const [showEditBlockDialog, setShowEditBlockDialog] = useState(false);

  // Sync only when the query returns a newer server revision.
  // This prevents stale query responses from overwriting local mutation results.
  useEffect(() => {
    const incomingDraft = data?.flowDraft;
    if (!incomingDraft) {
      return;
    }

    const currentDraft = useDraftStore.getState().draft;
    if (!currentDraft || currentDraft.draftId !== incomingDraft.draftId) {
      setDraft(incomingDraft);
      return;
    }

    if (currentDraft.updatedAt === incomingDraft.updatedAt) {
      return;
    }

    const incomingUpdatedAt = Date.parse(incomingDraft.updatedAt);
    const currentUpdatedAt = Date.parse(currentDraft.updatedAt);

    if (Number.isFinite(incomingUpdatedAt) && Number.isFinite(currentUpdatedAt) && incomingUpdatedAt < currentUpdatedAt) {
      return;
    }

    setDraft(incomingDraft);
  }, [data?.flowDraft, setDraft]);

  const handleAddBlock = useCallback(
    async (block: { id: string; version: number; name: string }) => {
      if (!draftId) return;
      const nodeRefId = uuidv4();
      try {
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
        const nextDraft = result.data?.addNodeToDraft;
        if (!nextDraft) {
          throw new Error(result.error?.message ?? "Failed to add block to draft");
        }
        setDraft(nextDraft);
        selectNode(nodeRefId);
        setSearchPanelOpen(false);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown add-block error";
        alert(`Add block failed: ${message}`);
      }
    },
    [draftId, addNode, selectNode, setDraft, setSearchPanelOpen]
  );

  const handleRemoveNode = useCallback(
    async (nodeReferenceId: string) => {
      if (!draftId) return;
      try {
        const result = await removeNode({ draftId, nodeReferenceId });
        const nextDraft = result.data?.removeNodeFromDraft;
        if (!nextDraft) {
          throw new Error(result.error?.message ?? "Failed to remove node from draft");
        }
        setDraft(nextDraft);
        selectNode(null);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown remove-node error";
        alert(`Remove node failed: ${message}`);
      }
    },
    [draftId, removeNode, setDraft, selectNode]
  );

  const handleRemoveEdge = useCallback(
    async (edge: { sourceId: string | null; targetId: string }) => {
      if (!draftId) return;
      try {
        const result = await removeEdge({
          draftId,
          sourceId: edge.sourceId,
          targetId: edge.targetId,
        });
        const nextDraft = result.data?.removeEdgeFromDraft;
        if (!nextDraft) {
          throw new Error(result.error?.message ?? "Failed to remove edge from draft");
        }
        setDraft(nextDraft);
        selectEdge(null);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown remove-edge error";
        alert(`Remove link failed: ${message}`);
      }
    },
    [draftId, removeEdge, selectEdge, setDraft]
  );

  const handleConnect = useCallback(
    async (source: string, target: string) => {
      if (!draftId) return;
      try {
        const result = await addEdge({
          draftId,
          edge: {
            sourceId: source || null,
            targetId: target,
            portMappings: [],
          },
        });
        const nextDraft = result.data?.addEdgeToDraft;
        if (!nextDraft) {
          throw new Error(result.error?.message ?? "Failed to connect nodes");
        }
        setDraft(nextDraft);
        setSearchPanelOpen(false);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown connect error";
        alert(`Connect failed: ${message}`);
      }
    },
    [draftId, addEdge, setDraft, setSearchPanelOpen]
  );

  const handleSavePositions = useCallback(async () => {
    if (!draftId || !draft) return;
    try {
      const result = await updatePositions({
        draftId,
        positions: draft.nodePositions.map((p) => ({
          nodeReferenceId: getNodePositionId(p),
          x: p.x,
          y: p.y,
        })),
      });
      const nextDraft = result.data?.updateNodePositions;
      if (!nextDraft) {
        throw new Error(result.error?.message ?? "Failed to save node positions");
      }
      setDraft(nextDraft);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown save-layout error";
      alert(`Save layout failed: ${message}`);
    }
  }, [draftId, draft, updatePositions, setDraft]);

  const handlePositionChange = useCallback(
    (positions: NodePositionData[]) => {
      useDraftStore.getState().updatePositions(positions);
    },
    []
  );

  const handleUpdateNode = useCallback(
    async (
      nodeReferenceId: string,
      input: {
        alias?: string | null;
        executionSchedule?: string | null;
        targetId?: string;
        targetVersion?: number;
      }
    ) => {
      if (!draftId) {
        throw new Error("Draft identifier is missing");
      }
      const result = await updateNode({ draftId, nodeReferenceId, input });
      const nextDraft = result.data?.updateNodeInDraft;
      if (!nextDraft) {
        throw new Error(result.error?.message ?? "Failed to update node");
      }
      setDraft(nextDraft);
    },
    [draftId, setDraft, updateNode]
  );

  const handleUpdateEdge = useCallback(
    async (
      edge: { sourceId: string | null; targetId: string },
      input: {
        condition: {
          description: string;
          predicate: unknown | null;
          metadata: Record<string, unknown>;
        } | null;
        portMappings: { sourcePort: string; targetPort: string }[];
      }
    ) => {
      if (!draftId) {
        throw new Error("Draft identifier is missing");
      }
      const result = await updateEdge({
        draftId,
        sourceId: edge.sourceId,
        targetId: edge.targetId,
        edge: {
          sourceId: edge.sourceId,
          targetId: edge.targetId,
          condition: input.condition,
          portMappings: input.portMappings,
        },
      });
      const nextDraft = result.data?.updateEdgeInDraft;
      if (!nextDraft) {
        throw new Error(result.error?.message ?? "Failed to update link");
      }
      setDraft(nextDraft);
    },
    [draftId, setDraft, updateEdge]
  );

  const openAddBlockLibrary = useCallback(() => {
    setSearchMode("add");
    setReplaceNodeId(null);
    setSearchPanelOpen(true);
  }, [setSearchPanelOpen]);

  const openReplaceBlockLibrary = useCallback(
    (nodeReferenceId: string) => {
      setSearchMode("replace");
      setReplaceNodeId(nodeReferenceId);
      setSearchPanelOpen(true);
    },
    [setSearchPanelOpen]
  );

  const handleSelectBlock = useCallback(
    async (block: { id: string; version: number; name: string }) => {
      try {
        if (searchMode === "replace" && replaceNodeId) {
          await handleUpdateNode(replaceNodeId, {
            targetId: block.id,
            targetVersion: block.version,
          });
          selectNode(replaceNodeId);
          setSearchPanelOpen(false);
          return;
        }
        await handleAddBlock(block);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown block selection error";
        alert(`Block selection failed: ${message}`);
      }
    },
    [handleAddBlock, handleUpdateNode, replaceNodeId, searchMode, selectNode, setSearchPanelOpen]
  );

  const handleEditWorkBlockVersion = useCallback((node: NodeReference) => {
    setEditingBlockNode(node);
    setShowEditBlockDialog(true);
  }, []);

  const handleSelectNode = useCallback(
    (nodeId: string | null) => {
      selectNode(nodeId);
      if (nodeId) {
        setSearchPanelOpen(false);
      }
    },
    [selectNode, setSearchPanelOpen]
  );

  const handleSelectEdge = useCallback(
    (edge: { sourceId: string | null; targetId: string } | null) => {
      selectEdge(edge);
      if (edge) {
        setSearchPanelOpen(false);
      }
    },
    [selectEdge, setSearchPanelOpen]
  );

  const publishDraftVersion = useCallback(async () => {
    if (!draftId) {
      throw new Error("Draft identifier is missing");
    }
    const result = await publishDraft({ draftId });
    const flow = result.data?.publishFlowDraft;
    if (flow) {
      navigate(`/flows/${flow.id}`);
      return flow;
    }
    if (result.error) {
      throw new Error(result.error.message);
    }
    throw new Error("Publish failed");
  }, [draftId, navigate, publishDraft]);

  const handlePublish = useCallback(async () => {
    if (!draftId) return;
    setPublishing(true);
    try {
      await publishDraftVersion();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown publish error";
      alert(`Publish failed: ${message}`);
    } finally {
      setPublishing(false);
    }
  }, [draftId, publishDraftVersion]);

  const handleDiscard = useCallback(async () => {
    if (!draftId) return;
    if (!confirm("Discard this draft? This cannot be undone.")) return;
    const result = await discardDraft({ draftId });
    if (result.error) {
      alert(`Discard failed: ${result.error.message}`);
      return;
    }
    if (!result.data?.discardFlowDraft) {
      alert("Discard failed: draft was not deleted");
      return;
    }
    navigate("/flows");
  }, [draftId, discardDraft, navigate]);

  if (fetching) return <LoadingState message="Loading draft..." />;
  if (error) return <ErrorState message={error.message} />;
  if (!draft) return <ErrorState message="Draft not found" />;

  const selectedNode = selectedNodeId
    ? draft.nodes.find((n: NodeReference) => n.id === selectedNodeId) ?? null
    : null;
  const selectedDraftEdge = selectedEdge
    ? draft.edges.find(
      (edge) =>
        edge.sourceId === selectedEdge.sourceId &&
        edge.targetId === selectedEdge.targetId,
    ) ?? null
    : null;

  return (
    <div className="flex flex-col h-full">
      <DraftToolbar
        draftName={draft.name}
        isDirty={isDirty}
        nodeCount={draft.nodes.length}
        edgeCount={draft.edges.length}
        onOpenBlockLibrary={openAddBlockLibrary}
        onPublish={handlePublish}
        onDiscard={handleDiscard}
        onSavePositions={handleSavePositions}
        publishing={publishing}
      />

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 min-h-0">
          <DraftCanvas
            draft={draft}
            onConnect={handleConnect}
            onNodeSelect={handleSelectNode}
            onEdgeSelect={handleSelectEdge}
            onNodesPositionChange={handlePositionChange}
            selectedEdge={selectedEdge}
          />
        </div>

        {searchPanelOpen && (
          <WorkBlockSearchPanel
            mode={searchMode}
            selectedBlockId={selectedNode?.targetId ?? null}
            selectedBlockVersion={selectedNode?.targetVersion ?? null}
            onSelectBlock={handleSelectBlock}
            onClose={() => setSearchPanelOpen(false)}
          />
        )}

        {selectedNode && !searchPanelOpen && (
          <NodeDetailPanel
            node={selectedNode}
            edges={draft.edges}
            allNodes={draft.nodes}
            onClose={() => handleSelectNode(null)}
            onUpdateNode={handleUpdateNode}
            onReplaceWorkBlock={openReplaceBlockLibrary}
            onEditWorkBlockVersion={handleEditWorkBlockVersion}
            onRemoveNode={handleRemoveNode}
          />
        )}

        {!selectedNode && selectedDraftEdge && !searchPanelOpen && (
          <EdgeDetailPanel
            edge={selectedDraftEdge}
            allNodes={draft.nodes}
            onClose={() => handleSelectEdge(null)}
            onUpdateEdge={handleUpdateEdge}
            onRemoveEdge={handleRemoveEdge}
          />
        )}
      </div>

      <WorkBlockFormDialog
        open={showEditBlockDialog}
        onOpenChange={setShowEditBlockDialog}
        title={
          editingBlockNode?.workBlock
            ? `Edit ${editingBlockNode.workBlock.name} as New Version`
            : "Edit Work Block as New Version"
        }
        submitLabel="Save New Work Block Version"
        initialValue={
          editingBlockNode?.workBlock
            ? {
              name: editingBlockNode.workBlock.name,
              description: editingBlockNode.workBlock.description,
              inputs: editingBlockNode.workBlock.inputs,
              outputs: editingBlockNode.workBlock.outputs,
              executionHints: editingBlockNode.workBlock.executionHints ?? [],
            }
            : undefined
        }
        onSubmit={async (input) => {
          if (!editingBlockNode || !draftId) {
            throw new Error("Cannot edit block without an active draft node");
          }
          const workBlockResult = await updateWorkBlock({
            id: editingBlockNode.targetId,
            input,
          });
          const nextBlock = workBlockResult.data?.updateWorkBlock;
          if (!nextBlock) {
            throw new Error(workBlockResult.error?.message ?? "Failed to create a new Work Block version");
          }
          const draftResult = await updateNode({
            draftId,
            nodeReferenceId: editingBlockNode.id,
            input: {
              targetId: nextBlock.id,
              targetVersion: nextBlock.version,
            },
          });
          const updatedDraft = draftResult.data?.updateNodeInDraft;
          if (!updatedDraft) {
            throw new Error(draftResult.error?.message ?? "Failed to update the draft node");
          }
          setDraft(updatedDraft);
          selectNode(editingBlockNode.id);
          setPublishing(true);
          try {
            await publishDraftVersion();
          } catch (err) {
            const message = err instanceof Error ? err.message : "Unknown publish error";
            alert(`Work Block version saved, but flow auto-publish failed: ${message}`);
          } finally {
            setPublishing(false);
          }
        }}
      />
    </div>
  );
}
