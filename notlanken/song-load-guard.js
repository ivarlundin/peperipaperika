/**
 * Monotonic token for in-flight song loads. Stale async work must not mutate player state.
 */
export function createSongLoadGuard() {
  let seq = 0;
  return {
    bump() {
      seq += 1;
      return seq;
    },
    isActive(token) {
      return token === seq;
    },
    current() {
      return seq;
    },
  };
}
