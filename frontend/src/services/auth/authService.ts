import { api } from '@services/api/client'
import { API_ENDPOINTS } from '@services/api/endpoints'
import type { 
  User, 
  LoginCredentials, 
  AuthResponse, 
  RefreshTokenResponse,
  RegisterData,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  ChangePasswordRequest 
} from '../../types/auth'

class AuthService {
  /**
   * Login user with credentials
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>(API_ENDPOINTS.AUTH.LOGIN, credentials)
    return response
  }

  /**
   * Register new user
   */
  async register(userData: RegisterData): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>(API_ENDPOINTS.AUTH.REGISTER, userData)
    return response
  }

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    await api.post(API_ENDPOINTS.AUTH.LOGOUT)
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    const response = await api.post<RefreshTokenResponse>(API_ENDPOINTS.AUTH.REFRESH, {
      refreshToken,
    })
    return response
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>(API_ENDPOINTS.AUTH.PROFILE)
    return response
  }

  /**
   * Update user profile
   */
  async updateProfile(updates: Partial<User>): Promise<User> {
    const response = await api.put<User>(API_ENDPOINTS.AUTH.PROFILE, updates)
    return response
  }

  /**
   * Request password reset
   */
  async forgotPassword(request: ForgotPasswordRequest): Promise<void> {
    await api.post(API_ENDPOINTS.AUTH.FORGOT_PASSWORD, request)
  }

  /**
   * Reset password with token
   */
  async resetPassword(request: ResetPasswordRequest): Promise<void> {
    await api.post(API_ENDPOINTS.AUTH.RESET_PASSWORD, request)
  }

  /**
   * Change password for authenticated user
   */
  async changePassword(request: ChangePasswordRequest): Promise<void> {
    await api.post(API_ENDPOINTS.AUTH.CHANGE_PASSWORD, request)
  }

  /**
   * Verify email address
   */
  async verifyEmail(token: string): Promise<void> {
    await api.post(API_ENDPOINTS.AUTH.VERIFY_EMAIL, { token })
  }

  /**
   * Check if user is authenticated (has valid token)
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('auth_token')
    if (!token) return false

    try {
      // Check if token is expired (basic JWT check)
      const tokenParts = token.split('.')
      if (tokenParts.length !== 3) return false
      
      const payload = JSON.parse(atob(tokenParts[1]!))
      const now = Date.now() / 1000
      return payload.exp > now
    } catch {
      return false
    }
  }

  /**
   * Get current auth token
   */
  getToken(): string | null {
    return localStorage.getItem('auth_token')
  }

  /**
   * Clear auth data from storage
   */
  clearAuthData(): void {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
  }
}

export const authService = new AuthService()
export default authService