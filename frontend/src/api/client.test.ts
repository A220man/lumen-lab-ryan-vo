import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api } from '../api/client'

// Mock fetch
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('GET requests return parsed JSON', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ items: [{ id: '1', name: 'Test' }], total: 1 }),
    })

    const result = await api.get('/api/v1/test')
    expect(result).toEqual({ items: [{ id: '1', name: 'Test' }], total: 1 })
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/test'),
      expect.objectContaining({ method: 'GET', credentials: 'include' })
    )
  })

  it('POST requests send JSON body', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => ({ id: '2', name: 'Created' }),
    })

    const result = await api.post('/api/v1/test', { name: 'Created' })
    expect(result).toEqual({ id: '2', name: 'Created' })
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/test'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ name: 'Created' }),
        credentials: 'include',
      })
    )
  })

  it('throws on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Not found' }),
    })

    await expect(api.get('/api/v1/test')).rejects.toThrow('Not found')
  })
})