"""Convertit le livret PDF (balisé, issu de PowerPoint) en .docx.
Usage: python3 -I build.py livret.pdf imgdir first last out.docx
"""
import sys, os, re, subprocess, statistics, json
import pdfplumber
from PIL import Image
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_BREAK, WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

PDF, IMGDIR, FIRST, LAST, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
DPI = 170
SCALE = 0.85            # taille d'image dans Word par rapport à la page PDF
TEXT_PARA_TYPES = {'P', 'H', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'Link', 'Span', 'Formula', 'Caption', 'Lbl', 'Quote', 'Note'}
report = {'flags': [], 'mismatch': []}


# ---------- utilitaires structure ----------
def all_mcids(n, acc=None):
    if acc is None:
        acc = []
    for m in n.get('mcids') or []:
        acc.append(m)
    for c in n.get('children', []):
        all_mcids(c, acc)
    return acc


class PageCtx:
    def __init__(self, page, pno):
        self.page, self.pno = page, pno
        self.chars_by_mcid = {}
        for idx, c in enumerate(page.chars):
            c['_i'] = idx
            self.chars_by_mcid.setdefault(c.get('mcid'), []).append(c)
        self.objs_by_mcid = {}
        for o in page.images + page.rects + page.curves:
            self.objs_by_mcid.setdefault(o.get('mcid'), []).append(o)
        self.used_chars = set()
        self.emitted = []        # texte émis (pour contrôle)
        self.render = None

    def chars_for(self, mcids):
        out = []
        for m in set(mcids):
            out.extend(self.chars_by_mcid.get(m, []))
        out.sort(key=lambda c: c['_i'])
        return out

    def bbox(self, node):
        ms = all_mcids(node)
        objs = self.chars_for(ms)
        if not objs:
            objs = [o for m in ms for o in self.objs_by_mcid.get(m, [])]
        if not objs:
            return None
        return (min(o['x0'] for o in objs), min(o['top'] for o in objs),
                max(o['x1'] for o in objs), max(o['bottom'] for o in objs))

    def page_image(self):
        if self.render is None:
            base = os.path.join(IMGDIR, f'pg{self.pno:03d}')
            if not os.path.exists(base + '.png'):
                subprocess.run(['pdftoppm', '-f', str(self.pno), '-l', str(self.pno), '-r', str(DPI),
                                '-png', '-singlefile', PDF.replace('.pdf', '_notext.pdf'), base], check=True)
            self.render = Image.open(base + '.png')
        return self.render

    def crop(self, bb, name):
        im = self.page_image()
        k = DPI / 72.0
        pad = 2
        box = (max(0, int((bb[0] - pad) * k)), max(0, int((bb[1] - pad) * k)),
               min(im.width, int((bb[2] + pad) * k)), min(im.height, int((bb[3] + pad) * k)))
        path = os.path.join(IMGDIR, f'{name}.png')
        im.crop(box).save(path)
        return path


# ---------- texte & mise en forme ----------
def color_of(c):
    col = c.get('non_stroking_color')
    if not col or not isinstance(col, (tuple, list)):
        return None
    col = [float(x) if isinstance(x, (int, float)) else 0 for x in col]
    if len(col) == 1:
        r = g = b = col[0]
    elif len(col) == 3:
        r, g, b = col
    elif len(col) == 4:
        C, M, Y, K = col
        r, g, b = (1 - C) * (1 - K), (1 - M) * (1 - K), (1 - Y) * (1 - K)
    else:
        return None
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    if lum > 0.62 or lum < 0.12:      # blanc/jaune sur fond coloré, ou noir -> noir
        return None
    return '%02X%02X%02X' % (int(r * 255), int(g * 255), int(b * 255))


def chars_to_runs(chars):
    """Retourne une liste de runs (texte, bold, italic, color, vert) avec espaces/sauts reconstruits."""
    if not chars:
        return []
    sizes = [c['size'] for c in chars if c['text'].strip()]
    big = max(sizes) if sizes else 10
    runs = []
    prev = None
    line_top, line_bottom = chars[0]['top'], chars[0]['bottom']
    for c in chars:
        t = c['text']
        if prev is not None:
            same_line = abs(c['top'] - prev['top']) < 0.6 * max(c['size'], prev['size']) and c['x0'] >= prev['x0'] - 1
            if not same_line:
                line_top, line_bottom = c['top'], c['bottom']
                last = runs[-1][0] if runs else ''
                if last and not last.endswith((' ', '-', '/')) and t != ' ':
                    runs.append([' ', False, False, None, None])
            else:
                gap = c['x0'] - prev['x1']
                if gap > 0.1 * min(c['size'], prev['size']) and t != ' ' and prev['text'] != ' ':
                    runs.append([' ', False, False, None, None])
        else:
            pass
        fn = c['fontname'].split('+')[-1]
        bold = 'Bold' in fn
        ital = 'Italic' in fn
        vert = None
        if c['size'] < 0.78 * big and t.strip():
            # exposant / indice par rapport aux voisins plus grands
            neigh = [d for d in chars if d['size'] >= 0.9 * big and abs(d['top'] - c['top']) < big and d['text'].strip()]
            if neigh:
                nb = statistics.median(d['bottom'] for d in neigh)
                ntop = statistics.median(d['top'] for d in neigh)
                if c['bottom'] < nb - 0.2 * c['size']:
                    vert = 'sup'
                elif c['top'] > ntop + 0.3 * c['size']:
                    vert = 'sub'
        col = color_of(c)
        if runs and runs[-1][1:] == [bold, ital, col, vert]:
            runs[-1][0] += t
        else:
            runs.append([t, bold, ital, col, vert])
        prev = c
    # nettoyage espaces multiples
    out = []
    for r in runs:
        if out and r[0] == ' ' and out[-1][0].endswith(' '):
            continue
        out.append(r)
    while out and not out[0][0].strip():
        out.pop(0)
    while out and not out[-1][0].strip():
        out.pop()
    if out:
        out[0][0] = out[0][0].lstrip()
        out[-1][0] = out[-1][0].rstrip()
    return out


def add_runs(par, runs, size=None, force_bold=False, color_override=None):
    for t, b, i, col, vert in runs:
        if not t:
            continue
        r = par.add_run(t)
        r.bold = b or force_bold
        r.italic = i
        if size:
            r.font.size = Pt(size)
        c = color_override or col
        if c:
            r.font.color.rgb = RGBColor.from_string(c)
        if vert == 'sup':
            r.font.superscript = True
        elif vert == 'sub':
            r.font.subscript = True


def runs_text(runs):
    return ''.join(r[0] for r in runs)


# ---------- rendu ----------
class Renderer:
    def __init__(self, doc):
        self.doc = doc
        self.img_count = 0

    def para(self, container, style=None):
        p = container.add_paragraph(style=style) if style else container.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(0)
        pf.space_after = Pt(2)
        return p

    def text_node(self, ctx, node, container, size=None, style=None, in_table=False, footer=False):
        chars = ctx.chars_for(all_mcids(node))
        chars = [c for c in chars if c['_i'] not in ctx.used_chars]
        if not chars:
            return
        for c in chars:
            ctx.used_chars.add(c['_i'])
        runs = chars_to_runs(chars)
        if not runs:
            return
        txt = runs_text(runs)
        ctx.emitted.append(txt)
        if in_table and container is not None:
            p = container
        else:
            # titre de fiche ?
            sz = statistics.median(c['size'] for c in chars if c['text'].strip()) if any(c['text'].strip() for c in chars) else 0
            if style is None and not footer and ctx.title_first is not None and any(c['_i'] == ctx.title_first for c in chars):
                style = 'Heading 1'
            p = self.para(container, style)
        if footer:
            add_runs(p, runs, size=7, color_override='808080')
        elif p.style is not None and p.style.name.startswith('Heading'):
            add_runs(p, runs)
        else:
            add_runs(p, runs, size=size)
        return p

    def image_block(self, ctx, bb, container, alt='', max_w=6.8):
        self.img_count += 1
        path = ctx.crop(bb, f'p{ctx.pno:03d}_img{self.img_count:04d}')
        w = (bb[2] - bb[0] + 4) / 72.0 * SCALE
        w = max(0.25, min(w, max_w))
        p = self.para(container)
        p.add_run().add_picture(path, width=Inches(w))
        return p

    def render_node(self, ctx, node, container, level=0, in_cell=False):
        t = node.get('type')
        if t == 'Table':
            self.table(ctx, node, container)
        elif t == 'L':
            self.lst(ctx, node, container, level)
        elif t == 'Figure':
            self.figure(ctx, node, container)
        elif t in TEXT_PARA_TYPES or (node.get('mcids') and not node.get('children')):
            self.text_node(ctx, node, container, size=(8 if in_cell else None))
        else:
            for c in node.get('children', []):
                self.render_node(ctx, c, container, level, in_cell)
            # mcids directs d'un conteneur
            if node.get('mcids') and t not in ('Table', 'L'):
                self.text_node(ctx, {'mcids': node['mcids']}, container, size=(8 if in_cell else None))

    def figure(self, ctx, node, container):
        ms = all_mcids(node)
        # texte éventuel dans la figure (ex. formule)
        if ctx.chars_for(ms):
            self.text_node(ctx, node, container)
            return
        objs = [o for m in ms for o in ctx.objs_by_mcid.get(m, [])]
        imgs = [o for o in objs if o['object_type'] == 'image']
        alt = (node.get('alt_text') or '').strip()
        meaningful_alt = alt and not alt.startswith('(') and 'Rectangle' not in alt
        if not imgs and not meaningful_alt:
            return  # flèches, cadres, fonds
        use = imgs or objs
        if not use:
            return
        bb = (min(o['x0'] for o in use), min(o['top'] for o in use), max(o['x1'] for o in use), max(o['bottom'] for o in use))
        if is_logo(bb):
            return
        for o in use:
            ctx.used_imgs.add(id(o))
        self.image_block(ctx, bb, container, alt)

    def lst(self, ctx, node, container, level):
        for li in node.get('children', []):
            if li.get('type') != 'LI':
                self.render_node(ctx, li, container, level)
                continue
            lbl = [c for c in li.get('children', []) if c.get('type') == 'Lbl']
            body = [c for c in li.get('children', []) if c.get('type') != 'Lbl']
            lbl_chars = ctx.chars_for(all_mcids({'children': lbl}))
            lbl_runs = chars_to_runs(lbl_chars)
            for c in lbl_chars:
                ctx.used_chars.add(c['_i'])
            # corps : texte direct + listes imbriquées
            nested = []
            text_nodes = []
            def split(n):
                if n.get('type') == 'L':
                    nested.append(n)
                else:
                    if n.get('mcids'):
                        text_nodes.append({'mcids': n['mcids']})
                    for ch in n.get('children', []):
                        split(ch)
            for b in body:
                split(b)
            chars = ctx.chars_for(all_mcids({'children': text_nodes}))
            chars = [c for c in chars if c['_i'] not in ctx.used_chars]
            for c in chars:
                ctx.used_chars.add(c['_i'])
            runs = chars_to_runs(chars)
            p = self.para(container)
            pf = p.paragraph_format
            pf.left_indent = Cm(0.6 + 0.6 * level)
            pf.first_line_indent = Cm(-0.5)
            if lbl_runs:
                add_runs(p, lbl_runs)
                p.add_run('\t')
                ctx.emitted.append(runs_text(lbl_runs))
            add_runs(p, runs)
            ctx.emitted.append(runs_text(runs))
            for n in nested:
                self.lst(ctx, n, container, level + 1)

    def table(self, ctx, node, container, side_imgs=()):
        rows = []
        def collect(n):
            for c in n.get('children', []):
                if c.get('type') == 'TR':
                    rows.append(c)
                elif c.get('type') in ('THead', 'TBody', 'TFoot'):
                    collect(c)
        collect(node)
        if not rows:
            return
        # placement en grille avec ColSpan/RowSpan ; lignes incomplètes placées selon la position réelle
        import itertools
        rowcells = []
        for tr in rows:
            cells = []
            for td in [c for c in tr.get('children', []) if c.get('type') in ('TD', 'TH')]:
                a = td.get('attributes') or {}
                bb = ctx.bbox(td)
                cells.append((td, int(a.get('ColSpan', 1)), int(a.get('RowSpan', 1)), ((bb[0] + bb[2]) / 2) if bb else None))
            rowcells.append(cells)
        # nombre de colonnes et centres des colonnes depuis les lignes "pleines"
        def width_of(r, cells, occupied):
            return sum(cs for _, cs, _, _ in cells) + sum(1 for (rr, _) in occupied if rr == r)
        ncols_guess = max(sum(cs for _, cs, _, _ in cells) for cells in rowcells)
        centers = [[] for _ in range(ncols_guess)]
        for cells in rowcells:
            if len(cells) == ncols_guess and all(cs == 1 for _, cs, _, _ in cells):
                for j, (_, _, _, cx) in enumerate(cells):
                    if cx is not None:
                        centers[j].append(cx)
        colc = [statistics.median(c) if c else None for c in centers]
        grid = {}
        placements = []
        irregular = False
        for r, cells in enumerate(rowcells):
            free = [c for c in range(ncols_guess) if (r, c) not in grid]
            need = sum(cs for _, cs, _, _ in cells)
            starts = None
            if need < len(free) and all(x is not None for x in colc) and len(free) == ncols_guess:
                holes = len(free) - need
                best = None
                k = len(cells)
                # répartir les trous avant chaque cellule (et à la fin)
                for comp in itertools.product(range(holes + 1), repeat=k):
                    if sum(comp) > holes:
                        continue
                    pos, cost, st = 0, 0.0, []
                    for (td, cs, rs, cx), gap in zip(cells, comp):
                        pos += gap
                        st.append(pos)
                        if cx is not None:
                            cost += abs(cx - sum(colc[pos:pos + cs]) / cs)
                        pos += cs
                    if best is None or cost < best[0]:
                        best = (cost, st)
                starts = best[1]
            elif need != len(free):
                irregular = True
            col = 0
            for i, (td, cs, rs, cx) in enumerate(cells):
                if starts is not None:
                    col = starts[i]
                while (r, col) in grid:
                    col += 1
                for dr in range(rs):
                    for dc in range(cs):
                        grid[(r + dr, col + dc)] = True
                placements.append((r, col, rs, cs, td))
                col += cs
        ncols = ncols_guess
        nrows = max(r for r, _ in grid) + 1 if grid else len(rows)
        ncols = max([c for _, c in grid] + [0]) + 1
        off = 1 if side_imgs else 0
        if off:
            row_bbs = [ctx.bbox(tr) for tr in rows]
            side_map = {}
            for bb in side_imgs:
                cy = (bb[1] + bb[3]) / 2
                best = min(range(len(rows)), key=lambda i: 1e9 if row_bbs[i] is None else abs((row_bbs[i][1] + row_bbs[i][3]) / 2 - cy))
                side_map.setdefault(best, []).append(bb)
            placements = [(r, c + 1, rs, cs, td) for r, c, rs, cs, td in placements]
            grid = {(r, c + 1): v for (r, c), v in grid.items()}
            for r in range(nrows):
                grid[(r, 0)] = True
            ncols += 1
        tbl = container.add_table(rows=nrows, cols=ncols)
        tbl.autofit = False
        tbl.style = 'Table Grid'
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        total = 17.5 if ncols > 4 else (12 if ncols > 1 else 16)
        widths = [total / ncols] * ncols
        if ncols >= 6:
            first = min(2.6, total * 0.16)
            widths = [first] + [(total - first) / (ncols - 1)] * (ncols - 1)
        if off:
            widths = [2.6] + [w * (total - 2.6) / (total - widths[0]) for w in widths[1:]] if ncols > 1 else widths
            for r, bbs in side_map.items():
                for bb in bbs:
                    self.image_block(ctx, bb, tbl.cell(r, 0), max_w=0.85)
        for i, col in enumerate(tbl.columns):
            col.width = Cm(widths[i])
        for row in tbl.rows:
            for i, cell in enumerate(row.cells):
                cell.width = Cm(widths[i])
        fsize = 8 if ncols <= 6 else (7 if ncols <= 12 else 6.5)
        holes = set((r, c) for r in range(nrows) for c in range(ncols)) - set(grid)
        if holes:
            report['flags'].append((ctx.pno, 'holes(empty cells): ' + str(sorted(holes))))
        holes = irregular
        if holes:
            report['flags'].append((ctx.pno, 'table grid holes'))
        for r, c, rs, cs, td in placements:
            cell = tbl.cell(r, c)
            if rs > 1 or cs > 1:
                cell = cell.merge(tbl.cell(min(r + rs, nrows) - 1, min(c + cs, ncols) - 1))
            self.fill_cell(ctx, cell, td, fsize, header=(td.get('type') == 'TH'))
        # espace après le tableau
        sp = self.para(container)
        sp.paragraph_format.space_after = Pt(4)
        if holes:
            p = self.para(container)
            r = p.add_run(f'[À VÉRIFIER – page {ctx.pno}] (structure du tableau ci-dessus irrégulière)')
            r.bold = True
            r.font.color.rgb = RGBColor(0xC0, 0, 0)

    def fill_cell(self, ctx, cell, td, fsize, header=False):
        texts = []
        def gather(n):
            t = n.get('type')
            if t in TEXT_PARA_TYPES or (n.get('mcids') and not n.get('children')):
                texts.append(n)
            elif t == 'Figure':
                texts.append(n)
            else:
                if n.get('mcids'):
                    texts.append({'mcids': n['mcids']})
                for ch in n.get('children', []):
                    gather(ch)
        gather(td)
        first = True
        for n in texts:
            if n.get('type') == 'Figure':
                continue
            chars = [c for c in ctx.chars_for(all_mcids(n)) if c['_i'] not in ctx.used_chars]
            if not chars:
                continue
            for c in chars:
                ctx.used_chars.add(c['_i'])
            runs = chars_to_runs(chars)
            if not runs:
                continue
            ctx.emitted.append(runs_text(runs))
            p = cell.paragraphs[0] if first else cell.add_paragraph()
            first = False
            p.paragraph_format.space_after = Pt(0)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_runs(p, runs, size=fsize, force_bold=header)
        if header:
            shade(cell, 'D9E2F3')


def shade(cell, hexcol):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hexcol)
    tcPr.append(shd)


def is_logo(bb):
    x0, top, x1, bottom = bb
    if top < 8 and x0 > 440 and (x1 - x0) < 80:      # bébé en haut à droite
        return True
    if top > 690:                                       # pied de page (logo)
        return True
    return False


def norm(s):
    return re.sub(r'\s+', '', s)


# ---------- page ----------
def flatten_roots(roots):
    nodes = list(roots)
    while len(nodes) == 1 and nodes[0].get('type') in ('Document', 'Sect', 'Part', 'Div') and not nodes[0].get('mcids'):
        nodes = nodes[0].get('children', [])
    return nodes


def visual_sort(items):
    """items: liste de (bbox, payload). Tri par rangées puis de gauche à droite."""
    items = sorted(items, key=lambda it: (it[0][1], it[0][0]))
    rows = []
    for it in items:
        placed = False
        if rows:
            row = rows[-1]
            ref = row[0][0]
            if it[0][1] <= ref[1] + 12 and all(it[0][0] >= o[0][2] - 2 or it[0][2] <= o[0][0] + 2 for o in row):
                row.append(it)
                placed = True
        if not placed:
            rows.append([it])
    out = []
    for row in rows:
        out.extend(sorted(row, key=lambda it: it[0][0]))
    return out


CONTAINER_TYPES = {'Sect', 'Div', 'Document', 'Part', 'Art', 'NonStruct', 'Private', 'TBody'}


def area(bb):
    return max(0.1, (bb[2] - bb[0])) * max(0.1, (bb[3] - bb[1]))


def inside(inner, outer):
    ix0, iy0 = max(inner[0], outer[0]), max(inner[1], outer[1])
    ix1, iy1 = min(inner[2], outer[2]), min(inner[3], outer[3])
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    return (ix1 - ix0) * (iy1 - iy0) / area(inner)


def fig_bbox(ctx, node):
    """bbox d'une figure à reproduire (image ou pictogramme), sinon None."""
    ms = all_mcids(node)
    if ctx.chars_for(ms):
        return ctx.bbox(node)
    objs = [o for m in ms for o in ctx.objs_by_mcid.get(m, [])]
    imgs = [o for o in objs if o['object_type'] == 'image']
    alt = (node.get('alt_text') or '').strip()
    meaningful_alt = alt and not alt.startswith('(') and 'Rectangle' not in alt
    use = imgs or (objs if meaningful_alt else [])
    if not use:
        return None
    bb = (min(o['x0'] for o in use), min(o['top'] for o in use), max(o['x1'] for o in use), max(o['bottom'] for o in use))
    if is_logo(bb):
        return None
    return bb


def units_of(node):
    if node.get('type') in CONTAINER_TYPES and not node.get('mcids'):
        out = []
        for c in node.get('children', []):
            out.extend(units_of(c))
        return out
    return [node]


class Block:
    def __init__(self, bb, kind, payload):
        self.bb, self.kind, self.payload = bb, kind, payload
        self.children = []
        self.side_imgs = []


def make_bands(blocks):
    blocks = sorted(blocks, key=lambda b: (b.bb[1], b.bb[0]))
    bands = []
    for b in blocks:
        if bands and b.bb[1] < bands[-1]['bottom'] - 2:
            bands[-1]['items'].append(b)
            bands[-1]['bottom'] = max(bands[-1]['bottom'], b.bb[3])
        else:
            bands.append({'top': b.bb[1], 'bottom': b.bb[3], 'items': [b]})
    return bands


class PageRenderer:
    def __init__(self, R, ctx):
        self.R, self.ctx = R, ctx

    def render_block(self, b, container):
        R, ctx = self.R, self.ctx
        if b.kind == 'node':
            n = b.payload
            footer = b.bb[1] > 688
            if n.get('type') == 'Table':
                R.table(ctx, n, container, side_imgs=b.side_imgs)
                self.render_bands(make_bands(b.children), container)
            elif n.get('type') == 'Figure':
                if n.get('_fig_bb') and not ctx.chars_for(all_mcids(n)):
                    R.image_block(ctx, n['_fig_bb'], container)
                else:
                    R.text_node(ctx, n, container)
                self.render_bands(make_bands(b.children), container)
            elif footer and n.get('type') not in ('L',):
                R.text_node(ctx, n, container, footer=True)
            else:
                self.render_container(n, b.children, container)
        elif b.kind == 'loose':
            chars = [c for c in b.payload if c['_i'] not in ctx.used_chars]
            for c in chars:
                ctx.used_chars.add(c['_i'])
            runs = chars_to_runs(chars)
            if runs:
                p = R.para(container)
                add_runs(p, runs)
                ctx.emitted.append(runs_text(runs))
            self.render_bands(make_bands(b.children), container)
        elif b.kind == 'img':
            R.image_block(ctx, b.payload, container)

    def render_container(self, node, contained, container):
        bands = make_bands(contained)
        for u in units_of(node):
            ub = self.ctx.bbox(u)
            if ub is not None:
                while bands and bands[0]['top'] < ub[1] - 2:
                    self.render_band(bands.pop(0), container)
            if u.get('type') == 'Figure':
                fb = fig_bbox(self.ctx, u)
                if fb is not None and not self.ctx.chars_for(all_mcids(u)):
                    self.R.image_block(self.ctx, fb, container)
                elif fb is not None:
                    self.R.text_node(self.ctx, u, container)
                continue
            self.R.render_node(self.ctx, u, container)
        self.render_bands(bands, container)

    def render_bands(self, bands, container):
        for band in bands:
            self.render_band(band, container)

    def render_band(self, band, container):
        items = band['items']
        if len(items) == 1:
            self.render_block(items[0], container)
            return
        # colonnes par recouvrement horizontal
        cols = []
        for b in sorted(items, key=lambda b: b.bb[0]):
            if cols and b.bb[0] < cols[-1]['x1'] - 2:
                cols[-1]['items'].append(b)
                cols[-1]['x1'] = max(cols[-1]['x1'], b.bb[2])
            else:
                cols.append({'x0': b.bb[0], 'x1': b.bb[2], 'items': [b]})
        if len(cols) == 1:
            for b in sorted(items, key=lambda b: b.bb[1]):
                self.render_block(b, container)
            return
        tbl = container.add_table(rows=1, cols=len(cols))
        tbl.autofit = False
        tot = sum(c['x1'] - c['x0'] + 6 for c in cols)
        full = 17.5 if container is self.R.doc else 8
        for i, c in enumerate(cols):
            cell = tbl.cell(0, i)
            w = Cm(max(1.0, full * (c['x1'] - c['x0'] + 6) / max(tot, 1)))
            cell.width = w
            tbl.columns[i].width = w
            first_p = cell.paragraphs[0]
            for b in sorted(c['items'], key=lambda b: b.bb[1]):
                self.render_block(b, cell)
            # supprimer le paragraphe vide initial s'il reste vide et n'est pas seul
            if not first_p.text and not first_p._p.xpath('.//w:drawing') and len(cell.paragraphs) > 1:
                first_p._p.getparent().remove(first_p._p)
        sp = self.R.para(container)
        sp.paragraph_format.space_after = Pt(0)


def render_page(doc, R, page, pno):
    ctx = PageCtx(page, pno)
    ctx.used_imgs = set()
    # titre de la fiche : paragraphe du haut de page contenant ®, sinon le plus grand
    cands = []
    def find_ps(n):
        if n.get('type') in ('P', 'H1', 'H2'):
            cs = [c for c in ctx.chars_for(all_mcids(n)) if c['text'].strip()]
            if cs and min(c['top'] for c in cs) < 75:
                txt = ''.join(c['text'] for c in cs)
                cands.append((('®' in txt), statistics.median(c['size'] for c in cs), -min(c['top'] for c in cs), cs[0]['_i'], txt))
            return
        for c in n.get('children', []):
            find_ps(c)
    for n in page.structure_tree:
        find_ps(n)
    cands = [c for c in cands if c[1] >= 9.5 and sum(ch.isalpha() for ch in c[4]) >= 4]
    ctx.title_first = max(cands)[3] if cands else None
    ctx.title_text = max(cands)[4] if cands else ''
    mp = R.para(doc)
    mp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = mp.add_run(f'— Page {pno} —')
    r.font.size = Pt(7)
    r.font.color.rgb = RGBColor(0x80, 0x80, 0x80)

    blocks = []
    def add_node(n):
        if n.get('type') == 'Figure':
            fb = fig_bbox(ctx, n)
            if fb is None:
                return
            n['_fig_bb'] = fb
            blocks.append(Block(fb, 'node', n))
            return
        bb = ctx.bbox(n)
        if bb is None:
            # conteneur sans texte direct : descendre (peut contenir des figures)
            if n.get('type') in CONTAINER_TYPES:
                for c in n.get('children', []):
                    add_node(c)
            return
        blocks.append(Block(bb, 'node', n))
    for n in flatten_roots(page.structure_tree):
        add_node(n)

    covered = set()
    for n in page.structure_tree:
        covered.update(all_mcids(n))
    loose = [c for c in page.chars if c.get('mcid') not in covered and c['text'].strip()
             and not (c['top'] > 690 and c['text'].isdigit())]
    loose_all = [c for c in page.chars if c.get('mcid') not in covered and not (c['top'] > 690 and c['text'].strip().isdigit())]
    if loose:
        bb = (min(c['x0'] for c in loose), min(c['top'] for c in loose), max(c['x1'] for c in loose), max(c['bottom'] for c in loose))
        blocks.append(Block(bb, 'loose', [c for c in loose_all if c['top'] >= bb[1] - 1 and c['bottom'] <= bb[3] + 1]))
    struct_objs = set()
    for m, objs in ctx.objs_by_mcid.items():
        if m in covered:
            for o in objs:
                struct_objs.add(id(o))
    for im in page.images:
        if id(im) in struct_objs:
            continue
        bb = (im['x0'], im['top'], im['x1'], im['bottom'])
        if is_logo(bb) or (bb[2] - bb[0]) < 6:
            continue
        blocks.append(Block(bb, 'img', bb))

    # Figures internes à un noeud texte déjà rendues par ce noeud : on retire les doublons
    nested_fig_ids = set()
    for b in blocks:
        if b.kind == 'node' and b.payload.get('type') != 'Figure':
            def mark(n):
                for c in n.get('children', []):
                    if c.get('type') == 'Figure':
                        nested_fig_ids.add(id(c))
                    mark(c)
            mark(b.payload)
    blocks = [b for b in blocks if not (b.kind == 'node' and id(b.payload) in nested_fig_ids)]

    # pictogrammes alignés à gauche d'un tableau -> colonne du tableau
    tables = [b for b in blocks if b.kind == 'node' and b.payload.get('type') == 'Table']
    for t in tables:
        for b in list(blocks):
            is_pic = b.kind == 'img' or (b.kind == 'node' and b.payload.get('type') == 'Figure' and not ctx.chars_for(all_mcids(b.payload)))
            if not is_pic:
                continue
            cy = (b.bb[1] + b.bb[3]) / 2
            if b.bb[2] <= t.bb[0] + 4 and t.bb[1] - 5 <= cy <= t.bb[3] + 5 and t.bb[0] - b.bb[2] < 60:
                t.side_imgs.append(b.bb)
                blocks.remove(b)

    # imbrication : chaque bloc va dans le plus petit bloc texte qui le contient
    roots = []
    for b in blocks:
        best = None
        for c in blocks:
            if c is b or c.kind not in ('node', 'loose'):
                continue
            if c.kind == 'node' and c.payload.get('type') == 'Figure':
                continue
            if area(c.bb) > area(b.bb) * 1.2 and inside(b.bb, c.bb) > 0.6:
                if best is None or area(c.bb) < area(best.bb):
                    best = c
        if best is None:
            roots.append(b)
        else:
            best.children.append(b)

    PR = PageRenderer(R, ctx)
    for it in visual_sort([(b.bb, b) for b in roots]):
        PR.render_block(it[1], doc)

    src = sorted(norm(''.join(c['text'] for c in page.chars if not (c['top'] > 690 and c['text'].strip().isdigit() and c.get('mcid') not in covered))))
    got = sorted(norm(''.join(ctx.emitted)))
    if src != got:
        from collections import Counter
        a, b = Counter(src), Counter(got)
        report['mismatch'].append((pno, ''.join(sorted((a - b).elements())), ''.join(sorted((b - a).elements()))))
        p = R.para(doc)
        rr = p.add_run(f'[À VÉRIFIER – page {pno}] (une partie du texte de cette page n\'a pas pu être extraite automatiquement)')
        rr.bold = True
        rr.font.color.rgb = RGBColor(0xC0, 0, 0)
    report.setdefault('titles', []).append((pno, ctx.title_text))
    return ctx


def setup(doc):
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    for side in ('left_margin', 'right_margin'):
        setattr(sec, side, Cm(1.5))
    sec.top_margin = sec.bottom_margin = Cm(1.5)
    st = doc.styles['Normal']
    st.font.name = 'Calibri'
    st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Calibri')
    st.font.size = Pt(10)
    h = doc.styles['Heading 1']
    h.font.name = 'Calibri'
    h.element.rPr.rFonts.set(qn('w:ascii'), 'Calibri')
    h.element.rPr.rFonts.set(qn('w:hAnsi'), 'Calibri')
    h.font.size = Pt(15)
    h.font.bold = True
    h.font.color.rgb = RGBColor(0x14, 0x55, 0x87)
    h.paragraph_format.space_before = Pt(4)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True


def main():
    doc = Document()
    setup(doc)
    R = Renderer(doc)
    os.makedirs(IMGDIR, exist_ok=True)
    with pdfplumber.open(PDF) as pdf:
        for pno in range(FIRST, LAST + 1):
            render_page(doc, R, pdf.pages[pno - 1], pno)
            if pno != LAST:
                doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
            pdf.pages[pno - 1].flush_cache()
    doc.core_properties.title = "Le livret du médicament pédiatrique (Urg'Ara, février 2026)"
    doc.save(OUT)
    with open(OUT + '.report.json', 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print('mismatch pages:', [m[0] for m in report['mismatch']], 'flags:', report['flags'])


main()
