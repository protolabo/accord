import { Request, Response } from "express";

export interface Controller {
  getAuthUrl(req: Request, res: Response): Promise<void>;
  handleAuthCallback(req: Request, res: Response): Promise<void>;
  fetchEmails(req: Request, res: Response): Promise<void>;
  getEmailById(req: Request, res: Response): Promise<void>;
  sendEmail(req: Request, res: Response): Promise<void>;
  markAsRead(req: Request, res: Response): Promise<void>;
  getFolders(req: Request, res: Response): Promise<void>;
  getUserProfile(req: Request, res: Response): Promise<void>;
}
