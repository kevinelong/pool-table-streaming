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

print('claims checked: %d table rows, the 34 in threshold, %d threshold statements '
      'and the fisheye spec' % (len(ROWS), len(thresholds)))
