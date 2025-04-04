import { mockEmails, MockEmail } from "./mockData";

// Import for type definitions
interface EmailFetchOptions {
  limit?: number;
  offset?: number;
  filter?: string;
  includeAttachments?: boolean;
  folderId?: string;
}

interface StandardizedEmail {
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

class MockEmailProvider {
  constructor() {}

  getAuthUrl(): string {
    // Return a dummy auth URL that would redirect back to our callback
    return "http://localhost:3000/auth/callback?code=mock_auth_code";
  }

  async handleAuthCallback(
    code: string
  ): Promise<{ accessToken: string; refreshToken?: string }> {
    // Return mock tokens
    return {
      accessToken: "mock_access_token_" + Date.now(),
      refreshToken: "mock_refresh_token_" + Date.now(),
    };
  }

  async refreshAccessToken(
    refreshToken: string
  ): Promise<{ accessToken: string; expiresIn: number }> {
    return {
      accessToken: "mock_refreshed_token_" + Date.now(),
      expiresIn: 3600,
    };
  }

  async fetchEmails(
    options: EmailFetchOptions = {}
  ): Promise<StandardizedEmail[]> {
    // Convert to StandardizedEmail format
    const standardizedEmails: StandardizedEmail[] = mockEmails.map(
      (email: MockEmail) => ({
        id: email["Message-ID"],
        subject: email.Subject,
        from: email.From,
        to: email.To.split(",").map((e: string) => e.trim()),
        cc: email.Cc.split(",").map((e: string) => e.trim()),
        body: email.Body,
        bodyType: email["Content-Type"].includes("html") ? "html" : "text",
        date: new Date(email.Date),
        isRead: email.IsRead,
        attachments: email.Attachments,
        categories: email.Categories,
        importance: email.Importance,
        threadId: email.ThreadId,
      })
    );

    // Apply filtering and pagination if needed
    let filtered = standardizedEmails;

    if (options.filter) {
      const filter = options.filter.toLowerCase();
      filtered = filtered.filter(
        (email: StandardizedEmail) =>
          email.subject.toLowerCase().includes(filter) ||
          email.from.toLowerCase().includes(filter)
      );
    }

    const start = options.offset || 0;
    const end = options.limit ? start + options.limit : undefined;

    return filtered.slice(start, end);
  }

  async fetchEmailById(id: string): Promise<StandardizedEmail> {
    const email = mockEmails.find((e) => e["Message-ID"] === id);
    if (!email) {
      throw new Error(`Email with ID ${id} not found`);
    }

    return {
      id: email["Message-ID"],
      subject: email.Subject,
      from: email.From,
      to: email.To.split(",").map((e: string) => e.trim()),
      cc: email.Cc.split(",").map((e: string) => e.trim()),
      body: email.Body,
      bodyType: email["Content-Type"].includes("html") ? "html" : "text",
      date: new Date(email.Date),
      isRead: email.IsRead,
      attachments: email.Attachments,
      categories: email.Categories,
      importance: email.Importance,
      threadId: email.ThreadId,
    };
  }

  async sendEmail(
    email: Omit<StandardizedEmail, "id" | "date">
  ): Promise<{ success: boolean; id?: string }> {
    console.log("Mock sending email:", email);
    return {
      success: true,
      id: "mock_email_id_" + Date.now(),
    };
  }

  async markAsRead(id: string): Promise<boolean> {
    console.log("Mock marking email as read:", id);
    return true;
  }

  async getFolders(): Promise<
    { id: string; name: string; unreadCount: number }[]
  > {
    return [
      { id: "inbox", name: "Inbox", unreadCount: 3 },
      { id: "sent", name: "Sent", unreadCount: 0 },
      { id: "drafts", name: "Drafts", unreadCount: 1 },
      { id: "important", name: "Important", unreadCount: 2 },
    ];
  }

  async getUserProfile(): Promise<{
    email: string;
    name: string;
    picture?: string;
  }> {
    return {
      email: "user@example.com",
      name: "Test User",
      picture: "https://via.placeholder.com/150",
    };
  }
}

module.exports = { MockEmailProvider };
