import cv2
import numpy as np
import matplotlib.pyplot as plt

# ---------- Load images ----------
arm_img = cv2.imread("arm.webp")
if arm_img is None:
    raise IOError("❌ arm.webp not found!")

arm_img = cv2.cvtColor(arm_img, cv2.COLOR_BGR2RGB)

bandaid = cv2.imread("bandaid.png", cv2.IMREAD_UNCHANGED)
if bandaid is None:
    raise IOError("❌ bandaid.png not found!")

if bandaid.shape[2] != 4:
    raise IOError("❌ bandaid.png must have an alpha channel (transparent background)")

orig = arm_img.copy()

# ---------- Helper: overlay with alpha ----------
def overlay_image_alpha(img, overlay, x, y):
    h, w = overlay.shape[:2]

    # Clip to image boundaries
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(img.shape[1], x + w), min(img.shape[0], y + h)

    if x1 >= x2 or y1 >= y2:
        return img

    overlay_cropped = overlay[y1 - y:y2 - y, x1 - x:x2 - x]

    overlay_rgb = overlay_cropped[:, :, :3]
    alpha = overlay_cropped[:, :, 3] / 255.0
    alpha = alpha[..., None]

    img[y1:y2, x1:x2] = (1 - alpha) * img[y1:y2, x1:x2] + alpha * overlay_rgb
    return img

# ---------- Detect wound (red color) ----------
hsv = cv2.cvtColor(arm_img, cv2.COLOR_RGB2HSV)

lower_red1 = np.array([0, 70, 50])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([170, 70, 50])
upper_red2 = np.array([180, 255, 255])

mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
mask = mask1 | mask2

kernel = np.ones((5, 5), np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel)

contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

result = orig.copy()

if len(contours) == 0:
    print("⚠️ No wound detected! Placing band-aid in center for demo.")
    cx, cy = orig.shape[1] // 2, orig.shape[0] // 2
    w, h, angle = 100, 50, 0
else:
    cnt = max(contours, key=cv2.contourArea)
    (cx, cy), (w, h), angle = cv2.minAreaRect(cnt)
    cx, cy = int(cx), int(cy)

# ---------- Resize bandaid ----------
scale_w = int(max(w, h) * 2)
scale_h = int(scale_w * bandaid.shape[0] / bandaid.shape[1])
scale_w = max(scale_w, 50)
scale_h = max(scale_h, 25)

bandaid_resized = cv2.resize(bandaid, (scale_w, scale_h))

# ---------- Rotate (KEEP alpha channel) ----------
center = (scale_w // 2, scale_h // 2)
rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)

bandaid_rot = cv2.warpAffine(
    bandaid_resized,
    rot_mat,
    (scale_w, scale_h),
    flags=cv2.INTER_LINEAR,
    borderMode=cv2.BORDER_CONSTANT,
    borderValue=(0, 0, 0, 0)
)

# ---------- Overlay ----------
x = int(cx - scale_w // 2)
y = int(cy - scale_h // 2)

result = overlay_image_alpha(result, bandaid_rot, x, y)

# ---------- Show results ----------
plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
plt.title("Original")
plt.imshow(orig)
plt.axis("off")

plt.subplot(1, 2, 2)
plt.title("With Band-Aid")
plt.imshow(result)
plt.axis("off")

plt.tight_layout()
plt.show()
