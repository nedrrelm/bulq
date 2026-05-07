import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Store } from 'lucide-react'
import { sellersApi } from '../api/sellers'
import { groupsApi } from '../api/groups'
import { useAuth } from '../hooks/useAuth'
import { useFollowSellerByToken } from '../hooks/queries/useSellers'
import { getErrorMessage } from '../utils/errorHandling'
import type { SellerPreview } from '../schemas/seller'
import type { Group } from '../api/groups'
import '../styles/pages/JoinGroup.css'

interface JoinSellerProps {
  inviteToken: string
  onJoinSuccess: () => void
}

export default function JoinSeller({ inviteToken, onJoinSuccess }: JoinSellerProps) {
  const { t } = useTranslation(['seller'])
  const { user } = useAuth()
  const navigate = useNavigate()
  const followMutation = useFollowSellerByToken()

  const [sellerPreview, setSellerPreview] = useState<SellerPreview | null>(null)
  const [groups, setGroups] = useState<Group[]>([])
  const [selectedGroupId, setSelectedGroupId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (!user) return

    const fetchData = async () => {
      try {
        setLoading(true)
        const [preview, myGroups] = await Promise.all([
          sellersApi.getSellerByInviteToken(inviteToken),
          groupsApi.getMyGroups(),
        ])
        setSellerPreview(preview)
        setGroups(myGroups)
        if (myGroups.length > 0) {
          setSelectedGroupId(myGroups[0].id)
        }
      } catch (err) {
        setError(getErrorMessage(err, t('seller:join.errors.loadFailed')))
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [inviteToken, user, t])

  const handleFollow = () => {
    if (!selectedGroupId) return
    setError('')

    followMutation.mutate(
      { inviteToken, groupId: selectedGroupId },
      {
        onSuccess: () => {
          setSuccess(true)
          setTimeout(() => {
            onJoinSuccess()
          }, 1500)
        },
        onError: (err) => {
          setError(getErrorMessage(err, t('seller:join.errors.followFailed')))
        },
      }
    )
  }

  if (!user) return null

  if (loading) {
    return (
      <div className="join-group-page">
        <div className="join-group-card">
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  if (error && !sellerPreview) {
    return (
      <div className="join-group-page">
        <div className="join-group-card">
          <div className="alert alert-error">{error}</div>
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            {t('seller:join.goHome')}
          </button>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="join-group-page">
        <div className="join-group-card">
          <Store size={48} />
          <h2>{t('seller:join.success')}</h2>
          <p>{t('seller:join.successDescription', { name: sellerPreview?.display_name })}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="join-group-page">
      <div className="join-group-card">
        <Store size={48} />
        <h2>{t('seller:join.title')}</h2>
        {sellerPreview && (
          <div className="join-group-info">
            <h3>{sellerPreview.display_name}</h3>
            {sellerPreview.description && <p>{sellerPreview.description}</p>}
          </div>
        )}

        {!sellerPreview?.is_joining_allowed ? (
          <div className="alert alert-error">{t('seller:join.joiningDisabled')}</div>
        ) : groups.length === 0 ? (
          <div className="alert alert-error">{t('seller:join.noGroups')}</div>
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
                  <option key={g.id} value={g.id}>
                    {g.name}
                  </option>
                ))}
              </select>
            </div>
            {error && <div className="alert alert-error">{error}</div>}
            <button
              className="btn btn-primary"
              onClick={handleFollow}
              disabled={followMutation.isPending || !selectedGroupId}
            >
              {followMutation.isPending ? t('seller:join.following') : t('seller:join.follow')}
            </button>
          </>
        )}
      </div>
    </div>
  )
}
