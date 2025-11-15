import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { runsApi } from '../api'
import { getErrorMessage } from '../utils/errorHandling'
import { logger } from '../utils/logger'

interface DownloadRunStateButtonProps {
  runId: string
  storeName: string
  className?: string
}

export default function DownloadRunStateButton({
  runId,
  storeName,
  className = 'btn btn-secondary'
}: DownloadRunStateButtonProps) {
  const { t } = useTranslation(['run'])
  const [isDownloading, setIsDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDownload = async () => {
    try {
      setIsDownloading(true)
      setError(null)

      // Fetch the run state data
      const data = await runsApi.exportRunState(runId)

      // Create a blob from the JSON data
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })

      // Create a download link
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url

      // Generate filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      const filename = `run-${storeName.replace(/\s+/g, '-')}-${timestamp}.json`
      link.download = filename

      // Trigger download
      document.body.appendChild(link)
      link.click()

      // Cleanup
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (err) {
      logger.error('Failed to download run state:', err)
      setError(getErrorMessage(err, 'Failed to download'))
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div style={{ display: 'inline-block' }}>
      <button
        onClick={handleDownload}
        className={className}
        disabled={isDownloading}
        title={t('run:actions.downloadStateTooltip')}
      >
        {isDownloading ? `⏳ ${t('run:actions.downloading')}` : `📥 ${t('run:actions.downloadState')}`}
      </button>
      {error && (
        <div style={{ color: 'var(--color-error)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
          {error}
        </div>
      )}
    </div>
  )
}
