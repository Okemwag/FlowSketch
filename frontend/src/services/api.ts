import axios, { AxiosResponse } from 'axios';
import {
  Project,
  Entity,
  Relationship,
  DiagramNode,
  DiagramEdge,
  Specification,
  ProjectCreateForm,
  TextParseRequest,
  ApiResponse,
  PaginatedResponse,
  ExportRequest
} from '../types';

// Configure axios defaults
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // For session-based auth
});

// Add request interceptor for authentication
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Project API
export const projectApi = {
  // Get all projects for the current user
  getProjects: (): Promise<AxiosResponse<PaginatedResponse<Project>>> =>
    apiClient.get('/projects/'),

  // Get a specific project
  getProject: (id: string): Promise<AxiosResponse<Project>> =>
    apiClient.get(`/projects/${id}/`),

  // Create a new project
  createProject: (data: ProjectCreateForm): Promise<AxiosResponse<Project>> =>
    apiClient.post('/projects/', data),

  // Update a project
  updateProject: (id: string, data: Partial<Project>): Promise<AxiosResponse<Project>> =>
    apiClient.put(`/projects/${id}/`, data),

  // Delete a project
  deleteProject: (id: string): Promise<AxiosResponse<void>> =>
    apiClient.delete(`/projects/${id}/`),

  // Get diagram data for a project
  getDiagram: (id: string): Promise<AxiosResponse<{ nodes: DiagramNode[]; edges: DiagramEdge[]; metadata: any }>> =>
    apiClient.get(`/projects/${id}/diagram/`),

  // Get specification for a project
  getSpecification: (id: string): Promise<AxiosResponse<Specification>> =>
    apiClient.get(`/projects/${id}/specification/`),

  // Parse text input and generate initial diagram/spec
  parseText: (data: TextParseRequest): Promise<AxiosResponse<any>> =>
    apiClient.post(`/projects/${data.project_id}/parse/`, { text: data.text }),

  // Export project in various formats
  exportProject: (data: ExportRequest): Promise<AxiosResponse<Blob>> =>
    apiClient.post(`/projects/${data.project_id}/export/`, { format: data.format }, {
      responseType: 'blob'
    }),

  // Create shareable link
  createShareLink: (id: string): Promise<AxiosResponse<{ share_token: string; public_url: string }>> =>
    apiClient.post(`/projects/${id}/share/`),
};

// Entity API
export const entityApi = {
  // Get all entities for user's projects
  getEntities: (): Promise<AxiosResponse<PaginatedResponse<Entity>>> =>
    apiClient.get('/entities/'),

  // Create a new entity
  createEntity: (data: Partial<Entity>): Promise<AxiosResponse<Entity>> =>
    apiClient.post('/entities/', data),

  // Update an entity
  updateEntity: (id: string, data: Partial<Entity>): Promise<AxiosResponse<Entity>> =>
    apiClient.put(`/entities/${id}/`, data),

  // Delete an entity
  deleteEntity: (id: string): Promise<AxiosResponse<void>> =>
    apiClient.delete(`/entities/${id}/`),
};

// Relationship API
export const relationshipApi = {
  // Get all relationships for user's projects
  getRelationships: (): Promise<AxiosResponse<PaginatedResponse<Relationship>>> =>
    apiClient.get('/relationships/'),

  // Create a new relationship
  createRelationship: (data: Partial<Relationship>): Promise<AxiosResponse<Relationship>> =>
    apiClient.post('/relationships/', data),

  // Update a relationship
  updateRelationship: (id: string, data: Partial<Relationship>): Promise<AxiosResponse<Relationship>> =>
    apiClient.put(`/relationships/${id}/`, data),

  // Delete a relationship
  deleteRelationship: (id: string): Promise<AxiosResponse<void>> =>
    apiClient.delete(`/relationships/${id}/`),
};

// Diagram Node API
export const diagramNodeApi = {
  // Get all diagram nodes for user's projects
  getNodes: (): Promise<AxiosResponse<PaginatedResponse<DiagramNode>>> =>
    apiClient.get('/diagram-nodes/'),

  // Create a new diagram node
  createNode: (data: Partial<DiagramNode>): Promise<AxiosResponse<DiagramNode>> =>
    apiClient.post('/diagram-nodes/', data),

  // Update a diagram node
  updateNode: (id: string, data: Partial<DiagramNode>): Promise<AxiosResponse<DiagramNode>> =>
    apiClient.put(`/diagram-nodes/${id}/`, data),

  // Delete a diagram node
  deleteNode: (id: string): Promise<AxiosResponse<void>> =>
    apiClient.delete(`/diagram-nodes/${id}/`),
};

// Diagram Edge API
export const diagramEdgeApi = {
  // Get all diagram edges for user's projects
  getEdges: (): Promise<AxiosResponse<PaginatedResponse<DiagramEdge>>> =>
    apiClient.get('/diagram-edges/'),

  // Create a new diagram edge
  createEdge: (data: Partial<DiagramEdge>): Promise<AxiosResponse<DiagramEdge>> =>
    apiClient.post('/diagram-edges/', data),

  // Update a diagram edge
  updateEdge: (id: string, data: Partial<DiagramEdge>): Promise<AxiosResponse<DiagramEdge>> =>
    apiClient.put(`/diagram-edges/${id}/`, data),

  // Delete a diagram edge
  deleteEdge: (id: string): Promise<AxiosResponse<void>> =>
    apiClient.delete(`/diagram-edges/${id}/`),
};

// Specification API
export const specificationApi = {
  // Get all specifications for user's projects
  getSpecifications: (): Promise<AxiosResponse<PaginatedResponse<Specification>>> =>
    apiClient.get('/specifications/'),

  // Create a new specification
  createSpecification: (data: Partial<Specification>): Promise<AxiosResponse<Specification>> =>
    apiClient.post('/specifications/', data),

  // Update a specification
  updateSpecification: (id: string, data: Partial<Specification>): Promise<AxiosResponse<Specification>> =>
    apiClient.put(`/specifications/${id}/`, data),

  // Delete a specification
  deleteSpecification: (id: string): Promise<AxiosResponse<void>> =>
    apiClient.delete(`/specifications/${id}/`),
};

// Export the configured axios instance for custom requests
export default apiClient;