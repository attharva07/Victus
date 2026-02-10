export type LogEntry = {
  timestamp?: string;
  level?: string;
  event?: string;
  domain?: string;
  service?: string;
  request_id?: string;
  data?: Record<string, unknown>;
};

export type MemoryItem = {
  id: string;
  type: string;
  content: string;
  source: string;
  confidence: number;
  tags: string[];
  created_at?: string;
};

export type Transaction = {
  amount: number;
  category: string;
  description?: string;
  timestamp?: string;
};
