import React from 'react';
import { Strategy } from '../../types/index';
import { PersonalStrategyCard } from './PersonalStrategyCard';

interface StrategyGridProps {
  strategies: Strategy[];
  onPersonalize: (strategy: Strategy) => void;
  onSelect: (strategy: Strategy) => void;
  selectedStrategy?: Strategy | null;
}

export const StrategyGrid: React.FC<StrategyGridProps> = ({
  strategies,
  onPersonalize,
  onSelect,
  selectedStrategy
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {strategies.map((strategy) => (
        <PersonalStrategyCard
          key={strategy.id}
          strategy={strategy}
          onPersonalize={onPersonalize}
          onSelect={onSelect}
          isSelected={selectedStrategy?.id === strategy.id}
        />
      ))}
    </div>
  );
};