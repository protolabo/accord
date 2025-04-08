import axios from "axios";

export type EmailService = "gmail" | "outlook";

export interface StandardizedEmail {
  id: string;
  external_id: string;
  platform: string;
  subject: string;
  from: string;
  from_email: string;
  to: string[];
  cc: string[];
  bcc?: string[];
  body: string;
  bodyType: "html" | "text";
  date: string | Date;
  isRead: boolean;
  isImportant: boolean;
  attachments: {
    filename: string;
    content_type: string;
    size: number;
    content_id?: string;
    url?: string;
  }[];
  categories: string[];
  labels?: string[];
  threadId?: string;
}

export interface Folder {
  id: string;
  name: string;
  platform: string;
  type: string;
  unreadCount?: number;
}

export interface UserProfile {
  email: string;
  name?: string;
  picture?: string;
  platform: string;
  authenticated: boolean;
}

export interface EmailFetchOptions {
  limit?: number;
  skip?: number;
  folder?: string;
  query?: string;
}

class EmailAPIService {
  private baseUrl: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private service: EmailService | null = null;

  constructor() {
    this.baseUrl = process.env.REACT_APP_API_URL || "http://localhost:8000/api";
  }

  private getHeaders() {
    return {
      "Content-Type": "application/json",
      Authorization: this.accessToken ? `Bearer ${this.accessToken}` : "",
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

  async getAuthUrl(service: EmailService): Promise<string> {
    try {
      // Notre nouvelle API utilise des routes différentes pour l'authentification
      const response = await axios.get(`${this.baseUrl}/auth/${service}/login`);
      return response.data.auth_url;
    } catch (error) {
      console.error(`Error getting ${service} auth URL:`, error);
      throw error;
    }
  }

  async handleAuthCallback(
    code: string,
    service: EmailService
  ): Promise<{ accessToken: string; refreshToken?: string }> {
    try {
      const response = await axios.get(
        `${this.baseUrl}/auth/${service}/callback`,
        {
          params: { code },
        }
      );

      const { access_token, refresh_token } = response.data;
      this.setTokens(access_token, refresh_token);
      this.setService(service);

      return { accessToken: access_token, refreshToken: refresh_token };
    } catch (error) {
      console.error(`Error handling ${service} auth callback:`, error);
      throw error;
    }
  }

  async fetchEmails(
    options: EmailFetchOptions = {}
  ): Promise<StandardizedEmail[]> {
    const service = this.getService();
    this.getTokens(); // Ensure we have tokens loaded

    if (!this.accessToken) {
      throw new Error("Not authenticated");
    }

    try {
      // Notre nouvelle API standardisée
      const response = await axios.get(`${this.baseUrl}/emails`, {
        headers: this.getHeaders(),
        params: {
          ...options,
          platform: service,
        },
      });

      // Transformer les dates en objets Date
      const emails = response.data.emails.map((email: any) => ({
        ...email,
        date: new Date(email.date),
      }));

      return emails;
    } catch (error) {
      console.error("Error fetching emails:", error);
      throw error;
    }
  }

  async fetchEmailById(id: string): Promise<StandardizedEmail> {
    const service = this.getService();
    this.getTokens(); // Ensure we have tokens loaded

    if (!this.accessToken) {
      throw new Error("Not authenticated");
    }

    try {
      const response = await axios.get(`${this.baseUrl}/emails/${id}`, {
        headers: this.getHeaders(),
        params: {
          platform: service,
        },
      });

      // Transformer la date en objet Date
      const email = {
        ...response.data,
        date: new Date(response.data.date),
      };

      return email;
    } catch (error) {
      console.error(`Error fetching email with ID ${id}:`, error);
      throw error;
    }
  }

  async sendEmail(email: {
    to: string[];
    cc?: string[];
    bcc?: string[];
    subject: string;
    body: string;
    body_type: string;
  }): Promise<{ success: boolean; message_id?: string }> {
    const service = this.getService();
    this.getTokens(); // Ensure we have tokens loaded

    if (!this.accessToken) {
      throw new Error("Not authenticated");
    }

    try {
      const response = await axios.post(`${this.baseUrl}/emails`, email, {
        headers: this.getHeaders(),
        params: {
          platform: service,
        },
      });

      return response.data;
    } catch (error) {
      console.error("Error sending email:", error);
      throw error;
    }
  }

  async markAsRead(id: string, read: boolean = true): Promise<boolean> {
    const service = this.getService();
    this.getTokens(); // Ensure we have tokens loaded

    if (!this.accessToken) {
      throw new Error("Not authenticated");
    }

    try {
      const response = await axios.patch(
        `${this.baseUrl}/emails/${id}/read`,
        {},
        {
          headers: this.getHeaders(),
          params: {
            platform: service,
            read,
          },
        }
      );

      return response.data.success;
    } catch (error) {
      console.error(`Error marking email ${id} as read:`, error);
      throw error;
    }
  }

  async getFolders(): Promise<Folder[]> {
    const service = this.getService();
    this.getTokens(); // Ensure we have tokens loaded

    if (!this.accessToken) {
      throw new Error("Not authenticated");
    }

    try {
      const response = await axios.get(`${this.baseUrl}/folders`, {
        headers: this.getHeaders(),
        params: {
          platform: service,
        },
      });

      return response.data.folders;
    } catch (error) {
      console.error("Error fetching folders:", error);
      throw error;
    }
  }

  async getUserProfile(): Promise<UserProfile> {
    const service = this.getService();
    this.getTokens(); // Ensure we have tokens loaded

    if (!this.accessToken) {
      throw new Error("Not authenticated");
    }

    try {
      const response = await axios.get(`${this.baseUrl}/profile`, {
        headers: this.getHeaders(),
        params: {
          platform: service,
        },
      });

      return response.data;
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
