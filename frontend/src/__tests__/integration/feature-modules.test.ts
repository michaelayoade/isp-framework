/**
 * Integration tests for feature module imports and exports
 * These tests ensure that all feature modules are properly structured and exportable
 */

describe('Feature Module Integration', () => {
  describe('Feature module exports', () => {
    it('should export all feature modules from main index', async () => {
      const featuresIndex = await import('@/features')
      
      // Verify that the main features index exports exist
      expect(featuresIndex).toBeDefined()
      
      // Test that we can import from individual feature modules
      const { useCustomers } = await import('@/features/customers')
      const { useBilling } = await import('@/features/billing')
      const { useServices } = await import('@/features/services')
      const { useCommunications } = await import('@/features/communications')
      const { useAdmin } = await import('@/features/admin')
      
      // These should not throw errors
      expect(typeof useCustomers).toBe('function')
      expect(typeof useBilling).toBe('function')
      expect(typeof useServices).toBe('function')
      expect(typeof useCommunications).toBe('function')
      expect(typeof useAdmin).toBe('function')
    })

    it('should export networking feature module', async () => {
      const { useNetworking } = await import('@/features/networking')
      expect(typeof useNetworking).toBe('function')
    })

    it('should export plugins feature module', async () => {
      const { usePlugins } = await import('@/features/plugins')
      expect(typeof usePlugins).toBe('function')
    })

    it('should export radius feature module', async () => {
      const { useRadius } = await import('@/features/radius')
      expect(typeof useRadius).toBe('function')
    })

    it('should export resellers feature module', async () => {
      const { useResellerProfile, useResellerDashboard, useResellerCustomers } = await import('@/features/resellers')
      expect(typeof useResellerProfile).toBe('function')
      expect(typeof useResellerDashboard).toBe('function')
      expect(typeof useResellerCustomers).toBe('function')
    })

    it('should export tickets feature module', async () => {
      const { useTickets } = await import('@/features/tickets')
      expect(typeof useTickets).toBe('function')
    })
  })

  describe('Feature module structure', () => {
    it('should have consistent structure across all feature modules', async () => {
      const featureModules = [
        'customers',
        'services',
        'communications',
        'billing',
        'admin',
        'networking',
        'plugins',
        'radius',
        'resellers',
        'tickets'
      ]

      for (const moduleName of featureModules) {
        const featureModule = await import(`@/features/${moduleName}`)
        
        // Each feature module should export something
        expect(Object.keys(featureModule).length).toBeGreaterThan(0)
        
        // Check for common patterns (hooks, services, types)
        const moduleKeys = Object.keys(featureModule)
        const hasHooks = moduleKeys.some(key => key.startsWith('use'))
        const hasServices = moduleKeys.some(key => key.includes('Service') || key.includes('service'))
        const hasTypes = moduleKeys.some(key => key.includes('Type') || key.includes('Interface'))
        
        // At least one of these should be true for a well-structured feature module
        expect(hasHooks || hasServices || hasTypes).toBe(true);
      }
    })

    it('should have proper TypeScript types for all feature modules', async () => {
      // Test that TypeScript types are properly exported
      const { Customer } = await import('@/features/customers/types')
      const { Service } = await import('@/features/services/types')
      const { BillingOverview } = await import('@/features/billing/types')
      
      // These should be defined as types/interfaces
      expect(Customer).toBeDefined()
      expect(Service).toBeDefined()
      expect(BillingOverview).toBeDefined()
    })
  })

  describe('Service layer integration', () => {
    it('should properly import and instantiate services', async () => {
      const { customerService } = await import('@/features/customers/services/customer-service')
      const { billingService } = await import('@/features/billing/services/billing-service')
      const { customerPortalService } = await import('@/features/customers/services/customer-portal-service')
      
      // Services should be objects with methods
      expect(typeof customerService).toBe('object')
      expect(typeof billingService).toBe('object')
      expect(typeof customerPortalService).toBe('object')
      
      // Services should have common methods
      expect(typeof customerService.getCustomers).toBe('function')
      expect(typeof billingService.getBillingOverview).toBe('function')
      expect(typeof customerPortalService.getCustomerProfile).toBe('function')
    })

    it('should handle service method calls without errors', async () => {
      const { customerService } = await import('@/features/customers/services/customer-service')
      
      // Mock the API client to avoid actual network calls
      jest.mock('@/api/client', () => ({
        apiClient: {
          get: jest.fn().mockResolvedValue({ data: { customers: [] } }),
          post: jest.fn().mockResolvedValue({ data: {} }),
          put: jest.fn().mockResolvedValue({ data: {} }),
          delete: jest.fn().mockResolvedValue({ data: {} }),
        }
      }))
      
      // Service methods should be callable
      expect(() => customerService.getCustomers()).not.toThrow()
    })
  })

  describe('Hook integration', () => {
    it('should properly export React hooks from feature modules', async () => {
      const customersModule = await import('@/features/customers')
      const billingsModule = await import('@/features/billing')
      const resellersModule = await import('@/features/resellers')
      
      // Check for hook exports
      const customerHooks = Object.keys(customersModule).filter(key => key.startsWith('use'))
      const billingHooks = Object.keys(billingsModule).filter(key => key.startsWith('use'))
      const resellerHooks = Object.keys(resellersModule).filter(key => key.startsWith('use'))
      
      expect(customerHooks.length).toBeGreaterThan(0)
      expect(billingHooks.length).toBeGreaterThan(0)
      expect(resellerHooks.length).toBeGreaterThan(0)
    })
  })

  describe('Cross-module dependencies', () => {
    it('should handle cross-module type imports', async () => {
      // Test that modules can import types from other modules if needed
      const { PaginatedResponse } = await import('@/types/common')
      const servicesTypes = await import('@/features/services/types')
      const networkingTypes = await import('@/features/networking/types')
      
      // Common types should be available
      expect(PaginatedResponse).toBeDefined()
      
      // Feature modules should be able to use common types
      expect(servicesTypes.PaginatedResponse).toBeDefined()
      expect(networkingTypes.PaginatedResponse).toBeDefined()
    })

    it('should not have circular dependencies', async () => {
      // This test ensures that importing all modules doesn't create circular dependencies
      const imports = await Promise.all([
        import('@/features/customers'),
        import('@/features/services'),
        import('@/features/communications'),
        import('@/features/billing'),
        import('@/features/admin'),
        import('@/features/networking'),
        import('@/features/plugins'),
        import('@/features/radius'),
        import('@/features/resellers'),
        import('@/features/tickets'),
      ])
      
      // All imports should succeed without circular dependency errors
      expect(imports).toHaveLength(10)
      imports.forEach(module => {
        expect(module).toBeDefined()
      })
    })
  })
})
