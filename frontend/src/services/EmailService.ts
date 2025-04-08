import axios from "axios";
import config from "../config";

// Utiliser directement l'URL de l'API depuis les variables d'environnement
const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Remplacez toutes les occurrences de '/api/' par:
const API_BASE_URL = `${config.apiBaseUrl}/api`;

// Types et interfaces pour les entités standardisées
export type EmailService = "gmail" | "outlook";

export interface StandardizedAttachment {
  filename: string;
  content_type: string;
  size: number;
  content_id?: string;
  url?: string;
}

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
  attachments: StandardizedAttachment[];
  categories: string[];
  labels?: string[];
  threadId?: string;
}

export interface EmailFolder {
  id: string;
  name: string;
  platform: string;
  type: string;
  unreadCount?: number;
  totalCount?: number;
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

// Méthodes d'API standardisées pour interagir avec le backend

// Méthode pour obtenir l'URL d'authentification
export const getAuthUrl = async (service: EmailService): Promise<string> => {
  try {
    // Utiliser l'URL complète avec le port correct
    const response = await axios.get(`${API_URL}/api/auth/${service}/login`);
    return response.data.auth_url;
  } catch (error) {
    console.error(`Error getting ${service} auth URL:`, error);
    throw error;
  }
};

// Méthode pour gérer le callback d'authentification
export const handleAuthCallback = async (
  code: string,
  service: EmailService
): Promise<{ accessToken: string; refreshToken?: string }> => {
  try {
    const response = await axios.get(
      `${API_URL}/api/auth/${service}/callback`,
      {
        params: { code },
      }
    );

    const { access_token, refresh_token } = response.data;

    // Stocker les tokens (à adapter selon votre mécanisme de stockage)
    localStorage.setItem("emailAccessToken", access_token);
    if (refresh_token) {
      localStorage.setItem("emailRefreshToken", refresh_token);
    }
    localStorage.setItem("emailService", service);

    return {
      accessToken: access_token,
      refreshToken: refresh_token,
    };
  } catch (error) {
    console.error(`Error handling ${service} auth callback:`, error);
    throw error;
  }
};

// Fonction utilitaire pour obtenir les headers d'authentification
const getAuthHeaders = () => {
  const accessToken = localStorage.getItem("emailAccessToken");
  return {
    "Content-Type": "application/json",
    Authorization: accessToken ? `Bearer ${accessToken}` : "",
  };
};

// Fonction utilitaire pour obtenir le service actuel
const getCurrentService = (): EmailService | null => {
  const service = localStorage.getItem("emailService");
  if (service === "gmail" || service === "outlook") {
    return service;
  }
  return null;
};

// Récupérer les emails
export const fetchEmails = async (
  options: EmailFetchOptions = {}
): Promise<StandardizedEmail[]> => {
  const service = getCurrentService();
  if (!service) {
    throw new Error("Email service not selected");
  }

  try {
    const response = await axios.get(`${API_URL}/api/emails`, {
      headers: getAuthHeaders(),
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
};

// Récupérer un email par ID
export const fetchEmailById = async (
  id: string
): Promise<StandardizedEmail> => {
  const service = getCurrentService();
  if (!service) {
    throw new Error("Email service not selected");
  }

  try {
    const response = await axios.get(`${API_URL}/api/emails/${id}`, {
      headers: getAuthHeaders(),
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
};

// Envoyer un email
export const sendEmail = async (email: {
  to: string[];
  cc?: string[];
  bcc?: string[];
  subject: string;
  body: string;
  body_type: string;
}): Promise<{ success: boolean; message_id?: string }> => {
  const service = getCurrentService();
  if (!service) {
    throw new Error("Email service not selected");
  }

  try {
    const response = await axios.post(`${API_URL}/api/emails`, email, {
      headers: getAuthHeaders(),
      params: {
        platform: service,
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error sending email:", error);
    throw error;
  }
};

// Marquer un email comme lu/non lu
export const markAsRead = async (
  id: string,
  read: boolean = true
): Promise<boolean> => {
  const service = getCurrentService();
  if (!service) {
    throw new Error("Email service not selected");
  }

  try {
    const response = await axios.patch(
      `${API_URL}/api/emails/${id}/read`,
      {},
      {
        headers: getAuthHeaders(),
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
};

// Récupérer les dossiers
export const getFolders = async (): Promise<EmailFolder[]> => {
  const service = getCurrentService();
  if (!service) {
    throw new Error("Email service not selected");
  }

  try {
    const response = await axios.get(`${API_URL}/api/folders`, {
      headers: getAuthHeaders(),
      params: {
        platform: service,
      },
    });

    return response.data.folders;
  } catch (error) {
    console.error("Error fetching folders:", error);
    throw error;
  }
};

// Récupérer le profil utilisateur
export const getUserProfile = async (): Promise<UserProfile> => {
  const service = getCurrentService();
  if (!service) {
    throw new Error("Email service not selected");
  }

  try {
    const response = await axios.get(`${API_URL}/api/profile`, {
      headers: getAuthHeaders(),
      params: {
        platform: service,
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error fetching user profile:", error);
    throw error;
  }
};

// Vérifier si l'utilisateur est authentifié
export const isAuthenticated = (): boolean => {
  return !!localStorage.getItem("emailAccessToken");
};

// Se déconnecter
export const logout = (): void => {
  localStorage.removeItem("emailAccessToken");
  localStorage.removeItem("emailRefreshToken");
  // Ne pas supprimer le service pour se souvenir de la préférence de l'utilisateur
};

// Changer de service (Gmail ou Outlook)
export const changeService = (service: EmailService): void => {
  localStorage.setItem("emailService", service);
};
