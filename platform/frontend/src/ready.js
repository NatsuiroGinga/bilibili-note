export function markPageReady(delay = 650) {
  window.setTimeout(() => {
    window.__PAGE_READY__ = true
  }, delay)
}

export function resetPageReady() {
  window.__PAGE_READY__ = false
}
