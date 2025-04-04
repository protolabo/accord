import axios from "axios";

export type EmailService = "gmail" | "outlook";

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
}

export interface Folder {
  id: string;
  name: string;
  unreadCount: number;
}

export interface UserProfile {
  email: string;
  name: string;
  picture?: string;
}

export interface EmailFetchOptions {
  limit?: number;
  offset?: number;
  filter?: string;
  includeAttachments?: boolean;
  folderId?: string;
}

class EmailAPIService {
  private baseUrl: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private service: EmailService | null = null;

  constructor() {
    this.baseUrl =
      process.env.REACT_APP_API_URL || "http://localhost:3000/api/email";
  }

  private getHeaders() {
    return {
      "Content-Type": "application/json",
      ...(this.accessToken ? { accessToken: this.accessToken } : {}),
    };
  }

  setService(service: EmailService) {
    this.service = service;
    // Store the selected service in localStorage for persistence
    localStorage.setItem("emailService", service);
    return this;
  }

  getService(): EmailService | null {
    if (!this.service) {
      // Try to get from localStorage
      const savedService = localStorage.getItem("emailService");
      if (savedService === "gmail" || savedService === "outlook") {
        this.service = savedService;
      }
    }
    return this.service;
  }

  setTokens(accessToken: string, refreshToken?: string) {
    this.accessToken = accessToken;
    if (refreshToken) {
      this.refreshToken = refreshToken;
    }

    // Store tokens securely (in a real app, consider using HTTP-only cookies)
    localStorage.setItem("emailAccessToken", accessToken);
    if (refreshToken) {
      localStorage.setItem("emailRefreshToken", refreshToken);
    }

    return this;
  }

  getTokens() {
    if (!this.accessToken) {
      const savedToken = localStorage.getItem("emailAccessToken");
      if (savedToken) {
        this.accessToken = savedToken;
      }
    }

    if (!this.refreshToken) {
      const savedRefreshToken = localStorage.getItem("emailRefreshToken");
      if (savedRefreshToken) {
        this.refreshToken = savedRefreshToken;
      }
    }

    return {
      accessToken: this.accessToken,
      refreshToken: this.refreshToken,
    };
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem("emailAccessToken");
    localStorage.removeItem("emailRefreshToken");
    return this;
  }

  async getAuthUrl(): Promise<string> {
    if (!this.service) {
      throw new Error("Email service not selected");
    }

    try {
      const response = await axios.get(`${this.baseUrl}/${this.service}/auth`);
      return response.data.authUrl;
    } catch (error) {
      console.error("Error getting auth URL:", error);
      throw error;
    }
  }

  async handleAuthCallback(
    code: string
  ): Promise<{ accessToken: string; refreshToken?: string }> {
    if (!this.service) {
      throw new Error("Email service not selected");
    }

    try {
      const response = await axios.get(
        `${this.baseUrl}/${this.service}/auth/callback`,
        {
          params: { code },
        }
      );

      const { accessToken, refreshToken } = response.data;
      this.setTokens(accessToken, refreshToken);

      return { accessToken, refreshToken };
    } catch (error) {
      console.error("Error handling auth callback:", error);
      throw error;
    }
  }

  async fetchEmails(
    options: EmailFetchOptions = {}
  ): Promise<StandardizedEmail[]> {
    if (!this.service) {
      throw new Error("Email service not selected");
    }

    this.getTokens(); // Ensure we have tokens loaded

    if (!this.accessToken) {
      throw new Error("Not authenticated");
    }

    try {
      const response = await axios.get(
        `${this.baseUrl}/${this.service}/emails`,
        {
          headers: this.getHeaders(),
          params: options,
        }
      );

      return response.data.emails;
    } catch (error) {
      console.error("Error fetching emails:", error);
      throw error;
    }
  }

  async fetchEmailById(id: string): Promise<StandardizedEmail> {
    if (!this.service) {
      throw new Error("Email service not selected");
    }

    this.getTokens(); // Ensure we have tokens loaded

    if (!this.accessToken) {
      throw new Error("Not authenticated");
    }

    try {
      const response = await axios.get(
        `${this.baseUrl}/${this.service}/emails/${id}`,
        {
          headers: this.getHeaders(),
        }
      );

      return response.data.email;
    } catch (error) {
      console.error(`Error fetching email with ID ${id}:`, error);
      throw error;
    }
  }

  async sendEmail(
    email: Omit<StandardizedEmail, "id" | "date">
  ): Promise<{ success: boolean; id?: string }> {
    if (!this.service) {
      throw new Error("Email service not selected");
    }

    this.getTokens(); // Ensure we have tokens loaded

    if (!this.accessToken) {
      throw new Error("Not authenticated");
    }

    try {
      const response = await axios.post(
        `${this.baseUrl}/${this.service}/emails`,
        email,
        {
          headers: this.getHeaders(),
        }
      );

      return response.data;
    } catch (error) {
      console.error("Error sending email:", error);
      throw error;
    }
  }

  async markAsRead(id: string): Promise<boolean> {
    if (!this.service) {
      throw new Error("Email service not selected");
    }

    this.getTokens(); // Ensure we have tokens loaded

    if (!this.accessToken) {
      throw new Error("Not authenticated");
    }

    try {
      const response = await axios.patch(
        `${this.baseUrl}/${this.service}/emails/${id}/read`,
        {},
        {
          headers: this.getHeaders(),
        }
      );

      return response.data.success;
    } catch (error) {
      console.error(`Error marking email ${id} as read:`, error);
      throw error;
    }
  }

  async getFolders(): Promise<Folder[]> {
    if (!this.service) {
      throw new Error("Email service not selected");
    }

    this.getTokens(); // Ensure we have tokens loaded

    if (!this.accessToken) {
      throw new Error("Not authenticated");
    }

    try {
      const response = await axios.get(
        `${this.baseUrl}/${this.service}/folders`,
        {
          headers: this.getHeaders(),
        }
      );

      return response.data.folders;
    } catch (error) {
      console.error("Error fetching folders:", error);
      throw error;
    }
  }

  async getUserProfile(): Promise<UserProfile> {
    if (!this.service) {
      throw new Error("Email service not selected");
    }

    this.getTokens(); // Ensure we have tokens loaded

    if (!this.accessToken) {
      throw new Error("Not authenticated");
    }

    try {
      const response = await axios.get(
        `${this.baseUrl}/${this.service}/profile`,
        {
          headers: this.getHeaders(),
        }
      );

      return response.data.profile;
    } catch (error) {
      console.error("Error fetching user profile:", error);
      throw error;
    }
  }

  isAuthenticated(): boolean {
    const { accessToken } = this.getTokens();
    return !!accessToken;
  }
}

// Create singleton instance
const emailAPIService = new EmailAPIService();
export default emailAPIService;
