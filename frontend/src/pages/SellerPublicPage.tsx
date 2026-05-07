import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Store, ArrowLeft } from 'lucide-react'
import { useSeller, useFollowSeller } from '../hooks/queries/useSellers'
import { groupsApi } from '../api/groups'
import type { Group } from '../api/groups'
import { useAuth } from '../hooks/useAuth'
import { getErrorMessage } from '../utils/errorHandling'
import { logger } from '../utils/logger'
import '../styles/pages/SellerDashboardPage.css'

export default function SellerPublicPage() {
  const { t } = useTranslation(['seller'])
  const { sellerId } = useParams<{ sellerId: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { data: seller, isLoading } = useSeller(sellerId)
  const followMutation = useFollowSeller()

  const [groups, setGroups] = useState<Group[]>([])
  const [selectedGroupId, setSelectedGroupId] = useState('')
  const [showFollowForm, setShowFollowForm] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleShowFollow = async () => {
    try {
      const myGroups = await groupsApi.getMyGroups()
      setGroups(myGroups)
      if (myGroups.length > 0) setSelectedGroupId(myGroups[0].id)
      setShowFollowForm(true)
    } catch (err) {
      logger.error('Failed to load groups:', err)
    }
  }

  const handleFollow = () => {
    if (!sellerId || !selectedGroupId) return
    setError('')

    followMutation.mutate(
      { sellerId, groupId: selectedGroupId },
      {
        onSuccess: () => {
          setSuccess(t('seller:join.success'))
          setShowFollowForm(false)
          setTimeout(() => setSuccess(''), 3000)
        },
        onError: (err) => {
          setError(getErrorMessage(err, t('seller:join.errors.followFailed')))
        },
      }
    )
  }

  if (isLoading || !user) return <div className="seller-page"><p>Loading...</p></div>

  if (!seller) {
    return (
      <div className="seller-page">
        <p>{t('seller:errors.createFailed')}</p>
      </div>
    )
  }

  return (
    <div className="seller-page">
      <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: '1rem' }}>
        <ArrowLeft size={16} /> Back
      </button>

      <div className="card seller-profile-card">
        <div className="seller-profile-info">
          <div className="seller-profile-header">
            <div>
              <h2><Store size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />{seller.display_name}</h2>
              {seller.description && <p className="seller-description">{seller.description}</p>}
            </div>
          </div>
        </div>
      </div>

      {success && <div className="alert alert-success">{success}</div>}

      {seller.is_joining_allowed && !showFollowForm && (
        <button className="btn btn-primary" onClick={handleShowFollow}>
          {t('seller:join.follow')}
        </button>
      )}

      {showFollowForm && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <h3>{t('seller:join.title')}</h3>
          {groups.length === 0 ? (
            <p>{t('seller:join.noGroups')}</p>
          ) : (
            <>
              <div className="form-group">
                <label className="form-label">{t('seller:join.selectGroup')}</label>
                <select
                  className="form-input"
                  value={selectedGroupId}
                  onChange={(e) => setSelectedGroupId(e.target.value)}
                >
                  {groups.map((g) => (
                    <option key={g.id} value={g.id}>{g.name}</option>
                  ))}
                </select>
              </div>
              {error && <div className="alert alert-error">{error}</div>}
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                <button
                  className="btn btn-primary"
                  onClick={handleFollow}
                  disabled={followMutation.isPending}
                >
                  {followMutation.isPending ? t('seller:join.following') : t('seller:join.follow')}
                </button>
                <button className="btn btn-secondary" onClick={() => setShowFollowForm(false)}>
                  Cancel
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
