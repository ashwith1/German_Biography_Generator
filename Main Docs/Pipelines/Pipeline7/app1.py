import streamlit as st
from final_file import process_file
from docx import Document
import io

# This must be the first Streamlit command used.
st.set_page_config(page_title="German Biography Generator", layout="wide")

# Custom header with HTML and CSS
header_html = """
<div style="background-color: #3B523B; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
    <h1 style="color: #E6F4EA; text-align: center; font-family: 'Arial', sans-serif; font-size: 2.5em; margin-bottom: 10px;">German Biography Generator</h1>
    <p style="color: #E6F4EA; text-align: center; font-family: 'Arial', sans-serif; font-size: 1.2em;">We generate short biographies in the German language. Please upload the interview text in Word format or CSV to generate a biography of the interviewee.</p>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# Inject CSS for "Generate new biography" button color
st.markdown("""
<style>
.stButton>button {
    border: 2px solid #4CAF50;
    border-radius: 8px; /* Match Streamlit's default button radius */
    color: white; /* Match Streamlit's default button text color */
    background-color: #4CAF50; /* Custom button color */
    font-size: 18px; /* Adjust to match Streamlit's default button size, if needed */
    font-family: 'Arial', sans-serif;
    padding: 10px 20px; /* Add padding for better button size */
    transition: background-color 0.3s ease, color 0.3s ease;
    cursor: pointer;
}
.stButton>button:hover {
    background-color: #45a049; /* Darker green on hover */
    color: white; /* Text color on hover */
}
</style>
""", unsafe_allow_html=True)



def create_word_document(biography_text):
    doc = Document()
    doc.add_paragraph(biography_text)
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

if 'biography_generated' not in st.session_state:
    st.session_state.biography_generated = False

if not st.session_state.biography_generated:
    uploaded_file = st.file_uploader("Choose a Word or CSV file", type=['docx', 'csv'], key="file_uploader")
    if uploaded_file is not None:
        with st.spinner('Processing the document and generating biography...'):
            # Save the uploaded file to a temporary path
            temp_file_path = f"temp_file.{uploaded_file.name.split('.')[-1]}"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Process the file and generate biography
            biography_text = process_file(temp_file_path)
            
            # Clean up the temporary file
            os.remove(temp_file_path)
            
            st.session_state.biography_text = biography_text
            st.session_state.biography_generated = True
            st.experimental_rerun()
else:
    st.success("Biography generated successfully.")
    
    # Add a heading for the biography preview
    st.markdown("""
        <h2 style='text-align: left; margin-top: 20px;'>Biography</h2>
        """, unsafe_allow_html=True)
    
    st.write(st.session_state.biography_text)
    doc_io = create_word_document(st.session_state.biography_text)
    st.download_button(label="Download Biography in Word Format",
                       data=doc_io,
                       file_name="biography.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    if st.button("Generate new biography"):
        st.session_state.biography_generated = False
        st.session_state.biography_text = ""
        st.experimental_rerun()
