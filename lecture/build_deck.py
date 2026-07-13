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


def straight_line(slide, x1, y1, x2, y2, color, width_pt):
    shape = slide.shapes.add_connector(1, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    shape.line.color.rgb = color
    shape.line.width = Pt(width_pt)
    return shape


MAP_PREP_BOXES = ["Docs", "Index"]
MAP_LIVE_BOXES = ["Question", "Search", "Draft", "Check", "Reply"]


def add_mini_map(slide, active_names):
    left = 9.35
    top = 0.42
    box_w = 0.62
    box_h = 0.30
    gap = 0.07
    live_y = top + box_h + 0.14

    def draw_map_box(name, x, y):
        is_active = name in active_names
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(box_w), Inches(box_h))
        shape.adjustments[0] = 0.18
        if is_active:
            solid(shape, TEAL)
            no_line(shape)
            centered_label(shape, name, 7.5, BG, bold=True)
        else:
            solid(shape, PANEL)
            outline(shape, PANEL_LINE, 0.75)
            centered_label(shape, name, 7.5, MUTED, bold=False)
        if is_active:
            lens_w = box_w + 0.2
            lens_h = box_h + 0.2
            cx = x + box_w / 2
            cy = y + box_h / 2
            lens = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - lens_w / 2), Inches(cy - lens_h / 2),
                                           Inches(lens_w), Inches(lens_h))
            lens.fill.background()
            outline(lens, AMBER, 1.75)
            straight_line(slide, cx + lens_w * 0.33, cy + lens_h * 0.42,
                          cx + lens_w * 0.33 + 0.13, cy + lens_h * 0.42 + 0.13, AMBER, 2.25)

    for i, name in enumerate(MAP_PREP_BOXES):
        draw_map_box(name, left + i * (box_w + gap), top)
    straight_line(slide, left + 1.5 * box_w + gap, top + box_h,
                  left + 1.5 * box_w + gap, live_y, MUTED, 1.0)
    for i, name in enumerate(MAP_LIVE_BOXES):
        draw_map_box(name, left + i * (box_w + gap), live_y)


def base_slide(prs, eyebrow_label, title, notes, mini_map_active=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    solid(bg, BG)
    no_line(bg)

    strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.16), prs.slide_height)
    solid(strip, TEAL)
    no_line(strip)

    eb = txt(slide, 0.65, 0.4, 8.5, 0.4, [(eyebrow_label, 12.5, TEAL, True, False, None)])
    set_letterspacing(eb.text_frame.paragraphs[0].runs[0], 2.2)

    txt(slide, 0.63, 0.74, 8.6, 0.9, [(title, 30, WHITE, True, False, 1.0)])

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
    txt(slide, 0.65, fy, 8.0, fh, [("ICT108  ·  MetMate case study", 10.5, MUTED, False, False, None)],
        anchor=MSO_ANCHOR.MIDDLE)

    if mini_map_active:
        add_mini_map(slide, mini_map_active)

    slide.notes_slide.notes_text_frame.text = notes
    return slide


def failure_chip(slide, text, x=8.6, y=1.62, w=4.05):
    chip = card(slide, x, y, w, 0.55, fill=PANEL, line_color=WRONG)
    txt(slide, x + 0.15, y, w - 0.3, 0.55, [(text, 11.5, WRONG, True, True, None)], anchor=MSO_ANCHOR.MIDDLE)
    return chip


def build_s01_title(prs, notes):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    solid(bg, BG)
    no_line(bg)
    strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.16), prs.slide_height)
    solid(strip, TEAL)
    no_line(strip)

    eb = txt(slide, 0.65, 1.35, 11.5, 0.4,
             [("GUEST LECTURE   ·   ICT108", 13, TEAL, True, False, None)])
    set_letterspacing(eb.text_frame.paragraphs[0].runs[0], 2.4)

    txt(slide, 0.62, 1.8, 12.0, 1.3, [("Talk to Your Documents", 48, WHITE, True, False, 1.0)])

    ul = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.68), Inches(2.85), Inches(1.9), Inches(0.08))
    solid(ul, AMBER)
    no_line(ul)

    txt(slide, 0.65, 3.1, 11.5, 0.7,
        [("Building an AI assistant that answers only from your documents — the way it happens in real life.",
          17, MUTED, False, False, 1.1)])

    txt(slide, 0.65, 4.0, 8.5, 0.5, [("Case study: MetMate", 15, TEAL, True, False, None)])
    txt(slide, 0.65, 4.45, 9.5, 0.5,
        [("A chatbot answering student questions about Sydney Met's rules.", 13, MUTED, False, True, None)])

    note = card(slide, 0.65, 5.2, 9.4, 0.85, fill=PANEL, line_color=PANEL_LINE)
    txt(slide, 0.9, 5.2, 8.9, 0.85,
        [("Concepts over terminology today — new terms arrive daily. Miss one? It will come back,", 12, MUTED, False, True, 1.25),
         ("or you can look it up later. You will follow the ideas either way.", 12, MUTED, False, True, None)],
        anchor=MSO_ANCHOR.MIDDLE)

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

    txt(slide, 0.65, fy, 7.0, fh, [
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


def build_s02_upload_chatgpt(prs, notes):
    slide = base_slide(prs, "WARM-UP", "Why not just upload it to ChatGPT?", notes)
    failure_chip(slide, "✗ works for one — can't scale to all")

    txt(slide, 1.1, 2.45, 10.5, 0.5, [("The laziest possible chatbot: upload the handbook to an existing product.", 15, MUTED, False, True, None)])

    doc = card(slide, 1.6, 3.15, 2.2, 2.4, fill=PANEL, line_color=TEAL)
    txt(slide, 1.85, 3.4, 1.7, 0.4, [("student", 12, MUTED, False, False, None)], align=PP_ALIGN.CENTER)
    txt(slide, 1.85, 3.68, 1.7, 0.4, [("handbook.pdf", 13, WHITE, True, False, None)], align=PP_ALIGN.CENTER)
    for i in range(4):
        line_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.95), Inches(4.25 + i * 0.28), Inches(1.7), Inches(0.06))
        solid(line_shape, PANEL_LINE)
        no_line(line_shape)

    txt(slide, 4.15, 3.1, 1.55, 0.3, [("upload to", 11, MUTED, False, True, None)], align=PP_ALIGN.CENTER)
    arrow_right(slide, 4.0, 3.45, 1.4, fill=TEAL)

    bubble = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.65), Inches(3.15), Inches(2.75), Inches(2.4))
    solid(bubble, PANEL)
    outline(bubble, TEAL, 1.25)
    bubble.adjustments[0] = 0.12
    txt(slide, 5.9, 3.35, 2.3, 0.4, [("ChatGPT", 15, TEAL, True, False, None)], align=PP_ALIGN.CENTER)
    txt(slide, 5.9, 3.85, 2.3, 1.5, [("Answers well — for one document, one person, one paid seat", 13, WHITE, False, False, 1.2)],
        align=PP_ALIGN.CENTER)

    txt(slide, 8.9, 2.85, 3.75, 3.2, [
        ("To give this to every student, Sydney Met would need to:", 13.5, TEAL, True, False, 1.25),
        ("build its own ChatGPT-like product, or", 13, WHITE, False, False, 1.3),
        ("buy a paid subscription per student", 13, WHITE, False, False, 1.3),
        ("...while documents keep changing and", 13, WHITE, False, False, 1.3),
        ("thousands ask questions at once.", 13, WHITE, False, False, None),
    ])

    txt(slide, 1.6, 6.15, 10.3, 0.5, [("We need one shared bot, always current, serving everyone at once — so we build.", 13, WHITE, False, False, None)])
    return slide


def build_s03_why_not_ready_made(prs, notes):
    slide = base_slide(prs, "WARM-UP", "Why not any ready-made chatbot?", notes)

    left_cx, right_cx = 3.6, 9.7
    icon_y = 2.45
    chrome_circle = circle(slide, left_cx, icon_y, 1.25, fill=PANEL)
    outline(chrome_circle, TEAL, 1.5)
    txt(slide, left_cx - 1.0, icon_y - 0.25, 2.0, 0.5, [("Chrome", 17, WHITE, True, False, None)],
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    txt(slide, left_cx - 1.6, icon_y + 0.8, 3.2, 0.5, [("common software — we don't build our own", 11, MUTED, False, True, None)],
        align=PP_ALIGN.CENTER)

    bot_circle = circle(slide, right_cx, icon_y, 1.25, fill=PANEL)
    outline(bot_circle, AMBER, 1.5)
    txt(slide, right_cx - 1.0, icon_y - 0.25, 2.0, 0.5, [("Chatbot", 17, WHITE, True, False, None)],
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    txt(slide, right_cx - 1.6, icon_y + 0.8, 3.2, 0.5, [("...but this, we often build ourselves?", 11, MUTED, False, True, None)],
        align=PP_ALIGN.CENTER)

    txt(slide, left_cx + 0.8, icon_y - 0.15, right_cx - left_cx - 1.6, 0.5,
        [("vs.", 22, MUTED, True, False, None)], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    reasons = [
        "Expectations are diversified: security, reliability, speed, cost",
        "The field is young — common expectations aren't well defined yet",
        "\"No-code\" builders exist — more complicated in practice, limited customisation",
        "It moves so fast, check again tomorrow",
    ]
    top = 3.95
    row_h = 0.56
    for i, reason in enumerate(reasons):
        y = top + i * row_h
        num = circle(slide, 1.15, y + 0.2, 0.42, fill=TEAL)
        centered_label(num, str(i + 1), 14, BG)
        txt(slide, 1.55, y, 10.3, 0.5, [(reason, 14.5, WHITE, False, False, None)], anchor=MSO_ANCHOR.MIDDLE)

    txt(slide, 1.15, 6.35, 11.0, 0.45,
        [("...and beyond these: every domain adds needs of its own — hold that thought for the end.", 12.5, AMBER, False, True, None)])
    return slide


def build_s04_birdseye(prs, notes):
    slide = base_slide(prs, "THE MAP", "MetMate at a glance", notes)

    left = 0.9
    right = SLIDE_W - 0.9
    n = 5
    gap = 0.25
    box_w = (right - left - gap * (n - 1)) / n

    def bx(i):
        return left + i * (box_w + gap)

    top_y = 2.3
    top_h = 0.8
    txt(slide, left, top_y - 0.37, 8.0, 0.32, [("BUILT ONCE, BEFORE ANY QUESTION", 11, MUTED, True, False, None)])

    card(slide, bx(0), top_y, box_w, top_h, fill=PANEL, line_color=PANEL_LINE)
    txt(slide, bx(0) + 0.1, top_y, box_w - 0.2, top_h, [("Documents", 13.5, WHITE, True, False, None)],
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    arrow_right(slide, bx(0) + box_w - 0.02, top_y + top_h / 2, gap + 0.04, h=0.2, fill=TEAL)

    card(slide, bx(1), top_y, box_w, top_h, fill=PANEL, line_color=TEAL)
    txt(slide, bx(1) + 0.1, top_y, box_w - 0.2, top_h, [("Index\n(searchable form)", 13, WHITE, True, False, 1.1)],
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    straight_line(slide, bx(1) + box_w / 2, top_y + top_h + 0.05,
                  bx(1) + box_w / 2, top_y + top_h + 0.5, TEAL, 2.25)

    bot_y = top_y + top_h + 0.6
    bot_h = 0.9
    txt(slide, left, bot_y + bot_h + 0.08, 8.0, 0.32, [("EVERY QUESTION, LIVE", 11, MUTED, True, False, None)])

    labels = ["Student\nquestion", "Search the\nindex", "Draft\nanswer", "Check the\nanswer", "Reply"]
    for i, label in enumerate(labels):
        line_color = TEAL if i in (1, 3) else PANEL_LINE
        card(slide, bx(i), bot_y, box_w, bot_h, fill=PANEL, line_color=line_color)
        txt(slide, bx(i) + 0.08, bot_y, box_w - 0.16, bot_h, [(label, 13, WHITE, True, False, 1.1)],
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if i < n - 1:
            arrow_right(slide, bx(i) + box_w - 0.02, bot_y + bot_h / 2, gap + 0.04, h=0.2, fill=TEAL)

    chips = [
        ("The classic first project", "every LLM course starts with a chatbot — with decent hardware you can build one fully on your own machine"),
        ("No standard blueprint yet", "a young, fast-growing field with many designs — this diagram is one way: the way we built it"),
        ("Real users → real APIs", "OpenAI: text into meaning-points + fast chores  ·  Anthropic: writes the answers  ·  Cohere: re-ranks results"),
    ]
    chip_y = 5.35
    chip_h = 1.25
    chip_w = (right - left - 2 * 0.22) / 3
    for i, (head, body) in enumerate(chips):
        x = left + i * (chip_w + 0.22)
        card(slide, x, chip_y, chip_w, chip_h, fill=PANEL, line_color=PANEL_LINE)
        txt(slide, x + 0.2, chip_y + 0.12, chip_w - 0.4, 0.35, [(head, 12.5, TEAL, True, False, None)])
        txt(slide, x + 0.2, chip_y + 0.48, chip_w - 0.4, 0.7, [(body, 10, MUTED, False, False, 1.15)])
    return slide


def build_s05_phase1_build(prs, notes):
    slide = base_slide(prs, "PHASE 1 — BUILD", "Phase 1 — just match the words", notes,
                       mini_map_active=["Search"])

    txt(slide, 1.1, 2.3, 8.0, 0.45,
        [("Search = count the words a passage shares with the question. Most overlap wins.", 14, MUTED, False, True, None)])

    qbubble = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.1), Inches(2.9), Inches(7.4), Inches(0.6))
    solid(qbubble, PANEL)
    outline(qbubble, TEAL, 1.25)
    qbubble.adjustments[0] = 0.3
    txt(slide, 1.4, 2.9, 6.9, 0.6, [("“When is the library open?”", 14, WHITE, True, True, None)],
        anchor=MSO_ANCHOR.MIDDLE)

    rows = [
        ("Passage A", 2.4, "shares 4 words — top result ✓", TEAL, WHITE),
        ("Passage B", 1.2, "shares 2 words", PANEL_LINE, MUTED),
        ("Passage C", 0.08, "shares 0 words", PANEL_LINE, MUTED),
    ]
    for i, (name, bar_w, score_text, line_color, score_color) in enumerate(rows):
        y = 3.8 + i * 0.75
        card(slide, 1.1, y, 7.4, 0.6, fill=PANEL, line_color=line_color)
        txt(slide, 1.35, y, 1.6, 0.6, [(name, 12.5, WHITE, True, False, None)], anchor=MSO_ANCHOR.MIDDLE)
        bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.0), Inches(y + 0.19), Inches(bar_w), Inches(0.22))
        solid(bar, TEAL if line_color is TEAL else PANEL_LINE)
        no_line(bar)
        bar.adjustments[0] = 0.5
        txt(slide, 5.6, y, 2.8, 0.6, [(score_text, 11.5, score_color, True, False, None)], anchor=MSO_ANCHOR.MIDDLE)

    txt(slide, 9.0, 3.4, 3.65, 2.6, [
        ("Decades-old search:", 13.5, TEAL, True, False, 1.3),
        ("fast, simple, no AI needed.", 12.5, WHITE, False, False, 1.35),
        ("Rare words count extra;", 12.5, WHITE, False, False, 1.35),
        ("best overlap wins.", 12.5, WHITE, False, False, None),
    ])

    txt(slide, 1.1, 6.2, 11.2, 0.5,
        [("The winning passages go to the language model to phrase a reply — that's the whole phase-1 bot.", 12.5, MUTED, False, True, None)])
    return slide


def build_s06_phase1_breaks(prs, notes):
    slide = base_slide(prs, "PHASE 1 — IT BREAKS", "Phase 1 breaks: right words, wrong rule", notes,
                       mini_map_active=["Search"])
    failure_chip(slide, "✗ high score, wrong rule", x=1.1, y=1.98, w=3.3)

    qbubble = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.1), Inches(2.72), Inches(11.1), Inches(0.7))
    solid(qbubble, PANEL)
    outline(qbubble, TEAL, 1.25)
    qbubble.adjustments[0] = 0.3
    txt(slide, 1.4, 2.72, 10.5, 0.7, [("Student asks: “Can I access the library 24/7?”", 15, WHITE, True, True, None)],
        anchor=MSO_ANCHOR.MIDDLE)

    card(slide, 1.6, 3.75, 5.0, 2.35, fill=PANEL, line_color=WRONG)
    txt(slide, 1.9, 3.95, 4.4, 0.4, [("Exam Period Appendix", 13, WRONG, True, False, None)])
    txt(slide, 1.9, 4.4, 4.4, 0.9, [("“library access is 24/7 during exam period”", 12.5, WHITE, False, True, 1.2)])
    txt(slide, 1.9, 5.35, 4.4, 0.5, [("shares 3 words → top result ✗", 11.5, WRONG, True, False, None)])

    card(slide, 6.9, 3.75, 5.0, 2.35, fill=PANEL, line_color=TEAL)
    txt(slide, 7.2, 3.95, 4.4, 0.4, [("General Library Hours", 13, TEAL, True, False, None)])
    txt(slide, 7.2, 4.4, 4.4, 0.9, [("“open 8am–10pm, term time” — the rule that", 12.5, WHITE, False, False, 1.2),
                                     ("actually governs an ordinary week", 12.5, WHITE, False, False, None)])
    txt(slide, 7.2, 5.35, 4.4, 0.5, [("shares 1 word → ranked low", 11.5, MUTED, True, False, None)])

    txt(slide, 1.6, 6.3, 10.3, 0.5,
        [("Every word came from a real document — and the answer is still wrong. Phase 1 is dead.", 13, WHITE, False, False, None)])
    return slide


def build_s07_phase2_meaning(prs, notes):
    slide = base_slide(prs, "PHASE 2 — THE FIX", "Phase 2 — search by meaning", notes,
                       mini_map_active=["Index", "Search"])

    txt(slide, 1.1, 2.35, 6.5, 0.5, [("Text → a point in \"meaning space\"", 15, MUTED, False, True, None)])

    card(slide, 1.1, 2.95, 6.6, 3.3, fill=PANEL, line_color=PANEL_LINE)

    pts = {
        "queen": (2.6, 3.7),
        "female": (3.5, 5.2),
        "king": (5.9, 3.55),
        "male": (6.7, 4.95),
    }
    for name, (x, y) in pts.items():
        circle(slide, x, y, 0.16, fill=AMBER if name in ("king", "queen") else TEAL)
        txt(slide, x - 0.7, y + 0.26, 1.6, 0.35, [(name, 12.5, WHITE, True, False, None)], align=PP_ALIGN.CENTER)

    straight_line(slide, pts["queen"][0], pts["queen"][1], pts["female"][0], pts["female"][1], MUTED, 2.25)
    straight_line(slide, pts["male"][0], pts["male"][1], pts["king"][0], pts["king"][1], MUTED, 2.25)

    txt(slide, 8.05, 3.0, 4.55, 3.3, [
        ("queen − female + male ≈ king", 20, WHITE, True, False, 1.35),
        ("Similar meaning → nearby points,", 13.5, MUTED, False, False, 1.4),
        ("even with zero shared words.", 13.5, MUTED, False, False, 1.35),
        ("Every passage becomes a point;", 13.5, MUTED, False, False, 1.4),
        ("the question becomes a point;", 13.5, MUTED, False, False, 1.35),
        ("search = find the nearby points.", 13.5, MUTED, False, False, 1.5),
        ("That's half the fix.", 13, AMBER, False, True, None),
    ])
    return slide


def build_s08_phase2_scope(prs, notes):
    slide = base_slide(prs, "PHASE 2 — THE FIX", "Phase 2 — say when each rule applies", notes,
                       mini_map_active=["Index"])

    txt(slide, 1.1, 2.3, 11.0, 0.45,
        [("Meaning search still finds the exam-period passage — it IS about library access. So store every rule with its scope.", 13.5, MUTED, False, True, None)])

    tag1 = card(slide, 1.1, 3.0, 1.95, 0.42, fill=AMBER, line_color=AMBER, radius=0.5)
    centered_label(tag1, "EXAM PERIOD ONLY", 9.5, BG)
    card(slide, 1.1, 3.42, 5.6, 0.95, fill=PANEL, line_color=PANEL_LINE)
    txt(slide, 1.35, 3.42, 5.1, 0.95, [("“library access is 24/7 during exam period”", 12.5, WHITE, False, True, None)],
        anchor=MSO_ANCHOR.MIDDLE)

    tag2 = card(slide, 1.1, 4.75, 1.4, 0.42, fill=AMBER, line_color=AMBER, radius=0.5)
    centered_label(tag2, "TERM TIME", 9.5, BG)
    card(slide, 1.1, 5.17, 5.6, 0.95, fill=PANEL, line_color=PANEL_LINE)
    txt(slide, 1.35, 5.17, 5.1, 0.95, [("“open 8am–10pm, term time”", 12.5, WHITE, False, True, None)],
        anchor=MSO_ANCHOR.MIDDLE)

    arrow_right(slide, 7.0, 4.55, 0.9, fill=TEAL)

    card(slide, 8.1, 3.6, 4.55, 1.95, fill=PANEL, line_color=TEAL)
    txt(slide, 8.35, 3.8, 4.05, 0.4, [("MetMate now answers:", 13, TEAL, True, False, None)])
    txt(slide, 8.35, 4.25, 4.05, 1.2, [("“8am–10pm in term time;", 13.5, WHITE, False, False, 1.3),
                                        ("24/7 only during exam period.” ✓", 13.5, WHITE, False, False, None)])

    txt(slide, 1.1, 6.25, 11.4, 0.5,
        [("A rule that carries its own scope can be set aside when its conditions don't hold. Phase 2 answers correctly.", 12.5, MUTED, False, True, None)])
    return slide


def build_s09_phase3_breaks(prs, notes):
    slide = base_slide(prs, "PHASE 3 — IT BREAKS", "Phase 3 — it refuses what it knows", notes,
                       mini_map_active=["Check"])
    failure_chip(slide, "✗ threw away a correct answer", x=1.1, y=1.98, w=3.7)

    qbubble = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.1), Inches(2.72), Inches(11.1), Inches(0.7))
    solid(qbubble, PANEL)
    outline(qbubble, TEAL, 1.25)
    qbubble.adjustments[0] = 0.3
    txt(slide, 1.4, 2.72, 10.5, 0.7, [("Student asks: “How many kinds of special consideration are there?”", 15, WHITE, True, True, None)],
        anchor=MSO_ANCHOR.MIDDLE)

    card(slide, 1.6, 3.7, 5.0, 2.5, fill=PANEL, line_color=TEAL)
    txt(slide, 1.9, 3.85, 4.4, 0.4, [("Master list (built from the documents)", 12.5, TEAL, True, False, None)])
    for i, item in enumerate(["Medical", "Bereavement", "Carer", "Equipment fault", "Misadventure", "Religious"]):
        y = 4.28 + i * 0.31
        txt(slide, 1.9, y, 4.2, 0.3, [(f"✓ {item}", 11.5, WHITE, False, False, None)])

    card(slide, 6.9, 3.7, 5.0, 2.5, fill=PANEL, line_color=WRONG)
    txt(slide, 7.2, 3.85, 4.4, 0.4, [("Passages the search pulled this turn", 12.5, WRONG, True, False, None)])
    for i, item in enumerate(["Medical", "Bereavement"]):
        y = 4.28 + i * 0.31
        txt(slide, 7.2, y, 4.2, 0.3, [(f"✓ {item}", 11.5, WHITE, False, False, None)])
    for i, item in enumerate(["Carer", "Equipment fault", "Misadventure", "Religious"]):
        y = 4.28 + (i + 2) * 0.31
        txt(slide, 7.2, y, 4.2, 0.3, [(f"✗ {item} — “unsupported”", 11.5, MUTED, False, True, None)])

    txt(slide, 1.6, 6.35, 10.3, 0.5,
        [("The checker kills the whole answer: “I couldn't confidently find this.” Too shy is a failure too.", 13, WHITE, False, False, None)])
    return slide


def build_s10_phase3_fix(prs, notes):
    slide = base_slide(prs, "PHASE 3 — THE FIX", "Phase 3 — the right evidence per claim", notes,
                       mini_map_active=["Check"])

    card(slide, 1.1, 2.45, 5.6, 1.5, fill=PANEL, line_color=TEAL)
    txt(slide, 1.35, 2.62, 5.1, 0.4, [("What exists / how many", 14, TEAL, True, False, None)])
    txt(slide, 1.35, 3.05, 5.1, 0.8, [("Trust the master list — it was built", 12.5, WHITE, False, False, 1.25),
                                       ("directly from the documents.", 12.5, WHITE, False, False, None)])

    card(slide, 7.0, 2.45, 5.6, 1.5, fill=PANEL, line_color=AMBER)
    txt(slide, 7.25, 2.62, 5.1, 0.4, [("Details of one specific rule", 14, AMBER, True, False, None)])
    txt(slide, 7.25, 3.05, 5.1, 0.8, [("Require the actual passage.", 12.5, WHITE, False, False, 1.25),
                                       ("No passage, no claim.", 12.5, WHITE, False, False, None)])

    txt(slide, 1.1, 4.25, 11.0, 0.4, [("And when a claim truly has neither:", 13, MUTED, False, True, None)])

    flow = [
        ("Claim still unsupported", PANEL_LINE),
        ("Search once more, sharper", PANEL_LINE),
        ("Answer — or an honest “I don't know”", TEAL),
    ]
    fx = [1.1, 5.05, 9.0]
    fw = [3.5, 3.5, 3.65]
    fy = 4.75
    fh2 = 0.85
    for i, (label, line_color) in enumerate(flow):
        card(slide, fx[i], fy, fw[i], fh2, fill=PANEL, line_color=line_color)
        txt(slide, fx[i] + 0.15, fy, fw[i] - 0.3, fh2, [(label, 12, WHITE, True, False, 1.15)],
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if i < 2:
            arrow_right(slide, fx[i] + fw[i] + 0.05, fy + fh2 / 2, 0.35, h=0.22, fill=TEAL)

    txt(slide, 1.1, 6.1, 11.4, 0.6,
        [("Never show an unchecked answer. Never refuse what you can prove. When you truly can't — say so.", 13.5, WHITE, True, False, None)])
    return slide


def build_s11_full_architecture(prs, notes):
    slide = base_slide(prs, "ALL TOGETHER", "The whole system — built by its failures", notes)

    left = 0.7
    right = SLIDE_W - 0.7

    prep = [
        ("Documents", MUTED),
        ("Split into passages", MUTED),
        ("Label: when it applies", TEAL),
        ("Meaning index", TEAL),
        ("Master list of rules", AMBER),
    ]
    n1 = len(prep)
    gap1 = 0.22
    w1 = (right - left - gap1 * (n1 - 1)) / n1
    y1 = 2.25
    h1 = 0.85
    txt(slide, left, y1 - 0.36, 8.0, 0.3, [("BUILT ONCE", 10.5, MUTED, True, False, None)])
    for i, (label, phase_color) in enumerate(prep):
        x = left + i * (w1 + gap1)
        card(slide, x, y1, w1, h1, fill=PANEL, line_color=phase_color)
        txt(slide, x + 0.08, y1, w1 - 0.16, h1, [(label, 11, WHITE, True, False, 1.1)],
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if i < n1 - 1:
            arrow_right(slide, x + w1 - 0.02, y1 + h1 / 2, gap1 + 0.04, h=0.16, fill=PANEL_LINE)

    live = [
        ("Student question", MUTED),
        ("Search by meaning", TEAL),
        ("Keep rules that apply now", TEAL),
        ("Draft answer", MUTED),
        ("Check every claim", AMBER),
        ("Weak? search again", AMBER),
        ("Reply — or “I don't know”", AMBER),
    ]
    n2 = len(live)
    gap2 = 0.18
    w2 = (right - left - gap2 * (n2 - 1)) / n2
    y2 = 4.3
    h2 = 1.0
    txt(slide, left, y2 - 0.36, 8.0, 0.3, [("EVERY QUESTION, LIVE", 10.5, MUTED, True, False, None)])
    for i, (label, phase_color) in enumerate(live):
        x = left + i * (w2 + gap2)
        card(slide, x, y2, w2, h2, fill=PANEL, line_color=phase_color)
        txt(slide, x + 0.07, y2, w2 - 0.14, h2, [(label, 10.5, WHITE, True, False, 1.1)],
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if i < n2 - 1:
            arrow_right(slide, x + w2 - 0.02, y2 + h2 / 2, gap2 + 0.04, h=0.16, fill=PANEL_LINE)

    index_cx = left + 3 * (w1 + gap1) + w1 / 2
    search_cx = left + 1 * (w2 + gap2) + w2 / 2
    master_cx = left + 4 * (w1 + gap1) + w1 / 2
    check_cx = left + 4 * (w2 + gap2) + w2 / 2
    straight_line(slide, index_cx, y1 + h1, search_cx, y2, MUTED, 1.25)
    straight_line(slide, master_cx, y1 + h1, check_cx, y2, MUTED, 1.25)

    legend = [
        ("Phase 1 — the bare skeleton", MUTED),
        ("Phase 2 — meaning + applicability", TEAL),
        ("Phase 3 — verification + honesty", AMBER),
    ]
    lx = left
    ly = 5.65
    for label, color in legend:
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(lx), Inches(ly + 0.07), Inches(0.16), Inches(0.16))
        solid(dot, color)
        no_line(dot)
        txt(slide, lx + 0.26, ly, 3.9, 0.35, [(label, 11.5, WHITE, False, False, None)])
        lx += 4.2

    txt(slide, left, 6.25, right - left, 0.5,
        [("Nothing here was designed up front — every coloured box exists because a failure forced it.", 13, AMBER, False, True, None)],
        align=PP_ALIGN.CENTER)
    return slide


def build_s12_skipped(prs, notes):
    slide = base_slide(prs, "SKIPPED ON PURPOSE", "What we skipped (look these up later)", notes)

    txt(slide, 1.1, 2.2, 11.2, 0.45,
        [("Six things the real system also does. None changes today's story — they squeeze out the last 20%.", 13.5, MUTED, False, True, None)])

    concepts = [
        ("Hybrid retrieval", "run word search and meaning search together, merge the results"),
        ("Reranking", "a second, smarter pass re-orders the found passages"),
        ("Query rewriting", "clean the question into a sharp search query first"),
        ("Question splitting", "one compound question becomes several simple ones"),
        ("Conversation memory", "condense the chat so far into one standalone question"),
        ("Two-model design", "a cheap fast model does the plumbing; the strong one writes the answer"),
    ]
    left = 0.9
    right = SLIDE_W - 0.9
    cols = 3
    gap = 0.22
    w = (right - left - gap * (cols - 1)) / cols
    h = 1.35
    for i, (term, gloss) in enumerate(concepts):
        row = i // cols
        col = i % cols
        x = left + col * (w + gap)
        y = 2.85 + row * (h + 0.25)
        card(slide, x, y, w, h, fill=PANEL, line_color=PANEL_LINE)
        txt(slide, x + 0.2, y + 0.14, w - 0.4, 0.35, [(term, 13.5, WHITE, True, False, None)])
        txt(slide, x + 0.2, y + 0.52, w - 0.4, 0.75, [(gloss, 10.5, MUTED, False, False, 1.2)])

    txt(slide, 0.9, 6.15, 11.5, 0.45,
        [("The promise from slide 1, kept: skip them today, look them up the day you need them.", 12.5, AMBER, False, True, None)],
        align=PP_ALIGN.CENTER)
    return slide


def build_s13_closing(prs, notes):
    slide = base_slide(prs, "TAKE-AWAY", "Make it fit the domain", notes)

    txt(slide, 1.1, 2.2, 11.2, 0.45,
        [("The thought you held from the start: every domain adds needs no generic product anticipates. For example:", 13.5, MUTED, False, True, None)])

    domains = [
        ("GIS assistant", "should know what the user is looking at right now — layers on, zoom, last click — not just answer from documents"),
        ("Weather assistant", "documents describe the past; its whole job is the future — forecasting must live inside it"),
        ("Finance assistant", "data moves all day — in idle time it analyses what changed and prepares answers people are about to ask"),
    ]
    left = 0.9
    right = SLIDE_W - 0.9
    gap = 0.25
    w = (right - left - 2 * gap) / 3
    y = 2.85
    h = 2.15
    for i, (head, body) in enumerate(domains):
        x = left + i * (w + gap)
        card(slide, x, y, w, h, fill=PANEL, line_color=TEAL if i == 0 else PANEL_LINE)
        txt(slide, x + 0.22, y + 0.2, w - 0.44, 0.4, [(head, 15, TEAL, True, False, None)])
        txt(slide, x + 0.22, y + 0.7, w - 0.44, 1.3, [(body, 11.5, WHITE, False, False, 1.3)])

    txt(slide, 0.9, 5.35, 11.5, 0.45,
        [("The recipe is public — fitting it to a domain is the part that's yours to chase.", 14, AMBER, False, True, None)],
        align=PP_ALIGN.CENTER)

    txt(slide, 0.9, 5.95, 11.5, 0.7, [("Thank you — questions?", 26, WHITE, True, False, None)],
        align=PP_ALIGN.CENTER)
    return slide


NOTES = {
    "s01_title": (
        "Good afternoon everyone, thanks for having me. I'm Arif, Analyst Programmer at Wimmera CMA in "
        "regional Victoria — my day job is building software and mapping systems for a natural-resource "
        "agency. Over the past year I've built several AI-powered tools for my organisation, but only a "
        "handful ended up genuinely used to solve a real problem — the rest were experiments. One that's in "
        "real daily use is a chatbot, and today I'll walk you through what it actually takes to build one "
        "properly, using the real problems I ran into along the way. Since I can't share my workplace's "
        "internal documents publicly, we'll use a stand-in case study: MetMate, an imaginary chatbot for "
        "Sydney Met itself, answering student questions about enrolment, library, and exam rules. Same "
        "ideas, public-friendly example. One promise before we start: this lecture stays at the level of "
        "concepts, so I'll use technical terminology sparingly and carefully. New terms appear in this "
        "field literally every day; nobody memorises them all. If a term flies past you today, don't worry "
        "— the important ones keep coming back, you can always look them up later, and you'll be able to "
        "follow the ideas either way."
    ),
    "s02_upload": (
        "So, a chatbot that answers student questions from the university's documents. Let's start with the "
        "laziest possible version: take an existing product like ChatGPT, upload the student handbook PDF, "
        "and start asking questions. And honestly — it works. For one document, one person, one paid seat. "
        "But look at what that means for an institution. To give this to every student, Sydney Met would "
        "either have to build its own ChatGPT-like product from scratch, or buy a paid subscription seat "
        "for every single student — and either way, the documents keep changing and thousands of students "
        "ask questions at the same time. Neither option scales. What we need is one shared bot, always "
        "current, serving everyone at once. That's the real engineering problem, and it starts here."
    ),
    "s03_why_not": (
        "A fair question before we build: chatbots are everywhere now, so why not grab a ready-made one, "
        "the way we grab Chrome for browsing? Nobody builds their own browser. Four reasons this is "
        "different, at least today. First, expectations are genuinely diversified — one organisation cares "
        "most about security and where its data lives, another about raw speed, another about cost, "
        "another about reliability under heavy use. A browser mostly just needs to render a page; a "
        "chatbot's bar depends entirely on who's asking. Second, this field is comparatively new, so "
        "common expectations aren't even well defined yet — there's no agreed checklist like there is for "
        "browsers. Third, 'no-code' chatbot builders exist that promise exactly this, but in my own "
        "experience they're more complicated to use well than they claim, and how far you can customise "
        "the behaviour is limited. Fourth — and I say this half-joking — this space moves so fast that a "
        "genuinely good ready-made bot might exist by the time we finish this lecture; when I checked "
        "before preparing this, it wasn't there yet. So for now, you still have to build, or at least "
        "understand the build well enough to steer it. And beyond these four there's a deeper reason "
        "you'll see by the end of the hour: every domain has specific needs that no generic product "
        "anticipates. Hold that thought — we'll come back to it in the very last slide."
    ),
    "s04_birdseye": (
        "Here's the whole of MetMate at a glance — deliberately coarse, just a handful of boxes. The top "
        "lane happens once, ahead of time, before any student asks anything: the documents get broken up "
        "and organised into an index, a searchable form. The bottom lane runs live, every single time a "
        "student asks: the question searches that index, the best passages feed a draft answer, the draft "
        "gets checked, and only then does the student see a reply. Keep this map in your head — the rest "
        "of the lecture is a magnifying glass moving across it, one box at a time. Three things worth "
        "saying while we look at it. First: a chatbot is usually the very first exercise in any course on "
        "large language models — LLMs, the AI models behind tools like ChatGPT — because the task is well "
        "defined, and with decent hardware you can build a complete chatbot running entirely on your own "
        "machine with free local models. Second: this is a young, still-growing field, so there is no "
        "standard blueprint for this diagram. What you're seeing is one way — the way we built it. Third — "
        "and this is where real life differs from the course exercise: real users expect quality answers, "
        "fast, at any scale, without the organisation running a data centre. So this system quietly calls "
        "three commercial AI services over the internet — three API providers. OpenAI turns text into its "
        "searchable meaning form and handles the fast mechanical chores, Anthropic writes the final "
        "answers, and Cohere re-orders search results by relevance. You pay per use, and in exchange "
        "nobody has to own a single GPU."
    ),
    "s05_phase1": (
        "Let's build phase one, the bare minimum. Almost everything in the map is standard software; the "
        "only genuinely new problem is the search box — given a question and thousands of passages, find "
        "the few that matter. The simplest possible answer: match words. Count how many words the question "
        "shares with each passage, give rare words a bit more weight, and the passage with the most "
        "overlap wins. This is decades-old search technology — it's fast, it's simple, it needs no AI at "
        "all. The winning passages then go to the language model, which phrases a reply out of them. And "
        "that's phase one complete: a working chatbot. Now watch it fail."
    ),
    "s06_phase1_breaks": (
        "A student asks: 'Can I access the library 24/7?' Somewhere in the documents there's an appendix "
        "about exam periods, and it literally contains the words '24/7 access'. The general rule — the one "
        "that actually governs an ordinary week — says open 8am to 10pm during term time, and it shares "
        "almost no words with the question. Count the overlap: the appendix scores high, the real rule "
        "scores low, and MetMate confidently tells the student the library never closes. Every word of "
        "that answer came from a real document — and it's still wrong, because word matching rewards the "
        "passage that echoes the question, not the rule that applies. This is the single most important "
        "failure mode of naive search, and the first version of my real bot did exactly this. A confident "
        "wrong answer is worse than no answer, so phase one is dead. Notice that two things broke at once: "
        "search matched words instead of meaning, and nothing anywhere asked 'does this rule even apply "
        "right now?' Phase two fixes both."
    ),
    "s07_phase2_meaning": (
        "First half of the fix: teach the computer meaning. That's what an embedding does — it converts a "
        "piece of text into a list of numbers. Think of it as plotting the text as a point in space, where "
        "meaning determines position: texts about similar things land near each other, even if they share "
        "no words at all. The classic illustration: take the point for 'queen', subtract the direction for "
        "'female', add the direction for 'male', and you land close to 'king'. The model captured a real "
        "relationship purely from patterns in language, as geometry. So during the build-once lane, every "
        "passage of every document becomes a point; live, the student's question becomes a point too, and "
        "search stops being 'count the shared words' and becomes 'find the nearby points'. A passage about "
        "opening hours now lands right next to a question about opening hours, even when the wording is "
        "completely different. That's half the fix."
    ),
    "s08_phase2_scope": (
        "Here's the second half, and it's the subtler one. Even searching by meaning, the exam-period "
        "passage still comes up — it genuinely is about library access. The missing ingredient is context: "
        "when each passage is stored, attach the conditions under which it applies — 'exam period only', "
        "'term time', whatever the surrounding document says. Now the pieces the bot retrieves aren't bare "
        "sentences; they're sentences that carry their own scope, and a simple check can set aside the "
        "ones whose conditions don't hold for this question. Ask about ordinary library hours and the "
        "appendix steps back: 8am to 10pm in term time, 24/7 only during exams. Phase two, MetMate answers "
        "the library question correctly. This idea — every piece of information carrying the context of "
        "when it's true — is probably the most transferable lesson in this whole lecture."
    ),
    "s09_phase3_breaks": (
        "Phase two works, so we got ambitious. A chatbot speaking to students on behalf of a university "
        "must not invent things — language models will happily produce fluent, confident, wrong sentences. "
        "So we added a safety check: before any answer is shown, a second pass verifies every claim "
        "against the passages that search retrieved, and unsupported claims kill the answer. Sensible, "
        "right? Here's what happened. A student asks: 'How many kinds of special consideration are "
        "there?' MetMate drafts the correct answer — six categories — because alongside the index it keeps "
        "a master list, a table of contents of every rule section, built directly from the documents. But "
        "search, tuned to fetch a handful of relevant passages, only pulled the full text for two of the "
        "six. The checker finds four claims with no passage in hand, stamps them 'unsupported', and throws "
        "the whole answer away. The bot tells the student 'I couldn't confidently find this' — on a "
        "question it demonstrably could answer. Too shy is a real failure too."
    ),
    "s10_phase3_fix": (
        "The fix is not to loosen the check — it's to give it the right evidence for each kind of claim. "
        "Claims about what exists, or how many there are: the master list is the authority. It was built "
        "directly from the documents themselves, so it's exactly as trustworthy as they are. Claims about "
        "the detail of one specific rule: those still require the actual passage, no exceptions. "
        "Existence and detail need different evidence — miss that distinction and your bot goes shy on "
        "precisely the questions it's best equipped to answer. And when a claim genuinely has neither kind "
        "of evidence? The bot doesn't guess. It quietly searches once more with a sharper query, and if "
        "the support still isn't there, it tells the student honestly that it doesn't know. That's the "
        "whole honesty policy in one breath: never show an unchecked answer, never refuse what you can "
        "prove, and when you truly can't — say so. Phase three complete, and this is the version people "
        "can rely on."
    ),
    "s11_architecture": (
        "Now zoom back out — same map as the start, but grown. The grey boxes are phase one, the bare "
        "skeleton: split the documents, match, draft, reply. The teal boxes are phase two: the meaning "
        "index, the applicability labels, the filter that keeps only rules that apply right now. The "
        "amber boxes are phase three: the master list, the claim checker, the retry, and the honest 'I "
        "don't know'. Here's the point of this slide: nothing in this picture was designed up front. Every "
        "coloured box exists because a real failure forced it. Which means you don't need the perfect "
        "architecture on day one — you need a working skeleton, and the discipline to treat every failure "
        "as a design instruction."
    ),
    "s12_skipped": (
        "Remember the promise from slide one — that terms keep coming back? Here are six I deliberately "
        "skipped today, all quietly at work in the real system. Hybrid retrieval: run word search and "
        "meaning search together and merge the results — old and new search are better combined than "
        "either alone. Reranking: a second, smarter pass re-orders the passages search found. Query "
        "rewriting: clean the student's question into a sharp search query before searching. Question "
        "splitting: one compound question becomes several simple ones, answered together. Conversation "
        "memory: condense the chat so far into one standalone question, so 'what about postgrads?' makes "
        "sense on its own. And the two-model design: a cheap, fast model does all this mechanical "
        "plumbing, while the strong, expensive model only writes the final answer — that's how the system "
        "stays both smart and affordable. None of these changes the story you just saw; they squeeze out "
        "the last twenty percent of quality. When you need them, look them up — you now have the map they "
        "attach to."
    ),
    "s13_closing": (
        "Last thing — back to the thought I asked you to hold at the start: why ready-made bots don't "
        "quite fit. Everything we built today is the generic recipe, and the recipe is public — anyone "
        "can follow it. The value, and honestly the fun, is fitting it to a domain. Three quick examples "
        "from the kinds of tools I get to build. A GIS assistant — mapping is my own field — shouldn't "
        "just answer questions about map data; it should know what the user is looking at right now: "
        "which layers are on, where they've zoomed, what they just clicked. A weather assistant can't "
        "only quote documents, because documents describe the past — its whole job is the future, so "
        "forecasting has to live inside it. A finance assistant sits on data that moves all day, so in "
        "its idle time it should be analysing what just changed and preparing the answers people are "
        "about to ask. Same skeleton, three completely different bots. Somewhere in whatever field you "
        "end up working in, there's a version of this waiting to be fitted — and that part isn't in any "
        "tutorial. That part is yours. Thank you — happy to take questions."
    ),
}


def main():
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)

    build_s01_title(prs, NOTES["s01_title"])
    build_s02_upload_chatgpt(prs, NOTES["s02_upload"])
    build_s03_why_not_ready_made(prs, NOTES["s03_why_not"])
    build_s04_birdseye(prs, NOTES["s04_birdseye"])
    build_s05_phase1_build(prs, NOTES["s05_phase1"])
    build_s06_phase1_breaks(prs, NOTES["s06_phase1_breaks"])
    build_s07_phase2_meaning(prs, NOTES["s07_phase2_meaning"])
    build_s08_phase2_scope(prs, NOTES["s08_phase2_scope"])
    build_s09_phase3_breaks(prs, NOTES["s09_phase3_breaks"])
    build_s10_phase3_fix(prs, NOTES["s10_phase3_fix"])
    build_s11_full_architecture(prs, NOTES["s11_architecture"])
    build_s12_skipped(prs, NOTES["s12_skipped"])
    build_s13_closing(prs, NOTES["s13_closing"])

    prs.save(OUT_PATH)
    print("saved", OUT_PATH)


if __name__ == "__main__":
    main()
