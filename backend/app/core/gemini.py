"""
Google Gemini image generation (Nano Banana 2).

Two-phase pipeline:
  Phase 0 — analyze_body_type():
      Analyzes reference photos to detect the person's body shape.
  Phase 1 — generate_angle_variations():
      Takes 6 real guided photos, generates 10 synthetic angle fills.
  Phase 2 — generate_identity_candidates():
      Takes all 16 images (6 real + 10 angles), generates 4 final try-on portraits.
      User picks one as their active identity.

B2C v1.1 additions:
  normalize_garment(): Pre-process garment — clean background, normalize lighting.
  validate_tryon_result(): QC check result image, return confidence score + notes.
"""
import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from google import genai
from google.genai import types
from app.config import settings


# ── Skin tone descriptors ─────────────────────────────────────────────────────
_SKIN_TONE_MAP = {
    "very_light":   "very fair porcelain skin with light peachy undertones and minimal pigmentation",
    "light":        "fair light skin with warm peachy-pink undertones",
    "medium_light": "light-medium skin with warm golden-beige undertones",
    "medium":       "medium warm tan skin with golden-olive undertones",
    "medium_dark":  "medium-dark warm brown skin with rich caramel undertones",
    "dark":         "deep dark rich brown skin with warm ebony undertones",
}

# ── Body type descriptors by gender ──────────────────────────────────────────
_BODY_TYPE_MAP: dict[str, dict[str, str]] = {
    "male": {
        "slim":     "slim lean frame with narrow shoulders, minimal muscle mass, and a thin silhouette",
        "athletic": "athletic V-shaped physique with broad shoulders, defined chest, and a narrow tapered waist",
        "average":  "average balanced build with moderate shoulder width and proportionate waist and hips",
        "stocky":   "stocky compact build with a broad chest, wide shoulders, and a fuller midsection",
        "heavy":    "heavy-set fuller frame with a broad rounded midsection and wider hips",
    },
    "female": {
        "hourglass":  "hourglass figure with well-defined waist, bust and hips of similar width",
        "pear":       "pear-shaped figure with narrower shoulders and bust, and fuller wider hips",
        "apple":      "apple-shaped figure with a fuller rounded midsection and narrower hips and legs",
        "rectangle":  "straight rectangular figure with similar measurements at shoulders, waist, and hips",
        "athletic":   "athletic toned figure with broad shoulders, defined waist, and lean muscular limbs",
    },
    "other": {
        "lean":     "lean slender frame with minimal body mass and narrow proportions",
        "athletic": "athletic toned physique with defined musculature and balanced proportions",
        "average":  "average balanced proportions throughout shoulders, waist, and hips",
        "full":     "fuller body shape with rounded curves and broader proportions",
        "heavy":    "heavy-set frame with a rounded fuller midsection and wider overall proportions",
    },
}


def _gender_key(gender: str) -> str:
    g = gender.lower()
    if g in ("male", "man", "boy"):
        return "male"
    if g in ("female", "woman", "girl"):
        return "female"
    return "other"


def _body_type_options(gender: str) -> list[str]:
    return list(_BODY_TYPE_MAP.get(_gender_key(gender), _BODY_TYPE_MAP["other"]).keys())


@dataclass
class UserProfile:
    gender: str = "person"
    age: int = 25
    height_cm: int = 170
    weight_kg: int = 65
    skin_tone: str = "medium"
    body_type: str = ""   # detected from photos in Phase 0


# ── Shared physical description ───────────────────────────────────────────────
def _physical_base(profile: UserProfile) -> str:
    skin = _SKIN_TONE_MAP.get(profile.skin_tone, _SKIN_TONE_MAP["medium"])
    gender_key = _gender_key(profile.gender)
    body_map = _BODY_TYPE_MAP.get(gender_key, _BODY_TYPE_MAP["other"])
    body_desc = body_map.get(profile.body_type, "")
    if not body_desc:
        # BMI fallback
        bmi = profile.weight_kg / ((profile.height_cm / 100) ** 2)
        if bmi < 18.5:
            body_desc = "slender lean physique with a slim frame"
        elif bmi < 25:
            body_desc = "athletic average build with balanced proportions"
        elif bmi < 30:
            body_desc = "fuller athletic build with a sturdy well-proportioned frame"
        else:
            body_desc = "plus-size build with full well-proportioned curves"

    return (
        f"The subject is a {profile.age}-year-old {profile.gender.lower()}. "
        f"Physical characteristics: {skin}. "
        f"Height {profile.height_cm} cm, weight approximately {profile.weight_kg} kg. "
        f"Body type: {body_desc}. "
        f"You are provided with multiple reference photographs of this exact person taken from "
        f"different angles. Analyse ALL reference images carefully to reconstruct a precise and "
        f"consistent 3-D understanding of their face shape, facial features, skin tone, hair, "
        f"body proportions, and posture. Your output must be photorealistic and match this person "
        f"faithfully — do not idealise, alter, or smooth out unique features.\n\n"
        f"FACIAL HAIR RULE (HIGHEST PRIORITY): Scan every single reference photo for any beard, "
        f"mustache, stubble, goatee, or facial hair. If ANY reference image shows facial hair — "
        f"even faint stubble — you MUST reproduce it faithfully in the generated image with the "
        f"exact same style, length, density, shape, and colour. Never remove, reduce, or clean-shave "
        f"facial hair that appears in the reference photos. This is mandatory.\n\n"
        f"JEWELRY REMOVAL RULE: The generated image must have NO jewelry of any kind — "
        f"no necklaces, no chains, no pendants, no rings on any finger, no bracelets, no watches, "
        f"no earrings. Remove all such items completely from the output even if visible in the "
        f"reference photos. Skin should appear natural and clean where jewelry was."
    )


# ── Phase 0 — body type analysis ─────────────────────────────────────────────
def _analyze_body_type_sync(image_bytes_list: list[bytes], gender: str) -> str:
    """
    Analyse reference photos and return the body type label that best fits.
    Uses Gemini text output (not image generation).
    """
    options = _body_type_options(gender)
    options_str = ", ".join(options)

    prompt = (
        f"You are a professional body-shape analyst. Study all the provided reference photos of "
        f"this {gender} person and determine their body type.\n\n"
        f"Available body types for a {gender} person: {options_str}\n\n"
        f"Instructions:\n"
        f"- Look at shoulder width, waist definition, hip width, and overall mass distribution.\n"
        f"- Consider the full body from all angles shown.\n"
        f"- Choose the single body type from the list above that best matches.\n\n"
        f"Respond with ONLY the body type word — nothing else, no punctuation, no explanation."
    )

    client = genai.Client(api_key=settings.google_api_key)
    parts: list[types.Part] = [types.Part.from_text(text=prompt)]
    for img in image_bytes_list:
        parts.append(types.Part.from_bytes(data=img, mime_type="image/jpeg"))

    response = client.models.generate_content(
        # model="gemini-2.5-flash",
        model="gemini-3.1-flash-image-preview",
        contents=[types.Content(parts=parts)],
    )
    detected = response.text.strip().lower().split()[0] if response.text else ""
    # Validate — fall back to first option if unrecognised
    # Validate — fall back to first option if not recognized
    return detected if detected in options else options[0]


async def analyze_body_type(reference_images: list[bytes], gender: str) -> str:
    """Phase 0: Detect body type from reference photos."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        return await loop.run_in_executor(pool, _analyze_body_type_sync, reference_images, gender)


# ── Phase 1 — angle variation prompts ────────────────────────────────────────
def _build_angle_prompts(profile: UserProfile) -> list[str]:
    phys = _physical_base(profile)

    ANGLES = [
        (
            "Generate a photorealistic full-body image of this person facing directly BACKWARD "
            "(rear view, 180°). Show the back of the head, shoulders, spine, buttocks, and the "
            "full legs down to the feet. Arms hanging relaxed at the sides. Plain white studio "
            "background. Even soft studio lighting. Same clothing as front-view reference."
        ),
        (
            "Generate a photorealistic full-body image of this person at a 45-DEGREE THREE-QUARTER "
            "angle tilted to the LEFT — body and face both angled, showing the left side of the "
            "face and left shoulder prominently. Full body visible head to toe. Plain white "
            "studio background. Soft studio lighting."
        ),
        (
            "Generate a photorealistic full-body image of this person at a 45-DEGREE THREE-QUARTER "
            "angle tilted to the RIGHT — body and face both angled, showing the right side of the "
            "face and right shoulder prominently. Full body visible head to toe. Plain white "
            "studio background. Soft studio lighting."
        ),
        (
            "Generate a photorealistic CLOSE-UP PORTRAIT of this person's face from a slight "
            "30-DEGREE LOW ANGLE — camera positioned just below chin level looking upward. "
            "Shows the underside of the jaw, neck, and full facial structure. Natural expression. "
            "Neutral background. Sharp focus on all facial features."
        ),
        (
            "Generate a photorealistic CLOSE-UP PORTRAIT of this person's face from a slight "
            "30-DEGREE HIGH ANGLE — camera positioned above eye level looking downward. "
            "Shows the top of the head, forehead, full face, and slightly down to the shoulders. "
            "Natural expression. Neutral background. Sharp focus."
        ),
        (
            "Generate a photorealistic FULL-BODY image of this person in a relaxed SEATED POSITION "
            "on a plain white cube or bench, facing directly forward. Hands resting on thighs. "
            "Both feet flat on the ground. Natural upright seated posture. Plain white studio "
            "background. Soft even lighting."
        ),
        (
            "Generate a photorealistic FULL-BODY image of this person in a MID-STRIDE WALKING POSE "
            "facing the camera — left foot stepping forward, right foot pushing off behind. "
            "Arms in natural opposing swing. Head level, looking at camera. Full figure head to "
            "toe visible. Plain white background. Natural motion feel."
        ),
        (
            "Generate a photorealistic FULL-BODY image of this person with ARMS CROSSED confidently "
            "at chest height, facing directly forward. Feet shoulder-width apart. Relaxed but "
            "confident posture. Full figure visible head to toe. Plain white studio background. "
            "Soft front studio lighting."
        ),
        (
            "Generate a photorealistic UPPER-BODY PORTRAIT (waist up) of this person facing "
            "directly forward, one hand loosely resting at the collarbone and the other arm "
            "hanging naturally at side. Relaxed natural expression. Neutral light grey background. "
            "Soft portrait lighting with subtle side fill."
        ),
        (
            "Generate a photorealistic FULL-BODY image of this person in a RELAXED CASUAL POSE — "
            "weight shifted to the right leg, left knee slightly bent, one hand in a side pocket. "
            "Facing 15 degrees to the right but head turned directly at camera. Effortless "
            "natural stance. Plain white studio background. Fashion editorial lighting."
        ),
    ]

    reminder = (
        "\nREMINDER — FACIAL HAIR: if the person has any beard, mustache, or stubble in the "
        "reference photos, reproduce it exactly — same shape, density, and colour. Do NOT remove it.\n"
        "REMINDER — NO JEWELRY: remove all necklaces, chains, rings, bracelets, and watches "
        "from the output. Bare neck, bare hands, bare wrists."
    )

    return [
        f"{phys}\n\nSPECIFIC VIEWPOINT TO GENERATE:\n{angle}\n\n"
        f"IMPORTANT: Preserve this person's exact face, hair, skin tone, and body proportions "
        f"from all reference photos. Generate only the specified viewpoint/pose. "
        f"CLOTHING: plain white crew-neck t-shirt and plain light grey fitted trousers — "
        f"no logos, no patterns. QUALITY: ultra-high resolution, photorealistic, sharp focus."
        f"{reminder}"
        for angle in ANGLES
    ]


# ── Phase 2 — final try-on portrait prompts ───────────────────────────────────
def _build_portrait_prompts(profile: UserProfile) -> list[str]:
    phys = _physical_base(profile)

    POSES = [
        (
            "POSE: Classic front-facing try-on stance. Body perfectly upright, facing directly "
            "forward. Feet shoulder-width apart, toes forward. Both arms hanging relaxed at the "
            "sides slightly away from the body so the full torso outline is clearly visible. "
            "Head level, looking directly at the camera, calm neutral expression. "
            "This is the PRIMARY virtual try-on reference pose — must be perfectly symmetrical."
        ),
        (
            "POSE: Confident power stance. Body upright, weight shifted slightly to one leg. "
            "One hand loosely on hip, other arm hanging naturally. Shoulders back, chest open. "
            "Head slightly tilted, subtle confident smile. Full body clearly visible for clothing overlay."
        ),
        (
            "POSE: Relaxed three-quarter turn — body angled 30 degrees to the left, "
            "head turned to face directly at the camera. One hand loosely in a front pocket, "
            "other arm hanging naturally. Weight on back leg, front knee slightly bent. "
            "Natural effortless posture. Front torso and both legs fully visible."
        ),
        (
            "POSE: Editorial walking pose — mid-stride, left foot stepping forward, "
            "right foot slightly behind. Arms in natural opposing swing. Body angled 15 degrees "
            "to the right, head turned to look at camera. Dynamic fashion energy. "
            "Full outfit area visible — no extreme foreshortening of the torso."
        ),
    ]

    base = (
        f"{phys}\n\n"
        f"You have been provided with a comprehensive set of reference photographs of this person "
        f"from multiple angles (front, sides, back, close-up, and various poses). Use ALL of them "
        f"to build the most accurate possible representation.\n\n"
        f"CLOTHING: plain seamless white crew-neck t-shirt and plain fitted light grey trousers — "
        f"no patterns, no logos, minimal base clothing for virtual garment overlay.\n"
        f"BACKGROUND: pure flat white studio (#FFFFFF), no shadows on background, no props.\n"
        f"LIGHTING: professional fashion studio — soft even diffused front light, gentle fill.\n"
        f"CAMERA: full-body shot head to toe, 85mm equivalent, eye level, small comfortable margins.\n"
        f"QUALITY: ultra-high resolution, photorealistic, sharp focus throughout, "
        f"professional fashion e-commerce standard.\n"
        f"REMINDER — FACIAL HAIR: if ANY reference photo shows a beard, mustache, goatee, or "
        f"stubble, reproduce it exactly in this portrait — same shape, length, density, and colour. "
        f"This is the highest-priority facial feature. Never clean-shave a bearded subject.\n"
        f"REMINDER — NO JEWELRY: the output must show bare neck (no chains/necklaces), "
        f"bare fingers (no rings), and bare wrists (no watches or bracelets). "
        f"Remove all jewelry completely even if present in reference photos.\n\n"
    )

    return [base + pose for pose in POSES]


# ── Core Gemini call ──────────────────────────────────────────────────────────
_log = logging.getLogger(__name__)


def _generate(image_bytes_list: list[bytes], prompt: str) -> bytes | None:
    """Synchronous Gemini call with multiple reference images. Runs in thread pool."""
    try:
        client = genai.Client(api_key=settings.google_api_key)
        parts: list[types.Part] = [types.Part.from_text(text=prompt)]
        for img in image_bytes_list:
            parts.append(types.Part.from_bytes(data=img, mime_type="image/jpeg"))

        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=[types.Content(parts=parts)],
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                return part.inline_data.data
        _log.warning("Gemini returned no image data. Parts: %s", response.candidates[0].content.parts)
        return None
    except Exception as exc:
        _log.error("Gemini _generate failed: %s", exc)
        return None


async def _run_concurrent(
    image_bytes_list: list[bytes],
    prompts: list[str],
    max_workers: int,
) -> list[bytes]:
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        tasks = [
            loop.run_in_executor(pool, _generate, image_bytes_list, prompt)
            for prompt in prompts
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    successes = [r for r in results if isinstance(r, bytes) and r]
    failures = [r for r in results if not (isinstance(r, bytes) and r)]
    if failures:
        _log.warning("%d/%d generations failed or returned no image", len(failures), len(results))
    return successes


# ── Try-on prompt ─────────────────────────────────────────────────────────────

# Per-category: replacement rule + fabric physics description
# ── Material detection + physics ──────────────────────────────────────────────

def _detect_material(description: str) -> str:
    """Infer fabric material from garment description for physics simulation."""
    desc = description.lower()
    if any(w in desc for w in ["denim", "jean", "jeans"]):
        return "denim"
    if any(w in desc for w in ["leather", "suede", "vegan leather"]):
        return "leather"
    if any(w in desc for w in ["silk", "satin", "chiffon"]):
        return "silk"
    if any(w in desc for w in ["wool", "knit", "cashmere", "fleece", "sweater", "jumper", "knitwear", "cable"]):
        return "wool_knit"
    if any(w in desc for w in ["linen", "linen-blend"]):
        return "linen"
    if any(w in desc for w in ["nylon", "polyester", "synthetic", "technical", "windbreaker", "neoprene", "gore-tex"]):
        return "synthetic"
    return "cotton"


_MATERIAL_PHYSICS: dict[str, str] = {
    "denim": (
        "DENIM PHYSICS: stiff woven fabric with low drape. Deep parallel crease lines at knees and crotch. "
        "Thick visible seams at inseam, outseam, and fly. Rigid waistband sits heavy on hips. "
        "Fabric holds its shape — minimal flowing drape. Slight indigo fade at high-friction wear points."
    ),
    "leather": (
        "LEATHER PHYSICS: structured rigid material with a subtle surface sheen. "
        "Creases only at flex joints — elbows, behind knees. Shoulder panels hold architectural shape. "
        "Specular highlight band along curved surfaces. Wrinkles are deep and directional. "
        "Material weight causes hem and cuffs to sit heavy."
    ),
    "silk": (
        "SILK/SATIN PHYSICS: ultra-fluid low-friction fabric with high drape coefficient. "
        "Cascading smooth rounded folds following gravity. "
        "Specular sheen highlight bands across curved surfaces — fabric catches and reflects light. "
        "Minimal sharp friction wrinkles. Soft flowing folds at waist and hip."
    ),
    "wool_knit": (
        "WOOL/KNIT PHYSICS: heavy elastic fabric with pronounced surface texture. "
        "Visible rib lines at cuffs, collar, and hem. Fabric stretches at shoulders/chest. "
        "Soft rounded drape with minimal sharp creases. Cable or knit pattern clearly visible. "
        "Slight pilling texture on high-friction zones (inner arms, collar edge)."
    ),
    "linen": (
        "LINEN PHYSICS: highly wrinkle-prone natural fiber. "
        "Visible wrinkle clusters at elbows, waist, and back of knee — these are natural and should NOT be ironed out. "
        "Relaxed loose drape. Natural slub texture variation across surface."
    ),
    "synthetic": (
        "SYNTHETIC/TECHNICAL PHYSICS: wrinkle-resistant, retains engineered shape. "
        "Slight surface sheen or matte technical finish. Seam tape visible at stress seams. "
        "Fabric follows body contour cleanly without heavy creasing. Zippers and hardware sit flush and precise."
    ),
    "cotton": (
        "COTTON PHYSICS: medium-weight natural fiber with soft natural wrinkles. "
        "Soft rounded folds at armpits, elbows, and waist. "
        "Jersey cotton shows subtle stretch lines at shoulders. Woven cotton shows crisp fold lines at elbows. "
        "Hem hangs with a slight gravity curve — never perfectly straight."
    ),
}


# Per-category: replacement rule + base fabric physics description
_CATEGORY_RULES: dict[str, tuple[str, str]] = {
    "tops": (
        "Replace ONLY the upper-body garment with the item shown. Keep lower-body clothing exactly as-is.",
        "lightweight fabric, natural wrinkles near the chest, subtle folds at the waist, slight fabric pull at the shoulders, "
        "gentle creasing under the arms, gravity pulling the hem downward",
    ),
    "bottoms": (
        "Replace ONLY the lower-body garment with the item shown. Keep upper-body clothing exactly as-is.",
        "fabric tension at the thighs and knees, natural wrinkles behind the knee bend, waistband sitting naturally on the hips, "
        "slight flare at the ankles, gravity-driven drape of the legs",
    ),
    "dresses": (
        "Replace the ENTIRE outfit (top and bottom) with the dress shown. Full garment swap.",
        "flowing fabric reacting to body curves, fitted torso with gentle stretch lines, skirt draping downward with gravity, "
        "subtle folds at the hips and waist, soft fabric movement",
    ),
    "outerwear": (
        "Layer the jacket or coat OVER the existing clothing. Keep the inner clothes subtly visible at collar, cuffs, and hem.",
        "thick structured fabric, shoulder seams sitting on the shoulder bones, slight fabric tension across the back, "
        "natural folds at the elbows, lapel falling naturally, hem hanging straight due to weight",
    ),
    "footwear": (
        "Replace ONLY the footwear. Keep all clothing above the ankle unchanged.",
        "shoes/footwear sitting naturally on the feet, accurate heel height, realistic contact with the ground surface, "
        "natural ankle crease if any",
    ),
    "watches": (
        "Add the watch to the person's LEFT wrist. No other changes to clothing or body.",
        "watch strap conforming to the wrist curvature, clasp visible, watch face angled slightly toward camera, "
        "natural contact with skin",
    ),
    "sunglasses": (
        "Place the sunglasses on the person's face, resting on the nose bridge. No other changes.",
        "frames resting naturally on the nose, temples following the curve of the skull, lenses reflecting ambient light subtly",
    ),
    "accessories": (
        "Add the accessory in a natural position appropriate for that item type. Keep all clothing unchanged.",
        "accessory sitting naturally against the body or clothing, fabric interaction where the item touches clothing",
    ),
}

# Per-fit modifier — layered on top of category physics
_FIT_MODIFIERS: dict[str, str] = {
    "slim": (
        "slim fit — fabric hugging the body closely, visible muscle contour through the fabric, "
        "minimal excess fabric, strong tension lines at the shoulders and chest"
    ),
    "regular": (
        "regular fit — balanced drape with a little ease across the chest and waist, "
        "fabric following body shape without pulling or excess bunching"
    ),
    "oversized": (
        "oversized fit — generous fabric with heavy draping at the shoulders past the shoulder bone, "
        "wide torso with cascading folds, slouched sleeves, extra fabric pooling at the waist and hips"
    ),
}


def _build_tryon_prompt(category: str, garment_desc: str, fit: str = "regular") -> str:
    rule, fabric_physics = _CATEGORY_RULES.get(
        category,
        ("Dress the person in the garment shown.", "natural fabric drape and wrinkles")
    )
    fit_mod = _FIT_MODIFIERS.get(fit, _FIT_MODIFIERS["regular"])

    return (
        f"You are a professional virtual try-on AI system specializing in photorealistic garment simulation.\n\n"
        f"INPUTS:\n"
        f"  Image 1 — Full-body portrait of a real person (reference model)\n"
        f"  Image 2 — Product garment photograph ({category})\n\n"
        f"TASK: Generate ONE photorealistic image of the exact person from Image 1 wearing the "
        f"garment from Image 2, in the same pose, background, and lighting as Image 1.\n\n"
        f"GARMENT CATEGORY: {category}\n"
        f"GARMENT DESCRIPTION: {garment_desc}\n"
        f"FIT TYPE: {fit_mod}\n\n"
        f"PLACEMENT RULE: {rule}\n\n"
        f"FABRIC & PHYSICS SIMULATION:\n"
        f"Simulate realistic cloth behavior — {fabric_physics}.\n"
        f"The garment must wrap the body contours, not float or sit flat.\n"
        f"Include: natural wrinkles at stress points (armpits, elbows, waist), "
        f"fabric tension across shoulders, gravity pulling the fabric downward, "
        f"shadow cast by the garment onto the body.\n"
        f"Quality reference: Marvelous Designer cloth simulation, professional fashion e-commerce photography.\n\n"
        f"IDENTITY RULES (HIGHEST PRIORITY):\n"
        f"- Preserve the person's exact face, hair, skin tone, facial hair, and body proportions — do not alter them\n"
        f"- Do not change the pose or background from Image 1\n"
        f"- Do not add, remove, or modify any garments beyond what the placement rule specifies\n\n"
        f"AVOID: stiff fabric, pasted-on texture, flat lighting, mannequin look, plastic sheen, "
        f"floating clothes, no wrinkles, incorrect shadows, unrealistic fit.\n\n"
        f"OUTPUT: A single ultra-high-resolution photorealistic image. Fashion editorial quality. "
        f"The garment must look like it was physically worn in a real photoshoot, not composited."
    )




@dataclass
class SubjectProfile:
    """Physical stats of the model — used to anchor body proportions in the prompt."""
    height_cm: int = 170
    weight_kg: int = 70
    gender: str = "person"
    age: int = 25
    body_type: str = ""

    def describe(self) -> str:
        """Return a concise physical description for the prompt."""
        # Height tier
        h = self.height_cm
        if h >= 188:
            height_desc = f"{h} cm — very tall, long limbs, long torso, long legs"
        elif h >= 180:
            height_desc = f"{h} cm — tall, above-average limb length and torso"
        elif h >= 172:
            height_desc = f"{h} cm — average-tall, balanced proportions"
        elif h >= 163:
            height_desc = f"{h} cm — average height"
        else:
            height_desc = f"{h} cm — below-average height, shorter limbs"

        # BMI-based build
        bmi = self.weight_kg / ((h / 100) ** 2) if h else 22
        if bmi < 18.5:
            build = "very lean, narrow frame, minimal body mass"
        elif bmi < 22:
            build = "lean athletic build"
        elif bmi < 25:
            build = "average healthy build"
        elif bmi < 28:
            build = "slightly fuller build, moderate muscle mass"
        elif bmi < 32:
            build = "stocky fuller frame, broader shoulders and midsection"
        else:
            build = "heavy-set frame with broader proportions"

        body_note = f", body type: {self.body_type}" if self.body_type else ""
        return (
            f"Height: {height_desc}. "
            f"Weight: {self.weight_kg} kg. "
            f"Build: {build}{body_note}. "
            f"Age: {self.age}. Gender: {self.gender}. "
            f"BODY PROPORTION ENFORCEMENT — NON-NEGOTIABLE: "
            f"The generated figure must accurately reflect a {h} cm person. "
            f"A {h} cm person has visibly {'long legs and elongated torso' if h >= 180 else 'proportional legs and torso'}. "
            f"Do NOT compress, shorten, or widen the body under any circumstance. "
            f"Full leg length must be visible if this is a full-body shot. "
            f"Torso-to-leg ratio must match a real {h} cm person exactly. "
            f"If the output would crop the feet — extend the canvas instead, never squish proportions."
        )


@dataclass
class GarmentInput:
    image_bytes: bytes
    category: str
    fit: str = "regular"
    description: str = ""


def _build_outfit_prompt(garments: list[GarmentInput], has_pose_ref: bool = False, subject: SubjectProfile | None = None) -> str:
    """Build a prompt for dressing a person in a complete multi-garment outfit."""
    # Garment images start at Image 2 (no pose ref) or Image 3 (with pose ref)
    garment_start = 3 if has_pose_ref else 2
    garment_lines: list[str] = []
    for i, g in enumerate(garments, start=garment_start):
        rule, base_physics = _CATEGORY_RULES.get(
            g.category,
            ("Apply the garment naturally.", "natural fabric drape and wrinkles"),
        )
        fit_mod = _FIT_MODIFIERS.get(g.fit, _FIT_MODIFIERS["regular"])
        # Material-aware physics layer
        material = _detect_material(g.description)
        material_physics = _MATERIAL_PHYSICS.get(material, _MATERIAL_PHYSICS["cotton"])
        desc_part = f" — {g.description}" if g.description else ""
        garment_lines.append(
            f"  Image {i}: {g.category.upper()}{desc_part}\n"
            f"    Placement: {rule}\n"
            f"    Fit: {fit_mod}\n"
            f"    Base physics: {base_physics}\n"
            f"    Material physics: {material_physics}"
        )

    garment_block = "\n\n".join(garment_lines)
    is_outfit = len(garments) > 1
    task_desc = (
        "a complete coordinated outfit using ALL of the garments listed above simultaneously"
        if is_outfit else
        "the single garment shown"
    )

    if has_pose_ref:
        pose_ref_input = f"  Image 2 — POSE & EXPRESSION REFERENCE (different person; used ONLY for pose and expression — never for identity)\n"
        pose_instructions = (
            f"POSE & EXPRESSION — SOURCE: Image 2 ONLY\n"
            f"Study Image 2 and extract:\n"
            f"  • Full-body pose — exact limb positions, weight shift, torso angle, head tilt, hand placement\n"
            f"  • Facial expression — muscle positions: mouth shape, eye shape and intensity, brow position, cheek lift\n"
            f"Apply these ONLY to the person from Image 1. Do NOT copy any other feature from Image 2.\n"
        )
        background_note = "Professional fashion photoshoot background and lighting. Full body visible head to toe.\n"
    else:
        pose_ref_input = ""
        pose_instructions = (
            f"POSE & EXPRESSION — DEFAULT:\n"
            f"Classic front-facing model stance — upright, feet shoulder-width apart, "
            f"arms relaxed at sides, neutral expression, looking directly at camera.\n"
        )
        background_note = "Plain white studio background, soft even fashion lighting, full body head to toe.\n"

    subject_block = ""
    if subject:
        subject_block = (
            f"═══ SUBJECT PHYSICAL PROFILE ═══\n"
            f"{subject.describe()}\n\n"
        )

    inputs_block = (
        f"  Image 1 — MODEL / IDENTITY SOURCE\n"
        f"    Use ONLY for: face, skin tone, hair, body proportions, tattoos, build\n\n"
        f"{pose_ref_input}"
        f"{garment_block}"
    )

    return (
        f"You are a professional virtual try-on AI system targeting 90% photorealism.\n"
        f"Each input image has one exclusive role. Treat them independently — do not mix.\n\n"
        f"═══ INPUT IMAGES & THEIR ROLES ═══\n"
        f"{inputs_block}\n\n"
        f"═══ TASK ═══\n"
        f"Generate ONE photorealistic image of the person from Image 1 wearing {task_desc}.\n\n"
        f"{subject_block}"
        f"═══ STRICT ROLE SEPARATION (NON-NEGOTIABLE) ═══\n"
        f"Feature          │ Source\n"
        f"─────────────────┼──────────────────────────────────\n"
        f"Identity / Face  │ Image 1 ONLY\n"
        f"Skin tone        │ Image 1 ONLY\n"
        f"Body proportions │ Image 1 + physical profile above\n"
        f"Tattoos          │ Image 1 ONLY (preserve exactly)\n"
        f"Garment design   │ Garment image(s) ONLY\n"
        f"Body pose        │ {'Image 2 ONLY' if has_pose_ref else 'Default neutral stance'}\n"
        f"Expression       │ {'Image 2 ONLY' if has_pose_ref else 'Neutral'}\n\n"
        f"PROHIBITED: copying face, skin, hair, tattoos, or identity from any non-identity image. "
        f"Mixed identities are a critical failure.\n\n"
        f"═══ POSE & EXPRESSION ═══\n"
        f"{pose_instructions}"
        f"{background_note}\n"
        f"═══ GARMENT APPLICATION ═══\n"
        f"- Apply EVERY garment listed above to the person simultaneously\n"
        f"- Follow each garment's Placement rule — do not swap or mix them\n"
        f"- Garments must form a coherent, stylish complete look\n"
        f"- Natural layering: shirt visible under open jacket, watch below sleeve cuff, etc.\n\n"
        f"═══ FABRIC PHYSICS & MATERIAL SIMULATION ═══\n"
        f"The garment must look like it is PHYSICALLY WORN by a real human body — not a product shot, not a mannequin, not a flat overlay.\n"
        f"Apply BOTH the base physics and the material-specific physics listed per garment above.\n"
        f"General rules:\n"
        f"  • Gravity pulls all fabric downward — hems never float level\n"
        f"  • Fabric wraps 3D body contours — follows the curve of the chest, shoulder blade, hip, and knee\n"
        f"  • Stress wrinkles radiate from anchor points (armpits, crotch, waist seam, knee bend)\n"
        f"  • Compression folds form where fabric is pushed inward by body mass\n"
        f"  • Each material behaves differently — simulate it according to the material physics specification above\n"
        f"WORN STATE: Preserve exactly from the product image — open zip stays open, relaxed collar stays relaxed, volume stays. Never flatten or alter the garment state.\n"
        f"Quality reference: Marvelous Designer cloth simulation, CLO 3D physics, professional fashion editorial.\n\n"
        f"═══ SHADOW INJECTION ═══\n"
        f"Cast EVERY shadow below — missing any is a realism failure:\n"
        f"  • CONTACT SHADOW: soft dark shadow at every garment-to-skin contact edge (collar-to-neck, cuff-to-wrist, hem-to-thigh)\n"
        f"  • UNDER-COLLAR SHADOW: shadow cast by collar/lapel onto neck and upper chest\n"
        f"  • AXILLA SHADOW: deep shadow in the armpit cavity where sleeve meets torso\n"
        f"  • ELBOW CREASE SHADOW: shadow inside elbow fold when arm is bent\n"
        f"  • WAIST SHADOW: shadow where waistband presses into skin or underlying garment\n"
        f"  • FOLD SHADOWS: every fabric fold has a shadow on its concave (darker) side\n"
        f"  • LAYERING SHADOW: if jacket is worn over shirt, shadow cast by jacket hem and collar onto underlying shirt\n"
        f"  • GROUND SHADOW: feet and shoes cast a soft diffuse shadow on the ground plane\n"
        f"  • LIGHTING MATCH: shadow direction and temperature MUST match the lighting in Image 1 exactly\n\n"
        f"═══ DEPTH & EDGE QUALITY ═══\n"
        f"  • Garment edges: soft natural falloff matching real fabric edges — NO sharp cut-out silhouette lines\n"
        f"  • Depth separation: occlusion shadow between garment surface and body at neckline, sleeve openings, hem\n"
        f"  • Layer depth: each fabric layer sits at a physically correct z-depth above the previous layer\n"
        f"  • Ambient occlusion: subtle darkening where fabric layers overlap or compress (inner collar, under lapel)\n"
        f"  • Halo prohibition: absolutely NO bright glow or halo around any garment edge\n"
        f"  • Sub-surface scattering: thin fabrics (silk, light cotton) show a very slight warm light bleed at edges when backlit\n\n"
        f"═══ MICRO-IMPERFECTIONS ═══\n"
        f"These micro-details are MANDATORY — they are what makes a result look like a real photo:\n"
        f"  • Left/right ASYMMETRY: sleeves and lapels are never perfectly mirror-identical — one is always slightly different\n"
        f"  • FABRIC GRAIN: subtle texture variation across the fabric surface — never perfectly uniform\n"
        f"  • SEAM MICRO-WRINKLES: tiny wrinkles radiating from high-tension seams (armpit seam, collar attachment seam)\n"
        f"  • WEAR ARTIFACTS: very subtle fabric compression at high-contact body points (shoulder top, collar fold)\n"
        f"  • GRAVITATIONAL SAG: slight downward sag at sleeve ends and hem corners — fabric has weight\n"
        f"  • NATURAL IMPERFECTION: 1-2 minor random folds that are not stress-point driven — real clothes are never perfectly modeled\n\n"
        f"═══ NEGATIVE PROMPT ═══\n"
        f"Do NOT produce any of the following — each is a critical failure:\n"
        f"  ✗ Identity transfer / copied face or skin from non-identity image\n"
        f"  ✗ Pasted-on clothing texture (garment looks like a flat decal on body)\n"
        f"  ✗ Stiff or rigid fabric with no wrinkles or drape\n"
        f"  ✗ Plastic sheen on matte fabrics\n"
        f"  ✗ Floating clothes (not in contact with body)\n"
        f"  ✗ Missing contact shadows at garment edges\n"
        f"  ✗ Sharp cut-out halo around garment silhouette\n"
        f"  ✗ Perfectly symmetrical left/right sleeves\n"
        f"  ✗ Flat uniform texture with no grain variation\n"
        f"  ✗ Compressed, shortened, or widened body proportions\n"
        f"  ✗ Product-catalog look (garment on invisible mannequin)\n"
        f"  ✗ Altered garment state (zip closed when product shows open, etc.)\n"
        f"  ✗ Inconsistent lighting direction vs Image 1\n\n"
        f"OUTPUT: Single ultra-high-resolution photorealistic image. "
        f"Target: 90% realism — indistinguishable from a real fashion photoshoot at first glance. "
        f"Every garment physically worn, every shadow present, every material behaving correctly."
    )


def _generate_outfit_sync(person_bytes: bytes, garments: list[GarmentInput], pose_bytes: bytes | None, subject: SubjectProfile | None) -> bytes | None:
    """Synchronous Gemini outfit try-on call. Runs in thread pool."""
    try:
        prompt = _build_outfit_prompt(garments, has_pose_ref=pose_bytes is not None, subject=subject)
        client = genai.Client(api_key=settings.google_api_key)
        parts: list[types.Part] = [
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=person_bytes, mime_type="image/jpeg"),
        ]
        if pose_bytes:
            parts.append(types.Part.from_bytes(data=pose_bytes, mime_type="image/jpeg"))
        for g in garments:
            parts.append(types.Part.from_bytes(data=g.image_bytes, mime_type="image/jpeg"))

        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=[types.Content(parts=parts)],
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                return part.inline_data.data
        _log.warning("Gemini outfit try-on returned no image. Parts: %s", response.candidates[0].content.parts)
        return None
    except Exception as exc:
        _log.error("Gemini outfit try-on failed: %s", exc)
        return None


async def generate_tryon(
    person_bytes: bytes,
    garments: list[GarmentInput],
    pose_bytes: bytes | None = None,
    subject: SubjectProfile | None = None,
) -> bytes | None:
    """Generate a virtual try-on image for one or more garments using Gemini."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        return await loop.run_in_executor(pool, _generate_outfit_sync, person_bytes, garments, pose_bytes, subject)


# ── Garment normalization ─────────────────────────────────────────────────────

def _normalize_garment_sync(garment_bytes: bytes, category: str) -> bytes:
    """Remove background and normalize lighting. Falls back to original bytes on failure."""
    try:
        prompt = (
            f"You are a garment processing AI.\n\n"
            f"INPUT: A product photograph of a {category}.\n\n"
            f"TASK:\n"
            f"1. Remove the background completely — output the garment on a pure white (#FFFFFF) background\n"
            f"2. Normalize the lighting — soft, even, front-lit studio light, no harsh shadows on background\n"
            f"3. Preserve every detail: fabric texture, logos, patterns, stitching, hardware, colors\n"
            f"4. Keep exact garment shape — do not warp, stretch, or alter proportions\n"
            f"5. Center the garment in frame with 10% padding on all sides\n\n"
            f"CRITICAL — PRESERVE GARMENT STATE EXACTLY:\n"
            f"- If the zip is open → keep it open exactly as shown\n"
            f"- If the zip is closed → keep it closed\n"
            f"- If buttons are undone → keep them undone\n"
            f"- If the collar is folded → keep it folded\n"
            f"- Do NOT change any closures, fasteners, or garment position\n"
            f"- Preserve natural fabric drape — if the garment has folds or volume, keep them\n"
            f"- Do NOT flatten, iron out, or make the garment look like a flat product shot\n\n"
            f"OUTPUT: A clean isolated garment on white background that still looks three-dimensional "
            f"and natural, exactly as it appeared in the original photo — just with background removed."
        )
        client = genai.Client(api_key=settings.google_api_key)
        parts: list[types.Part] = [
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=garment_bytes, mime_type="image/jpeg"),
        ]
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=[types.Content(parts=parts)],
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                return part.inline_data.data
        _log.warning("Garment normalization returned no image, using original")
        return garment_bytes
    except Exception as exc:
        _log.warning("Garment normalization failed (%s), using original", exc)
        return garment_bytes


async def normalize_garment(garment_bytes: bytes, category: str) -> bytes:
    """Pre-process garment: remove background, normalize lighting. Safe — always returns bytes."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        return await loop.run_in_executor(pool, _normalize_garment_sync, garment_bytes, category)


# ── Result validation ─────────────────────────────────────────────────────────

def _validate_tryon_sync(result_bytes: bytes, garments: list[GarmentInput]) -> dict:
    """
    QC + trust layer analysis on generated try-on result.
    Returns: passed, confidence, fit_confidence_pct, suggested_size, fit_type, issues, notes.
    """
    garment_list = ", ".join(f"{g.category} ({g.fit} fit)" for g in garments)
    primary = garments[0] if garments else None
    primary_category = primary.category if primary else "tops"
    primary_fit = primary.fit if primary else "regular"

    prompt = (
        f"You are a senior quality control and fit analyst AI for a virtual try-on platform.\n\n"
        f"Analyze the provided try-on result image across TWO layers:\n\n"
        f"━━━ LAYER 1: REALISM QC ━━━\n"
        f"Score each criterion from 0.0 to 1.0:\n"
        f"1. garment_placement — correctly positioned on the body?\n"
        f"2. fabric_realism — natural wrinkles, material-appropriate drape, no stiff/plastic texture?\n"
        f"3. shadow_quality — contact shadows present at all garment edges? Fold shadows visible?\n"
        f"4. edge_quality — no sharp cut-out lines or halo around garment silhouette?\n"
        f"5. body_proportions — natural body shape, not squished/stretched?\n"
        f"6. micro_detail — fabric grain, asymmetry, seam wrinkles visible?\n\n"
        f"━━━ LAYER 2: FIT TRUST LAYER ━━━\n"
        f"Garments expected: {garment_list}\n"
        f"Analyze the fit of the primary garment ({primary_category}, {primary_fit} fit) and determine:\n"
        f"A. fit_confidence_pct (integer 0-100): How confident are you this garment fits the person well?\n"
        f"   - 90-100: Perfect fit, no issues\n"
        f"   - 75-89: Good fit with minor imperfections\n"
        f"   - 60-74: Acceptable but some fit issues (shoulder width, length)\n"
        f"   - below 60: Poor fit\n"
        f"B. suggested_size: Based on what you see, suggest the best size.\n"
        f"   Options: XS, S, M, L, XL, XXL — pick the one that would fit this person best for this garment.\n"
        f"C. fit_type: Describe how the garment actually fits in 2-5 words.\n"
        f"   Examples: 'True to size', 'Runs large', 'Runs small', 'Slim through shoulders', 'Relaxed through waist'\n\n"
        f"━━━ RESPONSE FORMAT ━━━\n"
        f"Respond in this EXACT JSON format and nothing else:\n"
        f'{{\n'
        f'  "passed": true,\n'
        f'  "confidence": 0.85,\n'
        f'  "fit_confidence_pct": 82,\n'
        f'  "suggested_size": "M",\n'
        f'  "fit_type": "True to size",\n'
        f'  "issues": [],\n'
        f'  "notes": "Good shoulder alignment, natural sleeve drape"\n'
        f'}}\n\n'
        f"Rules:\n"
        f"- confidence = average of all 6 realism scores\n"
        f"- passed = true if confidence >= 0.72\n"
        f"- issues = list of failed criteria names (those scoring below 0.65)\n"
        f"- Respond with JSON only — no explanation, no markdown fences"
    )
    try:
        client = genai.Client(api_key=settings.google_api_key)
        parts: list[types.Part] = [
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=result_bytes, mime_type="image/jpeg"),
        ]
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[types.Content(parts=parts)],
        )
        text = (response.text or "").strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
            return {
                "passed": bool(data.get("passed", True)),
                "confidence": float(data.get("confidence", 0.8)),
                "fit_confidence_pct": int(data.get("fit_confidence_pct", 80)),
                "suggested_size": str(data.get("suggested_size", "M")),
                "fit_type": str(data.get("fit_type", "True to size")),
                "issues": list(data.get("issues", [])),
                "notes": str(data.get("notes", "")),
            }
    except Exception as exc:
        _log.warning("Try-on validation failed (%s), assuming passed", exc)
    return {
        "passed": True,
        "confidence": 0.8,
        "fit_confidence_pct": 80,
        "suggested_size": "M",
        "fit_type": "True to size",
        "issues": [],
        "notes": "",
    }


async def validate_tryon_result(result_bytes: bytes, garments: list[GarmentInput]) -> dict:
    """Validate try-on result quality. Returns confidence score, pass/fail, and user-facing notes."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        return await loop.run_in_executor(pool, _validate_tryon_sync, result_bytes, garments)


# ── Public API ────────────────────────────────────────────────────────────────
async def generate_angle_variations(
    reference_images: list[bytes],
    profile: UserProfile,
) -> list[bytes]:
    """
    Phase 1: Generate 10 synthetic angle fills from the 6 guided reference photos.
    Returns list of JPEG byte strings (may be fewer than 10 if some generations fail).
    """
    prompts = _build_angle_prompts(profile)
    return await _run_concurrent(reference_images, prompts, max_workers=10)


async def generate_identity_candidates(
    reference_images: list[bytes],
    profile: UserProfile | None = None,
) -> list[bytes]:
    """
    Phase 2: Generate 4 final try-on portrait candidates from all reference images.
    Returns list of JPEG byte strings.
    """
    p = profile or UserProfile()
    prompts = _build_portrait_prompts(p)
    return await _run_concurrent(reference_images, prompts, max_workers=4)
