/**
 * Bridge vitest-axe's matcher types into vitest 3's `Assertion` interface.
 * vitest-axe@0.1.0 only augments the legacy `Vi.Assertion` global namespace,
 * which vitest 3 no longer uses for `expect()` — so we re-augment here (the
 * same pattern @testing-library/jest-dom uses for vitest).
 */
import 'vitest'
import type { AxeMatchers } from 'vitest-axe/matchers'

declare module 'vitest' {
  /* Empty-extends + the generic param are required for declaration merging
     with vitest's own `Assertion<T>`; the lint rules don't apply here. */
  /* eslint-disable @typescript-eslint/no-empty-object-type, @typescript-eslint/no-unused-vars, @typescript-eslint/no-explicit-any */
  interface Assertion<T = any> extends AxeMatchers {}
  interface AsymmetricMatchersContaining extends AxeMatchers {}
  /* eslint-enable @typescript-eslint/no-empty-object-type, @typescript-eslint/no-unused-vars, @typescript-eslint/no-explicit-any */
}
