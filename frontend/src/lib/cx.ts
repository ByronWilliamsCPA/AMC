/** Join truthy class names. A 3-line replacement for clsx/classnames that keeps
 * the dependency surface (and the security review) minimal. */
export function cx(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(' ')
}
