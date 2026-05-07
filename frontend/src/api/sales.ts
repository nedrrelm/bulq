import { api } from './client'
import { z } from 'zod'
import {
  saleSchema,
  saleDetailSchema,
  type Sale,
  type SaleDetail,
} from '../schemas/sale'

export type { Sale, SaleDetail }

export interface CreateSaleRequest {
  title: string
  description?: string | null
}

export interface UpdateSaleRequest {
  title?: string | null
  description?: string | null
}

export interface AddSaleProductRequest {
  product_id: string
  price?: number | null
  available_quantity?: number | null
}

export interface UpdateSaleProductRequest {
  price?: number | null
  available_quantity?: number | null
}

export const salesApi = {
  createSale: (request: CreateSaleRequest) =>
    api.post<Sale>('/sales', request, saleSchema),

  getMySales: () =>
    api.get<Sale[]>('/sales/my-sales', z.array(saleSchema)),

  getSaleDetails: (saleId: string) =>
    api.get<SaleDetail>(`/sales/${saleId}`, saleDetailSchema),

  updateSale: (saleId: string, request: UpdateSaleRequest) =>
    api.patch<SaleDetail>(`/sales/${saleId}`, request, saleDetailSchema),

  addProduct: (saleId: string, request: AddSaleProductRequest) =>
    api.post<SaleDetail>(`/sales/${saleId}/products`, request, saleDetailSchema),

  updateProduct: (saleId: string, productId: string, request: UpdateSaleProductRequest) =>
    api.patch<SaleDetail>(`/sales/${saleId}/products/${productId}`, request, saleDetailSchema),

  removeProduct: (saleId: string, productId: string) =>
    api.delete<SaleDetail>(`/sales/${saleId}/products/${productId}`, saleDetailSchema),

  activateSale: (saleId: string) =>
    api.post<SaleDetail>(`/sales/${saleId}/activate`, {}, saleDetailSchema),

  deactivateSale: (saleId: string) =>
    api.post<SaleDetail>(`/sales/${saleId}/deactivate`, {}, saleDetailSchema),

  cancelSale: (saleId: string) =>
    api.post<SaleDetail>(`/sales/${saleId}/cancel`, {}, saleDetailSchema),

  confirmSale: (saleId: string) =>
    api.post<SaleDetail>(`/sales/${saleId}/confirm`, {}, saleDetailSchema),

  startDistributing: (saleId: string) =>
    api.post<SaleDetail>(`/sales/${saleId}/start-distributing`, {}, saleDetailSchema),

  getSaleRuns: (saleId: string) =>
    api.get(`/sales/${saleId}/runs`),

  getDistribution: (saleId: string) =>
    api.get(`/sales/${saleId}/distribution`),

  toggleHandover: (saleId: string, itemId: string) =>
    api.post(`/sales/${saleId}/distribution/${itemId}/handover`, {}),

  completeSale: (saleId: string) =>
    api.post(`/sales/${saleId}/complete`, {}),
}
