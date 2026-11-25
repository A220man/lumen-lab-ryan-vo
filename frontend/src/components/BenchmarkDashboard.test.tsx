import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BenchmarkDashboard } from './BenchmarkDashboard'

// Mock fetch
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('BenchmarkDashboard', () => {
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
      <BenchmarkDashboard />
    )

    expect(screen.getByText(/no benchmarks yet/i)).toBeInTheDocument()
    unmount()
  })

  it('fetches and displays benchmarks', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        items: [
          { id: 'bench-001', name: 'latency-test', status: 'running', created_at: '2024-01-15T10:30:00Z', max_latency_ms: 150 },
          { id: 'bench-002', name: 'click-test', status: 'completed', created_at: '2024-01-14T14:20:00Z', max_latency_ms: 85 },
        ],
      }),
    })

    const { unmount } = render(<BenchmarkDashboard />)

    await new Promise(resolve => setTimeout(resolve, 0))
    expect(screen.getByText(/latency-test/i)).toBeInTheDocument()
    expect(screen.getByText(/click-test/i)).toBeInTheDocument()
    expect(screen.getByText(/running/i)).toBeInTheDocument()
    expect(screen.getByText(/completed/i)).toBeInTheDocument()
    unmount()
  })

  it('shows error state on failed fetch', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Internal server error' }),
    })

    const { unmount } = render(
      <BenchmarkDashboard />
    )

    await new Promise(resolve => setTimeout(resolve, 0))
    expect(screen.getByText(/Failed to load benchmarks/i)).toBeInTheDocument()
    expect(screen.getByText(/Internal server error/i)).toBeInTheDocument()
    unmount()
  })

  it('renders empty state when no benchmarks', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ items: [] }),
    })

    const { unmount } = render(
      <BenchmarkDashboard />
    )

    expect(screen.getByText(/no benchmarks yet/i)).toBeInTheDocument()
    unmount()
  })

  it('cancels a running benchmark using fireEvent', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ id: 'bench-001', name: 'latency-test', status: 'cancelled' }),
    })

    const { unmount } = render(
      <BenchmarkDashboard />
    )

    await new Promise(resolve => setTimeout(resolve, 0))
    const cancelBtn = screen.getByRole('button', { name: /cancel/i })
    fireEvent.click(cancelBtn)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/benchmarks/bench-001/cancel'),
      expect.objectContaining({ method: 'POST' })
    )
    unmount()
  })
})
