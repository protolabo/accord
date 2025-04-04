const dotenv = require("dotenv");
const GmailProvider = require("./GmailProvider").GmailProvider;
const OutlookProvider = require("./OutlookProvider").OutlookProvider;
const MockEmailProvider = require("./MockEmailProvider").MockEmailProvider;

// Import types for better TypeScript support
import { Request, Response } from "express";

dotenv.config();

// Define email service type
type EmailServiceType = "gmail" | "outlook";

class EmailProviderFactory {
  static providers = new Map();
  static mockProvider = new MockEmailProvider();
  static useMock = process.env.USE_MOCK_PROVIDER === "true";

  static getProvider(type: EmailServiceType) {
    // Return mock provider if environment variable is set
    if (this.useMock) {
      console.log("Using mock email provider");
      return this.mockProvider;
    }

    if (this.providers.has(type)) {
      return this.providers.get(type);
    }

    let provider;

    switch (type) {
      case "gmail":
        provider = new GmailProvider(
          process.env.GMAIL_CLIENT_ID || "",
          process.env.GMAIL_CLIENT_SECRET || "",
          process.env.GMAIL_REDIRECT_URI || ""
        );
        break;

      case "outlook":
        provider = new OutlookProvider(
          process.env.OUTLOOK_CLIENT_ID || "",
          process.env.OUTLOOK_CLIENT_SECRET || "",
          process.env.OUTLOOK_REDIRECT_URI || "",
          process.env.OUTLOOK_TENANT_ID || "common"
        );
        break;

      default:
        throw new Error(`Unsupported email service type: ${type}`);
    }

    this.providers.set(type, provider);
    return provider;
  }
}

module.exports = {
  EmailProviderFactory,
  EmailServiceType: ["gmail", "outlook"] as EmailServiceType[],
};
