import React, { useEffect, useMemo, useState } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Asset {
  id: string
  filename: string
  status: string
  hls_path?: string
}

export const App: React.FC = () => {
  const [assets, setAssets] = useState<Asset[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [processing, setProcessing] = useState<string | null>(null)

  const fetchAssets = async () => {
    const res = await fetch(`${API}/assets`)
    const data = await res.json()
    setAssets(data)
  }

  useEffect(() => {
    fetchAssets()
  }, [])

  const onUpload = async () => {
    if (!file) return
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API}/upload`, { method: 'POST', body: form })
    const asset = await res.json()
    setProcessing(asset.id)
    await fetch(`${API}/process/${asset.id}`, { method: 'POST' })
    // Poll until ready
    const poll = setInterval(async () => {
      const r = await fetch(`${API}/assets/${asset.id}`)
      const a = await r.json()
      if (a.status === 'ready' || a.status === 'failed') {
        clearInterval(poll)
        setProcessing(null)
        fetchAssets()
      }
    }, 2000)
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: 20, fontFamily: 'sans-serif' }}>
      <h1>Video AI Manager</h1>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input type="file" accept="video/*" onChange={e => setFile(e.target.files?.[0] ?? null)} />
        <button onClick={onUpload} disabled={!file || !!processing}>Upload & Process</button>
        {processing && <span>Processing {processing}...</span>}
      </div>

      <h2 style={{ marginTop: 24 }}>Assets</h2>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {assets.map(a => (
          <li key={a.id} style={{ marginBottom: 16, padding: 12, border: '1px solid #ddd', borderRadius: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <strong>{a.filename}</strong>
              <span>Status: {a.status}</span>
            </div>
            {a.status === 'ready' && (
              <details style={{ marginTop: 8 }}>
                <summary>Preview & Downloads</summary>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 8 }}>
                  <div>
                    <video controls width={420} src={`${API}/stream/${a.id}/master.m3u8`}>
                      Your browser does not support the video tag.
                    </video>
                  </div>
                  <div>
                    <a href={`${API}/exports/${a.id}/edl`} target="_blank">Download EDL</a>
                    <br/>
                    <a href={`${API}/exports/${a.id}/fcpxml`} target="_blank">Download FCPXML</a>
                  </div>
                </div>
              </details>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
