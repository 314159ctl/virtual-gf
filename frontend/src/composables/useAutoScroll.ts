import { ref, type Ref, watch, nextTick } from 'vue'

export function useAutoScroll(containerRef: Ref<HTMLElement | null>) {
  const isUserScrolledUp = ref(false)

  function scrollToBottom(smooth = true) {
    const el = containerRef.value
    if (!el) return
    el.scrollTo({
      top: el.scrollHeight,
      behavior: smooth ? 'smooth' : 'instant',
    })
  }

  function checkScrollPosition() {
    const el = containerRef.value
    if (!el) return
    const threshold = 100
    isUserScrolledUp.value = el.scrollHeight - el.scrollTop - el.clientHeight > threshold
  }

  function onNewContent() {
    nextTick(() => {
      if (!isUserScrolledUp.value) {
        scrollToBottom()
      }
    })
  }

  return { scrollToBottom, onNewContent, isUserScrolledUp, checkScrollPosition }
}
