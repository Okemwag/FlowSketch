// Core data types based on the design document

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  owner: User;
  created_at: string;
  updated_at: string;
  is_public: boolean;
  share_token?: string;
  entities: Entity[];
  relationships: Relationship[];
  specification?: Specification;
  canonical_model?: CanonicalModel;
}

export interface Entity {
  id: string;
  project: string;
  name: string;
  type: EntityType;
  properties: Record<string, any>;
  position_x?: number;
  position_y?: number;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Relationship {
  id: string;
  project: string;
  source: string;
  target: string;
  source_name: string;
  target_name: string;
  type: RelationshipType;
  label?: string;
  properties: Record<string, any>;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface DiagramNode {
  id: string;
  entity: string;
  entity_name: string;
  entity_type: EntityType;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  style: Record<string, any>;
  label: string;
  created_at: string;
  updated_at: string;
}

export interface DiagramEdge {
  id: string;
  relationship: string;
  relationship_type: RelationshipType;
  source_node: string;
  target_node: string;
  source_label: string;
  target_label: string;
  style: Record<string, any>;
  label?: string;
  path: Point[];
  created_at: string;
  updated_at: string;
}

export interface Specification {
  id: string;
  project: string;
  title: string;
  content: string;
  sections: SpecSection[];
  acceptance_criteria: AcceptanceCriteria[];
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CanonicalModel {
  id: string;
  project: string;
  entities_data: any[];
  relationships_data: any[];
  business_rules: any[];
  version: number;
  last_modified: string;
}

// Enums and utility types
export type EntityType = 'object' | 'process' | 'actor' | 'data' | 'system' | 'event';

export type RelationshipType = 
  | 'association' 
  | 'composition' 
  | 'aggregation' 
  | 'inheritance' 
  | 'dependency' 
  | 'flow' 
  | 'sequence';

export type DiagramType = 'flowchart' | 'erd' | 'sequence' | 'class' | 'component';

export interface Point {
  x: number;
  y: number;
}

export interface Size {
  width: number;
  height: number;
}

export interface Position {
  x: number;
  y: number;
}

export interface SpecSection {
  id: string;
  title: string;
  content: string;
  order: number;
}

export interface AcceptanceCriteria {
  id: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  next?: string;
  previous?: string;
}

// WebSocket event types
export interface DiagramChange {
  type: 'node:add' | 'node:update' | 'node:delete' | 'edge:add' | 'edge:update' | 'edge:delete';
  nodeId?: string;
  edgeId?: string;
  data: any;
  timestamp: string;
  userId: string;
}

export interface SpecChange {
  type: 'section:add' | 'section:update' | 'section:delete' | 'content:update';
  sectionId?: string;
  content?: string;
  position?: number;
  timestamp: string;
  userId: string;
}

export interface SyncConflict {
  id: string;
  type: string;
  diagramChange: DiagramChange;
  specChange: SpecChange;
  suggestedResolution: any;
}

// Form types
export interface ProjectCreateForm {
  name: string;
  description: string;
  is_public: boolean;
}

export interface TextParseRequest {
  text: string;
  project_id: string;
}

// Export format types
export type ExportFormat = 'png' | 'svg' | 'pdf' | 'markdown' | 'word';

export interface ExportRequest {
  format: ExportFormat;
  project_id: string;
}