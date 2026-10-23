/** Images imported from the repository's assets folder resolve to their bundled URL. */
declare module '*.webp' {
  const url: string
  export default url
}
