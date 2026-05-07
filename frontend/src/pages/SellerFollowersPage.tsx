import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Users, ArrowLeft } from 'lucide-react'
import { useSellerFollowers } from '../hooks/queries/useSellers'
import '../styles/pages/SellerDashboardPage.css'

export default function SellerFollowersPage() {
  const { t } = useTranslation(['seller'])
  const navigate = useNavigate()
  const { data: followers = [], isLoading } = useSellerFollowers()

  return (
    <div className="seller-page">
      <div className="seller-profile-header">
        <h1>
          <button className="btn btn-secondary" onClick={() => navigate('/seller')} style={{ marginRight: '0.5rem' }}>
            <ArrowLeft size={16} />
          </button>
          {t('seller:dashboard.followers')}
        </h1>
      </div>

      {isLoading ? (
        <p>Loading...</p>
      ) : followers.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <Users size={48} />
            <p>{t('seller:followers.noFollowers')}</p>
          </div>
        </div>
      ) : (
        <div className="followers-list">
          {followers.map((f) => (
            <div key={f.id} className="card follower-card" onClick={() => navigate(`/groups/${f.group_id}`)}>
              <div className="follower-info">
                <h3>{f.group_name}</h3>
                <span className="follower-meta">{f.member_count} members</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
