/**
 * Accessibility smoke tests for the UI primitives. axe runs in jsdom (which
 * can't compute real colour contrast - that's covered by the hand-verified
 * token palette in docs/design/design-system.md), so these catch structural
 * issues: roles, labels, name/role/value. Scoped to the WCAG A/AA tags so
 * page-level best-practice rules (landmarks, single-h1) don't flag isolated
 * components.
 */
import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { axe } from 'vitest-axe'
import type { ReactElement } from 'react'
import { Alert } from './Alert'
import { Badge } from './Badge'
import { Button } from './Button'
import { Card } from './Card'
import { Checkbox } from './Checkbox'
import { RadioGroup } from './RadioGroup'
import { Select } from './Select'
import { TextField } from './TextField'

const WCAG_AA = {
  runOnly: { type: 'tag' as const, values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
}

async function expectNoViolations(ui: ReactElement) {
  const { container } = render(ui)
  expect(await axe(container, WCAG_AA)).toHaveNoViolations()
}

describe('UI primitive accessibility', () => {
  it('Button', async () => {
    await expectNoViolations(<Button>Save</Button>)
  })

  it('TextField (with hint + error)', async () => {
    await expectNoViolations(
      <TextField label="Email" type="email" hint="Work address" error="Required" />
    )
  })

  it('Select', async () => {
    await expectNoViolations(
      <Select
        label="Role"
        options={[
          { value: 'student', label: 'student' },
          { value: 'coach', label: 'coach' },
        ]}
      />
    )
  })

  it('Checkbox', async () => {
    await expectNoViolations(<Checkbox label="I solved this correctly" />)
  })

  it('RadioGroup', async () => {
    await expectNoViolations(
      <RadioGroup
        legend="Answer choices"
        name="q"
        value="A"
        options={[
          { value: 'A', label: 'Alpha' },
          { value: 'B', label: 'Beta' },
        ]}
        onChange={() => {}}
      />
    )
  })

  it('Alert', async () => {
    await expectNoViolations(<Alert severity="warning">Heads up</Alert>)
  })

  it('Badge', async () => {
    await expectNoViolations(<Badge tone="success">Correct</Badge>)
  })

  it('Card', async () => {
    await expectNoViolations(<Card>Some content</Card>)
  })
})
