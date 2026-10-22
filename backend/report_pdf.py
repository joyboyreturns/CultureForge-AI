"""The client-ready PDF: the exploration, its verdicts and its evidence.

Built on the server from the exploration the studio sends back, so the PDF
says exactly what the screen said. It makes no Qloo or model request. The
interest-cell plot is included only when the cells for the lead direction's
anchor are already held; otherwise the PDF says it was not fetched.

The built-in PDF fonts cover Latin-1 only. Typographic punctuation is mapped
to its plain form, and any other character outside Latin-1 is shown as "?",
which the PDF states. The JSON export keeps every character.
"""
from __future__ import annotations

import unicodedata
from datetime import datetime, timezone
from typing import Optional

from fpdf import FPDF

from .evidence_store import canonical_key, get_store
from .investigation import _geography_points
from .models import GenerateResponse
from .providers import where_popular_payload

_PLAIN = str.maketrans({'‘': "'", '’': "'", '“': '"', '”': '"', '–': '-', '—': '-',
                        '…': '...', '·': '-', '→': '->', ' ': ' ', '•': '-', '≤': '<=', '≥': '>='})
INK = (24, 34, 27)
MUTED = (96, 104, 96)
ACCENT = (190, 92, 60)
SCOPE = ('Scope: anchor fit within the retrieved sample. This is not evidence of demand, '
         'competition, rent, footfall, profitability or willingness to pay.')


def plain(text) -> str:
    """Latin-1 text for the built-in fonts; anything else becomes '?'."""
    value = str(text if text is not None else '').translate(_PLAIN)
    value = unicodedata.normalize('NFKC', value)
    return value.encode('latin-1', 'replace').decode('latin-1')


def _number(value, digits: int = 4) -> str:
    return f'{value:.{digits}f}' if isinstance(value, (int, float)) else '-'


class Report(FPDF):
    def __init__(self, title: str):
        super().__init__(format='A4')
        self.title_text = title
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 18, 18)

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', '', 7.5)
        self.set_text_color(*MUTED)
        self.cell(0, 5, plain(f'{self.title_text} - Qloo evidence, CultureForge interpretation - page {self.page_no()}'),
                  align='C')

    def heading(self, text: str, size: float = 15):
        self.ln(3)
        self.set_font('Helvetica', 'B', size)
        self.set_text_color(*INK)
        self.multi_cell(0, size * 0.5, plain(text), align='L', new_x='LMARGIN', new_y='NEXT')
        self.ln(1.5)

    def label(self, text: str):
        self.set_font('Helvetica', 'B', 7.5)
        self.set_text_color(*ACCENT)
        self.multi_cell(0, 4.2, plain(text.upper()), align='L', new_x='LMARGIN', new_y='NEXT')

    def body(self, text: str, size: float = 9.5, color=INK):
        self.set_font('Helvetica', '', size)
        self.set_text_color(*color)
        self.multi_cell(0, size * 0.52, plain(text), align='L', new_x='LMARGIN', new_y='NEXT')
        self.ln(0.8)

    def table(self, headers: list[str], rows: list[list[str]], widths: list[float]):
        self.set_font('Helvetica', 'B', 7.5)
        self.set_text_color(*MUTED)
        with self.table_context(widths) as table:
            header = table.row()
            for text in headers:
                header.cell(plain(text))
            self.set_font('Helvetica', '', 7.5)
            self.set_text_color(*INK)
            for values in rows:
                row = table.row()
                for text in values:
                    row.cell(plain(text))

    def table_context(self, widths: list[float]):
        return super().table(col_widths=widths, text_align='LEFT', line_height=4.2,
                             first_row_as_headings=True, borders_layout='HORIZONTAL_LINES')


def _held_interest_cells(response: GenerateResponse) -> tuple[Optional[str], list[dict]]:
    """The cells for the lead direction's anchor, if already held. Never fetches."""
    if not response.concepts:
        return None, []
    places = {item.id: item for item in response.evidence if item.kind == 'entity' and item.entityId}
    anchor = next((places[eid] for eid in response.concepts[0].evidenceIds if eid in places), None)
    if anchor is None:
        return None, []
    held = get_store().get(canonical_key('where_popular', where_popular_payload(
        anchor.entityId, response.project.location, None, 20)))
    return anchor.label, (_geography_points(held) if held else [])


def _plot(pdf: Report, points: list[dict]):
    """Interest cells on a plain equirectangular frame: dots, no basemap, no pins."""
    width, height = 120.0, 70.0
    x0, y0 = pdf.l_margin, pdf.get_y() + 2
    if y0 + height > pdf.h - 25:
        pdf.add_page()
        y0 = pdf.get_y() + 2
    lats = [p['lat'] for p in points]
    lons = [p['lon'] for p in points]
    span_lat = max(max(lats) - min(lats), 1e-4)
    span_lon = max(max(lons) - min(lons), 1e-4)
    pdf.set_draw_color(*MUTED)
    pdf.rect(x0, y0, width, height)
    pdf.set_fill_color(*ACCENT)
    for point in points:
        x = x0 + 4 + (point['lon'] - min(lons)) / span_lon * (width - 8)
        y = y0 + height - 4 - (point['lat'] - min(lats)) / span_lat * (height - 8)
        pdf.ellipse(x - 1.1, y - 1.1, 2.2, 2.2, style='F')
    pdf.set_y(y0 + height + 2)


def build_pdf(response: GenerateResponse, challenge: Optional[dict] = None, compress: bool = True) -> bytes:
    title = f'CultureForge evidence brief - {response.project.businessType}, {response.project.location}'
    pdf = Report(title)
    pdf.set_compression(compress)
    pdf.set_title(plain(title))
    pdf.set_author('CultureForge')
    pdf.add_page()

    # ---- cover ------------------------------------------------------------
    pdf.label('Location and concept strategy - evidence brief')
    pdf.heading(f'{response.project.businessType} for {response.project.audience}', 20)
    pdf.body(f'Location: {response.project.location}')
    pdf.body(f'Planning budget (a CultureForge planning assumption, not a cost estimate): {response.project.budget}')
    if response.project.objectives:
        pdf.body('Objectives: ' + ', '.join(response.project.objectives))
    delivery = response.delivery
    pdf.body(f'Exploration {response.projectId}. Evidence acquired '
             f'{delivery.acquiredAt if delivery and delivery.acquiredAt else "not recorded"}; '
             f'report generated {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}.', 8.5, MUTED)
    pdf.ln(2)
    pdf.body('Qloo supplied the audience tags, the places and every number in this report. The business '
             'directions are CultureForge\'s interpretation of that evidence, and each one names the Qloo '
             'evidence it was built from.', 9.5)
    pdf.body(SCOPE, 9, ACCENT)

    # ---- audience seeds ---------------------------------------------------
    seeds = [item for item in response.evidence if item.kind == 'tag']
    pdf.heading('Audience seeds')
    if seeds:
        pdf.table(['Seed', 'Qloo tag URN', 'Popularity'],
                  [[item.label, item.tagId or '-', _number(item.popularity)] for item in seeds], [50, 100, 24])
    else:
        pdf.body('The audience did not resolve into Qloo tags for this brief.')

    # ---- directions -------------------------------------------------------
    evidence = {item.id: item for item in response.evidence}
    verdicts = {row['directionId']: row for row in (challenge or {}).get('directions', [])}
    pdf.heading('Directions')
    if not response.concepts:
        pdf.body('The evidence did not support a distinct business direction, so none is proposed.')
    for index, concept in enumerate(response.concepts, start=1):
        pdf.label(f'Direction {index:02d}')
        pdf.heading(concept.name, 13)
        if concept.tagline:
            pdf.body(concept.tagline, 9.5, MUTED)
        pdf.body(concept.description)
        for decision in concept.decisions:
            cited = ', '.join(f'{evidence[eid].label} ({evidence[eid].entityId or evidence[eid].tagId})'
                              for eid in decision.evidenceIds if eid in evidence) or 'none cited'
            pdf.body(f'{decision.field}: {decision.proposal}', 8.5)
            pdf.body(f'   Rule {decision.ruleId}; Qloo evidence: {cited}', 7.5, MUTED)
        verdict = verdicts.get(concept.id)
        if verdict:
            index_data = verdict.get('index') or {}
            pdf.label(f'Evidence test: {verdict.get("verdict", "not run")}'
                      + (f' - confidence {index_data.get("confidence")}' if index_data else ''))
            pdf.body(verdict.get('reason', ''), 8.5)
            pdf.body(f'Claim: {verdict.get("claim", "")}', 8)
            pdf.body(f'Contradicted if: {verdict.get("falsifier", "")}', 8)
            if index_data:
                pdf.body(f'Rank check {index_data.get("rankCheck")}, tag check {index_data.get("tagCheck")}, '
                         f'sample {index_data.get("sampleSize")} places. {index_data.get("confidenceReason", "")}', 8, MUTED)
        if concept.limitations:
            pdf.body('Limits: ' + ' '.join(concept.limitations), 7.5, MUTED)
        pdf.ln(2)

    if challenge:
        profile = challenge.get('profile') or {}
        pdf.body(f'Evidence test policy {challenge.get("policyVersion")}; ranked for the '
                 f'"{profile.get("demographic", "?")}" profile ({profile.get("source", "proposed")}) near '
                 f'{profile.get("location", response.project.location)}. {challenge.get("whatThisIs", "")}', 8, MUTED)
    else:
        pdf.body('The evidence test was not run for this exploration, so no verdict is reported.', 8.5, MUTED)

    # ---- evidence table ---------------------------------------------------
    pdf.add_page()
    pdf.heading('Evidence')
    rows = [[{'entity': 'Place', 'tag': 'Audience seed', 'crossdomain': 'Beyond places'}.get(item.kind, item.kind),
             item.label, item.entityId or item.tagId or '-', _number(item.affinity), _number(item.popularity)]
            for item in response.evidence]
    pdf.table(['Kind', 'Label', 'Qloo ID', 'Affinity', 'Popularity'], rows, [24, 52, 62, 18, 18])
    pdf.body('Values are as Qloo returned them. Affinity and popularity are Qloo aggregate signals, not '
             'measures of business fit or demand.', 7.5, MUTED)

    # ---- interest cells ---------------------------------------------------
    anchor_label, points = _held_interest_cells(response)
    pdf.heading('Interest cells')
    if points:
        pdf.body(f'Where Qloo reports strong affinity for {anchor_label}, the lead direction\'s anchor, '
                 f'within {response.project.location}: {len(points)} cells. These are interest cells, not '
                 'venue pins; Qloo gives places an address, not a coordinate.', 8.5)
        _plot(pdf, points)
    else:
        pdf.body('Not included: interest cells for the lead direction\'s anchor were not fetched for this '
                 'exploration. Open the Interest map view to fetch them, then export again.', 8.5, MUTED)

    # ---- limitations ------------------------------------------------------
    pdf.heading('Limitations and non-claims')
    for line in (
        SCOPE,
        response.notice,
        'Directions are hypotheses for a field test, not validated business plans. No customer traction, '
        'demand validation or competitive advantage is claimed.',
        'The demographic profile used by the evidence test is proposed by CultureForge from the brief; it is not '
        'Qloo-inferred and is not the audience\'s full cultural profile.',
        'Characters outside Latin-1 (for example some place names) are shown as "?" in this PDF; the JSON export '
        'keeps them.',
    ):
        if line:
            pdf.body(f'- {line}', 8.5)
    return bytes(pdf.output())
