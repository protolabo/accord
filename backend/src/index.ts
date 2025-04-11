import express from "express";
import cors from "cors";
import dotenv from "dotenv";
// Importez vos contrôleurs ici
import * as EmailController from "../controllers/EmailController";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;
const FRONTEND_URL = process.env.FRONTEND_URL || "http://localhost:3000";

// Configuration CORS
app.use(
  cors({
    origin: FRONTEND_URL,
    credentials: true,
  })
);

// Body parsing middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Logging middleware for debugging
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// Définition des routes API pour les services de courriel
app.get("/api/email/:service/auth", EmailController.getAuthUrl);

// Autres routes API...

// Route par défaut pour les APIs non définies
app.use("/api/*", (req, res) => {
  res.status(404).json({ error: "API endpoint not found" });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Frontend URL: ${FRONTEND_URL}`);
});
