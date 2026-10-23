# Lenticular 2

**Lenticular 2: Physically Accurate Lenticular Optical Calculation, Prepress Interlacing, and Multi-View Synthesis Engine**

---

## 🎯 What is Lenticular 2?

Lenticular 2 is an end-to-end, high-performance lenticular engineering engine designed specifically for large format and direct-to-substrate UV flatbed printing, cold lamination, and digital 3D creation.

It resolves all 10 critical optical, mathematical, and pipeline bugs found in traditional lenticular software skeletons:
1. **Mathematically Correct ZPP Direction**:
   - `front` mode (pop-out towards viewer): $d(x,y) > 0 \implies \text{ZPP} < \rho_{\text{subject}}$ ($\rho_0 = \rho_s - 0.15$). The subject physically pops out in front of the lens.
   - `behind` mode (sink-in behind print surface): $d(x,y) < 0 \implies \text{ZPP} > \rho_{\text{subject}}$ ($\rho_0 = \rho_s + 0.15$).
2. **Registration & Skew Pass-Through**:
   - Unified phase equation along true lens normal: $\vec{r} \cdot \hat{n} - \delta_{\text{reg}}$.
   - Supports vertical lenticules, horizontal lenticules (flip/motion), and arbitrary skew angles without loss of phase alignment.
3. **Safe Whole-Pixel Default for CMYK Flatbeds**:
   - `use_subpixel_interlacing = False` default prevents CMYK droplet color separation and ghosting.
4. **Unified View Count Feasibility**:
   - Synchronized view selection between `ParallaxCalculator` and summary reports.
   - First-class support for both even and odd view counts (PRIVATE_AMOUNT^\circ$ optical center).
5. **Strict Effect Parameter Validation**:
   - Prevents silent fallbacks; throws clear errors on invalid presets.
6. **Zero-Trap Depth Normalization**:
   - Removed destructive border/center auto-inversion heuristics.
7. **Vectorized C++ DIBR Rendering**:
   - Replaced slow row-by-row Python loops with `cv2.remap` and Telea inpainting, rendering 2K views in milliseconds.
8. **Native Float32 Depth Filtering**:
   - High-precision float32 bilateral filtering and robust box-filter guided filtering without 8-bit quantization steps.
9. **Clean Pitch Test Patterns**:
   - Dedicated header margin preventing band 0 corruption.
   - Pixel-center phase calculations `(x + 0.5) / p`.
   - Multi-tier calibration (coarse & fine down to 0.001 LPI) and tilt verification rails.
10. **Robust Image Loading**:
    - Universal channel handling (2D grayscale, 3-channel RGB, 4-channel RGBA, 16-bit TIFF).

---

## 🚀 Quick Usage

### CLI Commands
```powershell
# 1. Generate Optical Pitch Test Pattern
python -m lenticular2.cli pitch-test --lpi 60.0 --ppi 720 --dist 400 --output pitch_60.png

# 2. Analyze Scene & Detect Optimal Angles & ZPP
python -m lenticular2.cli analyze --image photo.png --depth depth.png --lpi 60.0 --ppi 720

# 3. Complete End-to-End Production
python -m lenticular2.cli render --image photo.png --depth depth.png --lens "60 LPI Standard 3D" --width 150 --height 100 --strength balanced
```
