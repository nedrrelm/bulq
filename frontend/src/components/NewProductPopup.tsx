import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { storesApi, productsApi } from '../api'
import type { Store, ProductSearchResult } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { validateLength, validateAlphanumeric, validateDecimal, sanitizeString } from '../utils/validation'
import { useConfirm } from '../hooks/useConfirm'
import ConfirmDialog from './ConfirmDialog'
import { getErrorMessage } from '../utils/errorHandling'

interface NewProductPopupProps {
  onClose: () => void
  onSuccess: () => void
  initialStoreId?: string
}

const MAX_NAME_LENGTH = 100
const MIN_NAME_LENGTH = 2

export default function NewProductPopup({ onClose, onSuccess, initialStoreId }: NewProductPopupProps) {
  const { t } = useTranslation(['common', 'product', 'store'])
  const [productName, setProductName] = useState('')
  const [brand, setBrand] = useState('')
  const [unit, setUnit] = useState('')
  const [storeId, setStoreId] = useState(initialStoreId || '')
  const [price, setPrice] = useState('')
  const [minimumQuantity, setMinimumQuantity] = useState('')
  const [stores, setStores] = useState<Store[]>([])
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [loadingStores, setLoadingStores] = useState(true)
  const [similarProducts, setSimilarProducts] = useState<ProductSearchResult[]>([])
  const modalRef = useRef<HTMLDivElement>(null)
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()

  useModalFocusTrap(modalRef, true, onClose)

  useEffect(() => {
    const fetchStores = async () => {
      try {
        const storesData = await storesApi.getStores()
        setStores(Array.isArray(storesData) ? storesData : [])
      } catch (err) {
        setError(getErrorMessage(err, t('store:errors.loadFailed')))
        setStores([])
      } finally {
        setLoadingStores(false)
      }
    }

    fetchStores()
  }, [])

  // Check for similar products as user types
  useEffect(() => {
    const checkSimilar = async () => {
      const trimmed = productName.trim()

      // Only check if we have at least MIN_NAME_LENGTH characters
      if (trimmed.length < MIN_NAME_LENGTH) {
        setSimilarProducts([])
        return
      }

      try {
        const similar = await productsApi.checkSimilar(trimmed)
        setSimilarProducts(similar)
      } catch (err) {
        // Silently fail - this is a nice-to-have feature
        setSimilarProducts([])
      }
    }

    // Debounce the API call
    const timeoutId = setTimeout(checkSimilar, 300)
    return () => clearTimeout(timeoutId)
  }, [productName])

  const validateProductName = (value: string): boolean => {
    const trimmed = value.trim()

    if (trimmed.length === 0) {
      setError(t('product:validation.nameRequired'))
      return false
    }

    const lengthValidation = validateLength(trimmed, MIN_NAME_LENGTH, MAX_NAME_LENGTH, t('product:fields.name'))
    if (!lengthValidation.isValid) {
      setError(lengthValidation.error || t('product:validation.nameInvalid'))
      return false
    }

    const alphanumericValidation = validateAlphanumeric(trimmed, '- _&\'(),.', t('product:fields.name'), true)
    if (!alphanumericValidation.isValid) {
      setError(alphanumericValidation.error || t('product:validation.nameInvalidCharacters'))
      return false
    }

    return true
  }

  const validatePrice = (value: string): boolean => {
    // Price is optional
    if (!value.trim()) {
      return true
    }

    const priceValidation = validateDecimal(value, 0.01, 999999.99, 2, t('product:fields.price'))
    if (!priceValidation.isValid) {
      setError(priceValidation.error || t('product:validation.priceInvalid'))
      return false
    }

    return true
  }

  const handleNameChange = (value: string) => {
    const sanitized = sanitizeString(value, MAX_NAME_LENGTH)
    setProductName(sanitized)
    setError('')
  }

  const handlePriceChange = (value: string) => {
    // Allow only numbers and decimal point
    if (value && !/^\d*\.?\d{0,2}$/.test(value)) {
      return
    }
    setPrice(value)
    setError('')
  }

  const submitProduct = async () => {
    try {
      setSubmitting(true)

      await productsApi.createProduct({
        name: productName.trim(),
        brand: brand.trim() || null,
        unit: unit.trim() || null,
        store_id: storeId || null,
        price: price.trim() ? parseFloat(price) : null,
        minimum_quantity: minimumQuantity.trim() ? parseInt(minimumQuantity) : null
      })

      onSuccess()
    } catch (err) {
      setError(getErrorMessage(err, t('product:errors.createFailed')))
      setSubmitting(false)
    }
  }

  const checkStoreAndPrice = () => {
    // Nudge to add price if store is selected but no price
    if (storeId && !price.trim()) {
      showConfirm(
        t('product:validation.noPriceWarning'),
        submitProduct
      )
      return
    }

    // If all validations pass, submit directly
    submitProduct()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    setError('')

    if (!validateProductName(productName)) {
      return
    }

    if (!validatePrice(price)) {
      return
    }

    // Check for exact match
    const exactMatch = similarProducts.find(
      p => p.name.toLowerCase() === productName.trim().toLowerCase() &&
           (brand.trim() === '' || p.brand?.toLowerCase() === brand.trim().toLowerCase())
    )

    if (exactMatch) {
      const matchName = exactMatch.brand
        ? `${exactMatch.brand} ${exactMatch.name}`
        : exactMatch.name
      setError(t('product:validation.alreadyExists', { name: matchName }))
      return
    }

    // Warn if no store selected
    if (!storeId) {
      showConfirm(
        t('product:validation.noStoreWarning'),
        checkStoreAndPrice
      )
      return
    }

    // Check for price if store is selected
    checkStoreAndPrice()
  }

  // Check if there's an exact match
  const exactMatch = similarProducts.find(
    p => p.name.toLowerCase() === productName.trim().toLowerCase() &&
         (brand.trim() === '' || p.brand?.toLowerCase() === brand.trim().toLowerCase())
  )

  const hasNonExactSimilar = similarProducts.length > 0 && !exactMatch

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal modal-scrollable" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{t('product:create.title')}</h2>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="product-name" className="form-label">{t('product:fields.name')} *</label>
            <input
              id="product-name"
              type="text"
              className={`form-input ${error ? 'input-error' : ''}`}
              value={productName}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder={t('product:fields.namePlaceholder')}
              disabled={submitting}
              required
            />

            {exactMatch && (
              <div className="alert alert-error" style={{ marginTop: '0.5rem' }}>
                {t('product:validation.alreadyExists', { name: exactMatch.brand ? `${exactMatch.brand} ${exactMatch.name}` : exactMatch.name })}
              </div>
            )}

            {hasNonExactSimilar && (
              <div className="alert" style={{ marginTop: '0.5rem', backgroundColor: '#fff3cd', color: '#856404', border: '1px solid #ffc107' }}>
                <strong>{t('product:validation.similarFound')}:</strong>
                <ul style={{ marginTop: '0.5rem', marginBottom: 0, paddingLeft: '1.5rem' }}>
                  {similarProducts.map(product => (
                    <li key={product.id}>
                      {product.brand ? `${product.brand} ${product.name}` : product.name}
                      {product.stores && product.stores.length > 0 && (
                        <span style={{ fontSize: '0.85em', color: '#666' }}>
                          {' '}({t('product:validation.atStores', { stores: product.stores.map(s => s.store_name).join(', ') })})
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="brand" className="form-label">{t('product:fields.brand')}</label>
              <input
                id="brand"
                type="text"
                className="form-input"
                value={brand}
                onChange={(e) => {
                  setBrand(e.target.value)
                  setError('')
                }}
                placeholder={t('product:fields.brandPlaceholder')}
                disabled={submitting}
              />
            </div>

            <div className="form-group">
              <label htmlFor="unit" className="form-label">{t('product:fields.unit')}</label>
              <input
                id="unit"
                type="text"
                className="form-input"
                value={unit}
                onChange={(e) => {
                  setUnit(e.target.value)
                  setError('')
                }}
                placeholder={t('product:fields.unitPlaceholder')}
                disabled={submitting}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="store-select" className="form-label">{t('product:fields.store')}</label>
            <select
              id="store-select"
              className="form-input"
              value={storeId}
              onChange={(e) => {
                setStoreId(e.target.value)
                setError('')
              }}
              disabled={submitting || loadingStores}
            >
              <option value="">{t('product:fields.storeSelectPlaceholder')}</option>
              {Array.isArray(stores) && stores.map((store) => (
                <option key={store.id} value={store.id}>
                  {store.name}
                </option>
              ))}
            </select>
            {loadingStores && (
              <small className="input-hint">{t('store:states.loading')}</small>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="price" className="form-label">{t('product:fields.price')} ($)</label>
              <input
                id="price"
                type="text"
                inputMode="decimal"
                className="form-input"
                value={price}
                onChange={(e) => handlePriceChange(e.target.value)}
                placeholder={t('product:fields.pricePlaceholder')}
                disabled={submitting}
              />
            </div>

            <div className="form-group">
              <label htmlFor="minimum-quantity" className="form-label">{t('product:fields.minimumQuantity')}</label>
              <input
                id="minimum-quantity"
                type="number"
                inputMode="numeric"
                className="form-input"
                value={minimumQuantity}
                onChange={(e) => {
                  setMinimumQuantity(e.target.value)
                  setError('')
                }}
                placeholder={t('product:fields.minimumQuantityPlaceholder')}
                min="1"
                disabled={submitting}
              />
            </div>
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={submitting}
            >
              {t('common:buttons.cancel')}
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || loadingStores}
            >
              {submitting ? t('product:actions.creating') : t('product:actions.create')}
            </button>
          </div>
        </form>
      </div>

      {confirmState && (
        <ConfirmDialog
          message={confirmState.message}
          onConfirm={handleConfirm}
          onCancel={hideConfirm}
          danger={confirmState.danger}
        />
      )}
    </div>
  )
}
