import streamlit as st
import requests
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

# This must be the first Streamlit command used.
st.set_page_config(page_title="German Biography Generator", layout="wide")

# Custom header with HTML and CSS
header_html = """
    <div style="background-color:#618264; padding:10px; border-radius:10px">
    <h1 style="color:white; text-align:center;">German Biography Generator</h1>
    <p style="color:white; text-align:center;">We generate short biographies in the German language using interview text of any length. Please upload the interview text in CSV format to generate a biography of the interviewee.</p>
    </div>
    """
st.markdown(header_html, unsafe_allow_html=True)

# Inject CSS for "Generate new biography" button color
st.markdown("""
<style>
.stButton>button {
    border: 1px solid #4CAF50;
    border-radius: 4px; /* Match Streamlit's default button radius */
    color: black; /* Match Streamlit's default button text color */
    background-color: #D0E7D2; /* Custom button color */
    font-size: 16px; /* Adjust to match Streamlit's default button size, if needed */
}
</style>
""", unsafe_allow_html=True)

if 'biography_generated' not in st.session_state:
    st.session_state.biography_generated = False

if not st.session_state.biography_generated:
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'], key="file_uploader")
    if uploaded_file is not None:
        with st.spinner('Processing the document and generating biography...'):
            response = requests.post(
                'http://127.0.0.1:5000',  # Replace with actual backend server address
                files={'file': uploaded_file.getvalue()}
            )

            if response.status_code == 200:
                biography_text = response.json()['biography']
                st.session_state.biography_text = biography_text  # Store biography text in session state
                st.session_state.biography_generated = True
                st.experimental_rerun()
            else:
                st.error("Failed to process the CSV file.")
else:
    st.success("Biography generated successfully.")
    
    # Add a heading for the biography preview
    st.markdown("""
        <h2 style='text-align: left; margin-top: 20px;'>Biography</h2>
        """, unsafe_allow_html=True)
    
    st.write(st.session_state.biography_text)

    # Convert the biography text to a PDF file
    def create_pdf(biography_text):
        pdf_io = io.BytesIO()
        c = canvas.Canvas(pdf_io, pagesize=A4)
        text = biography_text.split('\n')
        text = [line.strip() for line in text if line.strip() != '']
        width, height = A4
        left_margin = 72
        right_margin = width - 72
        y = height - 72  # Start writing from the top of the page
        max_width = right_margin - left_margin
        
        for line in text:
            wrapped_lines = simpleSplit(line, "Helvetica", 12, max_width)
            for wrapped_line in wrapped_lines:
                c.drawString(left_margin, y, wrapped_line)
                y -= 15  # Move to the next line
                if y < 72:
                    c.showPage()  # Add a new page if the current is full
                    y = height - 72  # Reset y coordinate
        
        c.save()
        pdf_io.seek(0)
        return pdf_io

    pdf_io = create_pdf(st.session_state.biography_text)
    st.download_button(label="Download Biography in PDF Format",
                       data=pdf_io,
                       file_name="biography.pdf",
                       mime="application/pdf")
    if st.button("Generate new biography"):
        st.session_state.biography_generated = False
        st.session_state.biography_text = ""
        st.experimental_rerun()
