import axios from 'axios';

const API_URL = 'http://localhost:8000';

const MockDataService = {
  /**
   * Récupère les emails mockés depuis l'API backend
   */
  fetchMockEmails: async () => {
    console.log("Tentative de récupération des données mockées");
    try {
      const response = await axios.get(`${API_URL}/mock/emails`);
      console.log("Données mockées récupérées:", response.data.length, "emails");
      return response.data;
    } catch (error) {
      console.error("Erreur lors de la récupération des emails mockés:", error);
      return [];
    }
  }
};

export default MockDataService;