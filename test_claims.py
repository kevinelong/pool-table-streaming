"""Guard the numbers the bill of materials rests on.

A research repository has no program to test, so this checks its *claims*: it
recomputes the field-of-view table and the derived thresholds from the stated
geometry, then requires every published copy of a figure to agree with the
arithmetic. The point is that the number Kevin is about to spend money against
cannot move in an edit without turning this red.

Inputs, as stated in NOTES.md section 2: a 78 x 39 in playing surface, a
1/2.8" 16:9 sensor (5.58 mm active width), a 3.95 mm stock lens, and a camera
height h above the cloth.

    HFOV = 2*atan(39/h)   VFOV = 2*atan(19.5/h)
    DFOV = 2*atan(sqrt(tan^2(HFOV/2) + tan^2(VFOV/2)))
    lens_f = (sensor_width/2) / tan(HFOV/2)

Run from the repository root:

    python3 test_claims.py

Standard library only, no dependencies.
"""
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
NOTES = (ROOT / 'NOTES.md').read_text(encoding='utf-8')
README = (ROOT / 'README.md').read_text(encoding='utf-8')

LENGTH_IN = 78.0            # playing surface, along the table
WIDTH_IN = 39.0             # playing surface, across the table
SENSOR_W_MM = 5.58          # 1/2.8" 16:9 active width
STOCK_F_MM = 3.95
FISHEYE_F_MM = 2.2
FISHEYE_HFOV = 121.0        # the lens's own spec; a fisheye, so not f = w/(2 tan(H/2))


def hfov(h):
    """Horizontal field of view needed to span the 78 in length from height h."""
    return 2 * math.degrees(math.atan((LENGTH_IN / 2) / h))


def vfov(h):
    """Vertical field of view needed to span the 39 in width from height h."""
    return 2 * math.degrees(math.atan((WIDTH_IN / 2) / h))


def dfov(h):
    """Diagonal field of view: the sensor diagonal from the two tangent ratios."""
    return 2 * math.degrees(math.atan(math.hypot(
        math.tan(math.radians(hfov(h) / 2)),
        math.tan(math.radians(vfov(h) / 2)))))


def lens_f(h):
    """The focal length a rectilinear lens needs on this sensor at height h."""
    return (SENSOR_W_MM / 2) / math.tan(math.radians(hfov(h) / 2))


def rectilinear_hfov(f_mm):
    return 2 * math.degrees(math.atan((SENSOR_W_MM / 2) / f_mm))


STOCK_HFOV = rectilinear_hfov(STOCK_F_MM)
COVERED_PER_INCH = 2 * math.tan(math.radians(STOCK_HFOV / 2))
COVERS_78_AT = LENGTH_IN / COVERED_PER_INCH
COVERS_78_MARGIN_AT = (LENGTH_IN * 1.1) / COVERED_PER_INCH
FISHEYE_COVERS = 2 * 34 * math.tan(math.radians(FISHEYE_HFOV / 2))


def decimals(text):
    """Digits after the point, i.e. the precision a published figure claims."""
    return len(text.split('.')[1]) if '.' in text else 0


def close(claimed, computed, n_dec):
    """True when `claimed` is `computed` correctly rounded to n_dec places."""
    return abs(claimed - computed) <= 0.5 * 10 ** -n_dec + 1e-9


def matching(pattern):
    """Every string captured by `pattern` in NOTES.md."""
    return re.findall(pattern, NOTES)


def table_rows():
    """The height rows of the FOV table in NOTES.md section 2."""
    rows = []
    for line in NOTES.splitlines():
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) != 5:
            continue
        height = re.match(r'^\**\s*(\d+)(?:\s*\([^)]*\))?\s*\**$', cells[0])
        numbers = [re.search(r'~?\**\s*(\d+(?:\.\d+)?)', c) for c in cells[1:]]
        if height and all(numbers):
            rows.append((int(height.group(1)), cells[1:], [n.group(1) for n in numbers]))
    return rows


def assert_all_equal(pattern, computed, what):
    """Every published occurrence must equal the arithmetic; there must be one."""
    found = matching(pattern)
    assert(found), 'NOTES.md no longer states %s' % what
    for text in found:
        assert(close(float(text), computed, decimals(text))), \
            'NOTES.md states %s for %s; the geometry gives %.4f' % (text, what, computed)
    return found


ROWS = table_rows()
assert(len(ROWS) == 7), 'NOTES.md section 2 should carry seven height rows, found %d' % len(ROWS)

# 1. Every cell of the published table must equal the arithmetic, at the precision
#    it claims. This is the guard that would have caught the five wrong cells.
for height, cells, numbers in ROWS:
    for cell, number, value in zip(cells, numbers, (hfov(height), vfov(height),
                                                    dfov(height), lens_f(height))):
        assert(close(float(number), value, decimals(number))), \
            'NOTES.md %d in says %s in the %s column but the geometry gives %.4f' % (
                height, number, cell.split()[0], value)

# 2. The binding numbers and the docs that state them.
assert(close(97.84, hfov(34), 2)), 'HFOV at 34 in moved: %.4f' % hfov(34)
assert(close(59.67, vfov(34), 2)), 'VFOV at 34 in moved: %.4f' % vfov(34)
assert(close(104.1, dfov(34), 1)), 'DFOV at 34 in moved: %.4f' % dfov(34)
assert(close(2.43, lens_f(34), 2)), 'lens at 34 in moved: %.4f' % lens_f(34)
assert('97.8' in NOTES and '104.1' in NOTES), \
    'the 34 in HFOV/DFOV figures are missing from NOTES.md'
assert('97.8' in README or '98 deg' in README), \
    'the README no longer states the ~98 deg horizontal requirement'
assert('2.2 mm M12 fisheye' in README and '55 in or' in README), \
    'the README no longer offers both ways out (fisheye, or mount at 55 in)'

# 3. The stock lens: coverage per inch of height and the two thresholds it implies.
assert(close(70.47, STOCK_HFOV, 2)), 'stock lens HFOV moved: %.4f' % STOCK_HFOV
assert(close(1.4127, COVERED_PER_INCH, 4)), 'coverage per inch moved: %.4f' % COVERED_PER_INCH
assert(close(55.2, COVERS_78_AT, 1)), 'h covering 78 in moved: %.4f' % COVERS_78_AT
assert(close(60.7, COVERS_78_MARGIN_AT, 1)), \
    'h covering 78 in with 10% margin moved: %.4f' % COVERS_78_MARGIN_AT
assert_all_equal(r'([\d.]+) in (?:of table covered )?per inch', COVERED_PER_INCH,
                 'the coverage per inch of height')
thresholds = matching(r'h >= ([\d.]+) in')
assert(thresholds), 'NOTES.md no longer states the height thresholds'
for text in thresholds:
    assert(close(float(text), COVERS_78_AT, decimals(text))
           or close(float(text), COVERS_78_MARGIN_AT, decimals(text))), \
        'NOTES.md states h >= %s in, which is neither the 78 in threshold (%.1f) ' \
        'nor the 10%% margin (%.1f)' % (text, COVERS_78_AT, COVERS_78_MARGIN_AT)
assert(any(close(float(t), COVERS_78_AT, decimals(t)) for t in thresholds)), \
    'NOTES.md no longer states h >= %.1f in' % COVERS_78_AT
assert(any(close(float(t), COVERS_78_MARGIN_AT, decimals(t)) for t in thresholds)), \
    'NOTES.md no longer states the 10%% margin threshold (h >= %.1f in)' % COVERS_78_MARGIN_AT

# 4. Superseded figures must not come back. Each of these was published here and is
#    wrong; a guard that only checked presence could let them return.
for stale, why in (('1.4122', 'the pre-audit coverage-per-inch figure'),
                   ('60.9', 'the pre-audit 10% margin threshold'),
                   ('105.5', 'the DFOV computed in angle space, not from the tangents'),
                   ('128 deg', 'the bad h=26 DFOV'),
                   ('49.1', 'the bad h=48 VFOV'),
                   ('2.57 mm', 'the truncated h=36 lens')):
    assert(stale not in NOTES), 'NOTES.md carries %s again: %s' % (why, stale)

# 5. The fisheye: what it covers if it delivers its spec, and what a rectilinear
#    lens of the same focal length would give - the reason its spec is load-bearing.
spec = re.search(r'~([\d.]+) deg H', NOTES)
assert(spec), 'NOTES.md no longer quotes the fisheye spec (~121 deg H)'
assert(close(float(spec.group(1)), FISHEYE_HFOV, 0)), \
    'the quoted fisheye spec moved: %s deg H' % spec.group(1)
assert(close(120, FISHEYE_COVERS, 0)), 'fisheye coverage moved: %.2f in' % FISHEYE_COVERS
assert('~120 in' in NOTES and '154%' in NOTES), \
    'NOTES.md no longer carries the fisheye coverage and its share of the table'
assert(close(103, rectilinear_hfov(FISHEYE_F_MM), 0)), \
    'the rectilinear comparison moved: %.2f deg' % rectilinear_hfov(FISHEYE_F_MM)
assert('~103 deg H' in NOTES), \
    'NOTES.md no longer says what a rectilinear lens of that focal length would give'
assert(close(109.6, 2 * 31 * math.tan(math.radians(FISHEYE_HFOV / 2)), 1)), \
    'the fisheye covers %.1f in at 31 in' % (2 * 31 * math.tan(math.radians(FISHEYE_HFOV / 2)))
assert('109.6 in at 31 in' in NOTES), \
    'NOTES.md no longer states the fisheye coverage at the low end of the light heights'

# 6. The decision packet (NOTES.md section 0) carries its own arithmetic: the
#    staged subtotals, the two totals, the mains variant, and the power figures
#    that pick the bank. Same treatment: recompute, then compare with what is
#    published, so a price or a runtime cannot drift quietly.
def boms():
    """The priced rows of the section 5 BOM, in order."""
    prices = []
    for line in NOTES.splitlines():
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) == 4 and re.match(r'^\d+$', cells[0]):
            price = re.search(r'\$([\d.]+)', cells[3])
            if price:
                prices.append(float(price.group(1)))
    return prices


BOM = boms()
assert(len(BOM) == 4), 'section 5 should list four priced BOM items, found %d' % len(BOM)
BOARD, CAMERA, LENS_PRICE, BANK = BOM

# The direct-store prices the packet's "direct" column is built from must be in
# the section 5 source table, so the column is not invented in section 0.
SPARES = []
for line in NOTES.splitlines():
    if not line.startswith('|'):
        continue
    cells = [c.strip() for c in line.strip('|').split('|')]
    if len(cells) == 3 and 'direct' in cells[1]:
        for price in re.findall(r'\$([\d.]+)', cells[2]):
            SPARES.append(float(price))
for needed in (50.99, 8.99):
    assert(needed in SPARES), \
        'the direct price $%.2f is not in the section 5 source list %s' % (needed, SPARES)
BOARD_DIRECT, CAMERA_DIRECT = 50.99, 8.99

STAGE1_AMAZON = BOARD + CAMERA
STAGE1_DIRECT = BOARD_DIRECT + CAMERA_DIRECT
assert(close(78.38, STAGE1_AMAZON, 2)), 'stage 1 (Amazon) is $%.2f' % STAGE1_AMAZON
assert(close(59.98, STAGE1_DIRECT, 2)), 'stage 1 (direct) is $%.2f' % STAGE1_DIRECT
assert(close(199.38, sum(BOM), 2)), 'the itemised DIY total is $%.2f' % sum(BOM)
assert(close(180.98, STAGE1_DIRECT + LENS_PRICE + BANK, 2)), \
    'the direct-priced DIY total is $%.2f' % (STAGE1_DIRECT + LENS_PRICE + BANK)
assert(close(125.38, STAGE1_AMAZON + LENS_PRICE, 2)), \
    'the mains-fed DIY total is $%.2f' % (STAGE1_AMAZON + LENS_PRICE)
for published in ('$78.38', '$59.98', '$199.38', '$180.98', '$125.38', '~$70'):
    assert(published in NOTES), \
        'the decision packet no longer publishes %s' % published

# The one comparison the packet draws between build and buy, checked from the
# figures rather than asserted.
Mevo = re.search(r'about (\d+)% of the refurbished', NOTES)
assert(Mevo), 'the packet no longer compares stage 1 with the refurbished Mevo Core'
assert(close(float(Mevo.group(1)), 100 * STAGE1_AMAZON / 699.99, 0)), \
    'stage 1 is %.1f%% of the refurbished Mevo Core' % (100 * STAGE1_AMAZON / 699.99)

# Power: the measured idle draw, what it makes sufficient, and the one route the
# packet rejects on the strength of it.
IDLE_W = 5.0 * 22.0 / 1000.0
assert(close(0.11, IDLE_W, 2)), 'the idle draw is %.4f W' % IDLE_W
idle = matching(r'([\d.]+) W \((?:[^)\n]{0,20})?22 mA')
assert(len(idle) >= 3), \
    'the packet states the idle draw in section 0, 5 and 10, found %d' % len(idle)
for text in idle:
    assert(close(float(text), IDLE_W, decimals(text))), \
        'NOTES.md states %s W for 22 mA at 5 V, which is %.2f W' % (text, IDLE_W)
headroom = matching(r'(\d+)x\s+(?:headroom\s+over\s+idle|the\s+idle\s+draw)')
assert(len(headroom) == 2), \
    'the packet states the mains headroom twice (section 0 and section 10), found %d' % len(headroom)
for text in headroom:
    assert(close(float(text), 5.0 / IDLE_W, decimals(text))), \
        'NOTES.md states %sx the idle draw; a 5 W supply is %.1fx' % (text, 5.0 / IDLE_W)
# The retail route's one quantitative claim: its published FOV must imply its
# published coverage at 34 in, at the precision it claims.
m = re.search(r'(\d+(?:\.\d+)?) deg horizontal = \*\*([\d.]+) in of coverage at 34 in',
              NOTES)
assert(m), 'the packet no longer states the C325WB FOV and its coverage together'
TAPO_HFOV, TAPO_COVER = float(m.group(1)), float(m.group(2))
assert(close(TAPO_COVER, 2 * 34 * math.tan(math.radians(TAPO_HFOV / 2)),
             decimals(m.group(2)))), \
    'the C325WB covers %.2f in at 34 in, not %.1f' % (
        2 * 34 * math.tan(math.radians(TAPO_HFOV / 2)), TAPO_COVER)


BANKS = re.findall(
    r'\| ([\d,]+) mAh \((?:[^|\n]*?)(\d+) Wh\) \| ~([\d.]+) Wh \| ~([\d.]+) h \| ~([\d.]+) h \|',
    NOTES)
assert(len(BANKS) == 3), \
    'the power table should carry three bank rows, found %d' % len(BANKS)
for mAh, capacity, usable, idle_hours, stream_hours in BANKS:
    assert(close(float(usable), float(capacity) * 0.8, 0)), \
        'the %s mAh row shows %s Wh usable; 80%% of %s Wh is %.1f Wh' % (
            mAh, usable, capacity, float(capacity) * 0.8)


def bank_hours(wh, load):
    return wh * 0.8 / load


for published, computed in (('~270 h', bank_hours(37, IDLE_W)),
                            ('~350 h', bank_hours(48, IDLE_W)),
                            ('~540 h', bank_hours(74, IDLE_W)),
                            ('~15 h', bank_hours(37, 2.0)),
                            ('~19 h', bank_hours(48, 2.0)),
                            ('~30 h', bank_hours(74, 2.0))):
    assert(published in NOTES), 'NOTES.md no longer publishes %s' % published
    assert(abs(float(published.strip('~ h')) - computed) <= 5.0), \
        'NOTES.md publishes %s where the 80%% conversion gives %.1f h' % (published, computed)
assert('~12 h' not in NOTES), \
    'the 10,000 mAh row is back to the 65%-conversion figure (~12 h)'
assert('$699.99' in NOTES and '$949.99' in NOTES), \
    'the Mevo Core prices are missing from the packet'

print('claims checked: %d table rows, the 34 in threshold, %d threshold statements, '
      'the fisheye spec, and the decision packet (%d priced items, $%.2f + $%.2f '
      'staged, %.2f W idle)' % (len(ROWS), len(thresholds), len(BOM),
                                STAGE1_AMAZON, STAGE1_DIRECT, IDLE_W))
