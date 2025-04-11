import { google, gmail_v1 } from "googleapis";
import {
  EmailProvider,
  StandardizedEmail,
  EmailFetchOptions,
} from "./interfaces/EmailProvider";

export class GmailProvider implements EmailProvider {
  private oauth2Client;
  private gmailClient: gmail_v1.Gmail | null = null;

  constructor(
    private clientId: string,
    private clientSecret: string,
    private redirectUri: string
  ) {
    this.oauth2Client = new google.auth.OAuth2(
      clientId,
      clientSecret,
      redirectUri
    );
  }

  getAuthUrl(): string {
    const scopes = [
      "https://www.googleapis.com/auth/gmail.readonly",
      "https://www.googleapis.com/auth/gmail.send",
      "https://www.googleapis.com/auth/gmail.modify",
      "https://www.googleapis.com/auth/userinfo.profile",
      "https://www.googleapis.com/auth/userinfo.email",
    ];

    return this.oauth2Client.generateAuthUrl({
      access_type: "offline",
      scope: scopes,
    });
  }

  async handleAuthCallback(
    code: string
  ): Promise<{ accessToken: string; refreshToken?: string }> {
    const { tokens } = await this.oauth2Client.getToken(code);
    this.oauth2Client.setCredentials(tokens);

    return {
      accessToken: tokens.access_token || "",
      refreshToken: tokens.refresh_token || undefined,
    };
  }

  async refreshAccessToken(
    refreshToken: string
  ): Promise<{ accessToken: string; expiresIn: number }> {
    this.oauth2Client.setCredentials({ refresh_token: refreshToken });
    const { credentials } = await this.oauth2Client.refreshAccessToken();

    return {
      accessToken: credentials.access_token || "",
      expiresIn: credentials.expiry_date
        ? Math.floor((credentials.expiry_date - Date.now()) / 1000)
        : 3600,
    };
  }

  private initializeGmailClient(): void {
    if (!this.gmailClient) {
      this.gmailClient = google.gmail({
        version: "v1",
        auth: this.oauth2Client,
      });
    }
  }

  // Helper to convert Gmail message to StandardizedEmail
  private convertGmailMessageToStandardized(
    message: gmail_v1.Schema$Message
  ): StandardizedEmail {
    this.initializeGmailClient();

    const headers = message.payload?.headers || [];
    const subject =
      headers.find((h) => h.name?.toLowerCase() === "subject")?.value || "";
    const from =
      headers.find((h) => h.name?.toLowerCase() === "from")?.value || "";
    const to =
      headers
        .find((h) => h.name?.toLowerCase() === "to")
        ?.value?.split(",")
        .map((e) => e.trim()) || [];
    const cc =
      headers
        .find((h) => h.name?.toLowerCase() === "cc")
        ?.value?.split(",")
        .map((e) => e.trim()) || [];
    const date = new Date(
      headers.find((h) => h.name?.toLowerCase() === "date")?.value || ""
    );

    // Extract body based on MIME type
    let body = "";
    let bodyType: "html" | "text" = "text";

    const getBodyFromPart = (
      part: gmail_v1.Schema$MessagePart | undefined
    ): void => {
      if (!part) return;

      if (part.mimeType === "text/html") {
        body = Buffer.from(part.body?.data || "", "base64").toString("utf-8");
        bodyType = "html";
      } else if (part.mimeType === "text/plain" && bodyType !== "html") {
        body = Buffer.from(part.body?.data || "", "base64").toString("utf-8");
        bodyType = "text";
      }

      if (part.parts) {
        part.parts.forEach(getBodyFromPart);
      }
    };

    getBodyFromPart(message.payload);

    // Extract attachments
    const attachments: Array<{
      filename: string;
      contentType: string;
      size: number;
      contentId?: string;
      url?: string;
    }> = [];

    const extractAttachments = (
      part: gmail_v1.Schema$MessagePart | undefined
    ) => {
      if (!part) return;

      if (part.filename && part.filename.length > 0 && part.body) {
        attachments.push({
          filename: part.filename,
          contentType: part.mimeType || "application/octet-stream",
          size: parseInt(String(part.body.size || "0"), 10),
          contentId:
            part.headers?.find((h) => h.name?.toLowerCase() === "content-id")
              ?.value || undefined,
          url: part.body.attachmentId
            ? `https://gmail.googleapis.com/gmail/v1/users/me/messages/${message.id}/attachments/${part.body.attachmentId}`
            : undefined,
        });
      }

      if (part.parts) {
        part.parts.forEach(extractAttachments);
      }
    };

    if (message.payload) {
      extractAttachments(message.payload);
    }

    // Map Gmail labels to categories
    const categories: string[] = [];
    const labelMap: { [key: string]: string } = {
      IMPORTANT: "important",
      CATEGORY_PERSONAL: "personal",
      CATEGORY_SOCIAL: "social",
      CATEGORY_PROMOTIONS: "promotions",
      CATEGORY_UPDATES: "updates",
      CATEGORY_FORUMS: "forums",
    };

    if (message.labelIds) {
      message.labelIds.forEach((label) => {
        if (labelMap[label]) {
          categories.push(labelMap[label]);
        }
      });
    }

    // Determine importance
    let importance: "high" | "normal" | "low" = "normal";
    if (message.labelIds?.includes("IMPORTANT")) {
      importance = "high";
    }

    return {
      id: message.id || "",
      subject,
      from,
      to,
      cc,
      body,
      bodyType,
      date,
      isRead: !message.labelIds?.includes("UNREAD"),
      attachments,
      categories,
      importance,
      threadId: message.threadId || undefined,
      originalPayload: message,
    };
  }

  async fetchEmails(
    options: EmailFetchOptions = {}
  ): Promise<StandardizedEmail[]> {
    this.initializeGmailClient();

    if (!this.gmailClient) {
      throw new Error("Gmail client not initialized");
    }

    try {
      const query = options.filter || "";
      const maxResults = options.limit || 50;

      const response = await this.gmailClient.users.messages.list({
        userId: "me",
        maxResults,
        q: query,
        labelIds: options.folderId ? [options.folderId] : undefined,
      });

      const messages = response.data.messages || [];
      const standardizedEmails: StandardizedEmail[] = [];

      for (const messageRef of messages) {
        if (messageRef.id) {
          const messageResponse = await this.gmailClient.users.messages.get({
            userId: "me",
            id: messageRef.id,
            format: "full",
          });

          standardizedEmails.push(
            this.convertGmailMessageToStandardized(messageResponse.data)
          );
        }
      }

      return standardizedEmails;
    } catch (error) {
      console.error("Error fetching Gmail messages:", error);
      throw error;
    }
  }

  async fetchEmailById(id: string): Promise<StandardizedEmail> {
    this.initializeGmailClient();

    if (!this.gmailClient) {
      throw new Error("Gmail client not initialized");
    }

    try {
      const response = await this.gmailClient.users.messages.get({
        userId: "me",
        id,
        format: "full",
      });

      return this.convertGmailMessageToStandardized(response.data);
    } catch (error) {
      console.error(`Error fetching Gmail message with ID ${id}:`, error);
      throw error;
    }
  }

  async sendEmail(
    email: Omit<StandardizedEmail, "id" | "date">
  ): Promise<{ success: boolean; id?: string }> {
    this.initializeGmailClient();

    if (!this.gmailClient) {
      throw new Error("Gmail client not initialized");
    }

    try {
      // Construct RFC 2822 formatted email
      let emailContent = "";
      emailContent += `From: ${email.from}\r\n`;
      emailContent += `To: ${email.to.join(", ")}\r\n`;

      if (email.cc.length > 0) {
        emailContent += `Cc: ${email.cc.join(", ")}\r\n`;
      }

      emailContent += `Subject: ${email.subject}\r\n`;
      emailContent += `Content-Type: ${
        email.bodyType === "html" ? "text/html" : "text/plain"
      }; charset=UTF-8\r\n\r\n`;
      emailContent += email.body;

      // Encode the email
      const encodedEmail = Buffer.from(emailContent)
        .toString("base64")
        .replace(/\+/g, "-")
        .replace(/\//g, "_")
        .replace(/=+$/, "");

      // Send the email
      const response = await this.gmailClient.users.messages.send({
        userId: "me",
        requestBody: {
          raw: encodedEmail,
        },
      });

      return {
        success: true,
        id: response.data.id || undefined,
      };
    } catch (error) {
      console.error("Error sending Gmail message:", error);
      return { success: false };
    }
  }

  async markAsRead(id: string): Promise<boolean> {
    this.initializeGmailClient();

    if (!this.gmailClient) {
      throw new Error("Gmail client not initialized");
    }

    try {
      await this.gmailClient.users.messages.modify({
        userId: "me",
        id,
        requestBody: {
          removeLabelIds: ["UNREAD"],
        },
      });

      return true;
    } catch (error) {
      console.error(`Error marking Gmail message ${id} as read:`, error);
      return false;
    }
  }

  async getFolders(): Promise<
    { id: string; name: string; unreadCount: number }[]
  > {
    this.initializeGmailClient();

    if (!this.gmailClient) {
      throw new Error("Gmail client not initialized");
    }

    try {
      const response = await this.gmailClient.users.labels.list({
        userId: "me",
      });

      const labels = response.data.labels || [];
      const folders = [];

      for (const label of labels) {
        if (label.id && label.name) {
          // Get unread count for this label
          const countResponse = await this.gmailClient.users.messages.list({
            userId: "me",
            labelIds: [label.id, "UNREAD"],
            maxResults: 1,
          });

          folders.push({
            id: label.id,
            name: label.name,
            unreadCount: countResponse.data.resultSizeEstimate || 0,
          });
        }
      }

      return folders;
    } catch (error) {
      console.error("Error fetching Gmail folders:", error);
      throw error;
    }
  }

  async getUserProfile(): Promise<{
    email: string;
    name: string;
    picture?: string;
  }> {
    const oauth2 = google.oauth2({
      auth: this.oauth2Client,
      version: "v2",
    });

    try {
      const response = await oauth2.userinfo.get();

      return {
        email: response.data.email || "",
        name: response.data.name || "",
        picture: response.data.picture || undefined,
      };
    } catch (error) {
      console.error("Error fetching Gmail user profile:", error);
      throw error;
    }
  }
}
