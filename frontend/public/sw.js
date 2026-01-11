// Service Worker for CBSC Dashboard PWA
const CACHE_NAME = 'cbsc-dashboard-v1.0.0';
const STATIC_CACHE = 'cbsc-static-v1.0.0';
const DYNAMIC_CACHE = 'cbsc-dynamic-v1.0.0';

// Assets to cache immediately on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  // CSS
  '/assets/index.css',
  // JS
  '/assets/index.js',
  // Icons
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  // Core fonts
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
];

// API endpoints that support offline caching
const CACHE_API_PATTERNS = [
  /^\/api\/strategies/,
  /^\/api\/users\/profile/,
  /^\/api\/dashboard\/stats/,
];

// Network timeout threshold
const NETWORK_TIMEOUT = 3000;

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');

  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Network helper with timeout
function networkWithTimeout(request) {
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      reject(new Error('Network timeout'));
    }, NETWORK_TIMEOUT);

    fetch(request).then((response) => {
      clearTimeout(timeoutId);
      resolve(response);
    }).catch((error) => {
      clearTimeout(timeoutId);
      reject(error);
    });
  });
}

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip external resources except fonts
  if (url.origin !== location.origin && !url.href.includes('fonts.googleapis.com')) {
    return;
  }

  // Strategy for static assets
  if (STATIC_ASSETS.some(asset => url.pathname === asset)) {
    event.respondWith(
      caches.match(request)
        .then((response) => {
          return response || networkWithTimeout(request);
        })
    );
    return;
  }

  // Strategy for API calls
  if (url.pathname.startsWith('/api/')) {
    // Check if this API supports offline caching
    const supportsOffline = CACHE_API_PATTERNS.some(pattern => pattern.test(url.pathname));

    if (supportsOffline) {
      event.respondWith(
        networkWithTimeout(request)
          .then((response) => {
            // Cache successful responses
            if (response.ok) {
              const responseClone = response.clone();
              caches.open(DYNAMIC_CACHE).then((cache) => {
                cache.put(request, responseClone);
              });
            }
            return response;
          })
          .catch(() => {
            // Return cached response if network fails
            return caches.match(request);
          })
      );
    } else {
      // Network first for non-cacheable APIs
      event.respondWith(
        networkWithTimeout(request)
          .catch(() => {
            // Return a generic offline response
            return new Response(
              JSON.stringify({
                success: false,
                error: {
                  code: 'NETWORK_ERROR',
                  message: '網絡連接失敗，請檢查您的網絡設置',
                },
              }),
              {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
              }
            );
          })
      );
    }
    return;
  }

  // Strategy for navigation requests (HTML pages)
  if (request.mode === 'navigate') {
    event.respondWith(
      networkWithTimeout(request)
        .catch(() => {
          // Return cached index.html for offline navigation
          return caches.match('/');
        })
    );
    return;
  }

  // Default strategy: Cache first with network fallback
  event.respondWith(
    caches.match(request)
      .then((response) => {
        if (response) {
          return response;
        }
        return networkWithTimeout(request)
          .then((response) => {
            // Cache successful responses for future use
            if (response.ok) {
              const responseClone = response.clone();
              caches.open(DYNAMIC_CACHE).then((cache) => {
                cache.put(request, responseClone);
              });
            }
            return response;
          });
      })
  );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(
      // Sync offline actions
      syncOfflineActions()
    );
  }
});

// Sync offline actions
async function syncOfflineActions() {
  // Get all offline actions from IndexedDB
  const offlineActions = await getOfflineActions();

  for (const action of offlineActions) {
    try {
      // Retry the action
      await fetch(action.url, {
        method: action.method,
        headers: action.headers,
        body: action.body,
      });

      // Remove successfully synced action
      await removeOfflineAction(action.id);
    } catch (error) {
      console.error('[SW] Failed to sync action:', error);
    }
  }
}

// Push notification handler
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : '您有新的通知',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: '查看詳情',
        icon: '/icons/checkmark.png'
      },
      {
        action: 'close',
        title: '關閉',
        icon: '/icons/xmark.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('CBSC量化系統', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'explore') {
    // Open the app to relevant page
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// IndexedDB helpers for offline actions
async function getOfflineActions() {
  // Implementation depends on your IndexedDB setup
  return [];
}

async function removeOfflineAction(id) {
  // Implementation depends on your IndexedDB setup
  return true;
}

// Cache cleanup
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'CACHE_UPDATED') {
    // Clear dynamic cache when app updates
    caches.delete(DYNAMIC_CACHE);
  }
});