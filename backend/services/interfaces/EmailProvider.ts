export interface StandardizedEmail {
  id: string;
  subject: string;
  from: string;
  to: string[];
  cc: string[];
  body: string;
  bodyType: "html" | "text";
  date: Date;
  isRead: boolean;
  attachments: {
    filename: string;
    contentType: string;
    size: number;
    contentId?: string;
    url?: string;
  }[];
  categories: string[];
  importance: "high" | "normal" | "low";
  threadId?: string;
  originalPayload?: any; // Original provider-specific data
}

export interface EmailFetchOptions {
  limit?: number;
  offset?: number;
  filter?: string;
  includeAttachments?: boolean;
  folderId?: string;
}

export interface EmailProvider {
  // Authentication methods
  getAuthUrl(): string;
  handleAuthCallback(
    code: string
  ): Promise<{ accessToken: string; refreshToken?: string }>;
  refreshAccessToken(
    refreshToken: string
  ): Promise<{ accessToken: string; expiresIn: number }>;

  // Email operations
  fetchEmails(options?: EmailFetchOptions): Promise<StandardizedEmail[]>;
  fetchEmailById(id: string): Promise<StandardizedEmail>;
  sendEmail(
    email: Omit<StandardizedEmail, "id" | "date">
  ): Promise<{ success: boolean; id?: string }>;
  markAsRead(id: string): Promise<boolean>;

  // Folders operations
  getFolders(): Promise<{ id: string; name: string; unreadCount: number }[]>;

  // User profile
  getUserProfile(): Promise<{ email: string; name: string; picture?: string }>;
}
