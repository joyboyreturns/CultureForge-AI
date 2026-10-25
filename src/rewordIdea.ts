/** The most a business idea may hold; the backend rejects anything longer. */
export const IDEA_MAX_LENGTH = 160
const IDEA_MIN_LENGTH = 3

export type RewordCheck = { ok: true; idea: string } | { ok: false; message: string }

const squash = (text: string) => text.replace(/\s+/g, ' ').trim()

/**
 * Whether a reworded idea can be run, and why not when it cannot. Running the
 * same words again would spend a request to get the same answer, so an
 * unchanged idea is refused with a reason rather than sent.
 */
export function checkReword(current: string, next: string): RewordCheck {
  const idea = squash(next)
  if (idea.length < IDEA_MIN_LENGTH) return { ok: false, message: 'Describe the business in a few words, starting with the kind of business.' }
  if (idea.length > IDEA_MAX_LENGTH) return { ok: false, message: `Keep the idea to ${IDEA_MAX_LENGTH} characters or fewer; it is ${idea.length}.` }
  if (idea.toLowerCase() === squash(current).toLowerCase()) return { ok: false, message: 'That is the same wording. Change it, for example by naming the kind of business first, to get a different reading.' }
  return { ok: true, idea }
}
