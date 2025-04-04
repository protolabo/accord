import { Request, Response } from "express";
const { EmailProviderFactory } = require("../services/EmailProviderFactory");

const EmailController = {
  // Get authentication URL for a specific service
  async getAuthUrl(req: Request, res: Response) {
    try {
      const { service } = req.params;

      if (!service || (service !== "gmail" && service !== "outlook")) {
        res.status(400).json({ error: "Invalid email service specified" });
        return;
      }

      const provider = EmailProviderFactory.getProvider(service);
      const authUrl = provider.getAuthUrl();

      res.json({ authUrl });
    } catch (error) {
      console.error("Error generating auth URL:", error);
      res.status(500).json({ error: "Failed to generate authentication URL" });
    }
  },

  // Handle auth callback from OAuth provider
  async handleAuthCallback(req: Request, res: Response) {
    try {
      const { service } = req.params;
      const { code } = req.query;

      if (!service || (service !== "gmail" && service !== "outlook") || !code) {
        res.status(400).json({ error: "Invalid request parameters" });
        return;
      }

      const provider = EmailProviderFactory.getProvider(service);
      const tokens = await provider.handleAuthCallback(code as string);

      res.json({
        success: true,
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken,
      });
    } catch (error) {
      console.error("Error handling auth callback:", error);
      res.status(500).json({ error: "Failed to complete authentication" });
    }
  },

  // Fetch emails from the user's account
  async fetchEmails(req: Request, res: Response) {
    try {
      const { service } = req.params;
      const { accessToken } = req.headers;

      if (!service || !accessToken) {
        res.status(400).json({ error: "Missing required parameters" });
        return;
      }

      // Parse query parameters for options
      const options = {
        limit: req.query.limit
          ? parseInt(req.query.limit as string, 10)
          : undefined,
        offset: req.query.offset
          ? parseInt(req.query.offset as string, 10)
          : undefined,
        filter: req.query.filter as string | undefined,
        includeAttachments: req.query.includeAttachments === "true",
        folderId: req.query.folderId as string | undefined,
      };

      const provider = EmailProviderFactory.getProvider(service);
      const emails = await provider.fetchEmails(options);
      res.json({ emails });
    } catch (error) {
      console.error("Error fetching emails:", error);
      res.status(500).json({ error: "Failed to fetch emails" });
    }
  },

  // Get a specific email by ID
  async getEmailById(req: Request, res: Response) {
    try {
      const { service, emailId } = req.params;
      const { accessToken } = req.headers;

      if (!service || !emailId || !accessToken) {
        res.status(400).json({ error: "Missing required parameters" });
        return;
      }

      const provider = EmailProviderFactory.getProvider(service);
      const email = await provider.fetchEmailById(emailId);

      res.json({ email });
    } catch (error) {
      console.error("Error fetching specific email:", error);
      res.status(500).json({ error: "Failed to fetch email" });
    }
  },

  // Send an email
  async sendEmail(req: Request, res: Response) {
    try {
      const { service } = req.params;
      const { accessToken } = req.headers;
      const emailData = req.body;

      if (!service || !accessToken || !emailData) {
        res.status(400).json({ error: "Missing required parameters" });
        return;
      }

      const provider = EmailProviderFactory.getProvider(service);
      const result = await provider.sendEmail(emailData);

      res.json(result);
    } catch (error) {
      console.error("Error sending email:", error);
      res.status(500).json({ error: "Failed to send email" });
    }
  },

  // Mark an email as read
  async markAsRead(req: Request, res: Response) {
    try {
      const { service, emailId } = req.params;
      const { accessToken } = req.headers;

      if (!service || !emailId || !accessToken) {
        res.status(400).json({ error: "Missing required parameters" });
        return;
      }

      const provider = EmailProviderFactory.getProvider(service);
      const success = await provider.markAsRead(emailId);

      res.json({ success });
    } catch (error) {
      console.error("Error marking email as read:", error);
      res.status(500).json({ error: "Failed to mark email as read" });
    }
  },

  // Get folders/labels
  async getFolders(req: Request, res: Response) {
    try {
      const { service } = req.params;
      const { accessToken } = req.headers;

      if (!service || !accessToken) {
        res.status(400).json({ error: "Missing required parameters" });
        return;
      }

      const provider = EmailProviderFactory.getProvider(service);
      const folders = await provider.getFolders();

      res.json({ folders });
    } catch (error) {
      console.error("Error fetching folders:", error);
      res.status(500).json({ error: "Failed to fetch folders" });
    }
  },

  // Get user profile
  async getUserProfile(req: Request, res: Response) {
    try {
      const { service } = req.params;
      const { accessToken } = req.headers;

      if (!service || !accessToken) {
        res.status(400).json({ error: "Missing required parameters" });
        return;
      }

      const provider = EmailProviderFactory.getProvider(service);
      const profile = await provider.getUserProfile();

      res.json({ profile });
    } catch (error) {
      console.error("Error fetching user profile:", error);
      res.status(500).json({ error: "Failed to fetch user profile" });
    }
  },
};

module.exports = EmailController;
