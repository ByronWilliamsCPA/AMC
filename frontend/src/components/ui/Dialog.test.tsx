import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { Dialog } from './Dialog'

describe('Dialog', () => {
  it('renders nothing when closed', () => {
    render(
      <Dialog open={false} onClose={vi.fn()} title="Navigator">
        <button type="button">Inside</button>
      </Dialog>
    )
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('is a labelled modal and focuses the first focusable on open', () => {
    render(
      <Dialog open onClose={vi.fn()} title="Navigator">
        <button type="button">Inside</button>
      </Dialog>
    )
    const dialog = screen.getByRole('dialog', { name: 'Navigator' })
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(screen.getByRole('button', { name: 'Inside' })).toHaveFocus()
  })

  it('closes on Escape', async () => {
    const onClose = vi.fn()
    render(
      <Dialog open onClose={onClose} title="Navigator">
        <button type="button">Inside</button>
      </Dialog>
    )
    await userEvent.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('restores focus to the trigger when it closes', async () => {
    function Harness() {
      const [open, setOpen] = useState(false)
      return (
        <>
          <button type="button" onClick={() => setOpen(true)}>
            Open
          </button>
          <Dialog open={open} onClose={() => setOpen(false)} title="Navigator">
            <button type="button">Inside</button>
          </Dialog>
        </>
      )
    }
    render(<Harness />)
    const trigger = screen.getByRole('button', { name: 'Open' })
    trigger.focus()
    await userEvent.click(trigger)
    expect(screen.getByRole('button', { name: 'Inside' })).toHaveFocus()
    await userEvent.keyboard('{Escape}')
    expect(trigger).toHaveFocus()
  })
})
