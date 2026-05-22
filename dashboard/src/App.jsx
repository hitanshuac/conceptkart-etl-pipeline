import { useState, useEffect } from 'react'
import { supabase } from './supabaseClient'
import { Activity, ExternalLink, Clock, TrendingDown, AlertCircle, ShoppingBag } from 'lucide-react'

function App() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isSetup, setIsSetup] = useState(false)

  useEffect(() => {
    // Check if Supabase URL and Key are provided
    if (!import.meta.env.VITE_SUPABASE_URL || !import.meta.env.VITE_SUPABASE_ANON_KEY) {
      setLoading(false)
      setIsSetup(false)
      return
    }
    
    setIsSetup(true)
    fetchProducts()
  }, [])

  async function fetchProducts() {
    try {
      setLoading(true)
      // Fetch from the unified view to get the latest scraped prices and names
      const { data, error } = await supabase
        .from('dashboard_view')
        .select('*')
        .order('id', { ascending: false })

      if (error) throw error
      
      // If table doesn't exist or is empty, we handle it gracefully
      setProducts(data || [])
    } catch (error) {
      console.error('Error fetching products:', error)
      setError(error.message)
    } finally {
      setLoading(false)
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

      {error && (
        <div className="setup-banner" style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger-color)', borderColor: 'rgba(239, 68, 68, 0.2)'}}>
          <AlertCircle size={20} />
          <div>
            <strong>Error connecting to Supabase:</strong> {error}. Ensure you have created the `tracked_products` table.
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Syncing with data warehouse...</p>
        </div>
      ) : products.length === 0 && isSetup && !error ? (
        <div className="empty-state">
          <ShoppingBag size={48} strokeWidth={1} />
          <h2>No Products Tracked</h2>
          <p>Add products to your Supabase database to start monitoring prices.</p>
        </div>
      ) : (
        <div className="dashboard-grid">
          {products.map((product) => {
            const isTargetHit = product.price_current <= product.target_price;
            
            return (
              <div key={product.id} className="card">
                <div className="card-header">
                  <h3 className="card-title">{product.product_name || 'Unknown Product'}</h3>
                  <span className="vendor-tag">{product.vendor_name || 'ConceptKart'}</span>
                </div>
                
                <div className="price-container">
                  <span className="current-price">
                    {formatCurrency(product.price_current || 0)}
                  </span>
                  {product.target_price && (
                    <span className="target-price">
                      {formatCurrency(product.target_price)}
                    </span>
                  )}
                </div>
                
                {isTargetHit && product.target_price && (
                  <div className="price-drop">
                    <TrendingDown size={16} />
                    Target Hit! (Below {formatCurrency(product.target_price)})
                  </div>
                )}
                
                <div className="card-footer">
                  <div className="last-updated">
                    <Clock size={14} />
                    {formatDate(product.scraped_at_utc || product.updated_at)}
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
      )}
    </div>
  )
}

export default App
