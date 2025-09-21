export interface User {
  id: string
  email: string
  firstName: string
  lastName: string
  role: 'admin' | 'user' | 'manager'
  avatar?: string
  preferences: {
    language: string
    theme: 'light' | 'dark' | 'system'
    notifications: {
      email: boolean
      push: boolean
      sparky: boolean
    }
  }
  permissions: string[]
  createdAt: string
  updatedAt: string
  lastLoginAt?: string
  isActive: boolean
}

export interface LoginCredentials {
  email: string
  password: string
  rememberMe?: boolean
}

export interface RegisterData {
  email: string
  password: string
  confirmPassword: string
  firstName: string
  lastName: string
  role?: 'user'
}

export interface AuthResponse {
  user: User
  token: string
  refreshToken: string
  expiresIn: number
}

export interface AuthError {
  message: string
  code: string
  field?: string
  statusCode?: number
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ResetPasswordRequest {
  token: string
  password: string
  confirmPassword: string
}

export interface ChangePasswordRequest {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

export interface RefreshTokenResponse {
  token: string
  user: User
  expiresIn: number
}