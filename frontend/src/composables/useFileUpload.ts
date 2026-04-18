import { ref, computed } from 'vue'

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX_SIZE_MB = 20

/**
 * Photo slot types — ORDER IS MANDATORY.
 * Backend pipeline expects images in this exact sequence:
 *   [0] face_closeup   → Primary identity anchor (face close-up FIRST)
 *   [1] body_front     → Full body proportions anchor
 *   [2] left_30        → Left 30° three-quarter
 *   [3] right_30       → Right 30° three-quarter
 *   [4] walking        → Walking / casual pose
 */
export type GuidedPhotoType =
  | 'face_closeup'
  | 'body_front'
  | 'left_30'
  | 'right_30'
  | 'walking'

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
  tips: string[]
  file: UploadFile | null
}

export const GUIDED_SLOT_DEFINITIONS: Omit<GuidedSlot, 'file'>[] = [
  {
    type: 'face_closeup',
    label: 'Close-up Face',
    description: 'Face only, eyes forward, neutral expression',
    hint: 'This is the most important photo — your face identity',
    tips: [
      'Fill the frame with your face',
      'Look directly at the camera',
      'Neutral or slight smile — no sunglasses',
      'Even lighting, no harsh shadows',
      'No filters or heavy makeup',
    ],
  },
  {
    type: 'body_front',
    label: 'Full Body — Front',
    description: 'Stand straight, face the camera — head to toe',
    hint: 'Used to capture your exact height and body proportions',
    tips: [
      'Head to toe — full body in frame',
      'Stand straight, arms slightly away from body',
      'Feet shoulder-width apart',
      'Plain background if possible',
      'Fitted clothing works best',
    ],
  },
  {
    type: 'left_30',
    label: 'Left 30° Turn',
    description: 'Turn your body 30° to the left, face the camera',
    hint: 'Slight left turn — not full profile, just 30 degrees',
    tips: [
      'Turn your body 30° to the LEFT',
      'Head can look toward camera',
      'Full body visible head to toe',
      'Natural relaxed stance',
    ],
  },
  {
    type: 'right_30',
    label: 'Right 30° Turn',
    description: 'Turn your body 30° to the right, face the camera',
    hint: 'Mirror of the left turn — 30 degrees to the right',
    tips: [
      'Turn your body 30° to the RIGHT',
      'Head can look toward camera',
      'Full body visible head to toe',
      'Natural relaxed stance',
    ],
  },
  {
    type: 'walking',
    label: 'Walking / Casual',
    description: 'Natural walking pose or casual relaxed stance',
    hint: 'Captures your natural movement and posture',
    tips: [
      'Mid-stride walking pose OR casual relaxed stance',
      'Natural arm position — not forced',
      'Full body visible head to toe',
      'Any natural expression',
    ],
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
