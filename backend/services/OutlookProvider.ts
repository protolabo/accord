import * as msal from "@azure/msal-node";
import { Client } from "@microsoft/microsoft-graph-client";
import "isomorphic-fetch";
import {
  EmailProvider,
  StandardizedEmail,
  EmailFetchOptions,
} from "./interfaces/EmailProvider";

export class OutlookProvider implements EmailProvider {
  private msalClient: msal.ConfidentialClientApplication;
  private graphClient: Client | null = null;
  private redirectUri: string;

  constructor(
    private clientId: string,
    private clientSecret: string,
    redirectUri: string,
    private tenantId: string = "common"
  ) {
    this.redirectUri = redirectUri;

    this.msalClient = new msal.ConfidentialClientApplication({
      auth: {
        clientId,
        clientSecret,
        authority: `https://login.microsoftonline.com/${tenantId}`,
      },
    });
  }

  getAuthUrl(): string {
    const scopes = ["Mail.Read", "Mail.ReadWrite", "Mail.Send", "User.Read"];

    const authUrlRequest = {
      scopes,
      redirectUri: this.redirectUri,
    };

    // Return a Promise as async and handle it in the UI
    return `https://login.microsoftonline.com/${
      this.tenantId
    }/oauth2/v2.0/authorize?client_id=${
      this.clientId
    }&response_type=code&redirect_uri=${encodeURIComponent(
      this.redirectUri
    )}&scope=${encodeURIComponent(scopes.join(" "))}`;
  }

  async handleAuthCallback(
    code: string
  ): Promise<{ accessToken: string; refreshToken?: string }> {
    const tokenRequest = {
      code,
      scopes: ["Mail.Read", "Mail.ReadWrite", "Mail.Send", "User.Read"],
      redirectUri: this.redirectUri,
    };

    try {
      const response = await this.msalClient.acquireTokenByCode(tokenRequest);

      return {
        accessToken: response.accessToken,
        // The refresh token might not be available in all responses
        refreshToken: response.account?.homeAccountId, // Use a different property since refreshToken isn't directly available
      };
    } catch (error) {
      console.error("Error acquiring token:", error);
      throw error;
    }
  }

  async refreshAccessToken(
    refreshToken: string
  ): Promise<{ accessToken: string; expiresIn: number }> {
    const tokenRequest = {
      refreshToken,
      scopes: ["Mail.Read", "Mail.ReadWrite", "Mail.Send", "User.Read"],
    };

    try {
      const response = await this.msalClient.acquireTokenByRefreshToken(
        tokenRequest
      );

      if (!response) {
        throw new Error("Failed to refresh token");
      }

      return {
        accessToken: response.accessToken,
        expiresIn: response.expiresOn
          ? Math.floor((response.expiresOn.getTime() - Date.now()) / 1000)
          : 3600,
      };
    } catch (error) {
      console.error("Error refreshing token:", error);
      throw error;
    }
  }

  private initGraphClient(accessToken: string): void {
    this.graphClient = Client.init({
      authProvider: (done) => {
        done(null, accessToken);
      },
    });
  }

  // Helper method to convert Outlook message to StandardizedEmail
  private convertOutlookMessageToStandardized(message: any): StandardizedEmail {
    // Extract categories from Outlook categories
    const categories = message.categories || [];

    // Map importance
    let importance: "high" | "normal" | "low";
    switch (message.importance) {
      case "high":
        importance = "high";
        break;
      case "low":
        importance = "low";
        break;
      default:
        importance = "normal";
    }

    // Handle body content
    const bodyType =
      message.body.contentType.toLowerCase() === "html" ? "html" : "text";

    // Extract attachments
    const attachments = (message.attachments || []).map((attachment: any) => ({
      filename: attachment.name,
      contentType: attachment.contentType,
      size: attachment.size,
      contentId: attachment.contentId,
      url: attachment["@microsoft.graph.downloadUrl"],
    }));

    return {
      id: message.id,
      subject: message.subject || "",
      from: message.from?.emailAddress?.address || "",
      to: message.toRecipients?.map((r: any) => r.emailAddress.address) || [],
      cc: message.ccRecipients?.map((r: any) => r.emailAddress.address) || [],
      body: message.body.content,
      bodyType,
      date: new Date(message.receivedDateTime),
      isRead: message.isRead,
      attachments,
      categories,
      importance,
      threadId: message.conversationId,
      originalPayload: message,
    };
  }

  async fetchEmails(
    options: EmailFetchOptions = {}
  ): Promise<StandardizedEmail[]> {
    if (!this.graphClient) {
      throw new Error("Graph client not initialized");
    }

    try {
      let endpoint = "/me/messages";
      const queryParams: any = {
        $top: options.limit || 50,
        $skip: options.offset || 0,
        $orderby: "receivedDateTime desc",
        $expand: "attachments",
      };

      if (options.filter) {
        queryParams.$filter = options.filter;
      }

      if (options.folderId) {
        endpoint = `/me/mailFolders/${options.folderId}/messages`;
      }

      const response = await this.graphClient.api(endpoint).get();
      const messages = response.value || [];

      return messages.map((message: any) =>
        this.convertOutlookMessageToStandardized(message)
      );
    } catch (error) {
      console.error("Error fetching Outlook messages:", error);
      throw error;
    }
  }

  async fetchEmailById(id: string): Promise<StandardizedEmail> {
    if (!this.graphClient) {
      throw new Error("Graph client not initialized");
    }

    try {
      const message = await this.graphClient
        .api(`/me/messages/${id}`)
        .expand("attachments")
        .get();

      return this.convertOutlookMessageToStandardized(message);
    } catch (error) {
      console.error(`Error fetching Outlook message with ID ${id}:`, error);
      throw error;
    }
  }

  async sendEmail(
    email: Omit<StandardizedEmail, "id" | "date">
  ): Promise<{ success: boolean; id?: string }> {
    if (!this.graphClient) {
      throw new Error("Graph client not initialized");
    }

    try {
      const message = {
        subject: email.subject,
        body: {
          contentType: email.bodyType,
          content: email.body,
        },
        toRecipients: email.to.map((recipient) => ({
          emailAddress: {
            address: recipient,
          },
        })),
        ccRecipients: email.cc.map((recipient) => ({
          emailAddress: {
            address: recipient,
          },
        })),
        importance: email.importance,
      };

      const response = await this.graphClient.api("/me/sendMail").post({
        message,
        saveToSentItems: true,
      });

      return { success: true };
    } catch (error) {
      console.error("Error sending Outlook message:", error);
      return { success: false };
    }
  }

  async markAsRead(id: string): Promise<boolean> {
    if (!this.graphClient) {
      throw new Error("Graph client not initialized");
    }

    try {
      await this.graphClient.api(`/me/messages/${id}`).update({
        isRead: true,
      });

      return true;
    } catch (error) {
      console.error(`Error marking Outlook message ${id} as read:`, error);
      return false;
    }
  }

  async getFolders(): Promise<
    { id: string; name: string; unreadCount: number }[]
  > {
    if (!this.graphClient) {
      throw new Error("Graph client not initialized");
    }

    try {
      const response = await this.graphClient
        .api("/me/mailFolders")
        .select("id,displayName,unreadItemCount")
        .get();

      return (response.value || []).map((folder: any) => ({
        id: folder.id,
        name: folder.displayName,
        unreadCount: folder.unreadItemCount,
      }));
    } catch (error) {
      console.error("Error fetching Outlook folders:", error);
      throw error;
    }
  }

  async getUserProfile(): Promise<{
    email: string;
    name: string;
    picture?: string;
  }> {
    if (!this.graphClient) {
      throw new Error("Graph client not initialized");
    }

    try {
      const user = await this.graphClient
        .api("/me")
        .select("displayName,mail,userPrincipalName")
        .get();

      // Try to get profile photo
      let photoUrl;
      try {
        const photo = await this.graphClient.api("/me/photo/$value").get();

        if (photo) {
          // Convert to data URL or store and create a URL
          const photoBlob = new Blob([photo], { type: "image/jpeg" });
          photoUrl = URL.createObjectURL(photoBlob);
        }
      } catch (photoError) {
        console.log("No profile photo found");
      }

      return {
        email: user.mail || user.userPrincipalName,
        name: user.displayName,
        picture: photoUrl,
      };
    } catch (error) {
      console.error("Error fetching Outlook user profile:", error);
      throw error;
    }
  }
}
