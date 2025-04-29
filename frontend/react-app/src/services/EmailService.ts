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
    // Pointing to FastAPI backend on port 8000
    this.baseUrl = process.env.REACT_APP_API_URL || "http://localhost:8000";
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

  async getAuthUrl(): Promise<string> {
    try {
      const service = this.getService();
      if (!service) {
        throw new Error("No email service selected");
      }

      // Correction de l'URL pour correspondre à la route backend
      const response = await axios.get(`${this.baseUrl}/auth/${service}`);
      return response.data.auth_url;
    } catch (error) {
      console.error(`Error getting auth URL:`, error);
      throw error;
    }
  }

  async handleAuthCallback(
    code: string
  ): Promise<{ accessToken: string; refreshToken?: string }> {
    try {
      const service = this.getService();
      if (!service) {
        throw new Error("No email service selected");
      }

      // Correction de l'URL pour correspondre à la route backend
      const response = await axios.get(`${this.baseUrl}/auth/callback`, {
        params: { code, state: service },
      });

      // Adapter selon la structure de la réponse du backend
      const access_token = response.data.access_token || "";
      const refresh_token = response.data.refresh_token || "";

      this.setTokens(access_token, refresh_token);

      return { accessToken: access_token, refreshToken: refresh_token };
    } catch (error) {
      console.error(`Error handling auth callback:`, error);
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
      // Using the correct FastAPI route path from your backend/app/routes/emails.py
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
      body_type: string;
      subject: string;
      from: string;
      to: string[];
      cc: string[];
      body: string;
      bodyType: string;
      attachments: any[];
      categories: any[];
      importance: string;
      isRead: boolean
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

  // Nouvelle méthode pour déclencher l'exportation des emails Gmail
  async exportGmailEmails(
    email: string,
    maxEmails?: number,
    outputDir?: string,
    batchSize?: number
  ): Promise<{ status: string; message: string }> {
    try {
      const service = this.getService();
      if (service !== "gmail") {
        throw new Error("Cette fonction ne fonctionne qu'avec Gmail");
      }

      const response = await axios.post(
        `${this.baseUrl}/export/gmail`,
        {
          email,
          max_emails: maxEmails,
          output_dir: outputDir,
          batch_size: batchSize,
        },
        {
          headers: { "Content-Type": "application/json" },
        }
      );

      return {
        status: response.data.status,
        message: response.data.message,
      };
    } catch (error) {
      console.error("Erreur lors de l'exportation des emails Gmail:", error);
      throw error;
    }
  }

  // Nouvelle méthode pour vérifier le statut de la classification des emails
  async checkClassificationStatus(outputDir?: string): Promise<{
    status: string;
    mode?: string;
    total_emails?: number;
    total_batches?: number;
    message?: string;
  }> {
    try {
      const response = await axios.get(
        `${this.baseUrl}/classified-emails/status`,
        {
          params: { output_dir: outputDir },
        }
      );

      return response.data;
    } catch (error) {
      console.error(
        "Erreur lors de la vérification du statut de classification:",
        error
      );
      throw error;
    }
  }

  // Nouvelle méthode pour récupérer les emails classifiés
  async getClassifiedEmails(
    batchNumber?: number,
    outputDir?: string
  ): Promise<{ total_emails: number; emails: any[] }> {
    try {
      const response = await axios.get(`${this.baseUrl}/classified-emails`, {
        params: {
          batch_number: batchNumber,
          output_dir: outputDir,
        },
      });

      return response.data;
    } catch (error) {
      console.error(
        "Erreur lors de la récupération des emails classifiés:",
        error
      );
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
