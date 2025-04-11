const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");
// Import routes properly to avoid undefined middleware
const emailRoutes = require("./routes/emailRoutes");

// Load environment variables
dotenv.config();

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Import types for Express
import { Request, Response, NextFunction } from "express";

// Debug middleware
app.use((req: Request, res: Response, next: NextFunction) => {
  console.log(`${req.method} ${req.url}`);
  next();
});

// Routes
app.use("/api/email", emailRoutes);

// Test route
app.get("/api/health", (req: Request, res: Response) => {
  res.json({ status: "ok", message: "Server is running" });
});

// Start server
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
  console.log(`Email API available at http://localhost:${port}/api/email`);
  console.log(`Health check at http://localhost:${port}/api/health`);
  console.log(`Environment: ${process.env.NODE_ENV}`);
  console.log(
    `Using mock provider: ${process.env.USE_MOCK_PROVIDER === "true"}`
  );
});
