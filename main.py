import flet as ft
from fpdf import FPDF
from datetime import datetime
import os

# ============================================================================
# PART 1: PDF GENERATION LOGIC (12x18 Inch + Cutting Marks)
# ============================================================================

def generate_pdf_12x18(filename, layout_option, data):
    """
    Generates PDF using 12x18 inch industrial sheet dimensions with cutting marks.
    """
    
    # 1. Page Configuration
    W_12_INCH = 12 * 25.4  # ~304.8 mm
    H_18_INCH = 18 * 25.4  # ~457.2 mm

    # Determine Orientation
    if layout_option == "3x6":
        # Landscape 18" width x 12" height
        page_width, page_height = H_18_INCH, W_12_INCH
        cols, rows = 3, 6
    else: # 2x8
        # Portrait 12" width x 18" height
        page_width, page_height = W_12_INCH, H_18_INCH
        cols, rows = 2, 8

    # Create PDF
    pdf = FPDF(orientation='P', unit='mm', format=(page_width, page_height))
    pdf.set_auto_page_break(False)
    pdf.add_page()

    # 2. Dimensions & Spacing
    MARGIN_OUTER = 5  # 5mm edge margin
    GAP_BETWEEN = 10   # Gap between stickers

    # Calculate sticker size
    total_gap_w = (cols - 1) * GAP_BETWEEN
    available_w = page_width - (2 * MARGIN_OUTER) - total_gap_w
    sticker_w = available_w / cols

    total_gap_h = (rows - 1) * GAP_BETWEEN
    available_h = page_height - (2 * MARGIN_OUTER) - total_gap_h
    sticker_h = available_h / rows

    # --- HELPER: DRAW SINGLE STICKER ---
    def draw_sticker(x, y, w, h, d):
        # Draw Border Box
        pdf.set_line_width(0.3)
        pdf.set_draw_color(0, 0, 0) # Black
        pdf.rect(x, y, w, h)

        # --- SECTIONS ---
        header_h = h * 0.25
        footer_h = h * 0.30
        line_y_header = y + header_h
        line_y_footer = y + h - footer_h

        # Dividers
        pdf.line(x, line_y_header, x + w, line_y_header)
        pdf.line(x, line_y_footer, x + w, line_y_footer)

        # --- HEADER (Product) ---
        title_size = 20 if w > 80 else 14
        pdf.set_font("Helvetica", "B", title_size)
        text = d["product_name"]
        text_w = pdf.get_string_width(text)
        center_x = x + (w - text_w) / 2
        center_y = y + (header_h / 2) + (title_size * 0.15) 
        pdf.text(center_x, center_y, text)

        # --- MIDDLE SECTION ---
        body_size = 10
        pdf.set_font("Helvetica", "", body_size)
        padding_left = 5
        line_spacing = 5
        start_text_y = line_y_header + body_size - 4

        # Left Data
        pdf.text(x + padding_left, start_text_y, f"BATCH NO:      {d['batch_no']}")
        pdf.text(x + padding_left, start_text_y + line_spacing, f"DATE OF MFG:   {d['mfg_date']}")
        pdf.text(x + padding_left, start_text_y + (line_spacing * 2), f"RE-TEST DATE: {d['retest_date']}")

        # Right Data (Net Wt)
        right_col_x = x + (w * 0.55)
        pdf.text(right_col_x, start_text_y, f"NET WT: {d['net_wt']}")

        # Warning (Red)
        pdf.set_text_color(255, 0, 0)
        pdf.set_font("Helvetica", "B", body_size - 1)
        pdf.text(right_col_x, start_text_y + (line_spacing * 2), d["warning"])
        pdf.set_text_color(0, 0, 0) # Reset

        # --- FOOTER SECTION ---
        mid_x = x + (w * 0.5)
        pdf.set_line_width(0.2)
        pdf.line(mid_x, line_y_footer, mid_x, y + h)

        # Company Name
        comp_size = 14
        pdf.set_font("Helvetica", "B", comp_size)
        comp_text = d["company_name"]
        comp_w = pdf.get_string_width(comp_text)
        comp_x = x + ((w * 0.5) - comp_w) / 2
        comp_y = line_y_footer + (footer_h / 2) + (comp_size * 0.15)
        pdf.text(comp_x, comp_y, comp_text)

        # Address
        addr_size = 7
        pdf.set_font("Helvetica", "", addr_size)
        addr_x = mid_x + 3
        addr_start_y = line_y_footer + addr_size - 3
        addr_line_h = 3.5
        pdf.text(addr_x, addr_start_y, d["address_line1"])
        pdf.text(addr_x, addr_start_y + addr_line_h, d["address_line2"])
        pdf.text(addr_x, addr_start_y + (addr_line_h * 2), d["email"])

    # --- DRAW GRID ---
    for r in range(rows):
        for col in range(cols):
            x_pos = MARGIN_OUTER + (col * (sticker_w + GAP_BETWEEN))
            y_pos = MARGIN_OUTER + (r * (sticker_h + GAP_BETWEEN))
            draw_sticker(x_pos, y_pos, sticker_w, sticker_h, data)

    # --- CUTTING MARKS ---
    pdf.set_draw_color(255, 0, 0) # Red
    pdf.set_line_width(0.2)
    cross_size = 2

    # 1. Inner Crosses
    for i in range(cols - 1):
        for j in range(rows - 1):
            gap_center_x = MARGIN_OUTER + sticker_w + (i * (sticker_w + GAP_BETWEEN)) + (GAP_BETWEEN / 2)
            gap_center_y = MARGIN_OUTER + sticker_h + (j * (sticker_h + GAP_BETWEEN)) + (GAP_BETWEEN / 2)
            pdf.line(gap_center_x - cross_size, gap_center_y, gap_center_x + cross_size, gap_center_y)
            pdf.line(gap_center_x, gap_center_y - cross_size, gap_center_x, gap_center_y + cross_size)

    # 2. Outer Edge Marks
    for i in range(cols - 1):
        gap_center_x = MARGIN_OUTER + sticker_w + (i * (sticker_w + GAP_BETWEEN)) + (GAP_BETWEEN / 2)
        pdf.line(gap_center_x, 0, gap_center_x, MARGIN_OUTER)
        pdf.line(gap_center_x, page_height - MARGIN_OUTER, gap_center_x, page_height)

    for j in range(rows - 1):
        gap_center_y = MARGIN_OUTER + sticker_h + (j * (sticker_h + GAP_BETWEEN)) + (GAP_BETWEEN / 2)
        pdf.line(0, gap_center_y, MARGIN_OUTER, gap_center_y)
        pdf.line(page_width - MARGIN_OUTER, gap_center_y, page_width, gap_center_y)

    # Output file
    pdf.output(filename)

# ============================================================================
# PART 2: THE FLET APP (UI)
# ============================================================================

def main(page: ft.Page):
    page.title = "Sticker Generator"
    page.scroll = "adaptive"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 800

    # --- Helper to create data dict ---
    def get_form_data():
        return {
            "product_name": product_name.value,
            "batch_no": batch_no.value,
            "mfg_date": mfg_date.value,
            "retest_date": retest_date.value,
            "net_wt": net_wt.value,
            "warning": warning_text.value,
            "company_name": "M/S. NOVA ENTERPRISES",
            "address_line1": "Plot no. F-39, MIDC Shiroli, Kolhapur-416 122",
            "address_line2": "Ph.: +91-9922996051",
            "email": "e-mail: sales@novaent.in"
        }

    # --- Save Dialog (Only used on Windows/Desktop) ---
    def save_file_result(e: ft.FilePickerResultEvent):
        if e.path:
            try:
                generate_pdf_12x18(e.path, layout.value, get_form_data())
                page.open(ft.SnackBar(content=ft.Text(f"Saved to {e.path}"), bgcolor="green"))
                if os.name == 'nt': 
                    os.startfile(e.path)
            except Exception as err:
                page.open(ft.SnackBar(content=ft.Text(f"Error: {str(err)}"), bgcolor="red"))

    save_dialog = ft.FilePicker(on_result=save_file_result)
    page.overlay.append(save_dialog)

    # --- UI Inputs ---
    layout = ft.Dropdown(label="Layout", options=[ft.dropdown.Option("3x6"), ft.dropdown.Option("2x8")], value="3x6")
    product_name = ft.TextField(label="Product Name", value="TRIETHYLAMINE")
    batch_no = ft.TextField(label="Batch No", value="1113/2526")
    
    # Remove expand=True so they stay normal height
    mfg_date = ft.TextField(label="Mfg Date", value=datetime.now().strftime("%d/%m/%Y"))
    retest_date = ft.TextField(label="Retest Date", value="11/11/2026")

    net_wt = ft.TextField(label="Net Wt", value="150 KGS")
    warning_text = ft.TextField(label="Warning Text", value="(FOR INDUSTRIAL USE ONLY)")

    # --- BUTTON CLICK HANDLER ---
    def on_btn_click(e):
        # FIX 2: Check Platform to fix Android Path Error
        if page.platform == ft.PagePlatform.ANDROID:
            try:
                # Force path to standard Downloads folder
                filename = f"Label_{datetime.now().strftime('%H%M%S')}.pdf"
                save_path = f"/storage/emulated/0/Download/{filename}"
                
                generate_pdf_12x18(save_path, layout.value, get_form_data())
                
                page.open(ft.SnackBar(content=ft.Text(f"Saved to DOWNLOADS folder as {filename}"), bgcolor="green"))
            except Exception as err:
                # Fallback error message
                page.open(ft.SnackBar(content=ft.Text(f"Android Save Error: {str(err)}"), bgcolor="red"))
        else:
            # On PC, let user pick the folder
            fname = f"Label_{datetime.now().strftime('%H%M%S')}.pdf"
            save_dialog.save_file(dialog_title="Save PDF", file_name=fname, allowed_extensions=["pdf"])

    btn = ft.ElevatedButton(
        "Generate Labels", 
        icon=ft.Icons.PRINT, 
        on_click=on_btn_click,
        style=ft.ButtonStyle(bgcolor="blue", color="white"),
        height=50
    )

    page.add(
        ft.Text("Label Generator (12x18 + Cuts)", size=24, weight="bold", color="blue"),
        ft.Divider(),
        layout,
        product_name,
        batch_no,
        mfg_date,     # Added directly (Top)
        retest_date,  # Added directly (Bottom)
        net_wt,
        warning_text,
        ft.Divider(),
        btn
    )

ft.app(target=main)
