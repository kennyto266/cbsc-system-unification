/**
 * Strategy Action Buttons Component
 * 策略操作按鈕組件 - 展示如何集成策略嚮導和數據導出功能
 */

import React, { useState } from 'react';
import { Button } from '../ui/Button';
import { StrategyWizard } from '../StrategyWizard';
import { DataExporter, ShareManager } from '../DataExport';
import {
  PlusIcon,
  DocumentArrowDownIcon,
  ShareIcon
} from '@heroicons/react/24/outline';
import { Strategy } from '../../types/strategyTypes';

interface StrategyActionButtonsProps {
  strategies?: Strategy[];
  selectedStrategies?: string[];
  onStrategyCreated?: (strategy: Strategy) => void;
}

export const StrategyActionButtons: React.FC<StrategyActionButtonsProps> = ({
  strategies = [],
  selectedStrategies = [],
  onStrategyCreated
}) => {
  const [showWizard, setShowWizard] = useState(false);
  const [showExport, setShowExport] = useState(false);
  const [showShare, setShowShare] = useState(false);

  const handleExport = () => {
    const exportData = selectedStrategies.length > 0
      ? strategies.filter(s => selectedStrategies.includes(s.id))
      : strategies;

    setShowExport(true);
  };

  const handleShare = () => {
    if (selectedStrategies.length === 1) {
      // Share specific strategy
      setShowShare(true);
    }
  };

  return (
    <>
      <div className="flex flex-wrap gap-2">
        {/* Create Strategy with Wizard */}
        <Button
          variant="primary"
          icon={<PlusIcon />}
          onClick={() => setShowWizard(true)}
        >
          使用嚮導創建策略
        </Button>

        {/* Export Strategies */}
        <Button
          variant="outline"
          icon={<DocumentArrowDownIcon />}
          onClick={handleExport}
          disabled={strategies.length === 0}
        >
          導出策略
        </Button>

        {/* Share Selected Strategy */}
        <Button
          variant="outline"
          icon={<ShareIcon />}
          onClick={handleShare}
          disabled={selectedStrategies.length !== 1}
        >
          分享策略
        </Button>
      </div>

      {/* Strategy Wizard Modal */}
      <StrategyWizard
        isOpen={showWizard}
        onClose={() => setShowWizard(false)}
        onComplete={(strategy) => {
          console.log('Strategy created:', strategy);
          onStrategyCreated?.(strategy);
          setShowWizard(false);
        }}
      />

      {/* Data Export Modal */}
      {showExport && (
        <DataExporter
          isOpen={showExport}
          onClose={() => setShowExport(false)}
          data={
            selectedStrategies.length > 0
              ? strategies.filter(s => selectedStrategies.includes(s.id))
              : strategies
          }
          title={`策略數據_${new Date().toISOString().slice(0, 10)}`}
          type="strategy"
          onExportComplete={(filename) => {
            console.log('Exported:', filename);
            setShowExport(false);
          }}
        />
      )}

      {/* Share Manager Modal */}
      {showShare && (
        <ShareManager
          isOpen={showShare}
          onClose={() => setShowShare(false)}
          strategyId={selectedStrategies[0]}
          onShareCreate={(link) => {
            console.log('Share link created:', link);
            setShowShare(false);
          }}
        />
      )}
    </>
  );
};