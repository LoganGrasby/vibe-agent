'use client';

import { useCallback, useState } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
} from '@xyflow/react';

import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";
import { ThreadList } from "@/components/assistant-ui/thread-list";
import { Thread } from "@/components/assistant-ui/thread";
import { Button } from "@/components/ui/button";
import { Menu, X } from "lucide-react";

const initialNodes: Node[] = [
  {
    id: '1',
    position: { x: 250, y: 25 },
    data: { label: 'Start' },
    type: 'input',
  },
  {
    id: '2',
    position: { x: 100, y: 125 },
    data: { label: 'Process A' },
  },
  {
    id: '3',
    position: { x: 400, y: 125 },
    data: { label: 'Process B' },
  },
  {
    id: '4',
    position: { x: 250, y: 250 },
    data: { label: 'Decision' },
  },
  {
    id: '5',
    position: { x: 100, y: 350 },
    data: { label: 'Result A' },
  },
  {
    id: '6',
    position: { x: 400, y: 350 },
    data: { label: 'Result B' },
  },
  {
    id: '7',
    position: { x: 250, y: 450 },
    data: { label: 'End' },
    type: 'output',
  },
];

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
  { id: 'e1-3', source: '1', target: '3', animated: true },
  { id: 'e2-4', source: '2', target: '4' },
  { id: 'e3-4', source: '3', target: '4' },
  { id: 'e4-5', source: '4', target: '5', label: 'Yes' },
  { id: 'e4-6', source: '4', target: '6', label: 'No' },
  { id: 'e5-7', source: '5', target: '7' },
  { id: 'e6-7', source: '6', target: '7' },
];

const FlowCanvas = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <div className="w-full h-full p-4">
      <div className="w-full h-full border border-border rounded-lg overflow-hidden shadow-sm bg-background">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        </ReactFlow>
      </div>
    </div>
  );
};

export default function Home() {
  const [showThreadList, setShowThreadList] = useState(false);
  const runtime = useChatRuntime({
    api: "/api/chat",
  });

  const toggleThreadList = () => {
    setShowThreadList(!showThreadList);
  };

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="relative h-screen overflow-hidden">
        {/* Toggle Button in Top Left */}
        <div className="absolute top-4 left-4 z-20">
          <Button variant="outline" size="icon" onClick={toggleThreadList}>
            <Menu className="h-4 w-4" />
          </Button>
        </div>

        {/* Sliding Thread List Overlay */}
        <div className={`absolute left-0 top-0 h-full w-80 bg-background border-r shadow-lg z-10 transform transition-transform duration-300 ease-in-out ${
          showThreadList ? 'translate-x-0' : '-translate-x-full'
        }`}>
          <div className="h-full p-4">
            {/* Close button for the overlay */}
            <div className="flex justify-end mb-4">
              <Button variant="ghost" size="icon" onClick={toggleThreadList}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <ThreadList />
          </div>
        </div>

        {/* Main Content Grid - Always 2 columns */}
        <div className="grid h-full grid-cols-[1fr_400px] gap-x-2 px-4 py-4">
          {/* Flow Canvas */}
          <FlowCanvas />
          
          {/* Thread */}
          <Thread />
        </div>

        {/* Backdrop overlay when thread list is open */}
        {showThreadList && (
          <div 
            className="absolute inset-0 bg-black/20 z-5"
            onClick={toggleThreadList}
          />
        )}
      </div>
    </AssistantRuntimeProvider>
  );
}
