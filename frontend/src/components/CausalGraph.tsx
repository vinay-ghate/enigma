import React, { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  Handle,
  Position,
  NodeProps,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import { GitPullRequest, Rocket, MessageSquare, Ticket, FileText, Server, AlertTriangle, ShieldAlert, CheckCircle, XCircle } from 'lucide-react';
import { GraphNodeData } from '../types';

interface CausalGraphProps {
  nodes: Node[];
  edges: Edge[];
  onNodeClick?: (nodeId: string) => void;
}

// Custom Node Component respecting CODE_FRONTEND.md styling rules
const CustomNode: React.FC<NodeProps> = ({ data }) => {
  const d = data as unknown as GraphNodeData;

  // Icon mapping
  const renderIcon = () => {
    switch (d.nodeType) {
      case 'pr':
        return <GitPullRequest className="w-4 h-4 text-sky-400" />;
      case 'deploy':
        return <Rocket className="w-4 h-4 text-purple-400" />;
      case 'message':
        return <MessageSquare className="w-4 h-4 text-emerald-400" />;
      case 'ticket':
        return <Ticket className="w-4 h-4 text-amber-400" />;
      case 'doc':
        return <FileText className="w-4 h-4 text-amber-300" />;
      case 'service':
        return <Server className="w-4 h-4 text-indigo-400" />;
      case 'incident':
        return <AlertTriangle className="w-4 h-4 text-rose-400" />;
      default:
        return <Server className="w-4 h-4 text-slate-400" />;
    }
  };

  // State based border & glow styling
  let containerStyle = 'bg-slate-900/90 border-slate-700 text-slate-200';
  let badge = null;

  if (d.state === 'incident') {
    containerStyle = 'bg-rose-950/40 border-2 border-rose-500 animate-incident-pulse text-white';
    badge = (
      <div className="absolute -top-2.5 right-2 px-1.5 py-0.2 bg-rose-500 text-slate-950 text-[9px] font-bold uppercase rounded font-mono">
        Active Incident
      </div>
    );
  } else if (d.state === 'chosen_cause') {
    containerStyle = 'bg-emerald-950/40 border-2 border-emerald-400 root-cause-glow text-white';
    badge = (
      <div className="absolute -top-2.5 right-2 px-1.5 py-0.2 bg-emerald-400 text-slate-950 text-[9px] font-bold uppercase rounded font-mono flex items-center space-x-1">
        <CheckCircle className="w-2.5 h-2.5" />
        <span>Root Cause</span>
      </div>
    );
  } else if (d.state === 'ruled_out_candidate') {
    containerStyle = 'bg-slate-950/60 border border-dashed border-rose-400/50 text-slate-400 opacity-80';
    badge = (
      <div className="absolute -top-2.5 right-2 px-1.5 py-0.2 bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[9px] font-medium rounded font-mono flex items-center space-x-1">
        <XCircle className="w-2.5 h-2.5" />
        <span>Ruled Out</span>
      </div>
    );
  } else if (d.state === 'superseded_doc') {
    containerStyle = 'bg-amber-950/30 border-2 border-amber-500 text-amber-200';
    badge = (
      <div className="absolute -top-2.5 right-2 px-1.5 py-0.2 bg-amber-500 text-slate-950 text-[9px] font-bold uppercase rounded font-mono">
        {d.supersededBy ? `Superseded by ${d.supersededBy}` : 'Stale Runbook'}
      </div>
    );
  }

  return (
    <div className={`relative px-3.5 py-2.5 rounded-xl shadow-lg min-w-[200px] max-w-[260px] text-xs transition duration-200 ${containerStyle}`}>
      <Handle type="target" position={Position.Left} className="!bg-slate-500 !w-2 !h-2" />
      {badge}

      <div className="flex items-center space-x-2 mb-1.5">
        <div className="p-1 rounded bg-slate-800/80 border border-slate-700">
          {renderIcon()}
        </div>
        <div className="font-mono text-[10px] uppercase font-bold tracking-wider text-slate-400">
          {d.nodeType}
        </div>
      </div>

      <div className="font-semibold line-clamp-2 leading-tight text-slate-200">
        {d.label}
      </div>

      {d.ruledOutReason && (
        <div className="mt-2 p-1.5 bg-rose-950/40 border border-rose-500/30 rounded text-[10px] text-rose-300 font-mono leading-tight">
          ⚠️ {d.ruledOutReason}
        </div>
      )}

      {d.sourceLink && (
        <div className="mt-1.5 pt-1.5 border-t border-slate-800 text-[10px] text-slate-400 flex items-center justify-between font-mono">
          <span>{d.id}</span>
          <span className="text-emerald-400">provenance ↗</span>
        </div>
      )}

      <Handle type="source" position={Position.Right} className="!bg-slate-500 !w-2 !h-2" />
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

export const CausalGraph: React.FC<CausalGraphProps> = ({ nodes, edges, onNodeClick }) => {
  // Dagre layout computation: left-to-right (LR)
  const { layoutedNodes, layoutedEdges } = useMemo(() => {
    if (!nodes || nodes.length === 0) {
      return { layoutedNodes: [], layoutedEdges: [] };
    }

    const g = new dagre.graphlib.Graph();
    g.setGraph({ rankdir: 'LR', nodesep: 40, ranksep: 90, marginx: 20, marginy: 20 });
    g.setDefaultEdgeLabel(() => ({}));

    nodes.forEach((node) => {
      g.setNode(node.id, { width: 220, height: 95 });
    });

    edges.forEach((edge) => {
      g.setEdge(edge.source, edge.target);
    });

    dagre.layout(g);

    const laidOutNodes = nodes.map((node) => {
      const nodeWithPosition = g.node(node.id);
      return {
        ...node,
        position: {
          x: nodeWithPosition.x - 110,
          y: nodeWithPosition.y - 47,
        },
      };
    });

    return { layoutedNodes: laidOutNodes, layoutedEdges: edges };
  }, [nodes, edges]);

  return (
    <div className="w-full h-full min-h-[420px] bg-[#070b14] relative">
      <ReactFlow
        nodes={layoutedNodes}
        edges={layoutedEdges}
        nodeTypes={nodeTypes}
        fitView
        onNodeClick={(_, node) => onNodeClick && onNodeClick(node.id)}
        className="bg-[#070b14]"
      >
        <Background color="#1e293b" gap={18} size={1} />
        <Controls className="!bg-slate-900 !border-slate-800 !text-slate-200 fill-slate-200" />
        <MiniMap
          nodeColor={(n) => {
            const d = n.data as unknown as GraphNodeData;
            if (d?.state === 'incident') return '#ef4444';
            if (d?.state === 'chosen_cause') return '#10b981';
            if (d?.state === 'superseded_doc') return '#f59e0b';
            return '#334155';
          }}
          className="!bg-slate-950 !border-slate-800"
        />
      </ReactFlow>

      {/* Graph Legend Overlay */}
      <div className="absolute bottom-3 left-3 bg-slate-950/80 border border-slate-800 backdrop-blur-sm rounded-lg p-2.5 text-[11px] font-mono space-y-1.5 z-10">
        <div className="text-slate-400 font-bold uppercase text-[10px] mb-1">Graph Legend</div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
          <span className="text-slate-300">Active Incident Node</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
          <span className="text-slate-300">Deterministic Root Cause (Green)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full border border-dashed border-rose-400"></span>
          <span className="text-slate-300">Ruled-Out Semantic Decoy (Grey/Red)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
          <span className="text-slate-300">Superseded / Stale Runbook (Amber)</span>
        </div>
      </div>
    </div>
  );
};
