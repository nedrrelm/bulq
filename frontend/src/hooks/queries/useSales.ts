import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  salesApi,
  type CreateSaleRequest,
  type AddSaleProductRequest,
  type UpdateSaleProductRequest,
} from '../../api/sales'
import { createQueryKeys } from '../../utils/queryKeys'

export const saleKeys = createQueryKeys('sales', {
  custom: {
    mySales: (base) => [...base, 'my-sales'] as const,
  },
})

// ==================== Queries ====================

export function useMySales() {
  return useQuery({
    queryKey: saleKeys.mySales(),
    queryFn: () => salesApi.getMySales(),
  })
}

export function useSaleDetail(saleId: string | undefined) {
  return useQuery({
    queryKey: saleKeys.detail(saleId!),
    queryFn: () => salesApi.getSaleDetails(saleId!),
    enabled: !!saleId,
  })
}

// ==================== Mutations ====================

export function useCreateSale() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateSaleRequest) => salesApi.createSale(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: saleKeys.mySales() })
    },
  })
}

export function useAddSaleProduct(saleId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: AddSaleProductRequest) => salesApi.addProduct(saleId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: saleKeys.detail(saleId) })
      queryClient.invalidateQueries({ queryKey: saleKeys.mySales() })
    },
  })
}

export function useUpdateSaleProduct(saleId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ productId, data }: { productId: string; data: UpdateSaleProductRequest }) =>
      salesApi.updateProduct(saleId, productId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: saleKeys.detail(saleId) })
    },
  })
}

export function useRemoveSaleProduct(saleId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (productId: string) => salesApi.removeProduct(saleId, productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: saleKeys.detail(saleId) })
      queryClient.invalidateQueries({ queryKey: saleKeys.mySales() })
    },
  })
}

export function useActivateSale(saleId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => salesApi.activateSale(saleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: saleKeys.detail(saleId) })
      queryClient.invalidateQueries({ queryKey: saleKeys.mySales() })
    },
  })
}

export function useDeactivateSale(saleId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => salesApi.deactivateSale(saleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: saleKeys.detail(saleId) })
      queryClient.invalidateQueries({ queryKey: saleKeys.mySales() })
    },
  })
}

export function useCancelSale(saleId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => salesApi.cancelSale(saleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: saleKeys.detail(saleId) })
      queryClient.invalidateQueries({ queryKey: saleKeys.mySales() })
    },
  })
}
