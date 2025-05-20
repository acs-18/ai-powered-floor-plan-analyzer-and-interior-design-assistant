import streamlit as st
import cv2
import numpy as np
import easyocr
import re
from PIL import Image
from typing import List, Tuple, Dict

CONVERSION_FACTORS = {
    'feet': 1.0,
    'inches': 1 / 144,
    'meters': 10.764,
    'centimeters': 0.001076,
}


CEMENT_COMPANIES = {
    "UltraTech Cement": ["OPC 33", "OPC 43", "OPC 53", "PPC", "PSC", "White Cement", "RMC"],
    "Ambuja Cements": ["OPC", "PPC", "Composite"],
    "ACC Limited": ["OPC 43", "OPC 53", "PPC", "Bulk Cement", "RMC"],
    "Shree Cement": ["OPC", "PPC", "PSC", "Composite"],
    "Dalmia Bharat Cement": ["OPC 43", "OPC 53", "PPC", "PSC", "Sulphate Resisting", "Oil Well"],
    "Birla Corporation Limited": ["OPC", "PPC", "PSC", "Low Alkali"],
    "Ramco Cements": ["OPC 43", "OPC 53", "PPC", "PSC", "Sulphate Resisting", "Rapid Hardening"],
    "India Cements": ["OPC", "PPC", "PSC", "SRPC"],
    "JK Cement": ["OPC 43", "OPC 53", "PPC", "White Cement", "Wall Putty"],
    "Orient Cement": ["OPC 43", "OPC 53", "PPC"],
    "HeidelbergCement India": ["OPC 43", "OPC 53", "PPC"],
    "Sanghi Industries": ["OPC 53", "OPC 43", "PPC", "PSC"],
    "Penna Cement": ["OPC", "PPC", "PSC", "Composite"],
    "My Home Industries": ["OPC", "PPC", "PSC", "RMC"],
    "Nuvoco Vistas Corp. Ltd.": ["OPC", "PPC", "PSC", "Composite", "RMC"],
    "Chettinad Cement": ["OPC 43", "OPC 53", "PPC", "SRPC", "Composite"],
    "KCP Cement": ["OPC 43", "OPC 53", "PPC", "PSC"],
    "Deccan Cements": ["OPC 43", "OPC 53", "PPC", "SRPC", "Rapid Hardening"],
    "Meghalaya Cements Limited": ["OPC 43", "OPC 53", "PPC"],
    "Star Cement": ["OPC 43", "OPC 53", "PPC", "PSC"],
    "Anjani Portland Cement": ["OPC 53", "OPC 43", "PPC"],
    "Maha Cement": ["OPC 43", "OPC 53", "PPC", "PSC"],
    "Zuari Cement": ["OPC 43", "OPC 53", "PPC", "RMC"],
    "Sagar Cements": ["OPC 53", "OPC 43", "PPC", "PSC"],
    "JSW Cement": ["PSC", "Composite", "GGBS"],
    "Mangalam Cement": ["OPC 43", "OPC 53", "PPC"],
    "Kesoram Industries": ["OPC"],
}


TMT_BARS = {
    "Tata Steel": ["Fe 415", "Fe 500", "Fe 550", "Fe 600"],
    "JSW Steel": ["Fe 415", "Fe 500", "Fe 550", "Fe 600"],
    "SAIL": ["Fe 415", "Fe 500", "Fe 550", "Fe 600"],
    "RINL": ["Fe 415", "Fe 500", "Fe 550", "Fe 600"],
    "Essar Steel": ["Fe 415", "Fe 500", "Fe 550", "Fe 600"],
}


PAINT_BRANDS = {
    "Asian Paints": ["Emulsion", "Distemper", "Enamel", "Weather-Resistant", "Cement", "Texture", "Metallic", "Matte"],
    "Berger Paints": ["Emulsion", "Distemper", "Enamel", "Weather-Resistant", "Cement", "Texture", "Metallic", "Matte"],
    "Nerolac Paints": ["Emulsion", "Distemper", "Enamel", "Weather-Resistant", "Cement", "Texture", "Metallic", "Matte"],
    "Dulux Paints": ["Emulsion", "Distemper", "Enamel", "Weather-Resistant", "Cement", "Texture", "Metallic", "Matte"],
    "Shalimar Paints": ["Emulsion", "Distemper", "Enamel", "Weather-Resistant", "Cement", "Texture", "Metallic", "Matte"],
}

MATERIAL_COSTS = {
    'cement': {},  # Fill dynamically based on company/type
    'sand': {
        'River Sand': 1500, 'M-Sand': 1200, 'Pit Sand': 1300, 'Crushed Stone Sand': 1100
    },  # per cubic meter
    'steel': {},  # Fill dynamically based on company/type
    'bricks': {
        'Burnt Clay First Class': 7, 'Burnt Clay Second Class': 6.5, 'Burnt Clay Third Class': 6,
        'Fly Ash Bricks': 5.5, 'Concrete Bricks Solid': 6, 'Concrete Bricks Hollow': 5,
        'AAC Blocks': 12, 'Red Clay Bricks': 6, 'Sand Lime Bricks': 8, 'Engineering Bricks': 10,
        'Fire Bricks': 15, 'Perforated Bricks': 7, 'Hollow Bricks': 5.8
    },  # per unit
    'tiles': {
        'Ceramic': 80, 'Vitrified Glazed': 120, 'Vitrified Double Charged': 150, 'Vitrified Full Body': 180,
        'Marble': 300, 'Granite': 250, 'Kota Stone': 100, 'Sandstone': 150, 'Wooden': 400, 'Terrazzo': 200,
        'Vinyl': 60
    },  # per sq ft
    'flooring': {
        'Marble': 300, 'Granite': 250, 'Kota Stone': 100, 'Sandstone': 150, 'Wooden': 400,
        'Vinyl': 60, 'Terrazzo': 200, 'Cement Concrete': 50  # per sq ft
    },  # per sq ft
    'paints': {},  # Fill dynamically based on company/type
    'plumbing': {
        'PVC': 50, 'CPVC': 70, 'GI': 80, 'PPR': 60, 'Brass Faucets': 500,
        'Stainless Steel Fittings': 300, 'Water Tanks': 10000, 'SWR Pipes': 40
    },  # per unit/length. Modified
    'electrical': {
        'Copper Wiring': 70, 'Aluminum Wiring': 40, 'Modular Switches': 150, 'Conventional Switches': 80,
        'MCB': 200, 'RCCB': 500, 'LED Lights': 300, 'CFL Lights': 150, 'Halogen Lights': 100
    },  # per unit. Modified
    'doors': {
        'Wooden Teak': 8000, 'Wooden Sal': 7000, 'Wooden Pine': 6000, 'Flush': 4000,
        'UPVC/PVC': 5000, 'Steel': 6000
    },  # per unit
    'windows': {
        'Wooden': 6000, 'Aluminum': 5000, 'UPVC': 4500, 'Steel': 5500
    },  # per unit
    'roofing': {
        'RCC Roof': 150, 'Flat Roof': 120, 'Sloped Roof': 180, 'Metal': 200,
        'Clay Tile': 250, 'Asphalt Shingles': 160, 'Thatch': 80, 'Polycarbonate': 220,
        'Fiberglass/Plastic': 180
    },
    'aggregates': {
        'Coarse Crushed Stone': 900, 'Coarse Gravel': 800, 'Coarse Brick Aggregate': 700,
        'Fine River Sand': 1500, 'Fine M-Sand': 1200, 'Fine Pit Sand': 1300, 'Fine Crushed Stone Sand': 1100,
        'Recycled Aggregates': 600, 'Lightweight LECA': 1800, 'Lightweight Expanded Clay': 1700,
        'Lightweight Cinder': 1600
    }
}


for company, types in CEMENT_COMPANIES.items():
    MATERIAL_COSTS['cement'][company] = {}
    for cement_type in types:
        MATERIAL_COSTS['cement'][company][cement_type] = 380  # Base Price - Adjust as needed


for company, types in TMT_BARS.items():
    MATERIAL_COSTS['steel'][company] = {}
    for steel_type in types:
        MATERIAL_COSTS['steel'][company][steel_type] = 55000  # Base Price - Adjust as needed


for company, types in PAINT_BRANDS.items():
    MATERIAL_COSTS['paints'][company] = {}
    for paint_type in types:
        MATERIAL_COSTS['paints'][company][paint_type] = 15  # Base Price - Adjust as needed


THUMB_RULES = {
    'cement': 0.4,  # bags per sq ft
    'sand': 0.05,  # cubic meters per sq ft
    'steel': 2.5 / 1000,  # metric tons per sq ft
    'bricks': 7.5,  # units per sq ft
    'tiles': 1.0,  # sq ft per sq ft
    'flooring': 1.0,  # sq ft per sq ft
    'paints': 1.0,  # sq ft per sq ft
    'plumbing': 1.5,  # unit/length per sq ft (example)
    'electrical': 1.5,  # unit per sq ft (example)
    'doors': 0.1,  # units per sq ft (very rough estimate)
    'windows': 0.1,  # units per sq ft (very rough estimate)
    'roofing': 1.1,  # sq ft per sq ft (more than 1 for overlap/wastage)
    'aggregates': 0.06  # cubic meters per sq ft
}

def preprocess_image(image):
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return threshold, image_cv

def extract_text_from_image(image):
    reader = easyocr.Reader(['en'])
    results = reader.readtext(image)
    return ' '.join([text[1] for text in results])

def find_dimensions(text) -> List[Tuple[float, float]]:
    dimension_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:x|×|X)\s*(\d+(?:\.\d+)?)',
        r'(\d+)\s*(?:x|×|X)\s*(\d+)',
    ]

    dimensions = set()
    for pattern in dimension_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                dim1, dim2 = match.groups()
                dim1_val = float(dim1)
                dim2_val = float(dim2)
                if dim1_val > 0 and dim2_val > 0:
                    dimensions.add(tuple(sorted([dim1_val, dim2_val])))
            except:
                continue

    return list(dimensions)

def calculate_total_area(dimensions: List[Tuple[float, float]],
                         outer_length: float,
                         outer_width: float,
                         unit: str) -> Dict[str, float]:

    conv_factor = CONVERSION_FACTORS[unit]

    floor_area = sum(dim1 * dim2 for dim1, dim2 in dimensions) * conv_factor

    ceiling_area = floor_area

    total_length = sum(dim1 + dim2 for dim1, dim2 in dimensions) + outer_length + outer_width

    if unit == 'meters':
        wall_length_meters = total_length
    elif unit == 'centimeters':
        wall_length_meters = total_length / 100
    elif unit == 'feet':
        wall_length_meters = total_length * 0.3048
    else:  # inches
        wall_length_meters = total_length * 0.0254

    wall_area_meters = wall_length_meters * 3  # 3 meters height

    wall_area = wall_area_meters * 10.764

    total_area = floor_area + ceiling_area + wall_area

    return {
        'floor': floor_area,
        'ceiling': ceiling_area,
        'walls': wall_area,
        'total': total_area
    }

def calculate_material_costs(total_area: float, material_type: str, subtype=None, company=None):
    """Calculates material costs, handling company selection for cement, steel and paints.
       Also returns the material quantity."""
    quantity_per_sqft = THUMB_RULES[material_type]

    if material_type in ['cement', 'steel', 'paints']:
        cost_per_unit = MATERIAL_COSTS[material_type][company][subtype]  # Retrieve nested value
    else:
        cost_per_unit = MATERIAL_COSTS[material_type].get(subtype, MATERIAL_COSTS[material_type])  # if subtype exist

    total_quantity = total_area * quantity_per_sqft

    #Units modifications
    if material_type == 'cement':
        quantity_string = f"{total_quantity:,.2f} bags"
    elif material_type == 'sand' or material_type == 'aggregates':
        quantity_string = f"{total_quantity:,.2f} cubic meters"
    elif material_type == 'steel':
        quantity_string = f"{total_quantity:,.2f} metric tons"
    elif material_type == 'bricks':
        quantity_string = f"{total_quantity:,.2f} units"
    elif material_type == 'tiles' or material_type == 'flooring' or material_type == 'paints':
        quantity_string = f"{total_quantity:,.2f} sq ft"
    elif material_type == 'plumbing' or material_type == 'electrical':
        quantity_string = f"{total_quantity:,.2f} units"
    elif material_type == 'doors' or material_type == 'windows':
        quantity_string = f"{total_quantity:,.2f} units"
    elif material_type == 'roofing':
        quantity_string = f"{total_quantity:,.2f} sq ft"
    else:
        quantity_string = f"{total_quantity:,.2f}"

    total_cost = total_quantity * cost_per_unit

    return quantity_string, total_cost

def main():
    st.title("Construction Material Calculator")
    st.write("Upload a floor plan image to calculate material quantities and costs")

    unit = st.selectbox(
        "Select measurement unit of the dimensions in the image",
        options=['feet', 'inches', 'meters', 'centimeters'],
        index=0
    )

    col1, col2 = st.columns(2)
    with col1:
        outer_length = st.number_input(f"Outer Length ({unit})", min_value=0.0, value=0.0)
    with col2:
        outer_width = st.number_input(f"Outer Width ({unit})", min_value=0.0, value=0.0)

    if 'materials_selected' not in st.session_state:
        st.session_state.materials_selected = {}

    if 'calculation_results' not in st.session_state:
        st.session_state.calculation_results = {}

    uploaded_file = st.file_uploader("Choose a floor plan image", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Floor Plan', use_column_width=True)

        if st.button('Calculate Square Footage'):
            try:
                with st.spinner('Processing image...'):
                    processed_image, original_cv = preprocess_image(image)
                    extracted_text = extract_text_from_image(original_cv)

                    dimensions = find_dimensions(extracted_text)

                    if dimensions:
                        areas = calculate_total_area(dimensions, outer_length, outer_width, unit)
                        total_sqft = areas['total']

                        st.session_state.total_sqft = total_sqft

                        st.success(f"Total Square Footage: {total_sqft:,.2f} sq ft")

                        with st.expander("Detailed Breakdown"):
                            st.write(f"Floor Area: {areas['floor']:,.2f} sq ft")
                            st.write(f"Ceiling Area: {areas['ceiling']:,.2f} sq ft")
                            st.write(f"Wall Area: {areas['walls']:,.2f} sq ft")

                        with st.expander("Detected Room Dimensions"):
                            for dim1, dim2 in dimensions:
                                area_in_unit = dim1 * dim2
                                area_in_sqft = area_in_unit * CONVERSION_FACTORS[unit]
                                st.text(f"{dim1:.2f} {unit} × {dim2:.2f} {unit} = {area_in_sqft:.2f} sq ft")

                        with st.expander("Show extracted text"):
                            st.text(extracted_text)

                    else:
                        st.warning("Could not detect room dimensions. Try uploading a clearer image.")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

        if 'total_sqft' in st.session_state:
            st.subheader("Material Costs")

            # Dynamically create selection widgets based on available materials
            for material_type, subtypes in MATERIAL_COSTS.items():
                if material_type in ['doors', 'windows', 'sand', 'bricks', 'tiles', 'flooring', 'plumbing', 'electrical', 'roofing', 'aggregates']: # single selector
                    subtype = st.selectbox(
                        f"Select {material_type} type",
                        options=subtypes.keys(),
                        key=material_type
                    )
                    st.session_state.materials_selected[material_type] = {'subtype': subtype, 'company': None}

                elif material_type in ['cement', 'steel', 'paints']:
                    company = st.selectbox(
                        f"Select {material_type} Company",
                        options=MATERIAL_COSTS[material_type].keys(),
                        key=f'{material_type}_company'
                    )
                    subtype = st.selectbox(
                        f"Select {material_type} Type",
                        options=MATERIAL_COSTS[material_type][company].keys(),
                        key=f'{material_type}_type'
                    )
                    st.session_state.materials_selected[material_type] = {'company': company, 'subtype': subtype}

            if st.button('Calculate Material Costs'):
                total_sqft = st.session_state.total_sqft

                # Calculate all costs
                for material_type, selection in st.session_state.materials_selected.items():
                    subtype = selection['subtype']
                    company = selection['company']

                    material_quantity, total_cost = calculate_material_costs(
                        total_sqft, material_type, subtype, company
                    )

                    st.session_state.calculation_results[material_type] = {
                        'subtype': subtype,
                        'company': company,
                        'quantity': material_quantity,
                        'cost': total_cost
                    }

                # Show results
                st.subheader("Calculation Results")
                for material_type, result in st.session_state.calculation_results.items():
                    subtype = result['subtype']
                    company = result['company']
                    display_string = f"{material_type.capitalize()}"
                    if company:
                         display_string += f" ({company} - {subtype})"
                    else:
                        display_string += f" ({subtype})"
                    st.write(display_string+":")
                    st.write(f"  - Quantity: {result['quantity']}")
                    st.write(f"  - Total Cost: ₹{result['cost']:,.2f}")

if __name__ == "__main__":
    main()
