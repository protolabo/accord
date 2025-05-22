const API_URL = "http://localhost:8000";

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
  refresh_token?: string;
  scope?: string;
  user_email?: string;
}

interface DecodedToken {
  exp: number;
  email: string;
  user_id?: string;
}

export const authService = {
  async loginWithGoogle(): Promise<AuthResponse> {
    const response = await fetch(`${API_URL}/auth/google/login`);
    if (!response.ok) {
      throw new Error("Error during Google authentication");
    }
    const data = await response.json();
    window.location.href = data.auth_url;
    return data;
  },

  async loginWithOutlook(): Promise<AuthResponse> {
    const response = await fetch(`${API_URL}/auth/outlook/login`);
    if (!response.ok) {
      throw new Error("Error during Outlook authentication");
    }
    const data = await response.json();
    window.location.href = data.auth_url;
    return data;
  },

  async handleCallback(
    code: string,
    provider: "google" | "outlook"
  ): Promise<AuthResponse> {
    // First, handle the OAuth callback
    const response = await fetch(
      `${API_URL}/auth/${provider}/callback?code=${code}`
    );
    if (!response.ok) {
      throw new Error(`Error validating ${provider} code`);
    }
    const oauthData = await response.json();

    // Then, get a JWT token using the OAuth data
    const tokenResponse = await fetch(`${API_URL}/auth/${provider}/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: oauthData.email || localStorage.getItem('userEmail')
      })
    });

    if (!tokenResponse.ok) {
      throw new Error(`Error getting JWT token`);
    }

    const tokenData = await tokenResponse.json();

    // Store the JWT token
    localStorage.setItem("jwt_token", tokenData.access_token);
    localStorage.setItem("userEmail", tokenData.user_email);

    return tokenData;
  },

  async logout(): Promise<void> {
    try {
      // Get the user email
      const userEmail = localStorage.getItem("userEmail");

      // Call the backend to revoke tokens
      await fetch(`${API_URL}/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
        },
        body: JSON.stringify({ email: userEmail })
      });

      // Clear all local storage

      localStorage.removeItem("access_token");
      localStorage.removeItem("jwt_token");
      localStorage.removeItem("userEmail");
      localStorage.removeItem("emailAccessToken");
      localStorage.removeItem("emailRefreshToken");
      localStorage.removeItem("emailService");


      // Redirect to login page
      window.location.href = "/";
    } catch (error) {
      console.error("Error during logout:", error);
      // Even if API call fails, clear storage and redirect
      localStorage.clear();
      window.location.href = "/";
    }
  },

  isAuthenticated(): boolean {
    console.log(localStorage.getItem('jwt_token'));
    const token = localStorage.getItem('jwt_token');
    if (!token) return false;

    try {
      // Decode the token (client-side validation for expiration only)
      const parts = token.split('.');
      if (parts.length !== 3) return false;

      const decoded = JSON.parse(atob(parts[1])) as DecodedToken;
      const currentTime = Math.floor(Date.now() / 1000);

      // Check if token is expired
      if (decoded.exp < currentTime) {
        // Token expired, remove it
        localStorage.removeItem('jwt_token');
        return false;
      }

      return true;
    } catch (e) {
      console.error("Invalid token:", e);
      localStorage.removeItem('jwt_token');
      return false;
    }
  },

  getUserEmail(): string | null {
    return localStorage.getItem('userEmail');
  },

  getAuthHeader(): { Authorization: string } | {} {
    const token = localStorage.getItem('jwt_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
};