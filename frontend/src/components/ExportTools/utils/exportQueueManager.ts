export interface ExportJob {
  id: string;
  type: 'pdf' | 'excel';
  reportId: string;
  reportName: string;
  templateId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  createdAt: Date;
  completedAt?: Date;
  error?: string;
  result?: {
    url: string;
    filename: string;
    size: number;
  };
  options?: {
    emailTo?: string[];
    includeCharts?: boolean;
    branding?: any;
  };
}

export interface BatchExportJob extends ExportJob {
  type: 'batch';
  reportIds: string[];
  reportCount: number;
}

class ExportQueueManager {
  private queue: Map<string, ExportJob | BatchExportJob> = new Map();
  private processing: Set<string> = new Set();
  private maxConcurrentJobs = 3;
  private listeners: Set<(jobs: ExportJob[]) => void> = new Set();

  // Add job to queue
  addJob(job: Omit<ExportJob, 'id' | 'createdAt' | 'status' | 'progress'>): string {
    const id = `export_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const exportJob: ExportJob = {
      ...job,
      id,
      createdAt: new Date(),
      status: 'pending',
      progress: 0
    };

    this.queue.set(id, exportJob);
    this.notifyListeners();
    this.processQueue();

    return id;
  }

  // Add batch export job
  addBatchJob(job: Omit<BatchExportJob, 'id' | 'createdAt' | 'status' | 'progress'>): string {
    const id = `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const batchJob: BatchExportJob = {
      ...job,
      id,
      createdAt: new Date(),
      status: 'pending',
      progress: 0
    };

    this.queue.set(id, batchJob);
    this.notifyListeners();
    this.processQueue();

    return id;
  }

  // Get job by ID
  getJob(id: string): ExportJob | BatchExportJob | undefined {
    return this.queue.get(id);
  }

  // Get all jobs
  getAllJobs(): (ExportJob | BatchExportJob)[] {
    return Array.from(this.queue.values()).sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
  }

  // Get jobs by status
  getJobsByStatus(status: ExportJob['status']): (ExportJob | BatchExportJob)[] {
    return this.getAllJobs().filter(job => job.status === status);
  }

  // Cancel job
  cancelJob(id: string): boolean {
    const job = this.queue.get(id);
    if (!job || job.status === 'completed') return false;

    if (job.status === 'processing') {
      // In a real implementation, you would need to abort the actual export process
      job.status = 'failed';
      job.error = 'Export cancelled by user';
      job.completedAt = new Date();
      this.processing.delete(id);
    } else {
      this.queue.delete(id);
    }

    this.notifyListeners();
    return true;
  }

  // Retry failed job
  retryJob(id: string): boolean {
    const job = this.queue.get(id);
    if (!job || job.status !== 'failed') return false;

    job.status = 'pending';
    job.progress = 0;
    job.error = undefined;
    job.completedAt = undefined;
    delete job.result;

    this.notifyListeners();
    this.processQueue();

    return true;
  }

  // Clear completed jobs
  clearCompleted(): void {
    const completedJobs = Array.from(this.queue.entries()).filter(([_, job]) => job.status === 'completed');
    completedJobs.forEach(([id]) => this.queue.delete(id));
    this.notifyListeners();
  }

  // Subscribe to queue updates
  subscribe(listener: (jobs: ExportJob[]) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  // Notify all listeners
  private notifyListeners(): void {
    const jobs = this.getAllJobs() as ExportJob[];
    this.listeners.forEach(listener => listener(jobs));
  }

  // Process queue
  private async processQueue(): Promise<void> {
    const pendingJobs = Array.from(this.queue.values())
      .filter(job => job.status === 'pending')
      .slice(0, this.maxConcurrentJobs - this.processing.size);

    for (const job of pendingJobs) {
      if (this.processing.size >= this.maxConcurrentJobs) break;

      this.processing.add(job.id);
      job.status = 'processing';
      this.notifyListeners();

      try {
        await this.processJob(job);
      } catch (error: any) {
        job.status = 'failed';
        job.error = error.message || 'Export failed';
        job.completedAt = new Date();
      } finally {
        this.processing.delete(job.id);
        this.notifyListeners();
      }
    }

    // Continue processing if there are more jobs
    if (this.processing.size < this.maxConcurrentJobs) {
      setTimeout(() => this.processQueue(), 100);
    }
  }

  // Process individual job
  private async processJob(job: ExportJob | BatchExportJob): Promise<void> {
    const updateProgress = (progress: number) => {
      job.progress = progress;
      this.notifyListeners();
    };

    if (job.type === 'batch') {
      await this.processBatchExport(job as BatchExportJob, updateProgress);
    } else {
      await this.processSingleExport(job as ExportJob, updateProgress);
    }

    job.status = 'completed';
    job.completedAt = new Date();
  }

  // Process single export
  private async processSingleExport(
    job: ExportJob,
    updateProgress: (progress: number) => void
  ): Promise<void> {
    // In a real implementation, this would call the actual export functions
    updateProgress(10);

    // Simulate export process
    await new Promise(resolve => setTimeout(resolve, 2000));
    updateProgress(50);

    // Generate result
    const filename = `${job.reportName}_Report_${new Date().toISOString().split('T')[0]}.${job.type}`;
    const url = `blob:mock-url-${job.id}`;
    const size = Math.floor(Math.random() * 1000000) + 100000; // Random size between 100KB - 1.1MB

    updateProgress(90);

    // Send email if requested
    if (job.options?.emailTo && job.options.emailTo.length > 0) {
      updateProgress(95);
      // Simulate email sending
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    job.result = { url, filename, size };
    updateProgress(100);
  }

  // Process batch export
  private async processBatchExport(
    job: BatchExportJob,
    updateProgress: (progress: number) => void
  ): Promise<void> {
    const totalReports = job.reportIds.length;
    const progressPerReport = 80 / totalReports; // 80% for processing, 20% for finalization

    for (let i = 0; i < totalReports; i++) {
      const reportProgress = 10 + (i * progressPerReport);
      updateProgress(reportProgress);

      // Simulate processing each report
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    // Generate batch result
    const filename = `Batch_Export_${new Date().toISOString().split('T')[0]}.${job.type}`;
    const url = `blob:batch-mock-url-${job.id}`;
    const size = totalReports * 500000; // Estimate size based on report count

    updateProgress(90);

    // Send batch email if requested
    if (job.options?.emailTo && job.options.emailTo.length > 0) {
      updateProgress(95);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    job.result = { url, filename, size };
    updateProgress(100);
  }

  // Get queue statistics
  getStatistics(): {
    total: number;
    pending: number;
    processing: number;
    completed: number;
    failed: number;
  } {
    const jobs = this.getAllJobs();
    return {
      total: jobs.length,
      pending: jobs.filter(j => j.status === 'pending').length,
      processing: jobs.filter(j => j.status === 'processing').length,
      completed: jobs.filter(j => j.status === 'completed').length,
      failed: jobs.filter(j => j.status === 'failed').length
    };
  }

  // Estimate completion time for pending jobs
  getEstimatedCompletionTime(): Date | null {
    const processingJob = Array.from(this.queue.values()).find(job => job.status === 'processing');
    const pendingJobs = Array.from(this.queue.values()).filter(job => job.status === 'pending');

    if (!processingJob && pendingJobs.length === 0) return null;

    // Assume each job takes 3 seconds to complete
    const avgJobTime = 3000;
    const currentTime = new Date();
    const timeRemaining = (pendingJobs.length * avgJobTime) / this.maxConcurrentJobs;

    return new Date(currentTime.getTime() + timeRemaining);
  }
}

// Singleton instance
export const exportQueue = new ExportQueueManager();

// React hook for using the export queue
import React from 'react';

export function useExportQueue() {
  const [jobs, setJobs] = React.useState<ExportJob[]>([]);

  React.useEffect(() => {
    // Initial load
    setJobs(exportQueue.getAllJobs() as ExportJob[]);

    // Subscribe to updates
    const unsubscribe = exportQueue.subscribe(setJobs);

    return unsubscribe;
  }, []);

  return {
    jobs,
    addJob: exportQueue.addJob.bind(exportQueue),
    addBatchJob: exportQueue.addBatchJob.bind(exportQueue),
    cancelJob: exportQueue.cancelJob.bind(exportQueue),
    retryJob: exportQueue.retryJob.bind(exportQueue),
    clearCompleted: exportQueue.clearCompleted.bind(exportQueue),
    getStatistics: exportQueue.getStatistics.bind(exportQueue),
    getEstimatedCompletionTime: exportQueue.getEstimatedCompletionTime.bind(exportQueue)
  };
}