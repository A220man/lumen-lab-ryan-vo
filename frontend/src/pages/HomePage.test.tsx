import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { HomePage } from './HomePage'

describe('HomePage', () => {
  const renderWithRouter = (component: React.ReactElement) => {
    return render(<BrowserRouter>{component}</BrowserRouter>)
  }

  it('renders dashboard title and description', () => {
    renderWithRouter(<HomePage />)

    expect(screen.getByText(/Scale computer-use 2\.0 with open-source drivers/)).toBeInTheDocument()
  })

  it('renders three feature cards', () => {
    renderWithRouter(<HomePage />)

    expect(screen.getByText('Benchmarks')).toBeInTheDocument()
    expect(screen.getByText('Sandboxes')).toBeInTheDocument()
    expect(screen.getByText('Hyprland')).toBeInTheDocument()
  })

  it('links navigate to correct paths', () => {
    renderWithRouter(<HomePage />)

    const benchmarksLink = screen.getByText('Benchmarks').closest('a')
    const sandboxesLink = screen.getByText('Sandboxes').closest('a')
    const hyprlandLink = screen.getByText('Hyprland').closest('a')

    expect(benchmarksLink).toHaveAttribute('href', '/benchmarks')
    expect(sandboxesLink).toHaveAttribute('href', '/sandboxes')
    expect(hyprlandLink).toHaveAttribute('href', '/hyprland')
  })
})