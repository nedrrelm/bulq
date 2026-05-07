import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { productsApi } from '../../api'
import { tagsApi } from '../../api'
import type { TagSearchResult } from '../../api/tags'
import { validateLength, validateAlphanumeric, validateDecimal, sanitizeString } from '../../utils/validation'
import { useConfirm } from '../../hooks/useConfirm'
import ConfirmDialog from '../common/ConfirmDialog'
import { getErrorMessage } from '../../utils/errorHandling'
import BaseModal from '../common/BaseModal'
import { useSimilarEntities } from '../../hooks/useSimilarEntities'
import { useStores } from '../../hooks/queries'

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
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()
  const { data: storesData, isLoading: loadingStores } = useStores()
  const stores = Array.isArray(storesData) ? storesData : []

  // Tags state
  const [selectedTags, setSelectedTags] = useState<Array<{ id: string; value: string; type: string }>>([])
  const [tagSearch, setTagSearch] = useState('')
  const [tagResults, setTagResults] = useState<TagSearchResult[]>([])
  const [tagTypes, setTagTypes] = useState<string[]>([])
  const [showTagCreate, setShowTagCreate] = useState(false)
  const [newTagValue, setNewTagValue] = useState('')
  const [newTagType, setNewTagType] = useState('')

  const searchTags = useCallback(async (query: string) => {
    if (query.trim().length < 1) {
      setTagResults([])
      return
    }
    try {
      const results = await tagsApi.search(query)
      const selectedIds = new Set(selectedTags.map(t => t.id))
      setTagResults(results.filter(r => !selectedIds.has(r.id)))
    } catch {
      setTagResults([])
    }
  }, [selectedTags])

  const addSelectedTag = (tag: { id: string; value: string; type: string }) => {
    setSelectedTags(prev => [...prev, tag])
    setTagSearch('')
    setTagResults([])
  }

  const removeSelectedTag = (tagId: string) => {
    setSelectedTags(prev => prev.filter(t => t.id !== tagId))
  }

  const handleCreateAndAddTag = async () => {
    if (!newTagValue.trim() || !newTagType) return
    try {
      const result = await tagsApi.createTag({ value: newTagValue.trim(), type: newTagType })
      const created = result as { id: string; value: string; type: string }
      if (created?.id) {
        addSelectedTag({ id: created.id, value: created.value, type: created.type })
      }
      setNewTagValue('')
      setShowTagCreate(false)
    } catch {
      // silently fail
    }
  }

  const loadTagTypes = async () => {
    if (tagTypes.length > 0) return
    try {
      const types = await tagsApi.getTypes()
      setTagTypes(types)
      if (types.length > 0) setNewTagType(types[0])
    } catch {
      // use defaults
    }
  }

  // Check for similar products as user types (matches on name and brand)
  const { similar: similarProducts, exactMatch, hasNonExactSimilar } = useSimilarEntities({
    searchValue: productName,
    fetcher: productsApi.checkSimilar,
    minLength: MIN_NAME_LENGTH,
    getComparisonValue: (product) =>
      `${product.name}|${product.brand || ''}`.toLowerCase(),
    getInputComparisonValue: (name) =>
      `${name}|${brand.trim()}`.toLowerCase()
  })

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

      const result = await productsApi.createProduct({
        name: productName.trim(),
        brand: brand.trim() || null,
        unit: unit.trim() || null,
        store_id: storeId || null,
        price: price.trim() ? parseFloat(price) : null,
        minimum_quantity: minimumQuantity.trim() ? parseInt(minimumQuantity) : null
      })

      // Attach selected tags to the newly created product
      const productId = (result as { id?: string })?.id
      if (productId && selectedTags.length > 0) {
        for (const tag of selectedTags) {
          try {
            await tagsApi.addTagToProduct(tag.id, productId)
          } catch {
            // Continue even if a tag fails to attach
          }
        }
      }

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

  return (
    <>
      <BaseModal
        isOpen={true}
        onClose={onClose}
        title={t('product:create.title')}
        error={error}
        size="scrollable"
        submitButton={{
          text: submitting ? t('product:actions.creating') : t('product:actions.create'),
          onClick: handleSubmit,
          loading: submitting,
          disabled: submitting || loadingStores
        }}
      >

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
              <div className="alert alert-error mt-sm">
                {t('product:validation.alreadyExists', { name: exactMatch.brand ? `${exactMatch.brand} ${exactMatch.name}` : exactMatch.name })}
              </div>
            )}

            {hasNonExactSimilar && (
              <div className="alert-warning mt-sm">
                <strong>{t('product:validation.similarFound')}:</strong>
                <ul className="list-compact">
                  {similarProducts.map(product => (
                    <li key={product.id}>
                      {product.brand ? `${product.brand} ${product.name}` : product.name}
                      {product.stores && product.stores.length > 0 && (
                        <span className="text-hint text-secondary">
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
            <label className="form-label">{t('product:tags.title')}</label>
            <div className="tags-list" style={{ marginBottom: '0.5rem' }}>
              {selectedTags.map((tag) => (
                <span key={tag.id} className={`tag-chip tag-type-${tag.type}`}>
                  <span className="tag-chip-text">{tag.value}</span>
                  <button
                    type="button"
                    className="tag-chip-remove"
                    onClick={() => removeSelectedTag(tag.id)}
                  >
                    &times;
                  </button>
                </span>
              ))}
            </div>
            <input
              type="text"
              className="form-input"
              placeholder={t('product:tags.searchPlaceholder')}
              value={tagSearch}
              onChange={(e) => {
                setTagSearch(e.target.value)
                searchTags(e.target.value)
              }}
              onFocus={loadTagTypes}
              disabled={submitting}
            />
            {tagResults.length > 0 && (
              <div className="tag-results">
                {tagResults.map((tag) => (
                  <div
                    key={tag.id}
                    className="tag-result-item"
                    onClick={() => addSelectedTag({ id: tag.id, value: tag.value, type: tag.type })}
                  >
                    <span className="tag-result-value">{tag.value}</span>
                    <span className={`tag-type-badge tag-type-${tag.type}`}>{t(`product:tags.types.${tag.type}`, tag.type)}</span>
                  </div>
                ))}
              </div>
            )}
            {!showTagCreate ? (
              <button
                type="button"
                className="btn btn-sm"
                style={{ marginTop: '0.25rem' }}
                onClick={() => { setShowTagCreate(true); loadTagTypes() }}
                disabled={submitting}
              >
                {t('product:tags.createNew')}
              </button>
            ) : (
              <div className="tag-create-form" style={{ marginTop: '0.25rem' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder={t('product:tags.newValuePlaceholder')}
                  value={newTagValue}
                  onChange={(e) => setNewTagValue(e.target.value)}
                  disabled={submitting}
                />
                <select
                  className="form-input"
                  value={newTagType}
                  onChange={(e) => setNewTagType(e.target.value)}
                  disabled={submitting}
                >
                  {tagTypes.map((type) => (
                    <option key={type} value={type}>
                      {t(`product:tags.types.${type}`, type)}
                    </option>
                  ))}
                </select>
                <div className="tag-create-actions">
                  <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    onClick={handleCreateAndAddTag}
                    disabled={!newTagValue.trim() || !newTagType || submitting}
                  >
                    {t('common:actions.create')}
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm"
                    onClick={() => setShowTagCreate(false)}
                  >
                    {t('common:actions.cancel')}
                  </button>
                </div>
              </div>
            )}
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

      </BaseModal>

      {confirmState && (
        <ConfirmDialog
          message={confirmState.message}
          onConfirm={handleConfirm}
          onCancel={hideConfirm}
          danger={confirmState.danger}
        />
      )}
    </>
  )
}
