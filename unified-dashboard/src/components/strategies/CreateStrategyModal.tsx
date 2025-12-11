import React from 'react'

interface CreateStrategyModalProps {
  visible: boolean
  onClose: () => void
}

const CreateStrategyModal: React.FC<CreateStrategyModalProps> = ({ visible, onClose }) => {
  return (
    <div>
      <h3>创建策略模态框</h3>
      <p>开发中...</p>
    </div>
  )
}

export default CreateStrategyModal
