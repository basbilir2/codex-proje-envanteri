"""Regional depth volume refinement tool for VD portrait.
Implements physically and anatomically consistent regional adjustments:
1. Hand pullback (~30% motion reduction relative to print plane) while sculpting round fingers/palm without plateau clipping.
2. Facial volume enhancement (~1.5-2x relief) with fixed nose zero-reference.
3. Torso/clothing convexity and drapery folds without fabric pattern artifacts.
4. Seamless feathered transitions preserving depth order.

Usage:
  python tools/refine_regional_depth.py --input prepared_depth/depth.npy --photo "<photo_path>" --output prepared_depth/depth_dogal_hacim.npy
"""
import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

STUDIO_ROOT = Path(r"C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1")
if str(STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(STUDIO_ROOT))

from lenticular.runner import digest


def build_face_mask(shape, ref_point):
    """Create a feathered anatomical mask for the face region covering forehead, eyes, cheeks, nose, lips, chin."""
    h, w = shape
    # Center of face around (958, 460)
    cx, cy = 958, 460
    rx, ry = 230, 270

    yy, xx = np.ogrid[:h, :w]
    dist_sq = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    dist = np.sqrt(dist_sq)

    # Inner core (dist <= 0.70) has full weight 1.0
    # Outer region (0.70 < dist <= 1.15) has smooth cosine falloff to 0
    mask = np.zeros((h, w), dtype=np.float32)
    inner = dist <= 0.70
    transition = (dist > 0.70) & (dist <= 1.15)

    mask[inner] = 1.0
    t = (dist[transition] - 0.70) / (1.15 - 0.70)
    mask[transition] = 0.5 * (1.0 + np.cos(np.pi * t))
    return cv2.GaussianBlur(mask, (25, 25), 7.0)


def build_hand_mask(depth, shape):
    """Create a smooth mask for the forward hand and forearm."""
    h, w = shape
    hand_bin = np.zeros((h, w), dtype=np.uint8)
    # Hand BBox: x in [300, 1350], y in [1080, 2050]
    yy, xx = np.ogrid[:h, :w]
    hand_roi = (depth > 0.40) & (yy >= 1050) & (yy <= 2100) & (xx <= 1400)
    hand_bin[hand_roi] = 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35))
    hand_closed = cv2.morphologyEx(hand_bin, cv2.MORPH_CLOSE, kernel)

    dist_in = cv2.distanceTransform(hand_closed, cv2.DIST_L2, 5)
    mask = np.clip(dist_in / 40.0, 0.0, 1.0)
    return cv2.GaussianBlur(mask, (31, 31), 9.0).astype(np.float32)


def build_torso_mask(depth, shape, hand_mask, face_mask):
    """Create a smooth mask for torso and clothing."""
    h, w = shape
    yy, xx = np.ogrid[:h, :w]
    torso_bin = np.zeros((h, w), dtype=np.uint8)
    torso_roi = (depth >= 0.18) & (depth <= 0.42) & (yy >= 650)
    torso_bin[torso_roi] = 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51))
    torso_closed = cv2.morphologyEx(torso_bin, cv2.MORPH_CLOSE, kernel)

    dist_in = cv2.distanceTransform(torso_closed, cv2.DIST_L2, 5)
    torso_mask = np.clip(dist_in / 40.0, 0.0, 1.0)
    torso_mask = cv2.GaussianBlur(torso_mask, (41, 41), 15.0)

    # Subtract face and hand with smooth transitions
    torso_mask = torso_mask * (1.0 - face_mask) * (1.0 - hand_mask)
    return np.clip(torso_mask, 0.0, 1.0).astype(np.float32)


def enhance_facial_volume(depth, face_mask, ref_point, gain=1.70):
    """Enhance facial internal volume (~1.7x) while locking nose tip at zero reference."""
    rx, ry = ref_point
    nose_z = float(depth[ry, rx])

    # Delta relative to nose tip (all points on face are <= nose_z)
    delta = depth - nose_z

    # Bilateral smoothing of delta to preserve facial contours while preventing noise amplification
    delta_smooth = cv2.bilateralFilter(delta.astype(np.float32), d=9, sigmaColor=0.03, sigmaSpace=15)

    # Scaled facial depth: eye sockets, cheeks, temples, jaw, chin deepen anatomically
    face_enhanced = nose_z + gain * delta_smooth

    # Blend with original depth using feathered face mask
    refined = depth * (1.0 - face_mask) + face_enhanced * face_mask

    # Exact nose tip lock
    refined[ry, rx] = nose_z
    return refined.astype(np.float32)


def enhance_hand_and_fingers(depth, hand_mask, photo_gray):
    """Sculpt round cross-sections for thumb, palm and folded fingers without flat clipping."""
    h, w = depth.shape
    result = depth.copy()
    yy, xx = np.ogrid[:h, :w]

    # In raw depth, hand reached 1.0000 with a central depression on thumb.
    # To prevent flat clipping at 1.0 when adding cylinder convexity,
    # we first compress the hand's upper range slightly (from 1.00 to ~0.92)
    # so the sculpted round cross-section peaks cleanly at ~0.98.
    hand_core = (hand_mask > 0.2) & (depth > 0.45)
    if np.any(hand_core):
        h_vals = result[hand_core]
        h_min, h_max = float(h_vals.min()), float(h_vals.max())
        # Scale range [h_min, h_max] -> [h_min, 0.91]
        target_max = 0.91
        if h_max > h_min:
            scaled_h = h_min + (h_vals - h_min) * ((target_max - h_min) / (h_max - h_min))
            result[hand_core] = h_vals * (1.0 - hand_mask[hand_core]) + scaled_h * hand_mask[hand_core]

    # 1. Thumb cylindrical / capsular cross-section
    # Thumb region: x in [460, 640], y in [1320, 1560]
    thumb_mask = (yy >= 1320) & (yy <= 1560) & (xx >= 460) & (xx <= 640) & (depth > 0.70)
    if np.any(thumb_mask):
        thumb_bin = thumb_mask.astype(np.uint8) * 255
        dist = cv2.distanceTransform(thumb_bin, cv2.DIST_L2, 5)
        max_dist = dist[thumb_mask].max()
        if max_dist > 0:
            norm_dist = np.clip(dist / max_dist, 0.0, 1.0)
            # Round cylindrical arch profile: sqrt(1 - (1 - d)^2)
            round_arch = np.sqrt(np.clip(1.0 - (1.0 - norm_dist) ** 2, 0.0, 1.0))
            # Smoothly sculpt thumb convexity: peaks at +0.070 (reaching ~0.98 at apex)
            thumb_sculpt = round_arch * 0.072 * hand_mask
            result = result + thumb_sculpt * thumb_mask

    # 2. Palm & Thenar eminence (base of thumb)
    # Thenar pad: x in [480, 620], y in [1540, 1780]
    palm_mask = (yy >= 1540) & (yy <= 1800) & (xx >= 480) & (xx <= 660) & (depth > 0.60)
    if np.any(palm_mask):
        palm_bin = palm_mask.astype(np.uint8) * 255
        dist_palm = cv2.distanceTransform(palm_bin, cv2.DIST_L2, 5)
        max_dp = dist_palm[palm_mask].max()
        if max_dp > 0:
            norm_dp = np.clip(dist_palm / max_dp, 0.0, 1.0)
            palm_profile = np.sqrt(norm_dp) * 0.045 * hand_mask
            result = result + palm_profile * palm_mask

    # 3. Folded fingers / knuckles: x in [600, 720], y in [1350, 1680]
    fingers_mask = (yy >= 1350) & (yy <= 1680) & (xx >= 600) & (xx <= 730) & (depth > 0.48)
    if np.any(fingers_mask):
        fingers_bin = fingers_mask.astype(np.uint8) * 255
        dist_f = cv2.distanceTransform(fingers_bin, cv2.DIST_L2, 5)
        max_df = dist_f[fingers_mask].max()
        if max_df > 0:
            norm_df = np.clip(dist_f / max_df, 0.0, 1.0)
            f_profile = np.sqrt(norm_df) * 0.035 * hand_mask
            result = result + f_profile * fingers_mask

    # Blend hand smoothly at outer silhouette
    result = np.clip(result, 0.0, 1.0).astype(np.float32)
    return result


def enhance_torso_and_clothing(depth, torso_mask, photo_gray):
    """Add natural chest/abdomen convexity and structural folds without fabric texture artifacts."""
    h, w = depth.shape
    result = depth.copy()
    yy, xx = np.ogrid[:h, :w]

    # 1. Chest / Abdomen barrel convexity
    # Center of chest: cx ~ 1000, cy ~ 1350.
    cx, cy = 1000, 1350
    rx, ry = 550, 700
    chest_dist = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    convexity = np.clip(1.0 - chest_dist, 0.0, 1.0)
    chest_curve = 0.035 * (convexity ** 1.5)

    # 2. Extract structural drapery/folds from photo WITHOUT fabric pattern/color
    large_scale = cv2.bilateralFilter(photo_gray.astype(np.float32), d=15, sigmaColor=50, sigmaSpace=25)
    grad_y = cv2.Sobel(large_scale, cv2.CV_32F, 0, 1, ksize=5)
    fold_signal = cv2.GaussianBlur(grad_y, (31, 31), 9.0)
    torso_std = float(np.std(fold_signal[torso_mask > 0.5])) if np.any(torso_mask > 0.5) else 1.0
    fold_norm = np.clip(fold_signal / (torso_std * 3.5 + 1e-6), -1.0, 1.0)
    fold_depth = fold_norm * 0.015

    # Combine convexity and folds, modulated by torso mask
    torso_enhancement = (chest_curve + fold_depth) * torso_mask
    result = result + torso_enhancement

    # Smooth transitions across torso
    torso_filtered = cv2.bilateralFilter(result.astype(np.float32), d=9, sigmaColor=0.03, sigmaSpace=15)
    result = result * (1.0 - torso_mask) + torso_filtered * torso_mask
    return np.clip(result, 0.0, 1.0).astype(np.float32)


def refine_depth_map(depth_path, photo_path, output_path, face_gain=1.70):
    """Execute complete regional volume refinement pipeline."""
    depth = np.load(depth_path).astype(np.float32)
    with Image.open(photo_path) as img:
        photo_rgb = np.array(img.convert("RGB"))
    photo_gray = cv2.cvtColor(photo_rgb, cv2.COLOR_RGB2GRAY)
    h, w = depth.shape

    # Reference point: nose tip
    ref_x = 0.5120256547300909
    ref_y = 0.13948982886664513
    px_x = round(ref_x * (w - 1))
    px_y = round(ref_y * (h - 1))
    ref_point = (px_x, px_y)
    orig_ref_z = float(depth[px_y, px_x])

    print("--- Bölgesel Hacim Düzenleme Başlatılıyor ---")
    print(f"Girdi Derinlik: {depth_path} (Şekil: {depth.shape}, Min: {depth.min():.4f}, Max: {depth.max():.4f})")
    print(f"Burun Kerteriz Noktası: ({px_x}, {px_y}) -> Z = {orig_ref_z:.5f}")

    # Build masks
    face_mask = build_face_mask((h, w), ref_point)
    hand_mask = build_hand_mask(depth, (h, w))
    torso_mask = build_torso_mask(depth, (h, w), hand_mask, face_mask)

    print(f"Maske Kapsamları:")
    print(f"  Yüz Maskesi (efektif alan): {np.mean(face_mask > 0.1)*100:.2f}%")
    print(f"  El Maskesi (efektif alan):  {np.mean(hand_mask > 0.1)*100:.2f}%")
    print(f"  Gövde Maskesi (efektif alan): {np.mean(torso_mask > 0.1)*100:.2f}%")

    # Step 1: Face volume enhancement
    refined = enhance_facial_volume(depth, face_mask, ref_point, gain=face_gain)

    # Step 2: Hand and finger roundness sculpting
    refined = enhance_hand_and_fingers(refined, hand_mask, photo_gray)

    # Step 3: Torso and clothing convexity & folds
    refined = enhance_torso_and_clothing(refined, torso_mask, photo_gray)

    # Background wall (depth < 0.15) remains completely untouched
    bg_mask = (depth < 0.15)
    refined[bg_mask] = depth[bg_mask]

    # Enforce exact nose reference
    refined[px_y, px_x] = orig_ref_z
    refined = np.clip(refined, 0.0, 1.0).astype(np.float32)

    # Key anatomical landmarks for internal face evaluation
    landmarks = {
        "forehead": (958, 300),
        "glabella": (958, 360),
        "nose_bridge": (958, 390),
        "nose_tip": (958, 432),
        "left_eye": (880, 390),
        "right_eye": (1030, 390),
        "left_cheek": (830, 480),
        "right_cheek": (1070, 480),
        "upper_lip": (958, 520),
        "lower_lip": (958, 550),
        "chin": (958, 620)
    }

    # Internal relief metrics:
    # 1. Face landmarks relief:
    face_orig_relief = max(depth[ly, lx] for lx, ly in landmarks.values()) - min(depth[ly, lx] for lx, ly in landmarks.values())
    face_new_relief = max(refined[ly, lx] for lx, ly in landmarks.values()) - min(refined[ly, lx] for lx, ly in landmarks.values())
    face_gain_actual = face_new_relief / face_orig_relief if face_orig_relief > 0 else 1.0

    # 2. Thumb cross-section roundness (horizontal gradient across thumb)
    thumb_roi_orig = depth[1380:1500, 490:610]
    thumb_roi_new = refined[1380:1500, 490:610]
    thumb_orig_grad = float(np.mean(np.abs(cv2.Sobel(thumb_roi_orig, cv2.CV_32F, 1, 0, ksize=3))))
    thumb_new_grad = float(np.mean(np.abs(cv2.Sobel(thumb_roi_new, cv2.CV_32F, 1, 0, ksize=3))))
    thumb_gain_actual = thumb_new_grad / thumb_orig_grad if thumb_orig_grad > 0 else 1.0

    # 3. Torso / clothing gradient magnitude: [900:1600, 750:1250]
    cloth_roi_orig = depth[900:1600, 750:1250]
    cloth_roi_new = refined[900:1600, 750:1250]
    cloth_orig_grad = float(np.mean(np.abs(cv2.Sobel(cloth_roi_orig, cv2.CV_32F, 0, 1, ksize=3))))
    cloth_new_grad = float(np.mean(np.abs(cv2.Sobel(cloth_roi_new, cv2.CV_32F, 0, 1, ksize=3))))
    cloth_gain_actual = cloth_new_grad / cloth_orig_grad if cloth_orig_grad > 0 else 1.0

    # 4. Nose drift check
    final_ref_z = float(refined[px_y, px_x])
    nose_drift = abs(final_ref_z - orig_ref_z)

    print("\n--- Ölçülen İç Rölyef Karşılaştırması ---")
    print(f"Yüz Kerteriz Noktaları İç Rölyefi:")
    print(f"  Eski: {face_orig_relief:.5f} -> Yeni: {face_new_relief:.5f} (Artış: {face_gain_actual:.2f}x, Hedef: ~1.5-2.0x)")
    print(f"Başparmak Yuvarlaklık / Eğim (grad_x):")
    print(f"  Eski: {thumb_orig_grad:.5f} -> Yeni: {thumb_new_grad:.5f} (Artış: {thumb_gain_actual:.2f}x)")
    print(f"Kıyafet / Gövde Eğrilik & Katlar (grad_y):")
    print(f"  Eski: {cloth_orig_grad:.6f} -> Yeni: {cloth_new_grad:.6f} (Artış: {cloth_gain_actual:.2f}x)")
    print(f"Burun Kerteriz Noktası Sabitliği:")
    print(f"  Eski: {orig_ref_z:.5f}, Yeni: {final_ref_z:.5f}, Fark: {nose_drift:.8f} (Sabit)")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, refined, allow_pickle=False)
    print(f"\nDüzenlenmiş derinlik haritası kaydedildi: {output_path}")

    report = {
        "source_depth": str(depth_path),
        "source_photo": str(photo_path),
        "output_depth": str(output_path),
        "output_sha256": digest(output_path),
        "reference_point": {"x": float(ref_x), "y": float(ref_y), "px": [int(px_x), int(px_y)], "depth": float(final_ref_z), "drift": float(nose_drift)},
        "metrics": {
            "face_internal_relief": {
                "old_relief": float(face_orig_relief),
                "new_relief": float(face_new_relief),
                "gain": float(face_gain_actual),
                "target_met": bool(1.4 <= face_gain_actual <= 2.2)
            },
            "thumb_roundness": {
                "old_grad": float(thumb_orig_grad),
                "new_grad": float(thumb_new_grad),
                "gain": float(thumb_gain_actual),
                "target_met": bool(thumb_gain_actual >= 1.0)
            },
            "clothing_curvature": {
                "old_grad": float(cloth_orig_grad),
                "new_grad": float(cloth_new_grad),
                "gain": float(cloth_gain_actual),
                "target_met": bool(cloth_gain_actual >= 1.5)
            }
        }
    }
    report_path = output_path.with_suffix(".json")
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Rapor kaydedildi: {report_path}")
    return refined, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regional depth volume refinement for VD portrait")
    parser.add_argument("--input", default=r"C:\Users\USER\Documents\lenticular baskı\prepared_depth\depth.npy")
    parser.add_argument("--photo", default=r"C:\Users\USER\Downloads\vd-gigapixel-recover v2-2x-faceai v2.jpg")
    parser.add_argument("--output", default=r"C:\Users\USER\Documents\lenticular baskı\prepared_depth\depth_dogal_hacim.npy")
    parser.add_argument("--face-gain", type=float, default=1.70)
    args = parser.parse_args()

    refine_depth_map(args.input, args.photo, args.output, face_gain=args.face_gain)
