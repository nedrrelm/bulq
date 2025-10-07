export type ProductSearchResult = {
  id: string
  name: string
  store_id: string
  store_name: string
  base_price: number | null
}

export type AvailableProduct = {
  id: string
  name: string
  base_price: string
}
