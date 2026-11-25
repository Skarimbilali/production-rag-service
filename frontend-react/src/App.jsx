
import { useCallback, useEffect, useState } from 'react'
import './App.css'

const DEFAULT_TOP_K = 5
const DEFAULT_THRESHOLD = 0

async function apiRequest(endpoint, options = {}) {
  let response

  try {
    response = await fetch(endpoint, options)
  } catch {
    throw new Error(
      'Cannot connect to FastAPI. Make sure the backend is running on port 8000.'
    )
  }

  let result = null

  if (response.status !== 204) {
    const contentType = response.headers.get('content-type') || ''

    result = contentType.includes('application/json')
      ? await response.json()
      : await response.text()
  }

  if (!response.ok) {
    let errorMessage = `Request failed (${response.status}).`

    if (result && typeof result === 'object') {
      if (typeof result.detail === 'string') {
        errorMessage = result.detail
      } else if (Array.isArray(result.detail)) {
        errorMessage = result.detail
          .map((item) => item.msg || 'Validation error')
          .join('; ')
      }
    }

    throw new Error(errorMessage)
  }

  return result
}

function formatSimilarity(value) {
  const score = Number(value)

  if (!Number.isFinite(score)) {
    return 'N/A'
  }

  return `${(score * 100).toFixed(2)}%`
}

function formatDuration(value) {
  const duration = Number(value)

  return Number.isFinite(duration)
    ? `${duration.toFixed(2)} ms`
    : 'N/A'
}

function formatUptime(value) {
  const seconds = Number(value)

  if (!Number.isFinite(seconds)) {
    return 'N/A'
  }

  if (seconds < 60) {
    return `${Math.floor(seconds)} sec`
  }

  if (seconds < 3600) {
    return `${Math.floor(seconds / 60)} min`
  }

  return `${Math.floor(seconds / 3600)} hr ${Math.floor(
    (seconds % 3600) / 60
  )} min`
}

function Message({ message, isError = false }) {
  if (!message) {
    return null
  }

  return (
    <p
      className={`message ${
        isError ? 'message-error' : 'message-success'
      }`}
      role={isError ? 'alert' : 'status'}
    >
      {message}
    </p>
  )
}

function StatCard({ label, value, description }) {
  return (
    <article className="stat-card">
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{value}</strong>
      {description && (
        <span className="stat-description">{description}</span>
      )}
    </article>
  )
}

function App() {
  const [apiOnline, setApiOnline] = useState(null)

  const [documents, setDocuments] = useState([])
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [documentMessage, setDocumentMessage] = useState('')
  const [documentError, setDocumentError] = useState(false)

  const [question, setQuestion] = useState('')
  const [topK, setTopK] = useState(DEFAULT_TOP_K)
  const [threshold, setThreshold] = useState(DEFAULT_THRESHOLD)
  const [asking, setAsking] = useState(false)
  const [questionMessage, setQuestionMessage] = useState('')
  const [questionError, setQuestionError] = useState(false)

  const [answer, setAnswer] = useState('')
  const [citations, setCitations] = useState([])
  const [retrievedChunks, setRetrievedChunks] = useState([])
  const [retrievedCount, setRetrievedCount] = useState(0)
  const [hasAsked, setHasAsked] = useState(false)

  const [metrics, setMetrics] = useState(null)
  const [metricsLoading, setMetricsLoading] = useState(false)
  const [metricsError, setMetricsError] = useState('')

  const checkApiHealth = useCallback(async () => {
    try {
      await apiRequest('/health')
      setApiOnline(true)
    } catch {
      setApiOnline(false)
    }
  }, [])

  const loadDocuments = useCallback(async () => {
    setDocumentsLoading(true)

    try {
      const result = await apiRequest('/documents')

      const items = Array.isArray(result)
        ? result
        : Array.isArray(result?.documents)
          ? result.documents
          : []

      setDocuments(items)
    } catch (error) {
      setDocumentMessage(error.message)
      setDocumentError(true)
    } finally {
      setDocumentsLoading(false)
    }
  }, [])

  const loadMetrics = useCallback(async () => {
    setMetricsLoading(true)
    setMetricsError('')

    try {
      const result = await apiRequest('/metrics')
      setMetrics(result)
    } catch (error) {
      setMetricsError(error.message)
    } finally {
      setMetricsLoading(false)
    }
  }, [])

  useEffect(() => {
    checkApiHealth()
    loadDocuments()
    loadMetrics()
  }, [checkApiHealth, loadDocuments, loadMetrics])

  async function handleUpload(event) {
    event.preventDefault()

    if (!selectedFile) {
      setDocumentMessage('Please select a PDF or DOCX file.')
      setDocumentError(true)
      return
    }

    const extension = selectedFile.name
      .split('.')
      .pop()
      .toLowerCase()

    if (!['pdf', 'docx'].includes(extension)) {
      setDocumentMessage('Only PDF and DOCX files are supported.')
      setDocumentError(true)
      return
    }

    const formData = new FormData()
    formData.append('file', selectedFile)

    setUploading(true)
    setDocumentMessage('Uploading and processing document...')
    setDocumentError(false)

    try {
      const result = await apiRequest('/documents/upload', {
        method: 'POST',
        body: formData,
      })

      setDocumentMessage(
        `${result?.filename || selectedFile.name} uploaded successfully.`
      )
      setDocumentError(false)
      setSelectedFile(null)

      const fileInput = document.getElementById('documentFile')

      if (fileInput) {
        fileInput.value = ''
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

  async function handleDelete(documentId, filename) {
    const confirmed = window.confirm(
      `Delete "${filename}" and all its stored chunks?`
    )

    if (!confirmed) {
      return
    }

    setDeletingId(documentId)
    setDocumentMessage('')

    try {
      await apiRequest(
        `/documents/${encodeURIComponent(documentId)}`,
        { method: 'DELETE' }
      )

      setDocumentMessage(`"${filename}" deleted successfully.`)
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

    const trimmedQuestion = question.trim()

    if (!trimmedQuestion) {
      setQuestionMessage('Please enter a question.')
      setQuestionError(true)
      return
    }

    setAsking(true)
    setHasAsked(true)
    setAnswer('')
    setCitations([])
    setRetrievedChunks([])
    setRetrievedCount(0)
    setQuestionMessage('Retrieving relevant document chunks...')
    setQuestionError(false)

    try {
      const result = await apiRequest('/questions/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: trimmedQuestion,
          top_k: Number(topK),
          threshold: Number(threshold),
        }),
      })

      const chunks = Array.isArray(result?.retrieved_chunks)
        ? result.retrieved_chunks
        : []

      setAnswer(result?.answer || 'No answer returned.')
      setCitations(
        Array.isArray(result?.citations) ? result.citations : []
      )
      setRetrievedChunks(chunks)
      setRetrievedCount(result?.retrieved_count ?? chunks.length)

      setQuestionMessage('Question processed successfully.')
      setQuestionError(false)

      await loadMetrics()
    } catch (error) {
      setAnswer('Unable to generate an answer.')
      setQuestionMessage(error.message)
      setQuestionError(true)
    } finally {
      setAsking(false)
    }
  }

  const requestMetrics = metrics?.requests || {}
  const ragMetrics = metrics?.rag_performance || {}

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">R</div>
          <div>
            <strong>Production RAG</strong>
            <span>Knowledge Intelligence</span>
          </div>
        </div>

        <nav className="sidebar-nav" aria-label="Dashboard navigation">
          <a href="#overview" className="nav-item">
            Overview
          </a>
          <a href="#documents" className="nav-item">
            Documents
          </a>
          <a href="#assistant" className="nav-item">
            Ask AI
          </a>
          <a href="#sources" className="nav-item">
            Sources &amp; Evidence
          </a>
          <a href="#monitoring" className="nav-item">
            Monitoring
          </a>
        </nav>

        <div className="sidebar-footer">
          <span className="sidebar-footer-label">Backend status</span>
          <div
            className={`api-status ${
              apiOnline === true
                ? 'online'
                : apiOnline === false
                  ? 'offline'
                  : 'checking'
            }`}
          >
            <span className="status-dot" />
            {apiOnline === true
              ? 'API Online'
              : apiOnline === false
                ? 'API Offline'
                : 'Checking API...'}
          </div>
          <button
            className="text-button"
            type="button"
            onClick={checkApiHealth}
          >
            Check connection
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="page-header" id="overview">
          <div>
            <p className="eyebrow">AI KNOWLEDGE WORKSPACE</p>
            <h1>RAG Dashboard</h1>
            <p className="page-subtitle">
              Manage documents, ask grounded questions and inspect
              the evidence behind every answer.
            </p>
          </div>

          <div className="header-badge">
            React + FastAPI
          </div>
        </header>

        <section className="overview-grid" aria-label="Overview">
          <StatCard
            label="Indexed Documents"
            value={documents.length}
            description="Available knowledge sources"
          />
          <StatCard
            label="Indexed Chunks"
            value={documents.reduce(
              (total, item) =>
                total + Number(item.chunk_count ?? 0),
              0
            )}
            description="Across uploaded documents"
          />
          <StatCard
            label="Retrieved Chunks"
            value={retrievedCount}
            description="Most recent question"
          />
          <StatCard
            label="API Requests"
            value={requestMetrics.total ?? '—'}
            description="Since backend startup"
          />
        </section>

        <div className="workspace-grid">
          <section className="panel" id="documents">
            <div className="section-heading">
              <div>
                <p className="eyebrow">KNOWLEDGE BASE</p>
                <h2>Documents</h2>
                <p>Upload PDF or DOCX files for retrieval.</p>
              </div>
              <button
                className="secondary-button"
                type="button"
                onClick={loadDocuments}
                disabled={documentsLoading}
              >
                {documentsLoading ? 'Loading...' : 'Refresh'}
              </button>
            </div>

            <form
              className="upload-form"
              onSubmit={handleUpload}
            >
              <label htmlFor="documentFile" className="upload-area">
                <span className="upload-icon">↑</span>
                <strong>
                  {selectedFile
                    ? selectedFile.name
                    : 'Choose a document'}
                </strong>
                <span>PDF or DOCX format</span>
              </label>

              <input
                id="documentFile"
                type="file"
                accept=".pdf,.docx"
                onChange={(event) =>
                  setSelectedFile(event.target.files?.[0] || null)
                }
              />

              <button
                className="primary-button"
                type="submit"
                disabled={uploading}
              >
                {uploading
                  ? 'Uploading & Processing...'
                  : 'Upload Document'}
              </button>
            </form>

            <Message
              message={documentMessage}
              isError={documentError}
            />

            <div className="document-list">
              <h3>Uploaded Documents</h3>

              {documentsLoading && (
                <p className="empty-state">Loading documents...</p>
              )}

              {!documentsLoading && documents.length === 0 && (
                <p className="empty-state">
                  No documents uploaded yet.
                </p>
              )}

              {!documentsLoading &&
                documents.map((item) => {
                  const documentId =
                    item.document_id || item.id

                  const filename =
                    item.filename ||
                    item.name ||
                    'Unknown document'

                  const chunkCount =
                    item.chunk_count ??
                    item.chunks_count ??
                    item.total_chunks

                  return (
                    <article
                      className="document-item"
                      key={documentId || filename}
                    >
                      <div className="document-icon">
                        {filename.toLowerCase().endsWith('.pdf')
                          ? 'PDF'
                          : 'DOC'}
                      </div>

                      <div className="document-details">
                        <strong title={filename}>{filename}</strong>
                        <span>
                          {chunkCount !== undefined
                            ? `${chunkCount} chunks indexed`
                            : 'Indexed document'}
                        </span>
                      </div>

                      {documentId && (
                        <button
                          className="danger-button"
                          type="button"
                          disabled={deletingId === documentId}
                          onClick={() =>
                            handleDelete(documentId, filename)
                          }
                        >
                          {deletingId === documentId
                            ? 'Deleting...'
                            : 'Delete'}
                        </button>
                      )}
                    </article>
                  )
                })}
            </div>
          </section>

          <section className="panel assistant-panel" id="assistant">
            <div className="section-heading">
              <div>
                <p className="eyebrow">GROUNDED ANSWERS</p>
                <h2>Ask Your Documents</h2>
                <p>
                  Ask in English or Roman Urdu.
                </p>
              </div>
              <span className="feature-tag">RAG Enabled</span>
            </div>

            <form className="question-form" onSubmit={handleAsk}>
              <label htmlFor="questionInput">
                Your question
              </label>

              <textarea
                id="questionInput"
                value={question}
                onChange={(event) =>
                  setQuestion(event.target.value)
                }
                placeholder="Example: How many annual leave days do permanent employees get?"
                rows={5}
              />

              <div className="settings-grid">
                <div className="field">
                  <label htmlFor="topK">Top K</label>
                  <input
                    id="topK"
                    type="number"
                    min="1"
                    max="20"
                    step="1"
                    value={topK}
                    onChange={(event) =>
                      setTopK(event.target.value)
                    }
                    required
                  />
                </div>

                <div className="field">
                  <label htmlFor="threshold">
                    Similarity Threshold
                  </label>
                  <input
                    id="threshold"
                    type="number"
                    min="0"
                    max="1"
                    step="0.05"
                    value={threshold}
                    onChange={(event) =>
                      setThreshold(event.target.value)
                    }
                    required
                  />
                </div>
              </div>

              <button
                className="primary-button"
                type="submit"
                disabled={asking}
              >
                {asking ? 'Generating Answer...' : 'Ask Question'}
              </button>
            </form>

            <Message
              message={questionMessage}
              isError={questionError}
            />

            <div className="answer-section">
              <div className="answer-heading">
                <h3>AI Answer</h3>
                {hasAsked && (
                  <span className="feature-tag">
                    {asking ? 'Processing' : 'Latest Result'}
                  </span>
                )}
              </div>

              <div className="answer-box" aria-live="polite">
                {asking
                  ? 'Retrieving evidence and generating an answer...'
                  : answer ||
                    'Your document-grounded answer will appear here.'}
              </div>
            </div>
          </section>
        </div>

        <section className="panel evidence-panel" id="sources">
          <div className="section-heading">
            <div>
              <p className="eyebrow">TRANSPARENT RETRIEVAL</p>
              <h2>Sources &amp; Evidence</h2>
              <p>
                Inspect citations and the actual document chunks
                retrieved for your question.
              </p>
            </div>

            <span className="count-badge">
              {retrievedCount} chunks
            </span>
          </div>

          <div className="evidence-grid">
            <div className="citations-section">
              <h3>Source Citations</h3>

              {citations.length === 0 ? (
                <p className="empty-state">
                  No citations available.
                </p>
              ) : (
                <div className="citation-list">
                  {citations.map((citation, index) => {
                    const metadata = citation.metadata || {}

                    return (
                      <article
                        className="citation-item"
                        key={`${citation.chunk_id || 'source'}-${index}`}
                      >
                        <span className="source-id">
                          {citation.source_id || `S${index + 1}`}
                        </span>

                        <div className="citation-info">
                          <strong>
                            {metadata.filename || 'Unknown file'}
                          </strong>
                          <span>
                            Page: {metadata.page ?? 'N/A'}
                          </span>
                          <small>
                            Chunk ID: {citation.chunk_id || 'N/A'}
                          </small>
                        </div>
                      </article>
                    )
                  })}
                </div>
              )}
            </div>

            <div className="retrieval-section">
              <h3>Retrieved Document Chunks</h3>

              {retrievedChunks.length === 0 ? (
                <p className="empty-state">
                  No retrieved chunks to display.
                </p>
              ) : (
                <div className="chunk-list">
                  {retrievedChunks.map((chunk, index) => {
                    const metadata = chunk.metadata || {}

                    return (
                      <article
                        className="chunk-item"
                        key={`${chunk.id || 'chunk'}-${index}`}
                      >
                        <div className="chunk-header">
                          <strong>Chunk {index + 1}</strong>

                          <span className="score">
                            Similarity:{' '}
                            {formatSimilarity(
                              chunk.similarity_score
                            )}
                          </span>
                        </div>

                        <div className="chunk-meta">
                          <span>
                            {metadata.filename || 'Unknown file'}
                          </span>
                          <span>
                            Page {metadata.page ?? 'N/A'}
                          </span>
                        </div>

                        <p className="chunk-text">
                          {chunk.text || 'No text available.'}
                        </p>
                      </article>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="panel monitoring-panel" id="monitoring">
          <div className="section-heading">
            <div>
              <p className="eyebrow">OBSERVABILITY</p>
              <h2>API &amp; RAG Monitoring</h2>
              <p>
                Backend metrics since the last server restart.
              </p>
            </div>

            <button
              className="secondary-button"
              type="button"
              onClick={loadMetrics}
              disabled={metricsLoading}
            >
              {metricsLoading ? 'Refreshing...' : 'Refresh Metrics'}
            </button>
          </div>

          {metricsError && (
            <Message message={metricsError} isError />
          )}

          <div className="monitoring-grid">
            <StatCard
              label="Backend Uptime"
              value={formatUptime(metrics?.uptime_seconds)}
            />

            <StatCard
              label="Total Requests"
              value={requestMetrics.total ?? '—'}
            />

            <StatCard
              label="Successful Requests"
              value={requestMetrics.successful ?? '—'}
            />

            <StatCard
              label="Failed Requests"
              value={requestMetrics.failed ?? '—'}
            />

            <StatCard
              label="Average API Duration"
              value={formatDuration(
                requestMetrics.average_duration_ms
              )}
            />

            <StatCard
              label="Retrieval Calls"
              value={ragMetrics.retrieval_calls ?? '—'}
            />

            <StatCard
              label="Average Retrieval Time"
              value={formatDuration(
                ragMetrics.average_retrieval_ms
              )}
            />

            <StatCard
              label="Average Generation Time"
              value={formatDuration(
                ragMetrics.average_generation_ms
              )}
            />
          </div>

          <p className="monitoring-note">
            Metrics are maintained in memory and reset when the
            FastAPI server restarts.
          </p>
        </section>

        <footer className="app-footer">
          Production RAG Service · React + Vite · FastAPI
        </footer>
      </main>
    </div>
  )
}

export default App
