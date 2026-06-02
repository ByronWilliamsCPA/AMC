import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { RadioGroup, type RadioOption } from './RadioGroup'

const OPTIONS: RadioOption[] = [
  { value: 'A', label: 'Alpha' },
  { value: 'B', label: 'Beta' },
  { value: 'C', label: 'Gamma' },
]

describe('RadioGroup', () => {
  it('exposes a labelled radiogroup with the options as radios', () => {
    render(
      <RadioGroup
        legend="Answer choices"
        name="q"
        value={null}
        options={OPTIONS}
        onChange={vi.fn()}
      />
    )
    expect(screen.getByRole('radiogroup', { name: 'Answer choices' })).toBeInTheDocument()
    expect(screen.getAllByRole('radio')).toHaveLength(3)
  })

  it('selects with a click and reflects the checked value', async () => {
    const onChange = vi.fn()
    render(
      <RadioGroup
        legend="Answer choices"
        name="q"
        value="B"
        options={OPTIONS}
        onChange={onChange}
      />
    )
    expect(screen.getByRole('radio', { name: 'Beta' })).toBeChecked()

    await userEvent.click(screen.getByRole('radio', { name: 'Gamma' }))
    expect(onChange).toHaveBeenCalledWith('C')
  })

  it('moves the selection with arrow keys (native radiogroup semantics)', async () => {
    const onChange = vi.fn()
    render(
      <RadioGroup
        legend="Answer choices"
        name="q"
        value="A"
        options={OPTIONS}
        onChange={onChange}
      />
    )
    screen.getByRole('radio', { name: 'Alpha' }).focus()
    await userEvent.keyboard('{ArrowDown}')
    expect(onChange).toHaveBeenCalledWith('B')
  })

  it('freezes when disabled (no selection change)', async () => {
    const onChange = vi.fn()
    render(
      <RadioGroup
        legend="Answer choices"
        name="q"
        value={null}
        options={OPTIONS}
        disabled
        onChange={onChange}
      />
    )
    await userEvent.click(screen.getByRole('radio', { name: 'Alpha' }))
    expect(onChange).not.toHaveBeenCalled()
  })
})
