export type ProductAvailability = {
  store_id: string
  store_name: string
  price: number | null
}

export type ProductSearchResult = {
  id: string
  name: string
  brand: string | null
  stores: ProductAvailability[]
}

export type AvailableProduct = {
  id: string
  name: string
  brand: string | null
  stores: ProductAvailability[]
}
