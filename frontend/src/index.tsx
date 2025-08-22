import React from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'
import * as serviceWorker from './serviceWorker'
import { contentContext, newContentStore } from './stores/ContentStore'
import { serverInfoContext, newServerInfoStore } from './stores/ServerInfoStore'
import { mediaContext, deletedMediaContext, newMediaStore } from './stores/MediaStore'

const container = document.getElementById('root')
if (container) {
  const root = createRoot(container)

  // Create store instances
  const contentStore = newContentStore()
  const serverInfoStore = newServerInfoStore()
  const mediaStore = newMediaStore()
  const deletedMediaStore = newMediaStore() // Use the same function for both

  root.render(
    <contentContext.Provider value={contentStore}>
      <serverInfoContext.Provider value={serverInfoStore}>
        <mediaContext.Provider value={mediaStore}>
          <deletedMediaContext.Provider value={deletedMediaStore}>
            <App />
          </deletedMediaContext.Provider>
        </mediaContext.Provider>
      </serverInfoContext.Provider>
    </contentContext.Provider>,
  )
}

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister()
