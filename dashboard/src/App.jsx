import { useState, useEffect } from 'react'
import { supabase } from './supabaseClient'
import { Activity, ExternalLink, Clock, TrendingDown, AlertCircle, ShoppingBag, ShieldAlert } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'

function App() {
  const [products, setProducts] = useState([])
  const [history, setHistory] = useState({})
  const [errors, setErrors] = useState([])
  const [loading, setLoading] = useState(true)
  const [dbError, setDbError] = useState(null)
  const [isSetup, setIsSetup] = useState(false)
  const [newUrl, setNewUrl] = useState('')
  const [newTarget, setNewTarget] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    // Check if Supabase URL and Key are provided
    if (!import.meta.env.VITE_SUPABASE_URL || !import.meta.env.VITE_SUPABASE_ANON_KEY) {
      setLoading(false)
      setIsSetup(false)
      return
    }
    
    setIsSetup(true)
    fetchDashboardData()
  }, [])

  async function fetchDashboardData() {
    try {
      setLoading(true)
      
      // 1. Fetch latest products view
      const { data: viewData, error: viewError } = await supabase
        .from('dashboard_view')
        .select('*')
        .order('id', { ascending: false })

      if (viewError) throw viewError
      setProducts(viewData || [])

      // 2. Fetch historical prices for the charts
      const { data: priceData, error: priceError } = await supabase
        .from('raw_daily_prices')
        .select('*')
        .order('scraped_at_utc', { ascending: true })

      if (!priceError && priceData) {
        // Group history by tracked_product_id
        const historyMap = {}
        priceData.forEach(row => {
          if (!historyMap[row.tracked_product_id]) {
            historyMap[row.tracked_product_id] = []
          }
          historyMap[row.tracked_product_id].push({
            date: format(new Date(row.scraped_at_utc), 'MMM dd HH:mm'),
            price: row.price_current
          })
        })
        setHistory(historyMap)
      }

      // 3. Fetch Parquet DLQ Errors from Backend API
      try {
        const res = await fetch('/api/errors')
        if (res.ok) {
          const dlqData = await res.json()
          if (dlqData.errors) setErrors(dlqData.errors)
        }
      } catch (e) {
        console.log("Could not fetch DLQ errors, backend might not be running on same port.")
      }

    } catch (error) {
      console.error('Error fetching dashboard data:', error)
      setDbError(error.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleAddProduct(e) {
    e.preventDefault()
    if (!newUrl || !newTarget) return
    
    try {
      setIsSubmitting(true)
      const { error } = await supabase
        .from('tracked_products')
        .insert([{ url: newUrl, target_price: parseInt(newTarget, 10) }])
        
      if (error) throw error
      
      setNewUrl('')
      setNewTarget('')
      fetchDashboardData() // Refresh everything
    } catch (err) {
      console.error('Error adding product:', err)
      alert(`Failed to add product: ${err.message}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount)
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Never updated'
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    }).format(date)
  }

  const formatErrorMsg = (msg) => {
    if (!msg) return 'Unknown error';
    try {
      // Python dicts use single quotes, convert to valid JSON
      const jsonStr = msg.replace(/'/g, '"');
      const obj = JSON.parse(jsonStr);
      if (obj.details) return obj.details;
      if (obj.message) return obj.message;
      return msg;
    } catch (e) {
      return msg; // Fallback to raw string if it's not JSON
    }
  }

  return (
    <div className="app-container">
      <header>
        <h1>
          <Activity size={28} color="var(--accent-color)" />
          ConceptKart ETL Dashboard
        </h1>
        <div className="status-badge">
          <div className="status-dot"></div>
          Pipeline Active
        </div>
      </header>

      {!isSetup && (
        <div className="setup-banner">
          <AlertCircle size={20} />
          <div>
            <strong>Missing Supabase Configuration:</strong> Please add your VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to a .env file in the dashboard directory.
          </div>
        </div>
      )}

      {dbError && (
        <div className="setup-banner" style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger-color)', borderColor: 'rgba(239, 68, 68, 0.2)'}}>
          <AlertCircle size={20} />
          <div>
            <strong>Error connecting to Supabase:</strong> {dbError}. Ensure you have created the `tracked_products` table.
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Syncing with data warehouse...</p>
        </div>
      ) : products.length === 0 && isSetup && !dbError ? (
        <div className="empty-state">
          <ShoppingBag size={48} strokeWidth={1} />
          <h2>No Products Tracked</h2>
          <p>Add products to your Supabase database to start monitoring prices.</p>
        </div>
      ) : (
        <>
          <form className="add-product-form" onSubmit={handleAddProduct}>
            <div className="form-group">
              <input 
                type="url" 
                placeholder="Paste ConceptKart URL here..." 
                value={newUrl} 
                onChange={(e) => setNewUrl(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <input 
                type="number" 
                placeholder="Target Price (Rs.)" 
                value={newTarget} 
                onChange={(e) => setNewTarget(e.target.value)}
                required
                min="1"
              />
            </div>
            <button type="submit" className="submit-btn" disabled={isSubmitting}>
              {isSubmitting ? 'Adding...' : 'Track Product'}
            </button>
          </form>

          <div className="dashboard-grid">
          {products.map((product) => {
            const hasBeenScraped = product.price_current && product.price_current > 0;
            const isTargetHit = hasBeenScraped && product.price_current <= product.target_price;
            const productHistory = history[product.id] || [];
            
            return (
              <div key={product.id} className="card">
                <div className="card-header">
                  <h3 className="card-title">
                    {hasBeenScraped ? product.product_name : 'Pending Initial Scrape...'}
                  </h3>
                  <span className="vendor-tag">{product.vendor_name || 'ConceptKart'}</span>
                </div>
                
                <div className="price-container">
                  <span className="current-price">
                    {hasBeenScraped ? formatCurrency(product.price_current) : 'Pending'}
                  </span>
                  {product.target_price && (
                    <span className="target-price">
                       (Target: {formatCurrency(product.target_price)})
                    </span>
                  )}
                </div>
                
                {isTargetHit && product.target_price && (
                  <div className="price-drop">
                    <TrendingDown size={16} />
                    Target Hit! (Below {formatCurrency(product.target_price)})
                  </div>
                )}

                {productHistory.length > 0 && (
                  <div style={{ width: '100%', height: 120, marginTop: '1rem' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={productHistory}>
                        <XAxis dataKey="date" hide />
                        <YAxis domain={['auto', 'auto']} hide />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff' }}
                          itemStyle={{ color: '#60a5fa' }}
                        />
                        <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4, fill: '#3b82f6' }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
                
                <div className="card-footer" style={{ marginTop: productHistory.length > 0 ? '1rem' : 'auto' }}>
                  <div className="last-updated">
                    <Clock size={14} />
                    {hasBeenScraped ? formatDate(product.scraped_at_utc) : 'Never updated'}
                  </div>
                  <a 
                    href={product.url || '#'} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="action-btn"
                  >
                    View Store <ExternalLink size={14} />
                  </a>
                </div>
              </div>
            )
          })}
          </div>

          {errors.length > 0 && (
            <div className="error-panel">
              <div className="error-panel-header">
                <ShieldAlert size={20} color="var(--danger-color)" />
                <h3>Extraction Error Log (DLQ)</h3>
              </div>
              <div className="error-list">
                {errors.map((err, idx) => (
                  <div key={idx} className="error-item">
                    <div className="error-meta">
                      <span className="error-time">{formatDate(err.timestamp_utc)}</span>
                      <span className="error-tier">Tier: {err.extraction_tier}</span>
                    </div>
                    <div className="error-url" title={err.source_url}>{err.source_url}</div>
                    <div className="error-msg"><strong>{err.error_type}:</strong> {formatErrorMsg(err.error_message)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default App
