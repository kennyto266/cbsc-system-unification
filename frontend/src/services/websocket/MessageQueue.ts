/**
 * WebSocket Message Queue Manager
 * Handles message queuing, prioritization, and batch sending
 */

import { WSMessage, MessageType, QueuedMessage } from '../../types/websocket';

export interface MessageQueueConfig {
  maxSize: number;
  batchSize: number;
  batchInterval: number;
  maxRetries: number;
  retryDelay: number;
  priorityQueueSize: number;
}

export class MessageQueue {
  private queue: QueuedMessage[] = [];
  private priorityQueue: QueuedMessage[] = [];
  private processing = false;
  private batchTimer: NodeJS.Timeout | null = null;
  private config: MessageQueueConfig;
  private sendCallback: (message: WSMessage) => Promise<boolean>;
  private retryTimers: Map<string, NodeJS.Timeout> = new Map();

  constructor(
    sendCallback: (message: WSMessage) => Promise<boolean>,
    config: Partial<MessageQueueConfig> = {}
  ) {
    this.config = {
      maxSize: 1000,
      batchSize: 10,
      batchInterval: 100,
      maxRetries: 3,
      retryDelay: 1000,
      priorityQueueSize: 100,
      ...config
    };

    this.sendCallback = sendCallback;

    // Start batch processing
    this.startBatchProcessor();
  }

  /**
   * Add message to queue
   */
  enqueue(message: WSMessage, priority: 'high' | 'normal' | 'low' = 'normal'): boolean {
    // Check if queue is full
    if (this.getTotalSize() >= this.config.maxSize) {
      console.warn('[MessageQueue] Queue is full, dropping message');
      return false;
    }

    const queuedMessage: QueuedMessage = {
      message,
      timestamp: Date.now(),
      retries: 0,
      priority
    };

    // Add to appropriate queue based on priority
    if (priority === 'high') {
      // Ensure priority queue doesn't exceed size limit
      if (this.priorityQueue.length >= this.config.priorityQueueSize) {
        this.priorityQueue.shift(); // Remove oldest message
      }
      this.priorityQueue.push(queuedMessage);
    } else {
      this.queue.push(queuedMessage);
    }

    return true;
  }

  /**
   * Process queue and send messages
   */
  async process(): Promise<void> {
    if (this.processing) {
      return;
    }

    this.processing = true;

    try {
      // Process priority queue first
      await this.processQueue(this.priorityQueue, true);

      // Then process regular queue
      await this.processQueue(this.queue, false);
    } finally {
      this.processing = false;
    }
  }

  /**
   * Clear all messages from queue
   */
  clear(): void {
    this.queue = [];
    this.priorityQueue = [];

    // Clear all retry timers
    this.retryTimers.forEach(timer => clearTimeout(timer));
    this.retryTimers.clear();
  }

  /**
   * Get queue statistics
   */
  getStats() {
    return {
      totalSize: this.getTotalSize(),
      prioritySize: this.priorityQueue.length,
      normalSize: this.queue.length,
      processing: this.processing,
      oldestMessage: this.getOldestMessageTimestamp()
    };
  }

  /**
   * Process a specific queue
   */
  private async processQueue(queue: QueuedMessage[], isPriority: boolean): Promise<void> {
    const batchSize = isPriority ?
      Math.min(this.config.batchSize, this.priorityQueue.length) :
      Math.min(this.config.batchSize, this.queue.length);

    if (batchSize === 0) {
      return;
    }

    const batch: QueuedMessage[] = [];

    // Collect batch of messages
    for (let i = 0; i < batchSize && queue.length > 0; i++) {
      const message = queue.shift();
      if (message) {
        batch.push(message);
      }
    }

    // Send batch
    await this.sendBatch(batch);
  }

  /**
   * Send a batch of messages
   */
  private async sendBatch(batch: QueuedMessage[]): Promise<void> {
    const sendPromises = batch.map(async (queuedMessage) => {
      const { message, retries } = queuedMessage;

      try {
        const success = await this.sendCallback(message);

        if (!success) {
          await this.handleSendFailure(queuedMessage);
        }
      } catch (error) {
        console.error('[MessageQueue] Failed to send message:', error);
        await this.handleSendFailure(queuedMessage);
      }
    });

    await Promise.allSettled(sendPromises);
  }

  /**
   * Handle send failure with retry logic
   */
  private async handleSendFailure(queuedMessage: QueuedMessage): Promise<void> {
    const { message, retries } = queuedMessage;

    if (retries < this.config.maxRetries) {
      // Increment retry count
      queuedMessage.retries++;

      // Calculate delay with exponential backoff
      const delay = this.config.retryDelay * Math.pow(2, retries);

      // Schedule retry
      const timer = setTimeout(() => {
        this.retryTimers.delete(message.id);

        // Re-add to appropriate queue
        if (queuedMessage.priority === 'high') {
          this.priorityQueue.unshift(queuedMessage);
        } else {
          this.queue.unshift(queuedMessage);
        }
      }, delay);

      this.retryTimers.set(message.id, timer);
    } else {
      console.error('[MessageQueue] Max retries exceeded for message:', message.id);
    }
  }

  /**
   * Start batch processor
   */
  private startBatchProcessor(): void {
    if (this.batchTimer) {
      clearInterval(this.batchTimer);
    }

    this.batchTimer = setInterval(() => {
      this.process().catch(error => {
        console.error('[MessageQueue] Batch processing error:', error);
      });
    }, this.config.batchInterval);
  }

  /**
   * Get total queue size
   */
  private getTotalSize(): number {
    return this.queue.length + this.priorityQueue.length;
  }

  /**
   * Get oldest message timestamp
   */
  private getOldestMessageTimestamp(): number | null {
    let oldest: number | null = null;

    // Check priority queue
    if (this.priorityQueue.length > 0) {
      oldest = this.priorityQueue[0].timestamp;
    }

    // Check regular queue
    if (this.queue.length > 0) {
      const queueOldest = this.queue[0].timestamp;
      if (!oldest || queueOldest < oldest) {
        oldest = queueOldest;
      }
    }

    return oldest;
  }

  /**
   * Cleanup old messages
   */
  cleanup(maxAge: number = 300000): void { // Default 5 minutes
    const now = Date.now();
    const cutoff = now - maxAge;

    // Filter priority queue
    this.priorityQueue = this.priorityQueue.filter(msg => msg.timestamp > cutoff);

    // Filter regular queue
    this.queue = this.queue.filter(msg => msg.timestamp > cutoff);
  }

  /**
   * Pause batch processing
   */
  pause(): void {
    if (this.batchTimer) {
      clearInterval(this.batchTimer);
      this.batchTimer = null;
    }
  }

  /**
   * Resume batch processing
   */
  resume(): void {
    this.startBatchProcessor();
  }

  /**
   * Destroy message queue
   */
  destroy(): void {
    this.pause();
    this.clear();
  }
}