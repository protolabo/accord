import { Router } from "express";
const EmailController = require("../controllers/EmailController");

const router = Router();

// Authentication routes
router.get("/:service/auth", EmailController.getAuthUrl);
router.get("/:service/auth/callback", EmailController.handleAuthCallback);

// Email operations
router.get("/:service/emails", EmailController.fetchEmails);
router.get("/:service/emails/:emailId", EmailController.getEmailById);
router.post("/:service/emails", EmailController.sendEmail);
router.patch("/:service/emails/:emailId/read", EmailController.markAsRead);

// Folders
router.get("/:service/folders", EmailController.getFolders);

// User profile
router.get("/:service/profile", EmailController.getUserProfile);

// Export the router directly (don't use exports.default)
module.exports = router;
