/**
 * StrategyExecutionPanel Component
 * Grid of strategy cards with drag-drop reordering
 */

import React, { useState } from 'react';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { motion, AnimatePresence } from 'framer-motion';
import { Button, Empty } from 'antd';
import { Plus, RefreshCw } from 'lucide-react';
import { useAppSelector } from '../../../../hooks/redux';
import { StrategyCard } from './StrategyCard';
import { StrategyExecution } from '../../../../store/slices/monitoringSlice';
import './StrategyExecutionPanel.css';

interface DraggableCardProps {
  strategy: StrategyExecution;
  index: number;
  moveCard: (from: number, to: number) => void;
}

const DraggableCard: React.FC<DraggableCardProps> = ({ strategy, index, moveCard }) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'STRATEGY_CARD',
    item: { index },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const [, drop] = useDrop({
    accept: 'STRATEGY_CARD',
    hover: (item: { index: number }) => {
      if (item.index !== index) {
        moveCard(item.index, index);
        item.index = index;
      }
    },
  });

  return (
    <div
      ref={(node) => drag(drop(node))}
      style={{ opacity: isDragging ? 0.5 : 1 }}
    >
      <StrategyCard strategy={strategy} />
    </div>
  );
};

export const StrategyExecutionPanel: React.FC = () => {
  const strategies = useAppSelector((state) => state.monitoring.strategies);
  const [cardOrder, setCardOrder] = useState<string[]>(strategies.map((s) => s.id));

  // Update card order when strategies change
  React.useEffect(() => {
    const strategyIds = strategies.map((s) => s.id);
    if (JSON.stringify(strategyIds) !== JSON.stringify(cardOrder)) {
      setCardOrder(strategyIds);
    }
  }, [strategies]);

  const moveCard = (from: number, to: number) => {
    const newOrder = [...cardOrder];
    const [moved] = newOrder.splice(from, 1);
    newOrder.splice(to, 0, moved);
    setCardOrder(newOrder);
  };

  const orderedStrategies = cardOrder
    .map((id) => strategies.find((s) => s.id === id))
    .filter((s): s is StrategyExecution => !!s);

  return (
    <div className="strategy-execution-panel">
      <div className="panel-header">
        <h2>策略執行監控</h2>
        <Button icon={<RefreshCw size={14} />} size="small">
          刷新
        </Button>
      </div>

      {orderedStrategies.length === 0 ? (
        <Empty
          description="沒有運行中的策略"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <DndProvider backend={HTML5Backend}>
          <div className="strategy-grid">
            <AnimatePresence mode="popLayout">
              {orderedStrategies.map((strategy, index) => (
                <motion.div
                  key={strategy.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.2 }}
                  className="strategy-grid-item"
                >
                  <DraggableCard
                    strategy={strategy}
                    index={index}
                    moveCard={moveCard}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </DndProvider>
      )}

      <Button type="dashed" icon={<Plus size={14} />} block>
        添加策略到監控
      </Button>
    </div>
  );
};

export default StrategyExecutionPanel;
