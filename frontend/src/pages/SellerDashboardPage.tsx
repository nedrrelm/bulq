import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Copy, Check, RefreshCw, Store, Users } from 'lucide-react'
import {
  useMySellerProfile,
  useCreateSeller,
  useUpdateSeller,
  useToggleJoiningAllowed,
  useToggleSearchable,
  useRegenerateSellerToken,
  useSellerFollowers,
} from '../hooks/queries/useSellers'
import { logger } from '../utils/logger'
import '../styles/pages/SellerDashboardPage.css'

export default function SellerDashboardPage() {
  const { t } = useTranslation(['seller'])
  const navigate = useNavigate()
  const { data: seller, isLoading } = useMySellerProfile()
  const { data: followers = [] } = useSellerFollowers()
  const createSeller = useCreateSeller()
  const updateSeller = useUpdateSeller()
  const toggleJoining = useToggleJoiningAllowed()
  const toggleSearchable = useToggleSearchable()
  const regenerateToken = useRegenerateSellerToken()

  const [displayName, setDisplayName] = useState('')
  const [description, setDescription] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [linkCopied, setLinkCopied] = useState(false)

  if (isLoading) {
    return <div className="seller-page"><p>Loading...</p></div>
  }

  // No seller profile — show creation form
  if (!seller) {
    return (
      <div className="seller-page">
        <h1>{t('seller:dashboard.becomeSeller')}</h1>
        <div className="card">
          <div className="empty-state">
            <Store size={48} />
            <p>{t('seller:dashboard.noProfile')}</p>
          </div>
          <form
            className="seller-form"
            onSubmit={async (e) => {
              e.preventDefault()
              try {
                await createSeller.mutateAsync({
                  display_name: displayName,
                  description: description || null,
                })
              } catch (err) {
                logger.error('Failed to create seller:', err)
              }
            }}
          >
            <div className="form-group">
              <label className="form-label">{t('seller:form.displayName')}</label>
              <input
                className="form-input"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder={t('seller:form.displayNamePlaceholder')}
                required
                maxLength={200}
              />
            </div>
            <div className="form-group">
              <label className="form-label">{t('seller:form.description')}</label>
              <textarea
                className="form-input seller-description-input"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={t('seller:form.descriptionPlaceholder')}
                maxLength={2000}
                rows={3}
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!displayName.trim() || createSeller.isPending}
            >
              {createSeller.isPending ? t('seller:form.creating') : t('seller:form.create')}
            </button>
          </form>
        </div>
      </div>
    )
  }

  // Has seller profile — show dashboard
  const inviteUrl = `${window.location.origin}/seller/invite/${seller.invite_token}`

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(inviteUrl)
      setLinkCopied(true)
      setTimeout(() => setLinkCopied(false), 2000)
    } catch (err) {
      logger.error('Failed to copy link:', err)
    }
  }

  const handleSaveEdit = async () => {
    try {
      await updateSeller.mutateAsync({
        display_name: displayName || null,
        description: description || null,
      })
      setIsEditing(false)
    } catch (err) {
      logger.error('Failed to update seller:', err)
    }
  }

  const startEditing = () => {
    setDisplayName(seller.display_name)
    setDescription(seller.description || '')
    setIsEditing(true)
  }

  return (
    <div className="seller-page">
      <h1>{t('seller:dashboard.title')}</h1>

      {/* Profile Section */}
      <div className="card seller-profile-card">
        {isEditing ? (
          <div className="seller-form">
            <div className="form-group">
              <label className="form-label">{t('seller:form.displayName')}</label>
              <input
                className="form-input"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                maxLength={200}
              />
            </div>
            <div className="form-group">
              <label className="form-label">{t('seller:form.description')}</label>
              <textarea
                className="form-input seller-description-input"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={2000}
                rows={3}
              />
            </div>
            <div className="seller-edit-actions">
              <button
                className="btn btn-primary"
                onClick={handleSaveEdit}
                disabled={updateSeller.isPending}
              >
                {updateSeller.isPending ? t('seller:form.updating') : t('seller:form.update')}
              </button>
              <button className="btn btn-secondary" onClick={() => setIsEditing(false)}>
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="seller-profile-info">
            <div className="seller-profile-header">
              <div>
                <h2>{seller.display_name}</h2>
                {seller.description && <p className="seller-description">{seller.description}</p>}
              </div>
              <button className="btn btn-secondary" onClick={startEditing}>
                Edit
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Invite Link */}
      <div className="card">
        <h3>{t('seller:dashboard.inviteLink')}</h3>
        <div className="invite-link-row">
          <code className="invite-link-code">{inviteUrl}</code>
          <button className="btn btn-secondary" onClick={handleCopyLink} title={t('seller:dashboard.copyLink')}>
            {linkCopied ? <Check size={16} /> : <Copy size={16} />}
            {linkCopied ? t('seller:dashboard.linkCopied') : t('seller:dashboard.copyLink')}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => regenerateToken.mutate()}
            disabled={regenerateToken.isPending}
            title={t('seller:dashboard.regenerateToken')}
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Settings */}
      <div className="card">
        <h3>{t('seller:dashboard.settings')}</h3>
        <div className="seller-settings">
          <div className="setting-item">
            <div>
              <h3>{t('seller:dashboard.allowJoining')}</h3>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={seller.is_joining_allowed}
                onChange={() => toggleJoining.mutate()}
                disabled={toggleJoining.isPending}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>
          <div className="setting-item">
            <div>
              <h3>{t('seller:dashboard.searchable')}</h3>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={seller.is_searchable}
                onChange={() => toggleSearchable.mutate()}
                disabled={toggleSearchable.isPending}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>

      {/* Followers */}
      <div className="card clickable" onClick={() => navigate('/seller/followers')}>
        <div className="seller-profile-header">
          <h3><Users size={18} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />{t('seller:dashboard.followers')}</h3>
          <span className="follower-count">{followers.length}</span>
        </div>
      </div>

      {/* Sales placeholder (will be populated in Slice 3) */}
      <div className="card">
        <h3>{t('seller:dashboard.sales')}</h3>
        <div className="empty-state">
          <p>{t('seller:dashboard.noSales')}</p>
        </div>
      </div>
    </div>
  )
}
