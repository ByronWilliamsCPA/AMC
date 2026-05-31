/**
 * Renders one problem and its answer choices as an accessible radiogroup.
 *
 * Image-mode problems show the scanned image; latex-mode problems render the
 * body and each choice's HTML with KaTeX. Choice HTML comes from our own
 * backend (not user input) and is rendered via the KaTeX-aware {@link Math}
 * where it is LaTeX; plain choice labels (A–E) are always shown.
 */
import { Tex } from '@/components/Tex'
import type { ProblemRead } from '@/client'

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

  return (
    <div className="question">
      <h2 className="question__number">Problem {problem.number}</h2>

      <div className="question__body">
        {isImage && problem.image_path ? (
          <img
            src={problem.image_path}
            alt={`Problem ${problem.number}`}
            className="question__image"
          />
        ) : (
          <Tex tex={problem.body_latex ?? ''} display />
        )}
      </div>

      <fieldset
        className="choices"
        role="radiogroup"
        aria-label={`Answer choices for problem ${problem.number}`}
        disabled={disabled}
      >
        {choices.map((choice) => {
          const isSelected = selected === choice.letter
          return (
            <label key={choice.letter} className="choice">
              <input
                type="radio"
                name={`problem-${problem.number}`}
                value={choice.letter}
                checked={isSelected}
                onChange={() => onSelect(choice.letter)}
                disabled={disabled}
              />
              <span className="choice__letter">{choice.letter}</span>
              {!isImage && choice.html && (
                <span className="choice__body">
                  <Tex tex={stripDelimiters(choice.html)} />
                </span>
              )}
            </label>
          )
        })}
      </fieldset>

      {selected !== null && !disabled && (
        <button type="button" className="link-button" onClick={onClear}>
          Clear answer
        </button>
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
