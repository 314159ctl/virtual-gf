import { ref } from 'vue'

export function useImageUpload(maxSizeMB = 5) {
  const selectedImage = ref<string | null>(null)
  const previewUrl = ref<string | null>(null)
  const fileInput = ref<HTMLInputElement | null>(null)

  function selectFile() {
    fileInput.value?.click()
  }

  function onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement
    const file = input.files?.[0]
    if (!file) return
    processFile(file)
    input.value = ''
  }

  function onPaste(event: ClipboardEvent) {
    const items = event.clipboardData?.items
    if (!items) return
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile()
        if (file) processFile(file)
        break
      }
    }
  }

  function processFile(file: File) {
    if (file.size > maxSizeMB * 1024 * 1024) {
      alert(`图片大小不能超过 ${maxSizeMB}MB`)
      return
    }
    previewUrl.value = URL.createObjectURL(file)
    const reader = new FileReader()
    reader.onload = () => {
      selectedImage.value = reader.result as string
    }
    reader.readAsDataURL(file)
  }

  function clearImage() {
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value)
    }
    selectedImage.value = null
    previewUrl.value = null
  }

  return { selectedImage, previewUrl, fileInput, selectFile, onFileSelected, onPaste, clearImage }
}
