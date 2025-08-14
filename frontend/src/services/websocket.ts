import { io, Socket } from 'socket.io-client';
import { DiagramChange, SpecChange, SyncConflict } from '../types';

class WebSocketService {
  private socket: Socket | null = null;
  private projectId: string | null = null;
  private userId: string | null = null;

  connect(projectId: string, userId: string): void {
    if (this.socket?.connected) {
      this.disconnect();
    }

    const wsUrl = process.env.REACT_APP_WS_URL || 'http://localhost:8000';
    
    this.socket = io(wsUrl, {
      auth: {
        token: localStorage.getItem('authToken'),
        projectId,
        userId,
      },
      transports: ['websocket', 'polling'],
    });

    this.projectId = projectId;
    this.userId = userId;

    this.setupEventListeners();
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.projectId = null;
    this.userId = null;
  }

  private setupEventListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      if (this.projectId) {
        this.joinProject(this.projectId);
      }
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
    });
  }

  joinProject(projectId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('join_project', { projectId });
    }
  }

  leaveProject(projectId: string): void {
    if (this.socket?.connected) {
      this.socket.emit('leave_project', { projectId });
    }
  }

  // Diagram synchronization events
  onDiagramUpdate(callback: (changes: DiagramChange[]) => void): void {
    this.socket?.on('diagram:update', callback);
  }

  emitDiagramUpdate(changes: DiagramChange[]): void {
    if (this.socket?.connected && this.projectId) {
      this.socket.emit('diagram:update', {
        projectId: this.projectId,
        changes,
      });
    }
  }

  // Specification synchronization events
  onSpecUpdate(callback: (changes: SpecChange[]) => void): void {
    this.socket?.on('spec:update', callback);
  }

  emitSpecUpdate(changes: SpecChange[]): void {
    if (this.socket?.connected && this.projectId) {
      this.socket.emit('spec:update', {
        projectId: this.projectId,
        changes,
      });
    }
  }

  // Conflict resolution events
  onSyncConflict(callback: (conflict: SyncConflict) => void): void {
    this.socket?.on('sync:conflict', callback);
  }

  onSyncResolved(callback: (resolution: any) => void): void {
    this.socket?.on('sync:resolved', callback);
  }

  emitConflictResolution(conflictId: string, resolution: any): void {
    if (this.socket?.connected && this.projectId) {
      this.socket.emit('resolve_conflict', {
        projectId: this.projectId,
        conflictId,
        resolution,
      });
    }
  }

  // User cursor tracking
  onUserCursor(callback: (data: { userId: string; position: { x: number; y: number } }) => void): void {
    this.socket?.on('user:cursor', callback);
  }

  emitCursorPosition(position: { x: number; y: number }): void {
    if (this.socket?.connected && this.projectId && this.userId) {
      this.socket.emit('user:cursor', {
        projectId: this.projectId,
        userId: this.userId,
        position,
      });
    }
  }

  // Project locking for concurrent editing
  onProjectLock(callback: (lockInfo: { userId: string; section: string; locked: boolean }) => void): void {
    this.socket?.on('project:lock', callback);
  }

  emitLockSection(section: string): void {
    if (this.socket?.connected && this.projectId && this.userId) {
      this.socket.emit('lock_section', {
        projectId: this.projectId,
        userId: this.userId,
        section,
      });
    }
  }

  emitUnlockSection(section: string): void {
    if (this.socket?.connected && this.projectId && this.userId) {
      this.socket.emit('unlock_section', {
        projectId: this.projectId,
        userId: this.userId,
        section,
      });
    }
  }

  // Remove event listeners
  removeAllListeners(): void {
    if (this.socket) {
      this.socket.removeAllListeners();
    }
  }

  // Check connection status
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  // Get current project ID
  getCurrentProjectId(): string | null {
    return this.projectId;
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();
export default websocketService;