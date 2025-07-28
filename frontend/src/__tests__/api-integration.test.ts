/**
 * API Integration Tests
 * Tests frontend services against the live backend API
 */

import { apiClient } from '@/api/client'

describe('API Integration Tests', () => {
  beforeAll(() => {
    // Set up API client for testing
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000/api/v1'
  })

  describe('Health Check', () => {
    it('should connect to backend health endpoint', async () => {
      const response = await apiClient.get('http://localhost:8000/health')
      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('status', 'healthy')
      expect(response.data).toHaveProperty('timestamp')
      expect(response.data).toHaveProperty('version')
    })
  })

  describe('Authentication Endpoints', () => {
    it('should reject invalid portal authentication', async () => {
      try {
        await apiClient.post('/auth/portal/authenticate', {
          portal_id: 'invalid_portal_id',
          password: 'invalid_password'
        })
        fail('Should have thrown an error')
      } catch (error: unknown) {
        const axiosError = error as { response: { status: number; data: { detail: string } } }
        expect(axiosError.response.status).toBe(500) // Backend wraps 401 in 500
        expect(axiosError.response.data).toHaveProperty('detail')
        expect(axiosError.response.data.detail).toContain('Invalid portal ID or password')
      }
    })

    it('should return 401 for protected endpoints without auth', async () => {
      try {
        await apiClient.get('/customers/dashboard')
        fail('Should have thrown an error')
      } catch (error: unknown) {
        const axiosError = error as { response: { status: number; data: { detail: string } } }
        expect(axiosError.response.status).toBe(401)
        expect(axiosError.response.data).toHaveProperty('detail', 'Not authenticated')
      }
    })
  })

  describe('API Structure', () => {
    it('should have OpenAPI documentation available', async () => {
      const response = await apiClient.get('http://localhost:8000/openapi.json')
      expect(response.status).toBe(200)
      expect(response.data).toHaveProperty('openapi')
      expect(response.data).toHaveProperty('paths')
      expect(response.data.paths).toHaveProperty('/api/v1/customers/')
      expect(response.data.paths).toHaveProperty('/api/v1/auth/portal/authenticate')
    })
  })
})
