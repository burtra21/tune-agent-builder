"""
PDF Lead Magnet Generator for Casino Cost Savings Analysis
Generates personalized, data-driven PDFs with charts and visualizations
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io

def create_pie_chart(demand_charges, energy_charges):
    """Create demand vs energy charges pie chart"""
    fig, ax = plt.subplots(figsize=(6, 4))

    sizes = [demand_charges, energy_charges]
    labels = [f'Demand Charges\n${demand_charges/1000:.0f}K (40%)',
              f'Energy Charges\n${energy_charges/1000:.0f}K (60%)']
    colors_pie = ['#FF6B6B', '#4ECDC4']
    explode = (0.1, 0)

    ax.pie(sizes, explode=explode, labels=labels, colors=colors_pie,
           autopct='', shadow=True, startangle=90)
    ax.axis('equal')
    plt.title('Current Energy Bill Breakdown', fontsize=14, fontweight='bold', pad=20)

    # Save to bytes
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    img_buffer.seek(0)
    plt.close()

    return img_buffer

def create_savings_comparison_chart(current_annual, projected_annual):
    """Create current vs projected cost comparison bar chart"""
    fig, ax = plt.subplots(figsize=(6, 4))

    categories = ['Current\nAnnual Cost', 'Projected\nAnnual Cost']
    values = [current_annual, projected_annual]
    colors_bars = ['#FF6B6B', '#4ECDC4']

    bars = ax.bar(categories, values, color=colors_bars, width=0.5)

    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'${value/1e6:.1f}M',
                ha='center', va='bottom', fontsize=12, fontweight='bold')

    ax.set_ylabel('Annual Cost ($)', fontsize=11)
    ax.set_title('Cost Comparison: Current vs Projected', fontsize=14, fontweight='bold', pad=20)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M'))
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Save to bytes
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    img_buffer.seek(0)
    plt.close()

    return img_buffer

def create_5year_cumulative_savings_chart(annual_savings):
    """Create 5-year cumulative savings line chart"""
    fig, ax = plt.subplots(figsize=(7, 4))

    years = list(range(1, 6))
    cumulative = [annual_savings * i for i in years]

    ax.plot(years, cumulative, marker='o', linewidth=3, markersize=8, color='#4ECDC4')
    ax.fill_between(years, cumulative, alpha=0.3, color='#4ECDC4')

    # Add value labels
    for x, y in zip(years, cumulative):
        ax.text(x, y, f'${y/1e6:.1f}M', ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Cumulative Savings ($)', fontsize=11)
    ax.set_title('5-Year Cumulative Cost Savings', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(years)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M'))
    ax.grid(alpha=0.3, linestyle='--')

    # Save to bytes
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    img_buffer.seek(0)
    plt.close()

    return img_buffer

def generate_cost_analysis_pdf(prospect_data, output_dir="pdf_lead_magnets/generated"):
    """
    Generate a personalized cost savings analysis PDF for a casino prospect

    Args:
        prospect_data: Dict containing company_profile and financial projections
        output_dir: Directory to save the generated PDF

    Returns:
        str: Filename of the generated PDF
    """

    company = prospect_data['company_profile']
    company_name = company['company_name']

    # Create filename
    safe_name = company_name.lower().replace(' ', '_').replace(',', '')
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{safe_name}_cost_analysis_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Create PDF
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=1*inch, bottomMargin=0.75*inch)

    # Container for PDF elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=12,
        leading=16
    )

    # ============================================================================
    # COVER PAGE
    # ============================================================================

    elements.append(Spacer(1, 1.5*inch))

    elements.append(Paragraph("ENERGY COST SAVINGS ANALYSIS", title_style))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph(f"<b>{company_name}</b>", ParagraphStyle(
        'CompanyName', parent=styles['Heading2'], fontSize=18,
        textColor=colors.HexColor('#4ECDC4'), alignment=TA_CENTER, spaceAfter=10
    )))

    elements.append(Paragraph(company['location'], ParagraphStyle(
        'Location', parent=styles['Normal'], fontSize=12,
        textColor=colors.HexColor('#7F8C8D'), alignment=TA_CENTER, spaceAfter=30
    )))

    elements.append(Spacer(1, 0.5*inch))

    elements.append(Paragraph("Confidential Analysis", ParagraphStyle(
        'Confidential', parent=styles['Normal'], fontSize=10,
        textColor=colors.HexColor('#95A5A6'), alignment=TA_CENTER, spaceAfter=10
    )))

    elements.append(Paragraph(f"Prepared: {datetime.now().strftime('%B %d, %Y')}",
                              ParagraphStyle('Date', parent=styles['Normal'], fontSize=10,
                                           textColor=colors.HexColor('#95A5A6'), alignment=TA_CENTER)))

    elements.append(PageBreak())

    # ============================================================================
    # PAGE 1: EXECUTIVE SUMMARY
    # ============================================================================

    elements.append(Paragraph("Executive Summary", heading_style))
    elements.append(Spacer(1, 0.2*inch))

    # Summary table
    summary_data = [
        ['Metric', 'Value'],
        ['Current Est. Annual Energy Spend', f"${company['estimated_energy_spend']:,.0f}"],
        ['Projected Annual Savings', f"${company['annual_savings_dollars']:,.0f}"],
        ['Monthly Savings', f"${company['monthly_savings_dollars']:,.0f}"],
        ['Payback Period', f"{company['payback_months']} months"],
        ['5-Year Value', f"${company['five_year_savings']:,.0f}"],
        ['Carbon Reduction', f"{company['carbon_reduction_tons']:,.0f} tons CO₂/year"],
        ['Expected IRR', '25-40%']
    ]

    summary_table = Table(summary_data, colWidths=[3.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ECF0F1')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ECF0F1')])
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph(
        f"Based on verified results from a Las Vegas casino that achieved an <b>8.59% kW reduction</b> "
        f"(peak demand), {company_name} could realize <b>${company['annual_savings_dollars']:,.0f}</b> "
        f"in annual energy cost savings with a payback period of just {company['payback_months']} months.",
        body_style
    ))

    elements.append(PageBreak())

    # ============================================================================
    # PAGE 2: DEMAND CHARGES BREAKDOWN
    # ============================================================================

    elements.append(Paragraph("Understanding Your Energy Costs", heading_style))
    elements.append(Spacer(1, 0.2*inch))

    # Calculate demand vs energy charges
    estimated_peak_kw = company['estimated_sqft'] / 100
    demand_charge_rate = 15
    annual_demand_charges = estimated_peak_kw * demand_charge_rate * 12
    annual_energy_charges = company['estimated_energy_spend'] - annual_demand_charges

    elements.append(Paragraph(
        "<b>What Are Demand Charges?</b><br/>"
        "Demand charges are based on your <i>highest 15-minute power spike</i> each month, not your total consumption. "
        "For casinos, demand charges typically represent <b>30-50%</b> of your total utility bill due to high peak loads from gaming equipment and HVAC systems.",
        body_style
    ))

    elements.append(Spacer(1, 0.2*inch))

    # Add pie chart
    pie_chart = create_pie_chart(annual_demand_charges, annual_energy_charges)
    elements.append(Image(pie_chart, width=5*inch, height=3.3*inch))

    elements.append(Spacer(1, 0.2*inch))

    # Demand charges calculation
    demand_data = [
        ['Component', 'Value'],
        ['Estimated Peak Demand', f"{estimated_peak_kw:,.0f} kW"],
        ['Typical Demand Rate', f"${demand_charge_rate}/kW/month"],
        ['Annual Demand Charges', f"${annual_demand_charges:,.0f}"],
        ['Projected 8.59% Reduction', f"${annual_demand_charges * 0.0859:,.0f}/year"]
    ]

    demand_table = Table(demand_data, colWidths=[3.5*inch, 2.5*inch])
    demand_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E74C3C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FADBD8')])
    ]))

    elements.append(demand_table)
    elements.append(PageBreak())

    # ============================================================================
    # PAGE 3: ROI PROJECTIONS
    # ============================================================================

    elements.append(Paragraph("Return on Investment Analysis", heading_style))
    elements.append(Spacer(1, 0.2*inch))

    # Add savings comparison chart
    current_annual = company['estimated_energy_spend']
    projected_annual = current_annual - company['annual_savings_dollars']

    savings_chart = create_savings_comparison_chart(current_annual, projected_annual)
    elements.append(Image(savings_chart, width=5*inch, height=3.3*inch))

    elements.append(Spacer(1, 0.3*inch))

    # Add 5-year cumulative chart
    cumulative_chart = create_5year_cumulative_savings_chart(company['annual_savings_dollars'])
    elements.append(Image(cumulative_chart, width=5.5*inch, height=3.6*inch))

    elements.append(PageBreak())

    # ============================================================================
    # PAGE 4: VERIFIED CASE STUDY
    # ============================================================================

    elements.append(Paragraph("Verified Case Study Results", heading_style))
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph(
        "<b>Las Vegas Casino - Third-Party Verified</b>",
        ParagraphStyle('CaseStudyTitle', parent=styles['Heading3'], fontSize=13,
                      textColor=colors.HexColor('#4ECDC4'), spaceAfter=12)
    ))

    case_study_data = [
        ['Metric', 'Result'],
        ['kW Reduction (Peak Demand)', '8.59%'],
        ['Verification', 'Third-party verified over 12 months'],
        ['Installation', 'Zero downtime - live electrical panels'],
        ['Payback Period', '14 months'],
        ['Internal Rate of Return (IRR)', '25-40%'],
        ['Technology', 'Tune solid-state harmonic filtration'],
    ]

    case_study_table = Table(case_study_data, colWidths=[3.5*inch, 2.5*inch])
    case_study_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4ECDC4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#D5F4E6')])
    ]))

    elements.append(case_study_table)
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph(
        "<b>Key Insight:</b> The technology addresses <i>harmonic distortion</i> at the source - "
        "the root cause of inflated demand charges that LED upgrades and BMS systems cannot touch.",
        body_style
    ))

    elements.append(PageBreak())

    # ============================================================================
    # PAGE 5: HOW IT WORKS
    # ============================================================================

    elements.append(Paragraph("How the Technology Works", heading_style))
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("<b>The Problem: Harmonic Distortion</b>",
                              ParagraphStyle('SubHeading', parent=styles['Heading3'], fontSize=12,
                                           textColor=colors.HexColor('#E74C3C'), spaceAfter=10)))

    elements.append(Paragraph(
        "Gaming equipment (slot machines, servers, VFDs) creates <b>15-25% total harmonic distortion (THD)</b> "
        "in casino electrical systems - compared to just 5-8% in typical office buildings. This harmonic distortion "
        "inflates your apparent power (kVA), which drives up demand readings even when actual power consumption (kW) remains constant.",
        body_style
    ))

    elements.append(Spacer(1, 0.15*inch))

    thd_data = [
        ['Building Type', 'Typical THD', 'Impact'],
        ['Office Buildings', '5-8%', 'Minimal demand inflation'],
        ['Casinos', '15-25%', 'Significant demand charge increase'],
        ['After Tune Installation', '<5%', 'Optimized demand charges']
    ]

    thd_table = Table(thd_data, colWidths=[2*inch, 2*inch, 2*inch])
    thd_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ECF0F1'), colors.HexColor('#D5F4E6')])
    ]))

    elements.append(thd_table)
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("<b>The Solution: Solid-State Harmonic Filtration</b>",
                              ParagraphStyle('SubHeading', parent=styles['Heading3'], fontSize=12,
                                           textColor=colors.HexColor('#4ECDC4'), spaceAfter=10)))

    elements.append(Paragraph(
        "Tune filters install at the electrical panel level and use solid-state technology to eliminate "
        "harmonic distortion at the source. <b>No moving parts, no maintenance, 20+ year lifespan.</b>",
        body_style
    ))

    elements.append(Spacer(1, 0.1*inch))

    benefits_data = [
        ['✓ Zero downtime installation'],
        ['✓ No integration with existing systems'],
        ['✓ Reduces peak demand charges (kW)'],
        ['✓ Improves power quality facility-wide'],
        ['✓ Extends equipment lifespan'],
        ['✓ 50,000+ installations worldwide']
    ]

    benefits_table = Table(benefits_data, colWidths=[6*inch])
    benefits_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    elements.append(benefits_table)
    elements.append(PageBreak())

    # ============================================================================
    # PAGE 6: NEXT STEPS
    # ============================================================================

    elements.append(Paragraph("Next Steps", heading_style))
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("<b>5% Savings Guarantee</b>",
                              ParagraphStyle('Guarantee', parent=styles['Heading3'], fontSize=13,
                                           textColor=colors.HexColor('#27AE60'), spaceAfter=10)))

    elements.append(Paragraph(
        "With <b>50,000+ installations worldwide</b>, Tune has never achieved below a 5% reduction in energy costs. "
        "If savings don't meet the 5% minimum, you receive a <b>full refund</b>.",
        body_style
    ))

    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("<b>Proposed 30-Day Metered Pilot</b>",
                              ParagraphStyle('Pilot', parent=styles['Heading3'], fontSize=13,
                                           textColor=colors.HexColor('#4ECDC4'), spaceAfter=10)))

    pilot_steps = [
        ['1.', 'Install metering equipment before and after filters'],
        ['2.', '30-day measurement period with zero operational disruption'],
        ['3.', 'Pre-defined success criteria (minimum 5% reduction)'],
        ['4.', 'Third-party verification available for board reporting'],
        ['5.', 'Full removal at no cost if savings don\'t meet 5% minimum']
    ]

    pilot_table = Table(pilot_steps, colWidths=[0.5*inch, 5.5*inch])
    pilot_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    elements.append(pilot_table)
    elements.append(Spacer(1, 0.4*inch))

    # Contact CTA
    cta_data = [[
        Paragraph("<b>Ready to Explore?</b><br/>"
                 "Contact us to schedule a consultation and review the pilot terms.<br/><br/>"
                 "<i>This analysis is based on verified third-party results and transparent projections. "
                 "Actual savings may vary based on facility-specific conditions.</i>",
                 ParagraphStyle('CTA', parent=styles['Normal'], fontSize=10,
                              textColor=colors.HexColor('#2C3E50'), alignment=TA_CENTER))
    ]]

    cta_table = Table(cta_data, colWidths=[6*inch])
    cta_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#4ECDC4')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E8F8F5')),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
    ]))

    elements.append(cta_table)

    # Build PDF
    doc.build(elements)

    return filename
