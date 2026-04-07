import { openDB, type IDBPDatabase } from 'idb'

const DB_NAME = 'liseli-offline'
const DB_VERSION = 1

interface OfflineAction {
  id?: number
  type: 'translation' | 'vote' | 'comment'
  payload: Record<string, unknown>
  created_at: string
}

let dbPromise: Promise<IDBPDatabase> | null = null

function getDB() {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('pending-actions')) {
          db.createObjectStore('pending-actions', {
            keyPath: 'id',
            autoIncrement: true,
          })
        }
        if (!db.objectStoreNames.contains('cached-sentences')) {
          db.createObjectStore('cached-sentences', { keyPath: 'id' })
        }
      },
    })
  }
  return dbPromise
}

export async function queueAction(action: Omit<OfflineAction, 'id' | 'created_at'>) {
  const db = await getDB()
  await db.add('pending-actions', {
    ...action,
    created_at: new Date().toISOString(),
  })
}

export async function getPendingActions(): Promise<OfflineAction[]> {
  const db = await getDB()
  return db.getAll('pending-actions')
}

export async function clearAction(id: number) {
  const db = await getDB()
  await db.delete('pending-actions', id)
}

export async function syncPendingActions(
  syncFn: (action: OfflineAction) => Promise<boolean>
) {
  const actions = await getPendingActions()
  for (const action of actions) {
    try {
      const success = await syncFn(action)
      if (success && action.id) {
        await clearAction(action.id)
      }
    } catch {
      // will retry next sync
      break
    }
  }
}

export async function cacheSentences(sentences: Array<{ id: string } & Record<string, unknown>>) {
  const db = await getDB()
  const tx = db.transaction('cached-sentences', 'readwrite')
  for (const sentence of sentences) {
    await tx.store.put(sentence)
  }
  await tx.done
}

export async function getCachedSentences() {
  const db = await getDB()
  return db.getAll('cached-sentences')
}
