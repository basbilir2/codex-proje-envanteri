"""Explicit print sampling budgets. These are geometric diagnostics, not lens measurements."""
import math

import numpy as np


def sampling_budget(settings):
    p = settings
    axis_mm = p['width_mm'] if p['axis'] == 'vertical' else p['height_mm']
    lenses = axis_mm * p['effective_lpi'] / 25.4
    per_lens = p['ppi'] / p['effective_lpi']
    channels = p['ne']
    return dict(
        lenticules_across_motion_axis=lenses,
        pixels_per_channel=per_lens/channels,
        raster_channel_ceiling=min(64, math.floor(per_lens)),
        two_pixel_channel_start=min(64, math.floor(per_lens/2)),
        # An accumulated quarter-channel drift, not a universal acceptance limit.
        quarter_channel_pitch_error_lpi=25.4/(4*channels*axis_mm),
        quarter_channel_scale_error_percent=100/(4*channels*lenses),
        nominal_to_effective_drift_channels=(p['effective_lpi']-p['nominal_lpi'])*axis_mm/25.4*channels,
        physical_channel_capacity=None,
        basis='Raster arithmetic and quarter-channel drift sensitivity; usable optical capacity requires a printed test.')


def depth_sampling(depth, config, size, settings, indices):
    """Use the selected cameras, not Nr, for print angular-sampling risk."""
    width, height = size
    scale_mm = (max if settings['fit'] == 'cover' else min)(
        settings['width_mm']/width, settings['height_mm']/height)
    focal = width * config.get('focal_mm', 50) / config.get('sensor_width_mm', 36)
    positions = np.asarray(config['positions'], dtype=np.float64)
    inverse_depth = (1-depth)/config['far'] + depth/config['near']
    coefficient = focal*(1/config['zero']-inverse_depth)
    endpoint = coefficient*(positions.max()-positions.min())*scale_mm
    if settings['reverse_views']:
        endpoint = -endpoint
    selected = positions[indices]
    largest_step = float(np.max(np.abs(np.diff(selected))))
    step_lenses = np.abs(coefficient)*largest_step*scale_mm*settings['effective_lpi']/25.4
    sides = {}
    for name, mask in (('front', endpoint < -1e-6), ('back', endpoint > 1e-6)):
        values = np.abs(endpoint[mask])
        sides[name] = dict(pixel_fraction=float(mask.mean()),
            max_endpoint_mm=float(values.max()) if values.size else 0.,
            internal_relief_p10_p90_mm=float(np.ptp(np.quantile(values, [.1, .9]))) if values.size else 0.,
            adjacent_step_lenticules_p95=float(np.quantile(step_lenses[mask], .95)) if values.size else 0.)
    warnings = []
    for name, label in (('front', 'Ön'), ('back', 'Arka')):
        side = sides[name]
        if side['pixel_fraction'] > .05 and side['max_endpoint_mm'] > .01 and side['internal_relief_p10_p90_mm'] < .1*side['max_endpoint_mm']:
            warnings.append(f'{label} bölge baskı düzleminden ayrılıyor fakat kendi iç hacmi zayıf; genel açıyı artırmak yerine derinlik haritasındaki yüzey ayrıntısını düzeltin.')
    if float(np.quantile(step_lenses, .95)) > 1:
        warnings.append('Seçilen baskı kanalları arasında görüntü adımı bir lens aralığını aşıyor (p95). Geçiş/netlik riski: yalnız Nr artırmak yetmez; Ne, ön/arka paralaks ve gerçek kanal ayrımını birlikte değerlendirin.')
    return dict(sides=sides, largest_selected_camera_step=largest_step,
        adjacent_step_lenticules_p95=float(np.quantile(step_lenses, .95)),
        adjacent_step_lenticules_max=float(step_lenses.max()),
        over_one_lenticule_fraction=float(np.mean(step_lenses > 1)),
        warnings=warnings, physical_depth_verified=False,
        basis='Depth-derived camera disparity scaled to print and selected Ne channels. One-lenticule threshold is a diagnostic heuristic, not an optical pass/fail standard.'), step_lenses


PITCH_FIELDS = ('ppi','printer_dpi','nominal_lpi','effective_lpi','axis','tilt_deg',
    'mirror','phase','width_mm','height_mm','bleed_mm','viewing_distance_mm','icc_path','color_mode','white_underbase','stripe_sampling')
RASTER_FIELDS = ('ppi','printer_dpi','axis','tilt_deg','icc_path','color_mode','white_underbase')
ANGLE_FIELDS = ('nominal_lpi','lens_view_angle_deg')
MATRIX_FIELDS = tuple(dict.fromkeys(PITCH_FIELDS + ('ne','lens_view_angle_deg')))


def invalidate_calibration(old, new):
    """Invalidate inherited evidence only; do not manufacture new measurement data."""
    result, cleared = dict(new), []
    for flag, fields in (('pitch_verified', PITCH_FIELDS), ('raster_ppi_verified', RASTER_FIELDS),
                         ('lens_angle_verified', ANGLE_FIELDS)):
        if old.get(flag) and result.get(flag) and any(old.get(k) != new.get(k) for k in fields):
            result[flag] = False
            cleared.append(flag)
    if old.get('crosstalk_matrix') is not None and old.get('crosstalk_matrix') == new.get('crosstalk_matrix') and any(old.get(k) != new.get(k) for k in MATRIX_FIELDS):
        result['crosstalk_matrix'] = None
        # Avoid silently substituting a hypothetical model at the old correction strength.
        result['compensation'] = 0.
        cleared.append('crosstalk_matrix')
    return result, cleared
