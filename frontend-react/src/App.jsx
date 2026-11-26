
import { useCallback, useEffect, useRef, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

let accessToken = null
let refreshPromise = null

const MENU = [
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
  { id: 'documents', label: 'My Documents', icon: 'file' },
  { id: 'assistant', label: 'AI Assistant', icon: 'spark' },
  { id: 'monitoring', label: 'Monitoring', icon: 'activity' },
]

async function sendRequest(path, options = {}, token = null) {
  const headers = new Headers(options.headers || {})

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  let response

  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      credentials: 'same-origin',
    })
  } catch {
    throw new Error('Cannot connect to the backend server.')
  }

  let data = null

  if (response.status !== 204) {
    const type = response.headers.get('content-type') || ''

    data = type.includes('application/json')
      ? await response.json()
      : await response.text()
  }

  if (!response.ok) {
    const detail = data?.detail

    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map(item => item.msg || 'Validation error').join('; ')
          : `Request failed (${response.status})`

    const error = new Error(message)
    error.status = response.status
    throw error
  }

  return data
}

async function refreshSession() {
  if (!refreshPromise) {
    refreshPromise = sendRequest('/auth/refresh', {
      method: 'POST',
    })
      .then(result => {
        accessToken = result.access_token
        return result
      })
      .catch(error => {
        accessToken = null
        throw error
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  return refreshPromise
}

async function apiRequest(path, options = {}) {
  const protectedRoute =
    path.startsWith('/documents') ||
    path.startsWith('/questions')

  try {
    return await sendRequest(
      path,
      options,
      protectedRoute ? accessToken : null
    )
  } catch (error) {
    if (!protectedRoute || error.status !== 401) {
      throw error
    }

    try {
      await refreshSession()
    } catch {
      accessToken = null
      window.dispatchEvent(new Event('rag-session-expired'))
      throw new Error('Session expired. Please sign in again.')
    }

    return sendRequest(path, options, accessToken)
  }
}

function Icon({ name, size = 20 }) {
  const icons = {
    dashboard: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </>
    ),
    file: (
      <>
        <path d="M6 3h9l4 4v14H6z" />
        <path d="M15 3v5h4M9 13h7M9 17h7" />
      </>
    ),
    spark: (
      <path d="m12 2 2.7 7.3L22 12l-7.3 2.7L12 22l-2.7-7.3L2 12l7.3-2.7z" />
    ),
    activity: (
      <path d="M3 12h4l3-7 4 14 3-7h4" />
    ),
    upload: (
      <>
        <path d="M12 16V3m-5 5 5-5 5 5" />
        <path d="M4 16v4h16v-4" />
      </>
    ),
    arrow: (
      <path d="M5 12h14m-6-6 6 6-6 6" />
    ),
    trash: (
      <>
        <path d="M4 7h16M9 7V4h6v3M7 7l1 14h8l1-14" />
        <path d="M10 11v6M14 11v6" />
      </>
    ),
    logout: (
      <>
        <path d="M10 4H5v16h5M14 8l4 4-4 4M8 12h10" />
      </>
    ),
    check: (
      <path d="m5 12 4 4L19 6" />
    ),
    shield: (
      <>
        <path d="M12 2 4 6v6c0 5 3 8 8 10 5-2 8-5 8-10V6z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
    refresh: (
      <>
        <path d="M20 11a8 8 0 0 0-14-5L3 9" />
        <path d="M3 3v6h6M4 13a8 8 0 0 0 14 5l3-3" />
        <path d="M21 21v-6h-6" />
      </>
    ),
    menu: <path d="M4 7h16M4 12h16M4 17h16" />,
    close: <path d="M5 5l14 14M19 5 5 19" />,
    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </>
    ),
    lock: (
      <>
        <rect x="5" y="10" width="14" height="11" rx="2" />
        <path d="M8 10V7a4 4 0 0 1 8 0v3" />
      </>
    ),
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    copy: (
      <>
        <rect x="8" y="8" width="12" height="12" rx="2" />
        <path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3" />
      </>
    ),
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {icons[name] || icons.spark}
    </svg>
  )
}

function Button({
  children,
  variant = 'primary',
  className = '',
  ...props
}) {
  return (
    <button
      className={`rag-btn rag-btn-${variant} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

function Notice({ message, error = false }) {
  if (!message) return null

  return (
    <div
      className={`rag-notice ${error ? 'rag-notice-error' : ''}`}
      role={error ? 'alert' : 'status'}
    >
      {message}
    </div>
  )
}

function StatCard({ icon, label, value, helper }) {
  return (
    <article className="rag-stat">
      <div className="rag-stat-top">
        <span>{label}</span>
        <div className="rag-stat-icon">
          <Icon name={icon} size={19} />
        </div>
      </div>
      <strong>{value}</strong>
      <small>{helper}</small>
    </article>
  )
}

function EmptyState({
  icon = 'file',
  title,
  description,
  action,
  onAction,
}) {
  return (
    <div className="rag-empty">
      <div className="rag-empty-icon">
        <Icon name={icon} size={27} />
      </div>
      <h3>{title}</h3>
      <p>{description}</p>
      {action && (
        <Button
          type="button"
          variant="secondary"
          onClick={onAction}
        >
          {action}
          <Icon name="arrow" size={16} />
        </Button>
      )}
    </div>
  )
}

function AuthScreen({ onAuthenticated }) {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const result = await sendRequest(`/auth/${mode}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      })

      accessToken = result.access_token
      setPassword('')
      onAuthenticated(result.user)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rag-auth-page">
      <section className="rag-auth-side">
        <div className="rag-auth-brand">
          <span className="rag-brand-icon">
            <Icon name="spark" size={23} />
          </span>
          <div>
            <strong>Production RAG Service</strong>
            <small>AI Knowledge Workspace</small>
          </div>
        </div>

        <div className="rag-auth-pitch">
          <div className="rag-pill">
            <Icon name="spark" size={15} />
            INTELLIGENT DOCUMENT SEARCH
          </div>

          <h1>
            Your knowledge.
            <br />
            <span>Finally connected.</span>
          </h1>

          <p>
            Transform documents into a searchable knowledge
            workspace. Ask questions and get answers supported
            by real source evidence.
          </p>

          <div className="rag-auth-benefits">
            <div>
              <Icon name="file" />
              <span>Secure document management</span>
            </div>
            <div>
              <Icon name="spark" />
              <span>AI-powered question answering</span>
            </div>
            <div>
              <Icon name="shield" />
              <span>Private, user-specific knowledge</span>
            </div>
          </div>
        </div>

        <div className="rag-auth-copyright">
          Production RAG Service · React + FastAPI
        </div>
      </section>

      <section className="rag-auth-main">
        <div className="rag-auth-form-wrap">
          <div className="rag-auth-mobile-brand">
            <span className="rag-brand-icon">
              <Icon name="spark" size={21} />
            </span>
            <strong>Production RAG Service</strong>
          </div>

          <div className="rag-auth-small-icon">
            <Icon name="lock" size={22} />
          </div>

          <h2>
            {mode === 'login'
              ? 'Welcome back'
              : 'Create your account'}
          </h2>

          <p className="rag-auth-subtitle">
            {mode === 'login'
              ? 'Sign in to continue to your workspace.'
              : 'Start building your private knowledge base.'}
          </p>

          <form className="rag-auth-form" onSubmit={submit}>
            <label>
              Email address
              <input
                type="email"
                required
                autoComplete="email"
                placeholder="you@example.com"
                value={email}
                onChange={event => setEmail(event.target.value)}
              />
            </label>

            <label>
              Password
              <input
                type="password"
                required
                minLength={mode === 'signup' ? 8 : undefined}
                autoComplete={
                  mode === 'login'
                    ? 'current-password'
                    : 'new-password'
                }
                placeholder="Enter your password"
                value={password}
                onChange={event => setPassword(event.target.value)}
              />
            </label>

            {mode === 'signup' && (
              <p className="rag-password-hint">
                At least 8 characters, including uppercase,
                lowercase and a number.
              </p>
            )}

            <Notice message={error} error />

            <Button
              type="submit"
              className="rag-full"
              disabled={loading}
            >
              {loading
                ? 'Please wait...'
                : mode === 'login'
                  ? 'Sign in to workspace'
                  : 'Create account'}
              {!loading && <Icon name="arrow" size={17} />}
            </Button>
          </form>

          <div className="rag-auth-toggle">
            {mode === 'login'
              ? "Don't have an account?"
              : 'Already have an account?'}

            <button
              type="button"
              onClick={() => {
                setMode(mode === 'login' ? 'signup' : 'login')
                setError('')
              }}
            >
              {mode === 'login' ? 'Create one' : 'Sign in'}
            </button>
          </div>

          <div className="rag-auth-trust">
            <Icon name="shield" size={17} />
            Your documents are accessible only to your account.
          </div>
        </div>
      </section>
    </div>
  )
}

function App() {
  const [user, setUser] = useState(null)
  const [checking, setChecking] = useState(true)
  const [page, setPage] = useState('dashboard')
  const [mobileMenu, setMobileMenu] = useState(false)
  const [online, setOnline] = useState(null)
  const [loggingOut, setLoggingOut] = useState(false)

  const [documents, setDocuments] = useState([])
  const [docsLoading, setDocsLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [documentMessage, setDocumentMessage] = useState('')
  const [documentError, setDocumentError] = useState(false)
  const fileInput = useRef(null)

  const [question, setQuestion] = useState('')
  const [topK, setTopK] = useState(5)
  const [threshold, setThreshold] = useState(0)
  const [asking, setAsking] = useState(false)
  const [answer, setAnswer] = useState('')
  const [citations, setCitations] = useState([])
  const [chunks, setChunks] = useState([])
  const [retrievedCount, setRetrievedCount] = useState(0)
  const [questionMessage, setQuestionMessage] = useState('')
  const [questionError, setQuestionError] = useState(false)
  const [copied, setCopied] = useState(false)

  const [metrics, setMetrics] = useState(null)
  const [metricsLoading, setMetricsLoading] = useState(false)
  const [metricsError, setMetricsError] = useState('')

  const loadDocuments = useCallback(async () => {
    setDocsLoading(true)

    try {
      const result = await apiRequest('/documents')
      setDocuments(
        Array.isArray(result)
          ? result
          : Array.isArray(result?.documents)
            ? result.documents
            : []
      )
    } catch (error) {
      setDocumentMessage(error.message)
      setDocumentError(true)
    } finally {
      setDocsLoading(false)
    }
  }, [])

  const loadMetrics = useCallback(async () => {
    setMetricsLoading(true)
    setMetricsError('')

    try {
      setMetrics(await apiRequest('/metrics'))
    } catch (error) {
      setMetricsError(error.message)
    } finally {
      setMetricsLoading(false)
    }
  }, [])

  const checkHealth = useCallback(async () => {
    try {
      await apiRequest('/health')
      setOnline(true)
    } catch {
      setOnline(false)
    }
  }, [])

  useEffect(() => {
    let active = true

    refreshSession()
      .then(result => {
        if (active) setUser(result.user)
      })
      .catch(() => {
        if (active) setUser(null)
      })
      .finally(() => {
        if (active) setChecking(false)
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    const handleExpired = () => {
      accessToken = null
      setUser(null)
      setDocuments([])
      setAnswer('')
      setCitations([])
      setChunks([])
      setRetrievedCount(0)
      setMetrics(null)
      setPage('dashboard')
    }

    window.addEventListener(
      'rag-session-expired',
      handleExpired
    )

    return () => {
      window.removeEventListener(
        'rag-session-expired',
        handleExpired
      )
    }
  }, [])

  useEffect(() => {
    if (!user) return

    checkHealth()
    loadDocuments()
    loadMetrics()
  }, [user, checkHealth, loadDocuments, loadMetrics])

  function navigate(destination) {
    setPage(destination)
    setMobileMenu(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function logout() {
    if (loggingOut) return

    setLoggingOut(true)

    try {
      await sendRequest('/auth/logout', {
        method: 'POST',
      })
    } catch {
      // The local session is cleared even if the server fails.
    } finally {
      accessToken = null
      setUser(null)
      setPage('dashboard')
      setMobileMenu(false)
      setDocuments([])
      setSelectedFile(null)
      setQuestion('')
      setAnswer('')
      setCitations([])
      setChunks([])
      setRetrievedCount(0)
      setMetrics(null)
      setDocumentMessage('')
      setQuestionMessage('')
      setLoggingOut(false)
    }
  }

  function selectFile(file) {
    if (!file) return

    const extension = file.name.split('.').pop()?.toLowerCase()

    if (!['pdf', 'docx'].includes(extension)) {
      setDocumentError(true)
      setDocumentMessage('Please select a PDF or DOCX document.')
      return
    }

    setSelectedFile(file)
    setDocumentMessage('')
    setDocumentError(false)
  }

  function handleDrop(event) {
    event.preventDefault()
    setDragging(false)
    selectFile(event.dataTransfer.files?.[0])
  }

  async function handleUpload(event) {
    event.preventDefault()

    if (!selectedFile) {
      setDocumentMessage('Choose a document to upload.')
      setDocumentError(true)
      return
    }

    const formData = new FormData()
    formData.append('file', selectedFile)

    setUploading(true)
    setDocumentMessage('Uploading and indexing your document...')
    setDocumentError(false)

    try {
      const result = await apiRequest('/documents/upload', {
        method: 'POST',
        body: formData,
      })

      setDocumentMessage(
        `${result.filename} uploaded and indexed successfully.`
      )
      setSelectedFile(null)

      if (fileInput.current) {
        fileInput.current.value = ''
      }

      await loadDocuments()
      await loadMetrics()
    } catch (error) {
      setDocumentMessage(error.message)
      setDocumentError(true)
    } finally {
      setUploading(false)
    }
  }

  async function handleDelete(item) {
    const id = item.document_id || item.id
    const filename = item.filename || 'Document'

    if (!window.confirm(`Delete "${filename}" permanently?`)) {
      return
    }

    setDeletingId(id)
    setDocumentMessage('')

    try {
      await apiRequest(
        `/documents/${encodeURIComponent(id)}`,
        { method: 'DELETE' }
      )

      setDocumentMessage(`${filename} deleted successfully.`)
      setDocumentError(false)

      await loadDocuments()
      await loadMetrics()
    } catch (error) {
      setDocumentMessage(error.message)
      setDocumentError(true)
    } finally {
      setDeletingId(null)
    }
  }

  async function handleAsk(event) {
    event.preventDefault()

    if (!question.trim()) {
      setQuestionMessage('Please enter a question.')
      setQuestionError(true)
      return
    }

    setAsking(true)
    setQuestionError(false)
    setQuestionMessage('')
    setAnswer('')
    setCitations([])
    setChunks([])
    setRetrievedCount(0)

    try {
      const result = await apiRequest('/questions/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question.trim(),
          top_k: Number(topK),
          threshold: Number(threshold),
        }),
      })

      const retrieved = Array.isArray(result?.retrieved_chunks)
        ? result.retrieved_chunks
        : []

      setAnswer(result?.answer || 'No answer returned.')
      setCitations(
        Array.isArray(result?.citations)
          ? result.citations
          : []
      )
      setChunks(retrieved)
      setRetrievedCount(
        result?.retrieved_count ?? retrieved.length
      )
      setQuestionMessage('Answer generated successfully.')

      await loadMetrics()
    } catch (error) {
      setQuestionMessage(error.message)
      setQuestionError(true)
    } finally {
      setAsking(false)
    }
  }

  async function copyAnswer() {
    try {
      await navigator.clipboard.writeText(answer)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      setQuestionMessage('Unable to copy the answer.')
      setQuestionError(true)
    }
  }

  const totalChunks = documents.reduce(
    (total, item) => total + Number(item.chunk_count ?? 0),
    0
  )

  const requests = metrics?.requests || {}
  const performance = metrics?.rag_performance || {}

  const formatMs = value =>
    Number.isFinite(Number(value))
      ? `${Number(value).toFixed(1)} ms`
      : '—'

  const uptimeSeconds = Number(metrics?.uptime_seconds)

  const uptime = Number.isFinite(uptimeSeconds)
    ? `${Math.floor(uptimeSeconds / 3600)}h ${Math.floor(
        (uptimeSeconds % 3600) / 60
      )}m`
    : '—'

  const titles = {
    dashboard: {
      title: 'Dashboard',
      description: 'Your AI knowledge workspace at a glance.',
    },
    documents: {
      title: 'My Documents',
      description: 'Upload, manage and search your private documents.',
    },
    assistant: {
      title: 'AI Assistant',
      description: 'Ask questions and get answers grounded in your documents.',
    },
    monitoring: {
      title: 'Monitoring',
      description: 'Track API usage and RAG performance.',
    },
  }

  if (checking) {
    return (
      <>
        <style>{styles}</style>

        <div className="rag-loading-screen">
          <div className="rag-loader" />
          <strong>Production RAG Service</strong>
          <span>Checking your session...</span>
        </div>
      </>
    )
  }

  if (!user) {
    return (
      <>
        <style>{styles}</style>
        <AuthScreen onAuthenticated={setUser} />
      </>
    )
  }

  return (
    <div className="rag-app">
      <style>{styles}</style>

      {mobileMenu && (
        <button
          className="rag-mobile-overlay"
          onClick={() => setMobileMenu(false)}
          aria-label="Close navigation"
        />
      )}

      <aside
        className={`rag-sidebar ${
          mobileMenu ? 'rag-sidebar-open' : ''
        }`}
      >
        <div className="rag-sidebar-brand">
          <div className="rag-brand-icon">
            <Icon name="spark" size={23} />
          </div>

          <div className="rag-brand-text">
            <strong>Production RAG</strong>
            <small>AI Knowledge Workspace</small>
          </div>
        </div>

        <div className="rag-navigation-label">
          WORKSPACE
        </div>

        <nav className="rag-navigation">
          {MENU.map(item => (
            <button
              key={item.id}
              type="button"
              className={`rag-nav-item ${
                page === item.id
                  ? 'rag-nav-active'
                  : ''
              }`}
              onClick={() => navigate(item.id)}
            >
              <Icon name={item.icon} size={19} />
              <span>{item.label}</span>
              {page === item.id && (
                <span className="rag-active-dot" />
              )}
            </button>
          ))}
        </nav>

        <div className="rag-sidebar-bottom">
          <div className="rag-security-note">
            <Icon name="shield" size={20} />
            <div>
              <strong>Secure workspace</strong>
              <span>JWT authenticated</span>
            </div>
          </div>

          <div className="rag-user-card">
            <div className="rag-avatar">
              {user.email?.charAt(0).toUpperCase() || 'U'}
            </div>

            <div className="rag-user-info">
              <strong>{user.email?.split('@')[0]}</strong>
              <span title={user.email}>{user.email}</span>
            </div>
          </div>

          <button
            type="button"
            className="rag-signout-button"
            onClick={logout}
            disabled={loggingOut}
          >
            <Icon name="logout" size={18} />
            <span>
              {loggingOut ? 'Signing out...' : 'Sign Out'}
            </span>
            <Icon name="arrow" size={15} />
          </button>
        </div>
      </aside>

      <div className="rag-main">
        <header className="rag-topbar">
          <div className="rag-topbar-left">
            <button
              className="rag-menu-toggle"
              type="button"
              onClick={() => setMobileMenu(true)}
              aria-label="Open navigation"
            >
              <Icon name="menu" />
            </button>

            <span>Workspace</span>
            <span className="rag-divider-slash">/</span>
            <strong>{titles[page].title}</strong>
          </div>

          <div className="rag-topbar-right">
            <div
              className={`rag-system-status ${
                online === true ? 'rag-online' : ''
              }`}
            >
              <span />
              {online === null
                ? 'Checking'
                : online
                  ? 'System online'
                  : 'API offline'}
            </div>

            <div className="rag-top-avatar">
              {user.email?.charAt(0).toUpperCase()}
            </div>

            <button
              type="button"
              className="rag-header-signout"
              onClick={logout}
              disabled={loggingOut}
              title="Sign Out"
            >
              <Icon name="logout" size={17} />
              <span>Sign Out</span>
            </button>
          </div>
        </header>

        <main className="rag-content">
          <div className="rag-page-heading">
            <div>
              <div className="rag-kicker">
                PRODUCTION RAG SERVICE
              </div>
              <h1>{titles[page].title}</h1>
              <p>{titles[page].description}</p>
            </div>

            {page === 'dashboard' && (
              <Button
                type="button"
                onClick={() => navigate('documents')}
              >
                <Icon name="upload" size={17} />
                Upload document
              </Button>
            )}

            {page === 'documents' && (
              <Button
                type="button"
                variant="secondary"
                disabled={docsLoading}
                onClick={loadDocuments}
              >
                <Icon name="refresh" size={16} />
                Refresh
              </Button>
            )}

            {page === 'monitoring' && (
              <Button
                type="button"
                variant="secondary"
                disabled={metricsLoading}
                onClick={loadMetrics}
              >
                <Icon name="refresh" size={16} />
                Refresh metrics
              </Button>
            )}
          </div>

          {page === 'dashboard' && (
            <>
              <section className="rag-welcome">
                <div className="rag-welcome-copy">
                  <div className="rag-pill">
                    <Icon name="spark" size={15} />
                    YOUR INTELLIGENT WORKSPACE
                  </div>

                  <h2>
                    Knowledge in.
                    <br />
                    <span>Answers out.</span>
                  </h2>

                  <p>
                    Upload documents, ask questions in natural
                    language, and get answers backed by
                    real evidence.
                  </p>

                  <Button
                    type="button"
                    variant="white"
                    onClick={() => navigate('assistant')}
                  >
                    Ask AI Assistant
                    <Icon name="arrow" size={17} />
                  </Button>
                </div>

                <div
                  className="rag-welcome-visual"
                  aria-hidden="true"
                >
                  <div className="rag-visual-orbit rag-orbit-one" />
                  <div className="rag-visual-orbit rag-orbit-two" />
                  <div className="rag-visual-center">
                    <Icon name="spark" size={47} />
                  </div>
                </div>
              </section>

              <div className="rag-stats-grid">
                <StatCard
                  icon="file"
                  label="Documents"
                  value={documents.length}
                  helper="Your indexed files"
                />
                <StatCard
                  icon="dashboard"
                  label="Knowledge Chunks"
                  value={totalChunks}
                  helper="Searchable passages"
                />
                <StatCard
                  icon="search"
                  label="Latest Retrieval"
                  value={retrievedCount}
                  helper="Chunks from last question"
                />
                <StatCard
                  icon="activity"
                  label="API Requests"
                  value={requests.total ?? '—'}
                  helper="Since backend startup"
                />
              </div>

              <div className="rag-two-columns">
                <section className="rag-card">
                  <div className="rag-card-heading">
                    <div>
                      <span className="rag-section-kicker">
                        GET STARTED
                      </span>
                      <h2>What would you like to do?</h2>
                    </div>
                  </div>

                  <button
                    className="rag-quick-action"
                    onClick={() => navigate('documents')}
                  >
                    <div className="rag-quick-icon rag-blue">
                      <Icon name="upload" size={21} />
                    </div>
                    <div>
                      <strong>Upload a document</strong>
                      <span>
                        PDF or DOCX, automatically indexed
                      </span>
                    </div>
                    <Icon name="arrow" size={18} />
                  </button>

                  <button
                    className="rag-quick-action"
                    onClick={() => navigate('assistant')}
                  >
                    <div className="rag-quick-icon rag-purple">
                      <Icon name="spark" size={21} />
                    </div>
                    <div>
                      <strong>Ask your documents</strong>
                      <span>
                        Generate an evidence-backed answer
                      </span>
                    </div>
                    <Icon name="arrow" size={18} />
                  </button>

                  <button
                    className="rag-quick-action"
                    onClick={() => navigate('monitoring')}
                  >
                    <div className="rag-quick-icon rag-green">
                      <Icon name="activity" size={21} />
                    </div>
                    <div>
                      <strong>View performance</strong>
                      <span>
                        Monitor retrieval and generation
                      </span>
                    </div>
                    <Icon name="arrow" size={18} />
                  </button>
                </section>

                <section className="rag-card">
                  <div className="rag-card-heading">
                    <div>
                      <span className="rag-section-kicker">
                        KNOWLEDGE LIBRARY
                      </span>
                      <h2>Recent documents</h2>
                    </div>

                    <button
                      className="rag-text-link"
                      onClick={() => navigate('documents')}
                    >
                      View all
                      <Icon name="arrow" size={15} />
                    </button>
                  </div>

                  {documents.length === 0 ? (
                    <EmptyState
                      icon="file"
                      title="No documents yet"
                      description="Upload your first document to start asking questions."
                      action="Add a document"
                      onAction={() => navigate('documents')}
                    />
                  ) : (
                    documents.slice(0, 5).map(item => (
                      <div
                        className="rag-recent-document"
                        key={item.document_id || item.id}
                      >
                        <div className="rag-document-type">
                          {item.filename?.toLowerCase().endsWith('.pdf')
                            ? 'PDF'
                            : 'DOC'}
                        </div>
                        <div>
                          <strong>{item.filename}</strong>
                          <small>
                            {item.chunk_count ?? 0} indexed chunks
                          </small>
                        </div>
                      </div>
                    ))
                  )}
                </section>
              </div>
            </>
          )}

          {page === 'documents' && (
            <div className="rag-two-columns rag-document-layout">
              <section className="rag-card">
                <div className="rag-card-heading">
                  <div>
                    <span className="rag-section-kicker">
                      DOCUMENT INGESTION
                    </span>
                    <h2>Upload a document</h2>
                    <p>
                      Files are indexed into your private
                      knowledge base.
                    </p>
                  </div>
                </div>

                <form onSubmit={handleUpload}>
                  <div
                    className={`rag-dropzone ${
                      dragging ? 'rag-dragging' : ''
                    }`}
                    onDragOver={event => {
                      event.preventDefault()
                      setDragging(true)
                    }}
                    onDragLeave={event => {
                      event.preventDefault()
                      setDragging(false)
                    }}
                    onDrop={handleDrop}
                  >
                    <div className="rag-drop-icon">
                      <Icon name="upload" size={28} />
                    </div>

                    <strong>
                      {selectedFile
                        ? selectedFile.name
                        : 'Drag and drop your document here'}
                    </strong>

                    <p>or choose a file from your computer</p>

                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => fileInput.current?.click()}
                    >
                      Browse files
                    </Button>

                    <small>Supported formats: PDF, DOCX</small>
                  </div>

                  <input
                    ref={fileInput}
                    type="file"
                    accept=".pdf,.docx"
                    hidden
                    onChange={event =>
                      selectFile(event.target.files?.[0])
                    }
                  />

                  {selectedFile && (
                    <div className="rag-selected-file">
                      <Icon name="file" size={18} />
                      <span>{selectedFile.name}</span>
                      <button
                        type="button"
                        aria-label="Remove selected file"
                        onClick={() => {
                          setSelectedFile(null)
                          if (fileInput.current) {
                            fileInput.current.value = ''
                          }
                        }}
                      >
                        <Icon name="close" size={17} />
                      </button>
                    </div>
                  )}

                  <Button
                    type="submit"
                    className="rag-full rag-upload-submit"
                    disabled={uploading || !selectedFile}
                  >
                    <Icon name="upload" size={18} />
                    {uploading
                      ? 'Uploading and indexing...'
                      : 'Upload and index document'}
                  </Button>
                </form>

                <Notice
                  message={documentMessage}
                  error={documentError}
                />

                <div className="rag-upload-tip">
                  <Icon name="shield" size={19} />
                  Your documents can only be searched
                  by your account.
                </div>
              </section>

              <section className="rag-card">
                <div className="rag-card-heading">
                  <div>
                    <span className="rag-section-kicker">
                      YOUR KNOWLEDGE
                    </span>
                    <h2>Document library</h2>
                    <p>Manage your uploaded knowledge sources.</p>
                  </div>

                  <span className="rag-count-badge">
                    {documents.length}
                  </span>
                </div>

                {docsLoading && (
                  <div className="rag-inline-loading">
                    <div className="rag-loader" />
                    Loading documents...
                  </div>
                )}

                {!docsLoading && documents.length === 0 && (
                  <EmptyState
                    icon="file"
                    title="Your library is empty"
                    description="Upload a PDF or DOCX file to see it here."
                  />
                )}

                <div className="rag-document-list">
                  {documents.map(item => {
                    const id = item.document_id || item.id
                    const filename = item.filename || 'Document'

                    return (
                      <article
                        className="rag-document-item"
                        key={id}
                      >
                        <div className="rag-document-type">
                          {filename.toLowerCase().endsWith('.pdf')
                            ? 'PDF'
                            : 'DOC'}
                        </div>

                        <div className="rag-document-info">
                          <strong title={filename}>
                            {filename}
                          </strong>
                          <small>
                            {item.chunk_count ?? 0} searchable chunks
                          </small>
                        </div>

                        <button
                          type="button"
                          className="rag-icon-button rag-delete"
                          aria-label={`Delete ${filename}`}
                          title="Delete document"
                          disabled={deletingId === id}
                          onClick={() => handleDelete(item)}
                        >
                          <Icon name="trash" size={18} />
                        </button>
                      </article>
                    )
                  })}
                </div>
              </section>
            </div>
          )}

          {page === 'assistant' && (
            <div className="rag-assistant-layout">
              <section className="rag-card rag-question-card">
                <div className="rag-card-heading">
                  <div>
                    <span className="rag-section-kicker">
                      ASK YOUR KNOWLEDGE
                    </span>
                    <h2>What would you like to know?</h2>
                    <p>Ask in English or Roman Urdu.</p>
                  </div>

                  <div className="rag-ai-icon">
                    <Icon name="spark" size={22} />
                  </div>
                </div>

                {documents.length === 0 && (
                  <div className="rag-info-banner">
                    <Icon name="file" size={19} />
                    <div>
                      <strong>No documents uploaded yet</strong>
                      <p>
                        Upload a document first to get
                        document-grounded answers.
                      </p>
                      <button
                        type="button"
                        onClick={() => navigate('documents')}
                      >
                        Upload document
                        <Icon name="arrow" size={15} />
                      </button>
                    </div>
                  </div>
                )}

                <form onSubmit={handleAsk}>
                  <label
                    htmlFor="rag-question"
                    className="rag-field-label"
                  >
                    Your question
                  </label>

                  <textarea
                    id="rag-question"
                    className="rag-question-textarea"
                    rows={5}
                    placeholder="Example: How many annual leave days do permanent employees get?"
                    value={question}
                    onChange={event =>
                      setQuestion(event.target.value)
                    }
                  />

                  <div className="rag-suggestions">
                    <span>Try asking</span>

                    <button
                      type="button"
                      onClick={() =>
                        setQuestion(
                          'What are the main policies described in my documents?'
                        )
                      }
                    >
                      Summarize policies
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        setQuestion(
                          'What are the key requirements mentioned in my documents?'
                        )
                      }
                    >
                      Key requirements
                    </button>
                  </div>

                  <details className="rag-advanced">
                    <summary>
                      Advanced retrieval settings
                    </summary>

                    <div className="rag-settings-grid">
                      <label>
                        Top K
                        <input
                          type="number"
                          min="1"
                          max="20"
                          required
                          value={topK}
                          onChange={event =>
                            setTopK(event.target.value)
                          }
                        />
                      </label>

                      <label>
                        Similarity threshold
                        <input
                          type="number"
                          min="0"
                          max="1"
                          step="0.05"
                          required
                          value={threshold}
                          onChange={event =>
                            setThreshold(event.target.value)
                          }
                        />
                      </label>
                    </div>
                  </details>

                  <Button
                    type="submit"
                    disabled={asking || !question.trim()}
                    className="rag-ask-button"
                  >
                    <Icon name="spark" size={18} />
                    {asking
                      ? 'Generating answer...'
                      : 'Ask AI'}
                    {!asking && <Icon name="arrow" size={17} />}
                  </Button>
                </form>

                <Notice
                  message={questionMessage}
                  error={questionError}
                />
              </section>

              <section className="rag-card rag-answer-card">
                <div className="rag-card-heading">
                  <div>
                    <span className="rag-section-kicker">
                      AI RESPONSE
                    </span>
                    <h2>Your answer</h2>
                  </div>

                  {answer && (
                    <button
                      type="button"
                      className="rag-copy-button"
                      onClick={copyAnswer}
                      title="Copy answer"
                    >
                      <Icon
                        name={copied ? 'check' : 'copy'}
                        size={17}
                      />
                      {copied ? 'Copied' : 'Copy'}
                    </button>
                  )}
                </div>

                {asking ? (
                  <div className="rag-answer-loading">
                    <div className="rag-loader" />
                    <strong>
                      Searching your documents...
                    </strong>
                    <p>
                      Retrieving relevant passages
                      and generating an answer.
                    </p>
                  </div>
                ) : !answer ? (
                  <EmptyState
                    icon="spark"
                    title="Your answer will appear here"
                    description="Ask a question to get a response grounded in your uploaded documents."
                  />
                ) : (
                  <>
                    <div className="rag-answer-text">
                      {answer}
                    </div>

                    <div className="rag-answer-meta">
                      <span>
                        <Icon name="check" size={16} />
                        {retrievedCount} chunks retrieved
                      </span>
                      <span>
                        {citations.length} source citations
                      </span>
                    </div>
                  </>
                )}
              </section>

              {(citations.length > 0 || chunks.length > 0) && (
                <section className="rag-card rag-evidence-card">
                  <div className="rag-card-heading">
                    <div>
                      <span className="rag-section-kicker">
                        TRANSPARENT AI
                      </span>
                      <h2>Sources & evidence</h2>
                      <p>
                        Verify where the answer came from.
                      </p>
                    </div>
                  </div>

                  {citations.length > 0 && (
                    <div className="rag-source-list">
                      <h3>Source citations</h3>

                      {citations.map((citation, index) => {
                        const metadata =
                          citation.metadata || {}

                        return (
                          <article
                            key={`${citation.chunk_id || 'source'}-${index}`}
                            className="rag-source-item"
                          >
                            <span className="rag-source-label">
                              {citation.source_id ||
                                `S${index + 1}`}
                            </span>

                            <div>
                              <strong>
                                {metadata.filename ||
                                  'Unknown source'}
                              </strong>
                              <small>
                                Page {metadata.page ?? 'N/A'}
                              </small>
                            </div>
                          </article>
                        )
                      })}
                    </div>
                  )}

                  {chunks.length > 0 && (
                    <details className="rag-chunks-details">
                      <summary>
                        View retrieved passages ({chunks.length})
                      </summary>

                      <div className="rag-chunks-list">
                        {chunks.map((chunk, index) => {
                          const metadata =
                            chunk.metadata || {}
                          const score =
                            Number(chunk.similarity_score)

                          return (
                            <article
                              key={`${chunk.id || 'chunk'}-${index}`}
                              className="rag-chunk"
                            >
                              <div className="rag-chunk-header">
                                <strong>
                                  Passage {index + 1}
                                </strong>
                                <span>
                                  {Number.isFinite(score)
                                    ? `${(score * 100).toFixed(1)}% similarity`
                                    : 'Similarity N/A'}
                                </span>
                              </div>

                              <small>
                                {metadata.filename ||
                                  'Unknown document'}
                                {' · '}Page{' '}
                                {metadata.page ?? 'N/A'}
                              </small>

                              <p>
                                {chunk.text ||
                                  'No text available.'}
                              </p>
                            </article>
                          )
                        })}
                      </div>
                    </details>
                  )}
                </section>
              )}
            </div>
          )}

          {page === 'monitoring' && (
            <>
              <div className="rag-stats-grid">
                <StatCard
                  icon="clock"
                  label="Backend Uptime"
                  value={uptime}
                  helper="Current process"
                />
                <StatCard
                  icon="activity"
                  label="Total Requests"
                  value={requests.total ?? '—'}
                  helper="HTTP requests"
                />
                <StatCard
                  icon="check"
                  label="Successful"
                  value={requests.successful ?? '—'}
                  helper="Completed requests"
                />
                <StatCard
                  icon="shield"
                  label="Failed"
                  value={requests.failed ?? '—'}
                  helper="Failed requests"
                />
              </div>

              <section className="rag-card">
                <div className="rag-card-heading">
                  <div>
                    <span className="rag-section-kicker">
                      SYSTEM PERFORMANCE
                    </span>
                    <h2>API & RAG metrics</h2>
                    <p>
                      Measurements since the
                      last server restart.
                    </p>
                  </div>
                </div>

                <Notice
                  message={metricsError}
                  error
                />

                <div className="rag-performance-grid">
                  <StatCard
                    icon="clock"
                    label="Average API Duration"
                    value={formatMs(
                      requests.average_duration_ms
                    )}
                    helper="HTTP response time"
                  />
                  <StatCard
                    icon="search"
                    label="Retrieval Calls"
                    value={performance.retrieval_calls ?? '—'}
                    helper="Search operations"
                  />
                  <StatCard
                    icon="activity"
                    label="Average Retrieval"
                    value={formatMs(
                      performance.average_retrieval_ms
                    )}
                    helper="Search latency"
                  />
                  <StatCard
                    icon="spark"
                    label="Average Generation"
                    value={formatMs(
                      performance.average_generation_ms
                    )}
                    helper="LLM latency"
                  />
                </div>

                <div className="rag-monitor-note">
                  <Icon name="shield" size={19} />
                  Metrics are stored in memory
                  and reset when FastAPI restarts.
                </div>
              </section>
            </>
          )}
        </main>
      </div>
    </div>
  )
}

const styles = `
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
  font-family: 'DM Sans', sans-serif;
  color: #202c40;
  background: #f7f9fc;
  font-synthesis: none;
}

* { box-sizing: border-box; }
body { margin: 0; min-width: 320px; background: #f7f9fc; }
button, input, textarea { font: inherit; }
button { cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: .55; }

button:focus-visible,
input:focus-visible,
textarea:focus-visible,
summary:focus-visible {
  outline: 3px solid #a5b4fc;
  outline-offset: 3px;
}

.rag-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-radius: 10px;
  padding: 12px 17px;
  font-size: 12px;
  font-weight: 800;
  border: 1px solid transparent;
  transition: transform .15s ease, background .15s ease;
}

.rag-btn:not(:disabled):hover {
  transform: translateY(-1px);
}

.rag-btn-primary {
  background: #4b61e8;
  color: #fff;
}

.rag-btn-primary:hover {
  background: #384fcf;
}

.rag-btn-secondary {
  background: #fff;
  color: #394b68;
  border-color: #e3e7ef;
}

.rag-btn-secondary:hover {
  background: #f5f7fc;
}

.rag-btn-white {
  background: #fff;
  color: #2b417b;
}

.rag-full { width: 100%; }

.rag-notice {
  margin-top: 17px;
  padding: 12px 15px;
  background: #eaf8f0;
  color: #137d59;
  border-radius: 9px;
  font-size: 12px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.rag-notice-error {
  background: #fff0f2;
  color: #b63b54;
}

.rag-loader {
  height: 25px;
  width: 25px;
  border: 3px solid #e1e6ff;
  border-top-color: #4b61e8;
  border-radius: 50%;
  animation: rag-spin .7s linear infinite;
}

@keyframes rag-spin {
  to { transform: rotate(360deg); }
}

.rag-loading-screen {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 13px;
  color: #7b889f;
  font-size: 12px;
}

.rag-loading-screen strong {
  font-size: 18px;
  color: #1c2c46;
}

/* AUTHENTICATION */

.rag-auth-page {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(390px, .85fr);
  min-height: 100vh;
  background: #fff;
}

.rag-auth-side {
  background: #172541;
  color: #fff;
  min-height: 100vh;
  padding: 47px 60px 35px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.rag-auth-side:after {
  content: '';
  position: absolute;
  width: 570px;
  height: 570px;
  border: 1px solid #ffffff15;
  border-radius: 50%;
  right: -260px;
  bottom: -290px;
  box-shadow:
    0 0 0 90px #ffffff05,
    0 0 0 180px #ffffff04;
}

.rag-auth-brand,
.rag-sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rag-brand-icon {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  background: #5469ec;
  border-radius: 12px;
  color: #fff;
}

.rag-auth-brand strong,
.rag-sidebar-brand strong {
  display: block;
  font: 800 17px 'Manrope', sans-serif;
  letter-spacing: -.5px;
}

.rag-auth-brand small,
.rag-sidebar-brand small {
  display: block;
  color: #9fafc8;
  font-size: 10px;
  margin-top: 4px;
}

.rag-auth-pitch {
  margin: auto 0;
  padding: 55px 0;
  max-width: 540px;
  position: relative;
  z-index: 1;
}

.rag-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-weight: 800;
  font-size: 10px;
  letter-spacing: 1.1px;
  background: #ffffff1a;
  border: 1px solid #ffffff27;
  border-radius: 7px;
  padding: 9px 12px;
}

.rag-auth-pitch h1 {
  font: 800 clamp(39px, 4vw, 62px)/1.2 'Manrope', sans-serif;
  letter-spacing: -2.5px;
  margin: 26px 0 18px;
}

.rag-auth-pitch h1 span {
  color: #a7b5ff;
}

.rag-auth-pitch > p {
  color: #b9c7da;
  font-size: 15px;
  line-height: 1.9;
  max-width: 460px;
}

.rag-auth-benefits {
  display: grid;
  gap: 18px;
  margin-top: 45px;
}

.rag-auth-benefits > div {
  display: flex;
  align-items: center;
  gap: 13px;
  font-size: 13px;
  color: #d2ddf1;
}

.rag-auth-benefits svg {
  color: #a4b4ff;
}

.rag-auth-copyright {
  color: #8395b0;
  font-size: 11px;
  position: relative;
  z-index: 1;
}

.rag-auth-main {
  display: grid;
  place-items: center;
  padding: 35px;
}

.rag-auth-form-wrap {
  width: 100%;
  max-width: 405px;
}

.rag-auth-mobile-brand {
  display: none;
}

.rag-auth-small-icon {
  background: #edf1ff;
  color: #4b61e8;
  width: 48px;
  height: 48px;
  border-radius: 13px;
  display: grid;
  place-items: center;
  margin-bottom: 24px;
}

.rag-auth-form-wrap h2 {
  font: 800 31px 'Manrope', sans-serif;
  letter-spacing: -1.3px;
  margin: 0 0 9px;
}

.rag-auth-subtitle {
  font-size: 13px;
  color: #8491a5;
  margin: 0 0 31px;
}

.rag-auth-form {
  display: grid;
  gap: 19px;
}

.rag-auth-form label {
  display: grid;
  gap: 9px;
  font-size: 12px;
  font-weight: 800;
}

.rag-auth-form input {
  background: #fff;
  border: 1px solid #dfe5ee;
  border-radius: 10px;
  padding: 14px;
  color: #203047;
}

.rag-auth-form .rag-btn {
  padding: 15px;
  margin-top: 4px;
}

.rag-password-hint {
  margin: -8px 0 0;
  color: #8896aa;
  font-size: 11px;
}

.rag-auth-toggle {
  text-align: center;
  margin-top: 27px;
  color: #8491a5;
  font-size: 12px;
}

.rag-auth-toggle button {
  border: 0;
  background: none;
  color: #4b61e8;
  font-size: 12px;
  font-weight: 800;
  margin-left: 6px;
}

.rag-auth-trust {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  color: #94a0b1;
  margin-top: 48px;
  font-size: 11px;
  text-align: center;
}

/* MAIN LAYOUT */

.rag-app {
  min-height: 100vh;
  display: flex;
}

.rag-sidebar {
  width: 265px;
  min-height: 100vh;
  height: 100vh;
  position: sticky;
  top: 0;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 29px 17px 20px;
  background: #172338;
  color: #fff;
  z-index: 30;
  overflow-y: auto;
}

.rag-sidebar-brand {
  padding: 0 9px 49px;
}

.rag-sidebar-brand strong {
  font-size: 15px;
}

.rag-navigation-label {
  color: #7888a4;
  padding: 0 14px 12px;
  letter-spacing: 1.5px;
  font-size: 10px;
  font-weight: 800;
}

.rag-navigation {
  display: grid;
  gap: 6px;
}

.rag-nav-item {
  width: 100%;
  border: 0;
  border-radius: 10px;
  padding: 14px 15px;
  display: flex;
  align-items: center;
  gap: 14px;
  text-align: left;
  background: transparent;
  color: #aab7cc;
  font-size: 13px;
  font-weight: 700;
  transition: background .15s, color .15s;
}

.rag-nav-item:hover {
  background: #273550;
  color: #fff;
}

.rag-nav-active {
  background: #303e60;
  color: #fff;
  box-shadow: inset 3px 0 0 #8294ff;
}

.rag-active-dot {
  margin-left: auto;
  height: 6px;
  width: 6px;
  background: #a6b4ff;
  border-radius: 50%;
}

.rag-sidebar-bottom {
  margin-top: auto;
  padding-top: 25px;
}

.rag-security-note {
  background: #22334c;
  border: 1px solid #2d415d;
  border-radius: 12px;
  padding: 15px 13px;
  display: flex;
  align-items: center;
  gap: 11px;
  color: #a8b8fc;
}

.rag-security-note strong {
  display: block;
  color: #fff;
  font-size: 12px;
}

.rag-security-note span {
  display: block;
  color: #9eafc7;
  margin-top: 4px;
  font-size: 10px;
}

.rag-user-card {
  margin-top: 22px;
  border-top: 1px solid #2e3b50;
  padding-top: 18px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.rag-avatar,
.rag-top-avatar {
  width: 39px;
  height: 39px;
  border-radius: 11px;
  background: #5069b8;
  color: #fff;
  font-weight: 800;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.rag-user-info {
  flex: 1;
  min-width: 0;
}

.rag-user-info strong {
  display: block;
  font-size: 12px;
}

.rag-user-info span {
  display: block;
  font-size: 10px;
  color: #99a9c2;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  margin-top: 4px;
}

/* CLEARLY VISIBLE SIGN OUT */

.rag-signout-button {
  width: 100%;
  margin-top: 15px;
  padding: 13px 15px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  border: 1px solid #425574;
  border-radius: 10px;
  background: #2b3c58;
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  transition: background .15s ease;
}

.rag-signout-button:hover {
  background: #40577c;
}

.rag-signout-button span {
  flex: 1;
  text-align: left;
}

.rag-header-signout {
  border: 1px solid #e1e6ee;
  border-radius: 9px;
  background: #fff;
  color: #34445d;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  font-size: 12px;
  font-weight: 800;
}

.rag-header-signout:hover {
  color: #bd415a;
  border-color: #f2c7d0;
  background: #fff5f7;
}

.rag-icon-button {
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 9px;
  color: #8493aa;
  display: grid;
  place-items: center;
  background: transparent;
}

.rag-icon-button:hover {
  background: #eef1fa;
  color: #354d79;
}

.rag-main {
  min-width: 0;
  flex: 1;
}

.rag-topbar {
  height: 75px;
  padding: 0 39px;
  background: #fff;
  border-bottom: 1px solid #e7ebf2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
}

.rag-topbar-left,
.rag-topbar-right {
  display: flex;
  align-items: center;
  gap: 13px;
  font-size: 12px;
}

.rag-topbar-left > span:first-child {
  color: #93a0b1;
}

.rag-topbar-left strong {
  font-weight: 800;
}

.rag-divider-slash {
  color: #cbd2dd;
}

.rag-system-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #a6aebc;
  font-size: 11px;
  font-weight: 700;
}

.rag-system-status > span {
  height: 7px;
  width: 7px;
  background: #f0ab36;
  border-radius: 50%;
}

.rag-online {
  color: #168966;
}

.rag-online > span {
  background: #22b284;
}

.rag-top-avatar {
  width: 34px;
  height: 34px;
}

.rag-content {
  padding: 40px 40px 75px;
  max-width: 1600px;
  margin: auto;
}

.rag-page-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 28px;
}

.rag-kicker,
.rag-section-kicker {
  display: block;
  font-size: 10px;
  letter-spacing: 1.5px;
  color: #6278d9;
  font-weight: 800;
  margin-bottom: 9px;
}

.rag-page-heading h1 {
  font: 800 30px 'Manrope', sans-serif;
  letter-spacing: -1.1px;
  margin: 0 0 7px;
}

.rag-page-heading p {
  margin: 0;
  color: #8e9aab;
  font-size: 13px;
}

/* DASHBOARD */

.rag-welcome {
  min-height: 259px;
  border-radius: 17px;
  background: #213657;
  color: #fff;
  padding: 38px 46px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  overflow: hidden;
  margin-bottom: 21px;
}

.rag-welcome-copy {
  position: relative;
  z-index: 1;
  max-width: 560px;
}

.rag-welcome h2 {
  font: 800 33px/1.25 'Manrope', sans-serif;
  letter-spacing: -1.2px;
  margin: 18px 0 10px;
}

.rag-welcome h2 span {
  color: #b6c6ff;
}

.rag-welcome p {
  max-width: 500px;
  font-size: 13px;
  color: #c5d2e2;
  line-height: 1.8;
}

.rag-welcome .rag-btn {
  margin-top: 10px;
}

.rag-welcome-visual {
  height: 210px;
  width: 270px;
  min-width: 250px;
  display: grid;
  place-items: center;
  position: relative;
}

.rag-visual-orbit {
  position: absolute;
  border: 1px solid #ffffff22;
  border-radius: 50%;
}

.rag-orbit-one {
  width: 165px;
  height: 165px;
}

.rag-orbit-two {
  width: 260px;
  height: 260px;
}

.rag-visual-center {
  display: grid;
  place-items: center;
  height: 110px;
  width: 110px;
  border-radius: 28px;
  background: #ffffff12;
  border: 1px solid #ffffff38;
  color: #d4dfff;
}

.rag-stats-grid,
.rag-performance-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 17px;
  margin-bottom: 22px;
}

.rag-stat {
  border: 1px solid #e8edf4;
  background: #fff;
  border-radius: 14px;
  padding: 22px;
  min-width: 0;
  box-shadow: 0 3px 12px #192a4405;
}

.rag-stat-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.rag-stat-top > span {
  font-size: 11px;
  color: #8794a6;
  font-weight: 700;
}

.rag-stat-icon {
  width: 35px;
  height: 35px;
  background: #edf1ff;
  color: #5a6ce8;
  display: grid;
  place-items: center;
  border-radius: 9px;
}

.rag-stat > strong {
  display: block;
  font: 800 29px 'Manrope', sans-serif;
  margin: 12px 0 6px;
  overflow-wrap: anywhere;
}

.rag-stat > small {
  color: #9da8b8;
  font-size: 11px;
}

/* COMMON CARDS */

.rag-two-columns,
.rag-assistant-layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: start;
  gap: 20px;
}

.rag-card {
  background: #fff;
  border: 1px solid #e8edf4;
  border-radius: 15px;
  padding: 27px;
  min-width: 0;
  box-shadow: 0 3px 12px #192a4405;
}

.rag-card-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 23px;
}

.rag-card-heading h2 {
  margin: 0 0 6px;
  font: 800 17px 'Manrope', sans-serif;
  letter-spacing: -.4px;
}

.rag-card-heading p {
  color: #8c98aa;
  font-size: 12px;
  margin: 0;
  line-height: 1.6;
}

.rag-text-link {
  border: 0;
  background: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #5268da;
  font-size: 11px;
  font-weight: 800;
  padding: 5px 0;
  white-space: nowrap;
}

.rag-quick-action {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 13px;
  padding: 17px 2px;
  background: none;
  border: 0;
  border-bottom: 1px solid #edf0f6;
  text-align: left;
  color: #53637c;
}

.rag-quick-action:last-child {
  border-bottom: 0;
}

.rag-quick-action > div:nth-child(2) {
  min-width: 0;
  flex: 1;
}

.rag-quick-action strong {
  display: block;
  color: #25334c;
  font-size: 12px;
}

.rag-quick-action span {
  display: block;
  color: #9aa6b7;
  font-size: 11px;
  margin-top: 6px;
}

.rag-quick-action:hover strong {
  color: #4b61e8;
}

.rag-quick-icon {
  height: 43px;
  width: 43px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  flex-shrink: 0;
}

.rag-blue {
  color: #5268df;
  background: #edf1ff;
}

.rag-purple {
  color: #8858c9;
  background: #f1edfc;
}

.rag-green {
  color: #159c77;
  background: #e5f8f2;
}

.rag-recent-document,
.rag-document-item {
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #edf0f6;
  padding: 15px 0;
}

.rag-recent-document strong {
  font-size: 12px;
  display: block;
  overflow-wrap: anywhere;
}

.rag-recent-document small {
  color: #95a1b4;
  font-size: 11px;
  display: block;
  margin-top: 5px;
}

.rag-document-type {
  background: #fff0ed;
  color: #da6a55;
  border-radius: 10px;
  height: 43px;
  width: 43px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 800;
}

.rag-empty {
  padding: 25px 15px;
  min-height: 186px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.rag-empty-icon {
  height: 55px;
  width: 55px;
  background: #f0f3fb;
  color: #7385be;
  display: grid;
  place-items: center;
  border-radius: 14px;
  margin-bottom: 14px;
}

.rag-empty h3 {
  font-size: 13px;
  margin: 0 0 8px;
}

.rag-empty p {
  margin: 0 0 17px;
  font-size: 11px;
  line-height: 1.7;
  color: #97a2b5;
  max-width: 300px;
}

/* DOCUMENTS */

.rag-document-layout {
  grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr);
}

.rag-dropzone {
  border: 1.5px dashed #ccd6e7;
  background: #fafbfe;
  border-radius: 13px;
  min-height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
  gap: 11px;
  transition: background .15s, border-color .15s;
}

.rag-dragging,
.rag-dropzone:hover {
  background: #f0f4ff;
  border-color: #5874e9;
}

.rag-drop-icon {
  background: #ecf0ff;
  color: #5269e4;
  padding: 12px;
  border-radius: 13px;
  display: grid;
  place-items: center;
}

.rag-dropzone strong {
  font-size: 13px;
  color: #31415c;
  overflow-wrap: anywhere;
}

.rag-dropzone p,
.rag-dropzone small {
  color: #9aa7b9;
  font-size: 11px;
  margin: 0;
}

.rag-dropzone small {
  margin-top: 5px;
}

.rag-selected-file {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 11px;
  border: 1px solid #e6ebf4;
  border-radius: 10px;
  padding: 12px;
  color: #5b6d87;
  font-size: 12px;
}

.rag-selected-file span {
  flex: 1;
  overflow-wrap: anywhere;
}

.rag-selected-file button {
  border: 0;
  background: none;
  color: #8591a6;
}

.rag-upload-submit {
  margin-top: 17px;
  padding: 15px;
}

.rag-upload-tip,
.rag-monitor-note {
  display: flex;
  align-items: center;
  gap: 11px;
  background: #f8fafc;
  color: #8492a8;
  border-radius: 10px;
  padding: 15px;
  font-size: 11px;
  line-height: 1.6;
  margin-top: 23px;
}

.rag-upload-tip svg,
.rag-monitor-note svg {
  color: #5b71d6;
  flex-shrink: 0;
}

.rag-document-list {
  max-height: 560px;
  overflow: auto;
}

.rag-document-info {
  flex: 1;
  min-width: 0;
}

.rag-document-info strong {
  display: block;
  font-size: 12px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.rag-document-info small {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  color: #98a4b5;
}

.rag-delete {
  color: #d65a75;
}

.rag-delete:hover {
  color: #c53655;
  background: #ffedf1;
}

.rag-count-badge {
  border-radius: 8px;
  padding: 7px 11px;
  background: #eef1ff;
  color: #5268de;
  font-size: 12px;
  font-weight: 800;
}

.rag-inline-loading {
  display: flex;
  gap: 11px;
  align-items: center;
  color: #98a3b6;
  font-size: 12px;
}

/* AI ASSISTANT */

.rag-assistant-layout {
  grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr);
}

.rag-question-card,
.rag-answer-card {
  min-height: 390px;
}

.rag-ai-icon {
  padding: 11px;
  background: #eef1ff;
  color: #5268db;
  display: grid;
  place-items: center;
  border-radius: 12px;
}

.rag-info-banner {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  background: #f4f6ff;
  border: 1px solid #e6eaff;
  border-radius: 11px;
  padding: 14px;
  margin-bottom: 19px;
  color: #5c71d2;
}

.rag-info-banner div {
  flex: 1;
}

.rag-info-banner strong {
  color: #35477e;
  font-size: 12px;
}

.rag-info-banner p {
  font-size: 11px;
  color: #7080a1;
  line-height: 1.6;
  margin: 5px 0 8px;
}

.rag-info-banner button {
  border: 0;
  background: none;
  padding: 0;
  display: inline-flex;
  gap: 6px;
  align-items: center;
  font-size: 11px;
  font-weight: 800;
  color: #4b61d4;
}

.rag-field-label {
  display: block;
  font-size: 12px;
  font-weight: 800;
  margin-bottom: 10px;
}

.rag-question-textarea,
.rag-settings-grid input {
  display: block;
  width: 100%;
  border: 1px solid #e0e6ef;
  color: #263751;
  border-radius: 11px;
  padding: 14px;
  outline: none;
  background: #fff;
}

.rag-question-textarea {
  resize: vertical;
  min-height: 135px;
  line-height: 1.7;
  font-size: 13px;
}

.rag-question-textarea:focus,
.rag-settings-grid input:focus {
  border-color: #8293ed;
  box-shadow: 0 0 0 3px #4b61e812;
}

.rag-suggestions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin: 15px 0;
}

.rag-suggestions > span {
  font-size: 11px;
  color: #9aa4b5;
}

.rag-suggestions button {
  padding: 7px 10px;
  background: #f6f8fc;
  border: 1px solid #e9edf4;
  border-radius: 7px;
  color: #64748b;
  font-size: 10px;
}

.rag-suggestions button:hover {
  background: #edf1ff;
  color: #4b61e8;
}

.rag-advanced {
  border-top: 1px solid #edf0f5;
  margin-top: 16px;
  padding-top: 16px;
}

.rag-advanced summary {
  font-size: 12px;
  font-weight: 700;
  color: #687994;
  cursor: pointer;
}

.rag-settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 15px;
}

.rag-settings-grid label {
  display: grid;
  gap: 8px;
  font-size: 11px;
  color: #718099;
  font-weight: 700;
}

.rag-settings-grid input {
  padding: 10px;
}

.rag-ask-button {
  margin-top: 22px;
}

.rag-copy-button {
  border: 1px solid #e5e9f2;
  background: #fff;
  border-radius: 9px;
  padding: 9px 11px;
  font-size: 11px;
  font-weight: 700;
  color: #6b7b92;
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.rag-answer-loading {
  min-height: 250px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
}

.rag-answer-loading strong {
  font-size: 13px;
}

.rag-answer-loading p {
  font-size: 11px;
  color: #91a0b2;
}

.rag-answer-text {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  line-height: 1.85;
  background: #fafbfe;
  border: 1px solid #e9edf4;
  padding: 20px;
  border-radius: 11px;
  font-size: 13px;
  color: #33435d;
}

.rag-answer-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  border-top: 1px solid #edf0f5;
  padding-top: 16px;
  margin-top: 19px;
  color: #8491a3;
  font-size: 11px;
}

.rag-answer-meta span {
  display: flex;
  align-items: center;
  gap: 7px;
}

.rag-answer-meta svg {
  color: #19a27b;
}

.rag-evidence-card {
  grid-column: 1 / -1;
}

.rag-source-list h3 {
  font-size: 12px;
  margin: 0 0 14px;
}

.rag-source-item {
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #edf0f5;
  padding: 12px 0;
}

.rag-source-label {
  min-width: 39px;
  height: 39px;
  border-radius: 9px;
  background: #eef1ff;
  color: #5268dd;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 800;
}

.rag-source-item strong {
  display: block;
  font-size: 12px;
}

.rag-source-item small {
  display: block;
  margin-top: 5px;
  color: #97a3b5;
  font-size: 11px;
}

.rag-chunks-details {
  margin-top: 20px;
}

.rag-chunks-details summary {
  font-size: 12px;
  font-weight: 800;
  color: #5268dd;
  cursor: pointer;
}

.rag-chunks-list {
  display: grid;
  gap: 12px;
  margin-top: 17px;
}

.rag-chunk {
  background: #fafbfe;
  border: 1px solid #e8edf4;
  border-radius: 11px;
  padding: 16px;
}

.rag-chunk-header {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.rag-chunk-header strong {
  font-size: 12px;
}

.rag-chunk-header span {
  font-size: 11px;
  color: #5268dd;
  font-weight: 800;
}

.rag-chunk small {
  display: block;
  color: #96a3b4;
  font-size: 10px;
  margin-top: 7px;
}

.rag-chunk p {
  color: #4a5a70;
  font-size: 12px;
  line-height: 1.8;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.rag-performance-grid {
  margin-bottom: 0;
}

.rag-performance-grid .rag-stat {
  background: #fbfcfe;
}

/* RESPONSIVE */

.rag-menu-toggle,
.rag-mobile-overlay {
  display: none;
}

@media (max-width: 1200px) {
  .rag-stats-grid,
  .rag-performance-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .rag-two-columns,
  .rag-assistant-layout {
    grid-template-columns: 1fr;
  }

  .rag-welcome-visual {
    min-width: 170px;
    width: 190px;
  }

  .rag-auth-side {
    padding-left: 35px;
    padding-right: 35px;
  }
}

@media (max-width: 850px) {
  .rag-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    transform: translateX(-100%);
    transition: transform .25s ease;
  }

  .rag-sidebar-open {
    transform: translateX(0);
  }

  .rag-mobile-overlay {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 20;
    background: #0d1b30a8;
    border: 0;
  }

  .rag-menu-toggle {
    display: grid;
    place-items: center;
    border: 0;
    background: none;
    padding: 5px;
    color: #53647e;
  }

  .rag-topbar {
    padding: 0 22px;
    height: 66px;
  }

  .rag-content {
    padding: 28px 20px 55px;
  }

  .rag-welcome {
    padding: 30px;
  }

  .rag-welcome-visual {
    display: none;
  }

  .rag-auth-page {
    grid-template-columns: 1fr;
  }

  .rag-auth-side {
    display: none;
  }

  .rag-auth-main {
    min-height: 100vh;
  }

  .rag-auth-mobile-brand {
    display: flex;
    gap: 11px;
    align-items: center;
    margin-bottom: 45px;
  }

  .rag-auth-mobile-brand strong {
    font-size: 15px;
  }
}

@media (max-width: 520px) {
  .rag-page-heading {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .rag-page-heading h1 {
    font-size: 26px;
  }

  .rag-welcome h2 {
    font-size: 27px;
  }

  .rag-welcome {
    padding: 27px;
  }

  .rag-card {
    padding: 19px;
  }

  .rag-stat {
    padding: 16px;
  }

  .rag-stat > strong {
    font-size: 23px;
  }

  .rag-stats-grid,
  .rag-performance-grid {
    gap: 10px;
  }

  .rag-stat-top > span {
    font-size: 10px;
  }

  .rag-topbar-right .rag-system-status {
    display: none;
  }

  .rag-settings-grid {
    grid-template-columns: 1fr;
  }

  .rag-auth-main {
    padding: 24px;
  }

  .rag-header-signout {
    padding: 9px;
  }

  .rag-header-signout span {
    display: none;
  }
}
`

export default App
