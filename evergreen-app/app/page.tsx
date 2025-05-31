'use client';

import { useCallback } from 'react';
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

export default function Home() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <div className="w-full h-screen">
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
  );
}
