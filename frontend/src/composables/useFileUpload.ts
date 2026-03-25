import { ref } from 'vue'

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX_SIZE_MB = 20

export interface UploadFile {
  id: string
  file: File
  preview: string
  type: 'front' | 'side' | 'full_body' | 'general'
  uploading: boolean
  error: string | null
}

export function useFileUpload() {
  const files = ref<UploadFile[]>([])
  const isDragging = ref(false)

  function validate(file: File): string | null {
    if (!ACCEPTED_TYPES.includes(file.type)) return 'Only JPEG, PNG, or WebP images are accepted'
    if (file.size > MAX_SIZE_MB * 1024 * 1024) return `Image must be under ${MAX_SIZE_MB}MB`
    return null
  }

  function addFile(file: File, type: UploadFile['type'] = 'general'): UploadFile | null {
    const error = validate(file)
    const preview = URL.createObjectURL(file)
    const entry: UploadFile = {
      id: crypto.randomUUID(),
      file,
      preview,
      type,
      uploading: false,
      error,
    }
    files.value.push(entry)
    return error ? null : entry
  }

  function addFiles(fileList: FileList | File[]) {
    Array.from(fileList).forEach((f) => addFile(f))
  }

  function removeFile(id: string) {
    const f = files.value.find((x) => x.id === id)
    if (f) URL.revokeObjectURL(f.preview)
    files.value = files.value.filter((x) => x.id !== id)
  }

  function handleDrop(event: DragEvent) {
    isDragging.value = false
    if (event.dataTransfer?.files) {
      addFiles(event.dataTransfer.files)
    }
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault()
    isDragging.value = true
  }

  function handleDragLeave() {
    isDragging.value = false
  }

  return {
    files,
    isDragging,
    addFile,
    addFiles,
    removeFile,
    handleDrop,
    handleDragOver,
    handleDragLeave,
  }
}
