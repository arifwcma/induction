import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE


BG = RGBColor(0x0B, 0x1B, 0x33)
PANEL = RGBColor(0x14, 0x28, 0x47)
PANEL_LINE = RGBColor(0x25, 0x3B, 0x5E)
TEAL = RGBColor(0x2D, 0xD4, 0xBF)
AMBER = RGBColor(0xF5, 0xB3, 0x42)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
MUTED = RGBColor(0x9F, 0xB3, 0xC8)
WRONG = RGBColor(0xE0, 0x6C, 0x6C)
FOOTER_BG = RGBColor(0x0F, 0x22, 0x40)

FONT = "Segoe UI"
SLIDE_W = 13.333
SLIDE_H = 7.5

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(HERE, "lecture_resources", "logo-wimmera-white.png")
OUT_PATH = os.path.join(HERE, "deck.pptx")


def solid(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color


def no_line(shape):
    shape.line.fill.background()


def outline(shape, color, w=1.0):
    shape.line.color.rgb = color
    shape.line.width = Pt(w)


def set_letterspacing(run, points):
    rPr = run._r.get_or_add_rPr()
    rPr.set("spc", str(int(points * 100)))


def txt(slide, x, y, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for i, (text, size, color, bold, italic, spacing) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if spacing is not None:
            p.line_spacing = spacing
        r = p.add_run()
        r.text = text
        f = r.font
        f.name = FONT
        f.size = Pt(size)
        f.color.rgb = color
        f.bold = bold
        f.italic = italic
    return box


def card(slide, x, y, w, h, fill=PANEL, line_color=PANEL_LINE, radius=0.06):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    solid(shape, fill)
    outline(shape, line_color, 1.0)
    shape.adjustments[0] = radius
    return shape


def circle(slide, cx, cy, diameter, fill=TEAL):
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - diameter / 2), Inches(cy - diameter / 2),
                                    Inches(diameter), Inches(diameter))
    solid(shape, fill)
    no_line(shape)
    return shape


def centered_label(shape, text, size, color, bold=True):
    tf = shape.text_frame
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.name = FONT
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color


def arrow_right(slide, x, y, w, h=0.3, fill=TEAL):
    shape = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y - h / 2), Inches(w), Inches(h))
    solid(shape, fill)
    no_line(shape)
    return shape


def base_slide(prs, step_label, title, notes):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    solid(bg, BG)
    no_line(bg)

    strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.16), prs.slide_height)
    solid(strip, TEAL)
    no_line(strip)

    eb = txt(slide, 0.65, 0.4, 11.5, 0.4, [(step_label, 12.5, TEAL, True, False, None)])
    set_letterspacing(eb.text_frame.paragraphs[0].runs[0], 2.2)

    txt(slide, 0.63, 0.74, 11.5, 0.9, [(title, 32, WHITE, True, False, 1.0)])

    ul = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.68), Inches(1.5), Inches(1.3), Inches(0.06))
    solid(ul, AMBER)
    no_line(ul)

    fh = 0.55
    fy = SLIDE_H - fh
    footer = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(fy), prs.slide_width, Inches(fh))
    solid(footer, FOOTER_BG)
    no_line(footer)
    faccent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(fy), prs.slide_width, Inches(0.04))
    solid(faccent, TEAL)
    no_line(faccent)
    ftxt = txt(slide, 0.65, fy, 8.0, fh, [("ICT108  ·  MetMate case study", 10.5, MUTED, False, False, None)],
               anchor=MSO_ANCHOR.MIDDLE)

    slide.notes_slide.notes_text_frame.text = notes
    return slide


def build_title_slide(prs, notes):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    solid(bg, BG)
    no_line(bg)
    strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.16), prs.slide_height)
    solid(strip, TEAL)
    no_line(strip)

    eb = txt(slide, 0.65, 1.55, 11.5, 0.4,
             [("GUEST LECTURE   ·   ICT108", 13, TEAL, True, False, None)])
    set_letterspacing(eb.text_frame.paragraphs[0].runs[0], 2.4)

    txt(slide, 0.62, 2.0, 12.0, 1.3, [("Talk to Your Documents", 48, WHITE, True, False, 1.0)])

    ul = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.68), Inches(3.05), Inches(1.9), Inches(0.08))
    solid(ul, AMBER)
    no_line(ul)

    txt(slide, 0.65, 3.3, 11.5, 0.7,
        [("Building an AI assistant that answers only from your documents.",
          18, MUTED, False, False, 1.1)])

    txt(slide, 0.65, 4.3, 8.5, 0.5, [("Case study: MetMate", 15, TEAL, True, False, None)])
    txt(slide, 0.65, 4.75, 9.5, 0.5,
        [("A chatbot answering student questions about Sydney Met's rules.", 13, MUTED, False, True, None)])

    if os.path.exists(LOGO_PATH):
        logo_h = 1.1
        logo_w_guess = logo_h * (1024 / 750)
        lx = SLIDE_W - 0.6 - logo_w_guess
        slide.shapes.add_picture(LOGO_PATH, Inches(lx), Inches(0.5), height=Inches(logo_h))

    fh = 0.9
    fy = SLIDE_H - fh
    footer = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(fy), prs.slide_width, Inches(fh))
    solid(footer, FOOTER_BG)
    no_line(footer)
    faccent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(fy), prs.slide_width, Inches(0.05))
    solid(faccent, TEAL)
    no_line(faccent)

    ftxt = txt(slide, 0.65, fy, 7.0, fh, [
        ("Tuesday 14 July 2026, 2–3 PM", 13, WHITE, False, False, None),
    ], anchor=MSO_ANCHOR.MIDDLE)

    frbox = slide.shapes.add_textbox(Inches(6.0), Inches(fy), Inches(6.68), Inches(fh))
    frtf = frbox.text_frame
    frtf.vertical_anchor = MSO_ANCHOR.MIDDLE
    frtf.word_wrap = True
    p1 = frtf.paragraphs[0]
    p1.alignment = PP_ALIGN.RIGHT
    r1 = p1.add_run(); r1.text = "Dr Mohammad Arifur Rahman"
    r1.font.name = FONT; r1.font.size = Pt(13.5); r1.font.color.rgb = TEAL; r1.font.bold = True
    p2 = frtf.add_paragraph()
    p2.alignment = PP_ALIGN.RIGHT
    r2 = p2.add_run(); r2.text = "Analyst Programmer  ·  Wimmera CMA, Victoria"
    r2.font.name = FONT; r2.font.size = Pt(10.5); r2.font.color.rgb = MUTED

    slide.notes_slide.notes_text_frame.text = notes
    return slide


def build_why_slide(prs, notes):
    slide = base_slide(prs, "WARM-UP", "Why not just use an existing chatbot?", notes)

    left_cx, right_cx = 3.6, 9.7
    icon_y = 2.55
    circle(slide, left_cx, icon_y, 1.3, fill=PANEL)
    outline(slide.shapes[-1], TEAL, 1.5)
    txt(slide, left_cx - 1.0, icon_y - 0.25, 2.0, 0.5, [("Chrome", 18, WHITE, True, False, None)],
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    txt(slide, left_cx - 1.6, icon_y + 0.85, 3.2, 0.5, [("common software — we don't build our own", 11, MUTED, False, True, None)],
        align=PP_ALIGN.CENTER)

    circle(slide, right_cx, icon_y, 1.3, fill=PANEL)
    outline(slide.shapes[-1], AMBER, 1.5)
    txt(slide, right_cx - 1.0, icon_y - 0.25, 2.0, 0.5, [("Chatbot", 18, WHITE, True, False, None)],
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    txt(slide, right_cx - 1.6, icon_y + 0.85, 3.2, 0.5, [("...but this, we often build ourselves?", 11, MUTED, False, True, None)],
        align=PP_ALIGN.CENTER)

    txt(slide, left_cx + 0.8, icon_y - 0.15, right_cx - left_cx - 1.6, 0.5,
        [("vs.", 22, MUTED, True, False, None)], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    reasons = [
        "Expectations are diversified: security, reliability, speed, cost",
        "The field is young — common expectations aren't well defined yet",
        "\"No-code\" builders exist — more complicated in practice, limited customisation",
        "It moves so fast, check again tomorrow",
    ]
    top = 4.35
    row_h = 0.62
    for i, reason in enumerate(reasons):
        y = top + i * row_h
        num = circle(slide, 1.15, y + 0.2, 0.42, fill=TEAL)
        centered_label(num, str(i + 1), 14, BG)
        txt(slide, 1.55, y, 10.3, 0.55, [(reason, 15, WHITE, False, False, None)], anchor=MSO_ANCHOR.MIDDLE)

    return slide


def build_step_frame(prs, n, title, breaks_text, notes):
    slide = base_slide(prs, f"STEP {n} OF 5", title, notes)
    badge = circle(slide, 1.1, 1.9, 0.7, fill=TEAL)
    centered_label(badge, str(n), 26, BG)
    if breaks_text:
        chip = card(slide, 8.6, 1.55, 4.05, 0.55, fill=PANEL, line_color=WRONG)
        txt(slide, 8.75, 1.55, 3.8, 0.55, [(breaks_text, 11.5, WRONG, True, True, None)], anchor=MSO_ANCHOR.MIDDLE)
    return slide


def build_step1(prs, notes):
    slide = build_step_frame(prs, 1, "Upload it to ChatGPT", "✗ can't scale to everyone", notes)

    txt(slide, 1.1, 2.55, 10.5, 0.5, [("The obvious first move: just upload the document to an existing chatbot.", 15, MUTED, False, True, None)])

    doc = card(slide, 1.6, 3.25, 2.2, 2.4, fill=PANEL, line_color=TEAL)
    txt(slide, 1.85, 3.5, 1.7, 0.4, [("student", 12, MUTED, False, False, None)], align=PP_ALIGN.CENTER)
    txt(slide, 1.85, 3.78, 1.7, 0.4, [("handbook.pdf", 13, WHITE, True, False, None)], align=PP_ALIGN.CENTER)
    for i in range(4):
        line_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.95), Inches(4.35 + i * 0.28), Inches(1.7), Inches(0.06))
        solid(line_shape, PANEL_LINE)
        no_line(line_shape)

    txt(slide, 4.15, 3.2, 1.55, 0.3, [("upload to", 11, MUTED, False, True, None)], align=PP_ALIGN.CENTER)
    arrow_right(slide, 4.0, 3.55, 1.4, fill=TEAL)

    bubble = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.65), Inches(3.25), Inches(2.75), Inches(2.4))
    solid(bubble, PANEL)
    outline(bubble, TEAL, 1.25)
    bubble.adjustments[0] = 0.12
    txt(slide, 5.9, 3.45, 2.3, 0.4, [("ChatGPT", 15, TEAL, True, False, None)], align=PP_ALIGN.CENTER)
    txt(slide, 5.9, 3.95, 2.3, 1.5, [("Answers well — for one document, one person, one paid seat", 13, WHITE, False, False, 1.2)],
        align=PP_ALIGN.CENTER)

    txt(slide, 8.9, 2.95, 3.75, 3.0, [
        ("To give this to every student, Sydney Met would need to:", 13.5, TEAL, True, False, 1.25),
        ("build its own ChatGPT-like product, or", 13, WHITE, False, False, 1.3),
        ("buy a paid subscription per student", 13, WHITE, False, False, 1.3),
        ("...while documents keep changing and", 13, WHITE, False, False, 1.3),
        ("thousands ask questions at once.", 13, WHITE, False, False, None),
    ])
    return slide


def build_architecture_slide(prs, notes):
    slide = base_slide(prs, "THE BIG PICTURE", "Here's the whole system, at a glance", notes)

    left = 0.9
    right = SLIDE_W - 0.9
    n = 5
    gap = 0.25
    box_w = (right - left - gap * (n - 1)) / n

    def bx(i):
        return left + i * (box_w + gap)

    top_y = 2.55
    top_h = 0.95
    txt(slide, left, top_y - 0.4, 8.0, 0.35, [("BUILT ONCE, BEFORE ANY QUESTION", 11.5, MUTED, True, False, None)])

    doc_card = card(slide, bx(0), top_y, box_w, top_h, fill=PANEL, line_color=PANEL_LINE)
    txt(slide, bx(0) + 0.1, top_y, box_w - 0.2, top_h, [("Documents", 14, WHITE, True, False, None)],
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    arrow_right(slide, bx(0) + box_w - 0.02, top_y + top_h / 2, gap + 0.04, h=0.2, fill=TEAL)

    idx_card = card(slide, bx(1), top_y, box_w, top_h, fill=PANEL, line_color=TEAL)
    txt(slide, bx(1) + 0.1, top_y, box_w - 0.2, top_h, [("Index\n(by meaning)", 14, WHITE, True, False, 1.1)],
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    txt(slide, bx(1) + 0.1, top_y + top_h + 0.06, box_w - 0.2, 0.3, [("zoom: Step 2", 10.5, AMBER, False, True, None)],
        align=PP_ALIGN.CENTER)

    down = slide.shapes.add_connector(1, Inches(bx(1) + box_w / 2), Inches(top_y + top_h + 0.35),
                                       Inches(bx(1) + box_w / 2), Inches(top_y + top_h + 0.85))
    down.line.color.rgb = TEAL
    down.line.width = Pt(2.25)

    bot_y = top_y + top_h + 0.95
    bot_h = 1.0
    txt(slide, left, bot_y - 0.4, 8.0, 0.35, [("EVERY QUESTION, LIVE", 11.5, MUTED, True, False, None)])

    labels = ["Student\nquestion", "Search the\nindex", "Draft\nanswer", "Check the\nanswer", "Final\nanswer"]
    tags = {1: "zoom: Step 3", 3: "zoom: Step 4 & 5"}
    for i, label in enumerate(labels):
        line_color = TEAL if i in (1, 3) else PANEL_LINE
        c = card(slide, bx(i), bot_y, box_w, bot_h, fill=PANEL, line_color=line_color)
        txt(slide, bx(i) + 0.08, bot_y, box_w - 0.16, bot_h, [(label, 13, WHITE, True, False, 1.1)],
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if i in tags:
            txt(slide, bx(i) + 0.05, bot_y + bot_h + 0.06, box_w - 0.1, 0.3, [(tags[i], 10.5, AMBER, False, True, None)],
                align=PP_ALIGN.CENTER)
        if i < n - 1:
            arrow_right(slide, bx(i) + box_w - 0.02, bot_y + bot_h / 2, gap + 0.04, h=0.2, fill=TEAL)

    txt(slide, left, bot_y + bot_h + 0.55, right - left, 0.5,
        [("Steps 2 to 5 each zoom into one box above. Keep this picture in mind as we go.", 12.5, MUTED, False, True, None)],
        align=PP_ALIGN.CENTER)
    return slide


def build_step2(prs, notes):
    slide = build_step_frame(prs, 2, "Teach it meaning (embeddings)", None, notes)

    txt(slide, 1.1, 2.55, 6.5, 0.5, [("Text → a point in \"meaning space\"", 16, MUTED, False, True, None)])

    plane = card(slide, 1.1, 3.15, 6.6, 3.3, fill=PANEL, line_color=PANEL_LINE)

    pts = {
        "queen": (2.6, 3.9),
        "female": (3.5, 5.4),
        "king": (5.9, 3.75),
        "male": (6.7, 5.15),
    }
    for name, (x, y) in pts.items():
        dot = circle(slide, x, y, 0.16, fill=AMBER if name in ("king", "queen") else TEAL)
        txt(slide, x - 0.7, y + 0.26, 1.6, 0.35, [(name, 12.5, WHITE, True, False, None)], align=PP_ALIGN.CENTER)

    def connector(p1, p2, color):
        x1, y1 = pts[p1]
        x2, y2 = pts[p2]
        line_shape = slide.shapes.add_connector(1, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        line_shape.line.color.rgb = color
        line_shape.line.width = Pt(2.25)

    connector("queen", "female", MUTED)
    connector("male", "king", MUTED)

    txt(slide, 8.05, 3.3, 4.55, 3.0, [
        ("queen − female + male ≈ king", 21, WHITE, True, False, 1.3),
        ("Similar meaning → nearby points,", 14, MUTED, False, False, 1.4),
        ("even with completely different words.", 14, MUTED, False, False, 1.2),
        ("This is how the system will later find", 14, MUTED, False, False, 1.4),
        ("the right passage for a question.", 14, MUTED, False, False, None),
    ])
    return slide


def build_step3(prs, notes):
    slide = build_step_frame(prs, 3, "Find the right passage (RAG)", "✗ grabbed the wrong rule", notes)

    qbubble = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.1), Inches(2.5), Inches(11.1), Inches(0.75))
    solid(qbubble, PANEL)
    outline(qbubble, TEAL, 1.25)
    qbubble.adjustments[0] = 0.3
    txt(slide, 1.4, 2.5, 10.5, 0.75, [("Student asks: “Can I access the library 24/7?”", 15, WHITE, True, True, None)],
        anchor=MSO_ANCHOR.MIDDLE)

    left = card(slide, 1.6, 3.7, 5.0, 2.35, fill=PANEL, line_color=WRONG)
    txt(slide, 1.9, 3.9, 4.4, 0.4, [("Exam Period Appendix", 13, WRONG, True, False, None)])
    txt(slide, 1.9, 4.35, 4.4, 0.9, [("“library access is 24/7 during exam period”", 12.5, WHITE, False, True, 1.2)])
    txt(slide, 1.9, 5.2, 4.4, 0.5, [("✗ matched on keywords — wrongly applied every week", 11, WRONG, True, False, None)])

    right = card(slide, 6.9, 3.7, 5.0, 2.35, fill=PANEL, line_color=TEAL)
    txt(slide, 7.2, 3.9, 4.4, 0.4, [("General Library Hours", 13, TEAL, True, False, None)])
    txt(slide, 7.2, 4.35, 4.4, 0.9, [("“open 8am–10pm, term time” — the rule that", 12.5, WHITE, False, False, 1.2), ("actually governs an ordinary week", 12.5, WHITE, False, False, None)])
    txt(slide, 7.2, 5.2, 4.4, 0.5, [("✓ the fix: attach WHEN each rule applies", 11, TEAL, True, False, None)])

    txt(slide, 1.6, 6.25, 10.3, 0.5, [("Fix: scope-aware retrieval — every passage carries its own context, not just its words.", 12.5, MUTED, False, True, None)])
    return slide


def build_step4(prs, notes):
    slide = build_step_frame(prs, 4, "Know what it knows", "✗ refused what it already had", notes)

    qbubble = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.1), Inches(2.5), Inches(11.1), Inches(0.75))
    solid(qbubble, PANEL)
    outline(qbubble, TEAL, 1.25)
    qbubble.adjustments[0] = 0.3
    txt(slide, 1.4, 2.5, 10.5, 0.75, [("Student asks: “How many kinds of special consideration are there?”", 15, WHITE, True, True, None)],
        anchor=MSO_ANCHOR.MIDDLE)

    left = card(slide, 1.6, 3.7, 5.0, 2.6, fill=PANEL, line_color=TEAL)
    txt(slide, 1.9, 3.9, 4.4, 0.4, [("Master index (table of contents)", 13, TEAL, True, False, None)])
    for i, item in enumerate(["Medical", "Bereavement", "Carer", "Equipment fault", "Misadventure", "Religious"]):
        y = 4.35 + i * 0.34
        txt(slide, 1.9, y, 4.2, 0.32, [(f"✓ {item}", 12, WHITE, False, False, None)])

    right = card(slide, 6.9, 3.7, 5.0, 2.6, fill=PANEL, line_color=WRONG)
    txt(slide, 7.2, 3.9, 4.4, 0.4, [("Retrieved passages this turn", 13, WRONG, True, False, None)])
    for i, item in enumerate(["Medical", "Bereavement"]):
        y = 4.35 + i * 0.34
        txt(slide, 7.2, y, 4.2, 0.32, [(f"✓ {item}", 12, WHITE, False, False, None)])
    for i, item in enumerate(["Carer", "Equipment fault", "Misadventure", "Religious"]):
        y = 4.35 + (i + 2) * 0.34
        txt(slide, 7.2, y, 4.2, 0.32, [(f"✗ {item} — “unsupported”", 12, MUTED, False, True, None)])

    txt(slide, 1.6, 6.55, 10.3, 0.5, [("Fix: trust the index for WHAT EXISTS; still require a real passage for any RULE DETAIL.", 12.5, MUTED, False, True, None)])
    return slide


def build_step5(prs, notes):
    slide = build_step_frame(prs, 5, "Never make it up", None, notes)

    draft = card(slide, 1.1, 2.7, 3.0, 1.5, fill=PANEL, line_color=TEAL)
    txt(slide, 1.3, 2.9, 2.6, 1.1, [("Draft answer", 13, WHITE, True, False, None), ("(not yet shown)", 11, MUTED, False, True, None)])

    arrow_right(slide, 4.25, 3.45, 1.0, fill=TEAL)

    gate = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, Inches(5.4), Inches(2.55), Inches(2.5), Inches(1.8))
    solid(gate, PANEL)
    outline(gate, AMBER, 1.5)
    txt(slide, 5.6, 3.15, 2.1, 0.6, [("Verifier:", 12.5, AMBER, True, False, None), ("grounded?", 12.5, WHITE, True, False, None)], align=PP_ALIGN.CENTER)

    arrow_right(slide, 8.05, 2.9, 1.0, fill=TEAL)
    pass_card = card(slide, 9.2, 2.5, 3.0, 0.9, fill=PANEL, line_color=TEAL)
    txt(slide, 9.4, 2.5, 2.6, 0.9, [("✓ Shown to student", 13, TEAL, True, False, None)], anchor=MSO_ANCHOR.MIDDLE)

    arrow_right(slide, 8.05, 4.0, 1.0, fill=WRONG)
    retry_card = card(slide, 9.2, 3.6, 3.0, 0.9, fill=PANEL, line_color=WRONG)
    txt(slide, 9.4, 3.6, 2.6, 0.9, [("✗ Retry / re-search once", 12.5, WRONG, True, False, None)], anchor=MSO_ANCHOR.MIDDLE)

    abstain = card(slide, 5.4, 4.85, 3.8, 0.9, fill=PANEL, line_color=MUTED)
    txt(slide, 5.6, 4.85, 3.4, 0.9, [("Still not grounded → admit it honestly", 12.5, MUTED, True, True, None)], anchor=MSO_ANCHOR.MIDDLE)

    txt(slide, 1.1, 6.0, 10.5, 0.7, [("Confidence and correctness are not the same thing for a language model — this gate is what closes the gap.", 13, WHITE, False, False, 1.2)])
    return slide


def build_closing(prs, notes):
    slide = base_slide(prs, "RECAP", "Five steps, five instructive failures", notes)

    steps = [
        ("1", "Upload a PDF", "doesn't scale"),
        ("2", "Embeddings", "teach it meaning"),
        ("3", "RAG", "grabbed wrong rule"),
        ("4", "Know its knowledge", "refused too much"),
        ("5", "Grounding", "never make it up"),
    ]
    left = 0.9
    right = SLIDE_W - 0.9
    n = len(steps)
    gap = 0.3
    w = (right - left - gap * (n - 1)) / n
    y = 2.7
    h = 2.4
    for i, (num, title, hint) in enumerate(steps):
        x = left + i * (w + gap)
        c = card(slide, x, y, w, h, fill=PANEL, line_color=PANEL_LINE)
        badge = circle(slide, x + w / 2, y + 0.55, 0.55, fill=TEAL)
        centered_label(badge, num, 18, BG)
        txt(slide, x + 0.15, y + 1.1, w - 0.3, 0.6, [(title, 13.5, WHITE, True, False, None)], align=PP_ALIGN.CENTER)
        txt(slide, x + 0.15, y + 1.65, w - 0.3, 0.6, [(hint, 10.5, AMBER, False, True, 1.1)], align=PP_ALIGN.CENTER)
        if i < n - 1:
            arrow_right(slide, x + w - 0.02, y + h / 2, gap + 0.04, h=0.22, fill=TEAL)

    txt(slide, 0.9, 5.55, 11.5, 1.0, [("Thank you — questions?", 30, WHITE, True, False, None)], align=PP_ALIGN.CENTER)
    return slide


NOTES = {
    "title": (
        "Good afternoon everyone, thanks for having me. I'm Arif, Analyst Programmer at Wimmera CMA in "
        "regional Victoria. Over the past year I've built several AI-powered tools for my organisation, but "
        "only a handful of them ended up genuinely used to solve a real problem — the rest were experiments. "
        "One that's in real daily use is a chatbot. Today I want to walk you through what it actually takes to "
        "build one properly, using the real problems I ran into along the way. Since I can't share my "
        "workplace's internal documents publicly, we'll use a stand-in case study: imagine a chatbot for "
        "Sydney Met itself, answering student questions about enrolment, library, and exam rules. Let's call "
        "it MetMate. Same ideas, public-friendly example."
    ),
    "why": (
        "Before we build anything, a fair question: chatbots are common now, so why doesn't everyone just grab "
        "one off the shelf, the way we grab Chrome for browsing? Nobody builds their own browser. Four reasons "
        "this is different, at least today. First, expectations are actually diversified — one organisation "
        "cares most about security and data residency, another about raw speed, another about cost, another "
        "about reliability under heavy use. A browser mostly just needs to render a page; a chatbot's bar "
        "depends entirely on who's asking. Second, this field is comparatively new, so common expectations "
        "aren't even well defined yet — there's no agreed checklist like there is for browsers. Third, "
        "'no-code' chatbot builders exist that promise exactly this, but in my own experience they're more "
        "complicated to use well than they claim, and how far you can customise the behaviour is limited. "
        "Fourth, and I say this half-joking, this space moves so fast that a genuinely good ready-made bot "
        "might exist by the time we finish this lecture — but when I checked before preparing this, it wasn't "
        "there yet. So for now, if you want a chatbot that fits your exact constraints, you still have to build "
        "one, or at least understand how it's built well enough to steer it."
    ),
    "step1": (
        "So let's build MetMate from scratch, and at every step we'll do the lazy obvious thing first, watch it "
        "break, and let that break motivate the next idea. Step one: the laziest possible chatbot. Take an "
        "existing product like ChatGPT, upload the student handbook PDF, and start asking it questions. It "
        "genuinely works, for one document, one person, one paid seat. But look at what 'just use ChatGPT' "
        "actually means for an institution: to give this to every student, Sydney Met would either have to "
        "build its own ChatGPT-like product from scratch, or buy a paid subscription seat for every single "
        "student — and either way, the documents keep changing and thousands of students need answers at the "
        "same time. Neither option scales. We need something that serves everyone at once, from one shared, "
        "always-current source of truth. That's the real engineering problem starting here."
    ),
    "architecture": (
        "Before we zoom into each concept one at a time, here's the full picture of what we're actually going "
        "to build, so you have a map to place each piece on as we go. Two halves. The top half happens once, "
        "ahead of time, before any student asks anything: every document gets broken up and organised into an "
        "index built around meaning, not exact words — that's what step two is about. The bottom half happens "
        "every single time a student asks a question, live: the question searches that index, pulls out a "
        "draft answer, and — this is the part that took the most work — checks that draft against the real "
        "source before it's ever shown to the student. Steps three, four, and five are really just zooming "
        "into different parts of that second row: how search finds the right passage, and how the system "
        "checks and knows what it does and doesn't actually know before it speaks. Keep this picture in your "
        "head; everything from here is detail on one box of it."
    ),
    "step2": (
        "To search across many documents automatically, the computer needs to understand what a question and a "
        "passage MEAN, not just whether the words match exactly. That's what an embedding does: it converts a "
        "piece of text into a list of numbers — think of it as plotting the text as a point in space, where "
        "meaning determines position. Texts about similar things land near each other, even without sharing any "
        "words. The classic illustration: take the point for 'queen', subtract the direction for 'female', add "
        "the direction for 'male', and you land close to 'king'. The model captured a real relationship purely "
        "from patterns in language, as geometry. Once every chunk of every document is turned into one of these "
        "points, and the student's question is turned into a point too, finding a relevant passage becomes: "
        "find the nearby points. That's the foundation everything else sits on."
    ),
    "step3": (
        "Now search actually works: a student asks 'can I access the library 24/7?' and the system finds the "
        "passage that mentions '24/7' access most closely. But here's the trap: that passage only exists in a "
        "rule for exam period, buried in an appendix — the general everyday rule says the library is open 8am "
        "to 10pm, term time. Because the exam-period rule contains the exact phrase the question echoes, it "
        "gets pulled up and answered as if it always applies — a confident, wrong answer, sourced from a real "
        "document, based purely on words matching rather than whether that rule actually governs right now. "
        "This is the single most important failure mode of naive AI search: matching on keywords instead of "
        "relevance or scope. The fix is to make sure every retrieved passage carries the context of WHEN it "
        "applies — attach that condition directly to the passage when it's stored, so retrieval and the model "
        "both see it, not just the raw sentence. Get this wrong and your chatbot confidently tells students the "
        "wrong thing, which is almost worse than not answering at all."
    ),
    "step4": (
        "Good, MetMate now avoids the wrong-rule trap. But a new failure shows up: a student asks 'how many "
        "kinds of special consideration are there for exams?' MetMate correctly lists them all — say six "
        "categories — because it has a master index, a table of contents of every rule section, and that "
        "index genuinely lists six. But then a safety check kicks in: a second pass verifies every claim "
        "against the actual passages retrieved for search. That check only had snippets for two of the six "
        "categories in hand, so it marks the other four 'unsupported' and throws the whole answer away — the "
        "bot tells the student 'I couldn't confidently find this', on a question it clearly could answer. The "
        "fix is to give that safety check two different sources of truth: use the master index as the "
        "authority for what EXISTS or how many there are, since it's built directly from the real documents, "
        "but still require an actual retrieved passage before trusting any DETAIL about one specific category. "
        "Existence and detail need different evidence. Miss that distinction and your bot becomes needlessly "
        "shy on exactly the questions it's best equipped to answer."
    ),
    "step5": (
        "Put steps three and four together and you get the real design principle behind a trustworthy chatbot: "
        "never let it show an answer it hasn't checked against the source first. Every draft answer goes "
        "through a verifier before the student ever sees it — did every claim actually come from a real, "
        "applicable rule? If yes, show it. If a claim doesn't check out, don't show it anyway — try again, "
        "maybe search once more with a refined question, and only if it genuinely still can't find solid "
        "grounding, tell the student honestly that it doesn't know, rather than guessing. That's the "
        "difference between a chatbot that sounds confident and one you can actually rely on. Confidence and "
        "correctness are not the same thing for a language model — it will happily generate a fluent, wrong "
        "answer unless you build a mechanism that catches it before publishing. This calibrated honesty — "
        "answer only when genuinely grounded, admit it when not — is really the whole reliability story in "
        "one sentence."
    ),
    "closing": (
        "So, five steps, five instructive failures: uploading one PDF doesn't scale; raw keyword-ish search "
        "grabs confident wrong rules; a verifier without the right authority becomes needlessly shy; and the "
        "fix running through both is the same idea — give every piece of information the CONTEXT it needs, "
        "whether that's when a rule applies, or what actually counts as evidence. That's what took this "
        "project from a demo to something people actually rely on daily. Happy to take questions, on any of "
        "these five steps, or anything else about how AI systems like this get built in practice."
    ),
}


def main():
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)

    build_title_slide(prs, NOTES["title"])
    build_why_slide(prs, NOTES["why"])
    build_step1(prs, NOTES["step1"])
    build_architecture_slide(prs, NOTES["architecture"])
    build_step2(prs, NOTES["step2"])
    build_step3(prs, NOTES["step3"])
    build_step4(prs, NOTES["step4"])
    build_step5(prs, NOTES["step5"])
    build_closing(prs, NOTES["closing"])

    prs.save(OUT_PATH)
    print("saved", OUT_PATH)


if __name__ == "__main__":
    main()
