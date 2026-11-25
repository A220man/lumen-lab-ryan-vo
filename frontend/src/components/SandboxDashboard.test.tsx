import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SandboxDashboard } from './SandboxDashboard'

// Mock fetch
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('SandboxDashboard', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders loading state initially', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ items: [] }),
    })

    const { unmount } = render(
      <SandboxDashboard />
    )

    expect(screen.getByText(/no sandboxes yet/i)).toBeInTheDocument()
    unmount()
  })

  it('fetches and displays sandboxes', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        items: [
          {
            id: 'sbox-001',
            name: 'arm64-sandbox',
            image: 'ghcr.io/lumen-lab/arm64-image:latest',
            arch: 'arm64',
            status: 'running',
            created_at: '2024-01-15T10:30:00Z',
          },
          {
            id: 'sbox-002',
            name: 'x86-sandbox',
            image: 'ghcr.io/lumen-lab/x86-image:latest',
            arch: 'amd64',
            status: 'stopped',
            created_at: '2024-01-14T14:20:00Z',
          },
        ],
      }),
    })

    const { unmount } = render(<SandboxDashboard />)

    await new Promise(resolve => setTimeout(resolve, 0))
    expect(screen.getByText(/arm64-sandbox/i)).toBeInTheDocument()
    expect(screen.getByText(/x86-sandbox/i)).toBeInTheDocument()
    expect(screen.getByText(/arm64/i)).toBeInTheDocument()
    expect(screen.getByText(/amd64/i)).toBeInTheDocument()
    expect(screen.getByText(/running/i)).toBeInTheDocument()
    expect(screen.getByText(/stopped/i)).toBeInTheDocument()
    unmount()
  })

  it('shows error state on failed fetch', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Internal server error' }),
    })

    const { unmount } = render(
      <SandboxDashboard />
    )

    await new Promise(resolve => setTimeout(resolve, 0))
    expect(screen.getByText(/Failed to load sandboxes/i)).toBeInTheDocument()
    expect(screen.getByText(/Internal server error/i)).toBeInTheDocument()
    unmount()
  })

  it('renders empty state when no sandboxes', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ items: [] }),
    })

    const { unmount } = render(
      <SandboxDashboard />
    )

    expect(screen.getByText(/no sandboxes yet/i)).toBeInTheDocument()
    unmount()
  })

  it('deletes a sandbox using fireEvent', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
    })

    const { unmount } = render(
      <SandboxDashboard />
    )

    await new Promise(resolve => setTimeout(resolve, 0))
    const deleteBtn = screen.getByRole('button', { name: /delete/i })
    fireEvent.click(deleteBtn)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/sandboxes/sbox-001'),
      expect.objectContaining({ method: 'DELETE' })
    )
    unmount()
  })
})
