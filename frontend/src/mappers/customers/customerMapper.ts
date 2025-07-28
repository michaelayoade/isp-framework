import { z } from 'zod';
import type { Customer as CustomerDTO, Address as AddressDTO } from '@/api/_schemas';

// UI models (what the frontend components expect)
export interface CustomerUI {
  id: number;
  name: string;
  email: string;
  phone: string;
  status: 'active' | 'inactive' | 'suspended';
  createdAt: Date;
  updatedAt: Date;
  address?: AddressUI;
  servicePlan?: string;
  monthlyFee?: number;
}

export interface AddressUI {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

// Validation schemas for graceful handling of unknown/optional fields
const AddressSchema = z.object({
  street: z.string().default(''),
  city: z.string().default(''),
  state: z.string().default(''),
  zip_code: z.string().default(''),
  country: z.string().default(''),
});

const CustomerSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string().email(),
  phone: z.string(),
  status: z.string().transform((val) => {
    if (['active', 'inactive', 'suspended'].includes(val)) {
      return val as 'active' | 'inactive' | 'suspended';
    }
    return 'active'; // Default for invalid values
  }),
  created_at: z.string(),
  updated_at: z.string(),
  address: AddressSchema.optional(),
  service_plan: z.string().optional(),
  monthly_fee: z.number().optional(),
});

/**
 * Convert API DTO to UI model
 */
export const toCustomerUI = (dto: CustomerDTO): CustomerUI => {
  // Use Zod to validate and provide defaults for missing/unknown fields
  const validated = CustomerSchema.parse(dto);
  
  return {
    id: validated.id,
    name: validated.name,
    email: validated.email,
    phone: validated.phone,
    status: validated.status,
    createdAt: new Date(validated.created_at),
    updatedAt: new Date(validated.updated_at),
    address: validated.address ? toAddressUI(validated.address) : undefined,
    servicePlan: validated.service_plan,
    monthlyFee: validated.monthly_fee,
  };
};

/**
 * Convert UI model to API DTO
 */
export const toCustomerDTO = (ui: Partial<CustomerUI>): Partial<CustomerDTO> => {
  return {
    name: ui.name,
    email: ui.email,
    phone: ui.phone,
    status: ui.status,
    address: ui.address ? toAddressDTO(ui.address) : undefined,
    service_plan: ui.servicePlan,
  };
};

/**
 * Convert address DTO to UI model
 */
export const toAddressUI = (dto: AddressDTO): AddressUI => {
  const validated = AddressSchema.parse(dto);
  
  return {
    street: validated.street,
    city: validated.city,
    state: validated.state,
    zipCode: validated.zip_code, // snake_case → camelCase
    country: validated.country,
  };
};

/**
 * Convert address UI model to DTO
 */
export const toAddressDTO = (ui: AddressUI): AddressDTO => {
  return {
    street: ui.street,
    city: ui.city,
    state: ui.state,
    zip_code: ui.zipCode, // camelCase → snake_case
    country: ui.country,
  };
};
