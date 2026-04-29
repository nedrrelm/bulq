import { useState, useCallback, lazy, Suspense } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import '../styles/pages/ShoppingPage.css'
import { WS_BASE_URL } from '../config'
import { shoppingApi } from '../api'
import type { ShoppingListItem } from '../api'
import type { AvailableProduct } from '../types'
import type { WebSocketMessage } from '../types/websocket'
import { useWebSocket } from '../hooks/useWebSocket'
import Toast from '../components/common/Toast'
import ConfirmDialog from '../components/common/ConfirmDialog'
import ShoppingItem from '../components/ShoppingItem'
import PricePopup from '../components/popups/PricePopup'
import PurchasePopup from '../components/popups/PurchasePopup'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'
import { useShoppingList, shoppingKeys, runKeys } from '../hooks/queries'
import { formatErrorForDisplay, getErrorMessage } from '../utils/errorHandling'

const AddProductPopup = lazy(() => import('../components/popups/AddProductPopup'))
const BidPopup = lazy(() => import('../components/popups/BidPopup'))

export default function ShoppingPage() {
  const { t } = useTranslation(['common', 'shopping'])
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()

  const { data: items = [], isLoading: loading, error: queryError } = useShoppingList(runId || '')
  const queryClient = useQueryClient()

  const error = getErrorMessage(queryError, '')

  const [showPurchasePopup, setShowPurchasePopup] = useState(false)
  const [isEditingPurchase, setIsEditingPurchase] = useState(false)
  const [selectedItem, setSelectedItem] = useState<ShoppingListItem | null>(null)
  const [showPricePopup, setShowPricePopup] = useState(false)
  const [showAddProductPopup, setShowAddProductPopup] = useState(false)
  const [showBidPopup, setShowBidPopup] = useState(false)
  const [selectedProductName, setSelectedProductName] = useState('')
  const [selectedProductId, setSelectedProductId] = useState('')
  const { toast, showToast, hideToast} = useToast()
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()

  // WebSocket for real-time updates
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'shopping_item_updated') {
      // Invalidate shopping list to refetch with updates
      queryClient.invalidateQueries({ queryKey: shoppingKeys.list(runId || '') })
    }
  }, [queryClient, runId])

  useWebSocket(
    runId ? `${WS_BASE_URL}/ws/runs/${runId}` : null,
    {
      onMessage: handleWebSocketMessage
    }
  )

  // Early return after all hooks have been called
  if (!runId) {
    navigate('/')
    return null
  }

  const handleAddPrice = (item: ShoppingListItem) => {
    setSelectedItem(item)
    setShowPricePopup(true)
  }

  const handleMarkPurchased = (item: ShoppingListItem) => {
    setSelectedItem(item)
    setIsEditingPurchase(false)
    setShowPurchasePopup(true)
  }

  const handleEditPurchase = (item: ShoppingListItem) => {
    setSelectedItem(item)
    setIsEditingPurchase(true)
    setShowPurchasePopup(true)
  }

  const handleSubmitPrice = async (price: number, notes: string, minimumQuantity?: number) => {
    if (!selectedItem) return

    try {
      await shoppingApi.updateAvailabilityPrice(runId, selectedItem.id, {
        price,
        notes,
        minimum_quantity: minimumQuantity
      })
      // Invalidate shopping list to refetch with updates
      queryClient.invalidateQueries({ queryKey: shoppingKeys.list(runId) })
      setShowPricePopup(false)
      setSelectedItem(null)
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'add price'), 'error')
    }
  }

  const handleSubmitPurchase = async (quantity: number, pricePerUnit: number, total: number) => {
    if (!selectedItem) return

    try {
      if (isEditingPurchase) {
        await shoppingApi.updatePurchase(runId, selectedItem.id, {
          quantity,
          price_per_unit: pricePerUnit,
          total
        })
      } else {
        await shoppingApi.markPurchased(runId, selectedItem.id, {
          quantity,
          price_per_unit: pricePerUnit,
          total
        })
      }
      // Invalidate shopping list to refetch with updates
      queryClient.invalidateQueries({ queryKey: shoppingKeys.list(runId) })
      setShowPurchasePopup(false)
      setIsEditingPurchase(false)
      setSelectedItem(null)
    } catch (err) {
      showToast(formatErrorForDisplay(err, isEditingPurchase ? 'update purchase' : 'mark as purchased'), 'error')
    }
  }

  const handleUnpurchase = async (item: ShoppingListItem) => {
    showConfirm(
      t('shopping:prompts.unpurchaseConfirm'),
      async () => {
        try {
          await shoppingApi.unpurchaseItem(runId, item.id)
          // Invalidate shopping list to refetch with updates
          queryClient.invalidateQueries({ queryKey: shoppingKeys.list(runId) })
        } catch (err) {
          showToast(formatErrorForDisplay(err, 'unpurchase item'), 'error')
        }
      }
    )
  }

  const handleAddProduct = () => {
    setShowAddProductPopup(true)
  }

  const handleProductSelected = (product: AvailableProduct) => {
    setShowAddProductPopup(false)
    setSelectedProductName(product.name)
    setSelectedProductId(product.id)
    setShowBidPopup(true)
  }

  const handleSubmitBid = async (quantity: number) => {
    try {
      await shoppingApi.addProductToShoppingList(runId, selectedProductId, quantity)
      // Invalidate shopping list and run details to refetch
      queryClient.invalidateQueries({ queryKey: shoppingKeys.list(runId) })
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
      showToast(t('shopping:messages.productAdded'), 'success')
      setShowBidPopup(false)
      setSelectedProductName('')
      setSelectedProductId('')
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'add product to shopping list'), 'error')
    }
  }

  const handleCancelBid = () => {
    setShowBidPopup(false)
    setSelectedProductName('')
    setSelectedProductId('')
  }

  const handleCancelAddProduct = () => {
    setShowAddProductPopup(false)
  }

  const handleCompleteShopping = async () => {
    const completeShoppingAction = async () => {
      try {
        await shoppingApi.completeShopping(runId)
        // Navigate back to run page
        navigate(`/runs/${runId}`)
      } catch (err) {
        showToast(formatErrorForDisplay(err, 'complete shopping'), 'error')
      }
    }

    if (unpurchasedItems.length > 0) {
      showConfirm(
        t('shopping:prompts.unpurchasedItems', { count: unpurchasedItems.length }),
        completeShoppingAction
      )
    } else {
      completeShoppingAction()
    }
  }

  const unpurchasedItems = items.filter(item => !item.is_purchased)
  const purchasedItems = items.filter(item => item.is_purchased)
  const totalSpent = purchasedItems.reduce((sum, item) => {
    return sum + (parseFloat(item.purchased_total || '0'))
  }, 0)

  if (loading) {
    return (
      <div className="shopping-page">
        <button onClick={() => navigate(`/runs/${runId}`)} className="back-button">{t('shopping:navigation.backToRun')}</button>
        <p>{t('shopping:messages.loadingShoppingList')}</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="shopping-page">
        <button onClick={() => navigate(`/runs/${runId}`)} className="back-button">{t('shopping:navigation.backToRun')}</button>
        <div className="error">
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="shopping-page">
      <div className="shopping-header">
        <button onClick={() => navigate(`/runs/${runId}`)} className="back-button">{t('shopping:navigation.backToRun')}</button>
        <h2>{t('shopping:labels.shoppingMode')}</h2>
        <div className="header-actions">
          <div className="total-display">
            {t('shopping:labels.total')}: {totalSpent.toFixed(2)} RSD
          </div>
          <button onClick={handleCompleteShopping} className="btn btn-success btn-lg">
            {t('shopping:actions.completeShopping')}
          </button>
        </div>
      </div>

      <div className="shopping-content">
        {unpurchasedItems.length > 0 && (
          <div className="shopping-section">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3>{t('shopping:labels.toBuy', { count: unpurchasedItems.length })}</h3>
              <button onClick={handleAddProduct} className="btn btn-secondary btn-sm">
                + {t('run:actions.addProduct')}
              </button>
            </div>
            <div className="shopping-list">
              {unpurchasedItems.map(item => (
                <ShoppingItem
                  key={item.id}
                  item={item}
                  onAddPrice={handleAddPrice}
                  onMarkPurchased={handleMarkPurchased}
                />
              ))}
            </div>
          </div>
        )}

        {purchasedItems.length > 0 && (
          <div className="shopping-section purchased-section">
            <h3>{t('shopping:labels.purchased', { count: purchasedItems.length })}</h3>
            <div className="shopping-list">
              {purchasedItems.map(item => (
                <ShoppingItem key={item.id} item={item} onEditPurchase={handleEditPurchase} onUnpurchase={handleUnpurchase} />
              ))}
            </div>
          </div>
        )}
      </div>

      {showPricePopup && selectedItem && (
        <PricePopup
          item={selectedItem}
          onSubmit={handleSubmitPrice}
          onClose={() => {
            setShowPricePopup(false)
            setSelectedItem(null)
          }}
        />
      )}

      {showPurchasePopup && selectedItem && (
        <PurchasePopup
          item={selectedItem}
          isEditMode={isEditingPurchase}
          onSubmit={handleSubmitPurchase}
          onClose={() => {
            setShowPurchasePopup(false)
            setIsEditingPurchase(false)
            setSelectedItem(null)
          }}
        />
      )}

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={hideToast}
        />
      )}

      {confirmState && (
        <ConfirmDialog
          message={confirmState.message}
          onConfirm={handleConfirm}
          onCancel={hideConfirm}
        />
      )}

      {showAddProductPopup && (
        <Suspense fallback={<div>Loading...</div>}>
          <AddProductPopup
            runId={runId}
            onProductSelected={handleProductSelected}
            onCancel={handleCancelAddProduct}
          />
        </Suspense>
      )}

      {showBidPopup && (
        <Suspense fallback={<div>Loading...</div>}>
          <BidPopup
            productName={selectedProductName}
            onSubmit={handleSubmitBid}
            onCancel={handleCancelBid}
          />
        </Suspense>
      )}
    </div>
  )
}
