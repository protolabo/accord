import axios from "axios";
import config from "../config";

// Utiliser directement l'URL de l'API depuis les variables d'environnement
const API_URL = process.env.REACT_APP_API_URL || "http://localhost:3001";

// Remplacez toutes les occurrences de '/api/' par:
const API_BASE_URL = `${config.apiBaseUrl}/api`;

// Méthode pour obtenir l'URL d'authentification
export const getAuthUrl = async (service: string): Promise<string> => {
  try {
    // Utiliser l'URL complète avec le port correct
    const response = await axios.get(`${API_URL}/api/email/${service}/auth`);
    return response.data.url;
  } catch (error) {
    console.error("Error getting auth URL: ", error);
    throw error;
  }
};
