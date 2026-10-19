"""Build native ComfyUI JPG previews from editable workflow card metadata.

Run with ComfyUI's Python (Pillow is already a package dependency).
Only documentation assets and the instructions node are updated.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BG, PANEL, INK, MUTED = '#101923', '#1c2938', '#f4f7fb', '#a9b7c9'


def font(size, bold=False):
    filename = 'Arial Bold.ttf' if bold else 'Arial.ttf'
    candidates = [Path('/System/Library/Fonts/Supplemental') / filename,
                  Path('/usr/share/fonts/truetype/dejavu') / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),
                  Path('C:/Windows/Fonts') / ('arialbd.ttf' if bold else 'arial.ttf')]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise RuntimeError('Install Arial or DejaVu Sans to rebuild the template cards.')


def icon(draw, kind, x, y, accent, scale=1):
    def box(coords):
        return tuple(round((x if i % 2 == 0 else y) + v * scale) for i, v in enumerate(coords))

    width = max(2, round(6 * scale))
    if '+' in kind:
        first, second = kind.split('+')
        icon(draw, first, x - 23 * scale, y - 10 * scale, accent, scale * .62)
        icon(draw, second, x + 64 * scale, y + 54 * scale, accent, scale * .62)
        return
    if kind in ('image', 'images', 'frames'):
        if kind in ('images', 'frames'):
            draw.rounded_rectangle(box((-14, -14, 136, 100)), radius=round(12 * scale), outline=MUTED, width=width)
        draw.rounded_rectangle(box((0, 0, 150, 114)), radius=round(12 * scale), fill=PANEL, outline=accent, width=width)
        draw.ellipse(box((104, 20, 124, 40)), fill=accent)
        draw.line(box((14, 94, 53, 51, 88, 89, 108, 67, 136, 96)), fill=accent, width=width, joint='curve')
        if kind == 'frames':
            draw.text(box((15, 18)), '1 / 2', font=font(round(24 * scale), True), fill=INK)
    elif kind == 'video':
        draw.rounded_rectangle(box((0, 0, 150, 114)), radius=round(12 * scale), outline=accent, width=width)
        for offset in (13, 131):
            for row in (16, 47, 78):
                draw.rectangle(box((offset, row, offset + 8, row + 17)), fill=accent)
        draw.polygon(box((62, 30, 62, 84, 102, 57)), fill=accent)
    elif kind == 'text':
        draw.rounded_rectangle(box((0, 0, 150, 114)), radius=round(12 * scale), outline=accent, width=width)
        for row, length in ((29, 94), (57, 108), (85, 62)):
            draw.line(box((22, row, length, row)), fill=accent, width=width)
    elif kind == 'audio':
        for i, height in enumerate((28, 55, 90, 118, 76, 105, 47, 22)):
            cx = 9 + i * 19
            draw.rounded_rectangle(box((cx, 57 - height / 2, cx + 8, 57 + height / 2)), radius=round(4 * scale), fill=accent)
    elif kind == 'portrait':
        draw.ellipse(box((48, 0, 104, 56)), outline=accent, width=width)
        draw.arc(box((18, 54, 132, 150)), 180, 360, fill=accent, width=width)
        draw.line(box((18, 103, 132, 103)), fill=accent, width=width)


def build(card):
    accent = card['color']
    image = Image.new('RGB', (768, 768), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 767, 8), fill=accent)
    draw.text((704, 49), 'FORMA', font=font(28, True), fill=INK, anchor='ra')
    draw.text((62, 107), card['mode'], font=font(28, True), fill=accent)
    for index, line in enumerate(card['title']):
        draw.text((58, 155 + index * 61), line, font=font(54, True), fill=INK)
    for x in (58, 448):
        draw.rounded_rectangle((x, 323, x + 260, 531), radius=22, fill=PANEL)
    icon(draw, card['flow'][0], 113, 354, accent)
    icon(draw, card['flow'][1], 503, 354, accent)
    draw.text((188, 492), card['labels'][0], font=font(24, True), fill=MUTED, anchor='mm')
    draw.text((578, 492), card['labels'][1], font=font(24, True), fill=MUTED, anchor='mm')
    draw.line((346, 419, 419, 419), fill=accent, width=7)
    draw.line((399, 400, 420, 419, 399, 438), fill=accent, width=7, joint='curve')
    for index, line in enumerate(card['description']):
        assert draw.textlength(line, font=font(34)) <= 652, line
        draw.text((60, 570 + 43 * index), line, font=font(34), fill=INK)
    draw.line((60, 686, 708, 686), fill='#344252', width=2)
    draw.text((60, 708), card['footer'], font=font(25), fill=MUTED)
    output = ROOT / 'workflows' / (card['file'] + '.jpg')
    image.save(output, quality=90, subsampling=0, optimize=True)

    workflow = output.with_suffix('.json')
    graph = json.loads(workflow.read_text())
    guide = next(n for n in graph['nodes'] if n['type'] == 'FormaApiKeySetup')
    instructions = guide['widgets_values'][0]
    instructions = instructions[instructions.index('GET YOUR FORMA API KEY'):]
    guide['title'] = 'Forma · ' + ' '.join(card['title']) + ' · Instructions'
    guide['widgets_values'][0] = ('ABOUT THIS WORKFLOW\n\n' + ' '.join(card['description'])
        + '\n' + card['detail'] + '\n\n' + instructions)
    workflow.write_text(json.dumps(graph, indent=2) + '\n')


if __name__ == '__main__':
    cards = json.loads((ROOT / 'scripts/template_cards.json').read_text())
    workflows = {p.stem for p in (ROOT / 'workflows').glob('*.json')}
    assert {card['file'] for card in cards} == workflows
    for card in cards:
        build(card)
    print(f'Built {len(cards)} thumbnails and workflow descriptions.')
