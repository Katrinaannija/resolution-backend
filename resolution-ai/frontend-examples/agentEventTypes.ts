export type PipelineEventType = "case_law" | "document";

export type AgentEventType = PipelineEventType | "judgement";

export interface Issue {
  date_event?: string;
  undisputed_facts?: string;
  claimant_position?: string;
  defendant_position?: string;
  legal_issue?: string;
  relevant_documents?: string[];
}

export interface WorkflowSnapshot {
  name?: PipelineEventType;
  recommendation?: string;
  suggestion?: string;
  solved?: boolean;
  documents?: boolean;
  case_law?: boolean;
}

export interface IssueWorkState {
  issue_index?: number;
  issue?: Issue;
  recommendation?: string;
  suggestion?: string;
  solved?: boolean;
  documents?: boolean;
  case_law?: boolean;
  requires_documents?: boolean;
  requires_case_law?: boolean;
  seen_keywords?: string[];
  case_law_runs?: WorkflowSnapshot[];
  document_runs?: WorkflowSnapshot[];
}

export interface JudgementResult {
  issues?: IssueWorkState[];
  issues_table?: string;
  statement_of_claim?: string;
  statement_of_defence?: string;
  judgement?: string;
}

interface BaseAgentEvent {
  type: AgentEventType;
  date: string;
}

interface PipelineAgentEvent extends BaseAgentEvent {
  type: PipelineEventType;
  recommendation?: string | null;
  suggestion?: string | null;
  solved?: boolean | null;
  iteration: number;
  issue_id: number | null;
  legal_issue?: string | null;
}

export interface CaseLawEvent extends PipelineAgentEvent {
  type: "case_law";
}

export interface DocumentEvent extends PipelineAgentEvent {
  type: "document";
}

export interface JudgementEvent extends BaseAgentEvent {
  type: "judgement";
  judgement: JudgementResult;
}

export type AgentEvent = CaseLawEvent | DocumentEvent | JudgementEvent;


