/**
 * Renders one problem and its answer choices.
 *
 * Image-mode problems show the scanned image; latex-mode problems render the
 * body and each choice's HTML with KaTeX. The A–E choices are delegated to the
 * reusable {@link RadioGroup} primitive; this component owns only the problem
 * presentation and the KaTeX-typeset choice labels. Choice HTML comes from our
 * own backend (not user input).
 */
import { Tex } from '@/components/Tex'
import { Button, RadioGroup, type RadioOption } from '@/components/ui'
import type { ProblemRead } from '@/client'
import styles from './Question.module.css'

const CHOICE_LETTERS = ['A', 'B', 'C', 'D', 'E'] as const

export interface QuestionProps {
  problem: ProblemRead
  /** The currently selected choice letter, or null. */
  selected: string | null
  disabled?: boolean
  onSelect: (choice: string) => void
  onClear: () => void
}

interface Choice {
  letter: string
  html: string
}

function readChoices(problem: ProblemRead): Choice[] {
  const raw = problem.choices ?? []
  return raw.map((choice, index) => ({
    letter: String(choice.L ?? CHOICE_LETTERS[index] ?? ''),
    html: String(choice.html ?? ''),
  }))
}

export function Question({
  problem,
  selected,
  disabled = false,
  onSelect,
  onClear,
}: QuestionProps) {
  const choices = readChoices(problem)
  const isImage = problem.render_mode === 'image'

  const options: RadioOption[] = choices.map((choice) => ({
    value: choice.letter,
    label: (
      <>
        <span className={styles.letter}>{choice.letter}</span>
        {!isImage && choice.html && (
          <span className={styles.choiceBody}>
            <Tex tex={stripDelimiters(choice.html)} />
          </span>
        )}
      </>
    ),
  }))

  return (
    <div className={styles.question}>
      <h2 className={styles.number}>Problem {problem.number}</h2>

      <div className={styles.body}>
        {isImage && problem.image_path ? (
          <img
            src={problem.image_path}
            alt={`Problem ${problem.number}`}
            className={styles.image}
          />
        ) : (
          <Tex tex={problem.body_latex ?? ''} display />
        )}
      </div>

      <RadioGroup
        legend={`Answer choices for problem ${problem.number}`}
        name={`problem-${problem.number}`}
        value={selected}
        options={options}
        disabled={disabled}
        onChange={onSelect}
      />

      {selected !== null && !disabled && (
        <Button type="button" variant="subtle" className={styles.clear} onClick={onClear}>
          Clear answer
        </Button>
      )}
    </div>
  )
}

/** Strip surrounding `\( ... \)` / `$...$` so KaTeX gets bare LaTeX. */
function stripDelimiters(html: string): string {
  return html
    .trim()
    .replace(/^\\\(/, '')
    .replace(/\\\)$/, '')
    .replace(/^\$/, '')
    .replace(/\$$/, '')
    .trim()
}
