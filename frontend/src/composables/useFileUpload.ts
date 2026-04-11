import { ref, computed } from 'vue'

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX_SIZE_MB = 20

export type GuidedPhotoType =
  | 'face_front'
  | 'profile_left'
  | 'profile_right'
  | 'body_front'
  | 'body_side'
  | 'three_quarter'

export interface UploadFile {
  id: string
  file: File
  preview: string
  type: string
  uploading: boolean
  error: string | null
}

export interface GuidedSlot {
  type: GuidedPhotoType
  label: string
  description: string
  hint: string
  file: UploadFile | null
}

export const GUIDED_SLOT_DEFINITIONS: Omit<GuidedSlot, 'file'>[] = [
  {
    type: 'face_front',
    label: 'Face — Front',
    description: 'Close-up face, looking directly at the camera',
    hint: 'Eyes forward · neutral expression · good lighting',
  },
  {
    type: 'profile_left',
    label: 'Left Profile',
    description: 'Turn 90° to your left — full side of face visible',
    hint: 'Ear fully visible · chin level · no tilt',
  },
  {
    type: 'profile_right',
    label: 'Right Profile',
    description: 'Turn 90° to your right — full side of face visible',
    hint: 'Ear fully visible · chin level · no tilt',
  },
  {
    type: 'body_front',
    label: 'Full Body — Front',
    description: 'Stand straight, face the camera — head to toe',
    hint: 'Arms slightly away from body · feet together',
  },
  {
    type: 'body_side',
    label: 'Full Body — Side',
    description: 'Turn sideways — full body visible from head to toe',
    hint: 'Arms relaxed · stand straight · full body in frame',
  },
  {
    type: 'three_quarter',
    label: '¾ Angle',
    description: 'Turn 45° toward the camera — natural angle',
    hint: 'Most natural pose · slight shoulder turn',
  },
]

export function validateImageFile(file: File): string | null {
  if (!ACCEPTED_TYPES.includes(file.type)) return 'Only JPEG, PNG, or WebP accepted'
  if (file.size > MAX_SIZE_MB * 1024 * 1024) return `Max ${MAX_SIZE_MB}MB per image`
  return null
}

// ── Guided slot-based upload (for onboarding) ─────────────────────────────────
export function useGuidedUpload() {
  const slots = ref<GuidedSlot[]>(
    GUIDED_SLOT_DEFINITIONS.map((def) => ({ ...def, file: null }))
  )

  function setSlotFile(type: GuidedPhotoType, file: File) {
    const slot = slots.value.find((s) => s.type === type)
    if (!slot) return
    if (slot.file) URL.revokeObjectURL(slot.file.preview)
    const error = validateImageFile(file)
    slot.file = {
      id: crypto.randomUUID(),
      file,
      preview: URL.createObjectURL(file),
      type,
      uploading: false,
      error,
    }
  }

  function clearSlot(type: GuidedPhotoType) {
    const slot = slots.value.find((s) => s.type === type)
    if (!slot) return
    if (slot.file) URL.revokeObjectURL(slot.file.preview)
    slot.file = null
  }

  const filledCount = computed(() => slots.value.filter((s) => s.file && !s.file.error).length)
  const allSlotsFilled = computed(() => filledCount.value === GUIDED_SLOT_DEFINITIONS.length)

  return { slots, setSlotFile, clearSlot, filledCount, allSlotsFilled }
}

// ── Free-form upload (kept for other views) ───────────────────────────────────
export function useFileUpload() {
  const files = ref<UploadFile[]>([])
  const isDragging = ref(false)

  function addFile(file: File, type: string = 'general'): UploadFile | null {
    const error = validateImageFile(file)
    const entry: UploadFile = {
      id: crypto.randomUUID(),
      file,
      preview: URL.createObjectURL(file),
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
    if (event.dataTransfer?.files) addFiles(event.dataTransfer.files)
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault()
    isDragging.value = true
  }

  function handleDragLeave() {
    isDragging.value = false
  }

  return { files, isDragging, addFile, addFiles, removeFile, handleDrop, handleDragOver, handleDragLeave }
}
