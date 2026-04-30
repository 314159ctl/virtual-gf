import { ref } from 'vue'

export interface FilePreview {
  name: string
  size: number
  type: string
}

const ALLOWED_EXTENSIONS = ['.txt', '.md', '.pdf', '.docx']
const MAX_SIZE = 10 * 1024 * 1024 // 10MB

export function useFileUpload() {
  const selectedFiles = ref<File[]>([])
  const filePreviews = ref<FilePreview[]>([])
  const fileInput = ref<HTMLInputElement | null>(null)
  const error = ref('')

  function selectFiles() {
    fileInput.value?.click()
  }

  function onFilesSelected(event: Event) {
    const input = event.target as HTMLInputElement
    const files = Array.from(input.files || [])
    if (files.length === 0) return

    error.value = ''

    for (const file of files) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase()
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        error.value = `不支持的文件类型: ${file.name} (仅支持 ${ALLOWED_EXTENSIONS.join(', ')})`
        return
      }
      if (file.size > MAX_SIZE) {
        error.value = `${file.name} 超过大小限制 (10MB)`
        return
      }
    }

    selectedFiles.value.push(...files)
    filePreviews.value.push(
      ...files.map(f => ({
        name: f.name,
        size: f.size,
        type: f.type || f.name.split('.').pop()?.toLowerCase() || 'unknown',
      }))
    )

    input.value = ''
  }

  function removeFile(index: number) {
    selectedFiles.value.splice(index, 1)
    filePreviews.value.splice(index, 1)
  }

  function clearFiles() {
    selectedFiles.value = []
    filePreviews.value = []
    error.value = ''
  }

  return {
    selectedFiles, filePreviews, fileInput, error,
    selectFiles, onFilesSelected, removeFile, clearFiles,
  }
}
