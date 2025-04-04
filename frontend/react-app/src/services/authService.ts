const API_URL = "http://localhost:5000"; // Ajuster selon votre configuration

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  scope: string;
}

export const authService = {
  async loginWithGoogle(): Promise<AuthResponse> {
    const response = await fetch(`${API_URL}/auth/google/login`);
    if (!response.ok) {
      throw new Error("Erreur lors de l'authentification Google");
    }
    const data = await response.json();
    window.location.href = data.auth_url;
    return data;
  },

  async loginWithOutlook(): Promise<AuthResponse> {
    const response = await fetch(`${API_URL}/auth/outlook/login`);
    if (!response.ok) {
      throw new Error("Erreur lors de l'authentification Outlook");
    }
    const data = await response.json();
    window.location.href = data.auth_url;
    return data;
  },

  async handleCallback(
    code: string,
    provider: "google" | "outlook"
  ): Promise<AuthResponse> {
    const response = await fetch(
      `${API_URL}/auth/${provider}/callback?code=${code}`
    );
    if (!response.ok) {
      throw new Error(`Erreur lors de la validation du code ${provider}`);
    }
    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
    return data;
  },
};
