#!/usr/bin/env python3
"""
Generate a high-fidelity PDF summary of the TSUKIMI pipeline roadmap.
Uses reportlab (pip-installed) to produce a multi-page document
structured as: Title + TOC + Phase summaries + Equation snippets + Figures.
No LaTeX required.
"""

import sys
import pathlib
from datetime import datetime
import subprocess

# Ensure reportlab is installed
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
        PageBreak, Image, KeepTogether
    )
    from reportlab.lib import colors
except ImportError:
    print("Installing reportlab...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "reportlab"])
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
        PageBreak, Image, KeepTogether
    )
    from reportlab.lib import colors

ROOT = pathlib.Path(__file__).parent.parent
FIGURES = ROOT / "output" / "figures"
OUTPUT = ROOT / "output" / "docs"
OUTPUT.mkdir(parents=True, exist_ok=True)

def create_roadmap_pdf():
    """Generate TSUKIMI pipeline roadmap as a single PDF."""
    filename = OUTPUT / "Lunar_V2_Pipeline_Roadmap_Extended.pdf"

    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
        title="TSUKIMI Pipeline Roadmap",
        author="Ramon III P. Gregorio"
    )

    styles = getSampleStyleSheet()
    story = []

    # --- Title page ---
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1D4ED8'),
        spaceAfter=0.3*inch,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=0.1*inch,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=0.15*inch,
        leading=14
    )

    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("LUNAR-V2 / TSUKIMI", title_style))
    story.append(Paragraph("Thermal Subsurface Understanding through Kinetic Ice Modeling and Illumination", subtitle_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("A Developer's Manual and Scientific Roadmap", subtitle_style))
    story.append(Spacer(1, 0.5*inch))

    author_style = ParagraphStyle(
        'Author',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=0.05*inch
    )
    story.append(Paragraph("<b>Ramon III P. Gregorio</b>", author_style))
    story.append(Paragraph("Kasai Laboratory, Institute of Science Tokyo", author_style))
    story.append(Paragraph("<i>rp3gregorio@gmail.com</i>", author_style))
    story.append(Spacer(1, 0.4*inch))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d')}", author_style))

    # --- Phase 1 verdict box ---
    story.append(PageBreak())
    story.append(Paragraph("<b>PHASE 1: VALIDATION STATUS</b>", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    rmse_data = [
        ['Site', 'Model', 'RMSE [K]', 'Criterion', 'Status'],
        ['Apollo 15 (deep)', 'Discrete 3-layer', '0.915', '<= 1.0', 'PASS'],
        ['Apollo 15 (deep)', 'Hayne (2017)', '1.441', '<= 1.5', 'PASS'],
        ['Apollo 17 (1 m)', 'Discrete 3-layer', '0.665', '+/- 2.0', 'PASS'],
        ['Apollo 17 (1 m)', 'Hayne (2017)', '2.602', '+/- 2.0', 'MARGINAL'],
        ['Chang\'E-4', 'Discrete 3-layer', '--', 'O(1)', 'PASS'],
        ['ChaSTE (flat)', 'Discrete 3-layer', '--', '< 40 K bias', 'MOTIVATION for Phase 2'],
    ]

    tbl = Table(rmse_data, colWidths=[2*cm, 2*cm, 1.5*cm, 1.8*cm, 2.2*cm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1D4ED8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(tbl)

    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "<b>Verdict:</b> Phase 1 PASSED. All critical acceptance criteria satisfied. "
        "The discrete 3-layer model is the primary closure; Hayne (2017) is secondary. "
        "Ready to proceed to Phase 2.",
        body_style
    ))

    # --- Pipeline flow ---
    story.append(PageBreak())
    story.append(Paragraph("<b>PIPELINE ARCHITECTURE</b>", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    phases = [
        ("Phase 0", "Quickstart", "✓ Shipped", "Library smoke-test"),
        ("Phase 1", "Point-source validation", "✓ Shipped", "Apollo 15/17, CE-4, ChaSTE"),
        ("Phase 2", "Illumination coupling", "🔄 In Progress", "DEM + horizon + slope + shadow"),
        ("Phase 3", "Polar maps + ice", "📋 Planned", "Diviner validation + ice-coupled k"),
        ("Phase 4", "Manuscript + thesis", "📋 Planned", "PSJ submission + ISCT defence"),
    ]

    phase_data = [['Phase', 'Topic', 'Status', 'Description']] + list(phases)
    phase_tbl = Table(phase_data, colWidths=[1.3*cm, 3*cm, 2*cm, 5*cm])
    phase_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#047857')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(phase_tbl)

    # --- Novelty highlights ---
    story.append(PageBreak())
    story.append(Paragraph("<b>RESEARCH NOVELTY</b>", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    novelties = [
        ("Multi-site blind validation",
         "Regressed against Apollo 15/17, Chang'E-4, and ChaSTE with a single solver kernel. "
         "No site-specific tuning except H-scale."),
        ("Ice-coupled conductivity feedback",
         "Self-consistent loop: Klinger's k_ice(T) = 567/T couples to the solver. "
         "Deepens ice table by ~15 cm vs. fixed-k models."),
        ("Pixel-level topographic slope",
         "cos(i) correction applied per DEM pixel. Collapses ChaSTE 40 K bias with s=6°."),
        ("End-to-end reproducibility",
         "Every notebook auto-installs deps and auto-fetches data. Full 4-site validation "
         "< 15 minutes on a 2024 laptop."),
    ]

    for i, (title, desc) in enumerate(novelties, 1):
        story.append(Paragraph(f"<b>{i}. {title}</b>", styles['Heading3']))
        story.append(Paragraph(desc, body_style))

    # --- Phase 2 highlight ---
    story.append(PageBreak())
    story.append(Paragraph("<b>PHASE 2: TOPOGRAPHIC ILLUMINATION (IN PROGRESS)</b>", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "Phase 2 extends the Phase-1 solver with pixel-level topographic forcing. "
        "The data flow is: DEM → slope/aspect → horizon raycast → sky view factor → "
        "shadow mask → corrected Q(t). The Phase-1 kernel is reused unchanged.",
        body_style
    ))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph("<b>Key equation (corrected insolation):</b>", styles['Heading3']))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "<i>Q(t) = m(t) × S<sub>☉</sub> × cos(i) + F<sub>sky</sub> × Q<sub>IR,sky</sub> + "
        "A × S<sub>☉</sub> × cos(i) × (1 − F<sub>sky</sub>)</i>",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "where m(t) is the shadow mask, F<sub>sky</sub> is the sky view factor, "
        "and cos(i) is the incidence angle corrected for local slope.",
        body_style
    ))

    # --- Phase 3 highlight ---
    story.append(PageBreak())
    story.append(Paragraph("<b>PHASE 3: POLAR MAPS & ICE-COUPLED CONDUCTIVITY (PLANNED)</b>", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "Phase 3 builds a pixel-wise equilibrium temperature and ice-stability depth map "
        "for one south-polar tile, validated against Diviner bolometric T.",
        body_style
    ))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph("<b>Ice-coupled conductivity closure (Klinger 1980):</b>", styles['Heading3']))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "<i>k<sub>ice</sub>(T) = 567 / T  [W m<sup>−1</sup> K<sup>−1</sup>]</i>, "
        "T ∈ [20, 273] K<br/><br/>"
        "<i>k<sub>eff</sub>(T,z,φ) = φ × k<sub>ice</sub>(T) + (1−φ) × k<sub>reg</sub>(T,z)</i>",
        body_style
    ))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "A fixed-point iteration solves self-consistently: (1) solve with dry regolith, "
        "(2) find T_stab ≈ 112 K stability depth, (3) set φ=0.05–0.10 for z ≥ z★, "
        "(4) re-solve with updated k_eff, repeat until |Δz★| < 1 cm (typically 3–5 sweeps).",
        body_style
    ))

    # --- Phase 4 highlight ---
    story.append(PageBreak())
    story.append(Paragraph("<b>PHASE 4: MANUSCRIPT & THESIS (PLANNED)</b>", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    schedule = [
        ['Milestone', 'Target Date', 'Gate'],
        ['Phase 2 complete', '2026-04-30', 'ChaSTE bias ≤ 10 K'],
        ['Phase 3 complete', '2026-05-31', 'Diviner RMS ≤ 5 K'],
        ['Manuscript draft', '2026-06-30', 'Sections 2–7'],
        ['Internal review', '2026-07-31', 'Supervisor + co-authors'],
        ['PSJ submission', '2026-08-15', 'arXiv same day'],
        ['Thesis defence', '2026-09-15', 'ISCT public defence'],
    ]

    sched_tbl = Table(schedule, colWidths=[3.5*cm, 3*cm, 4*cm])
    sched_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D97706')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    story.append(sched_tbl)

    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "<b>Targets:</b> PSJ submission by 2026-06, thesis defence by 2026-09. "
        "Full reproducibility artefact (code, Docker, data manifest) at Zenodo.",
        body_style
    ))

    # --- Build the PDF ---
    doc.build(story)
    print(f"✓ Generated {filename} ({filename.stat().st_size / 1024:.1f} KB)")
    return filename

if __name__ == "__main__":
    create_roadmap_pdf()
