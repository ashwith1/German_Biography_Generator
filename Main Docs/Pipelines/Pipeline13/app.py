from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify, send_from_directory
from docx import Document
import os
import io
import zipfile
import threading
import pandas as pd
from nltk.tokenize import word_tokenize, sent_tokenize
from fpdf import FPDF
import time
from flask_socketio import SocketIO, emit
from langchain_together import Together
import nltk
from flask import send_from_directory
from io import BytesIO
from docx import Document
from PyPDF2 import PdfReader, PdfWriter


nltk.download('punkt')

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = "126022cbbf2d4e73287470a6cafe29a87a3423b0c0511c2a68c9da83f16f2665"

# Define the upload and processed folders
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'

# Ensure the directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

output_directory = "output_pdfs"
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

ALLOWED_EXTENSIONS = {'csv'}


def read_csv(file):
    try:
        # Use BytesIO to read the file correctly
        file.stream.seek(0)
        file_content = file.read()  # Read file content
        df = pd.read_csv(BytesIO(file_content), sep='\t')  # Use BytesIO to pass the content
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

def read_docx(file):
    try:
        file.stream.seek(0)
        doc = Document(BytesIO(file.read()))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip() != '']
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"Error reading DOCX file: {e}")
        return None

def read_pdf(file):
    try:
        file.stream.seek(0)
        reader = PdfReader(BytesIO(file.read()))
        text = []
        for page in reader.pages:
            text.append(page.extract_text())
        return "\n".join(filter(None, text))
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to save text to PDF
def save_text_to_pdf(text, pdf_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add text to the PDF
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    
    # Save the PDF
    pdf.output(pdf_path)

# Function to extract rows
def extract_rows_with_sprecher(df, sprecher_prefix):
    df = df.dropna(subset=['Sprecher'])
    filtered_rows = df[df['Sprecher'].str.startswith(sprecher_prefix)]
    transkript_list = filtered_rows['Transkript'].tolist()
    return transkript_list

# Convert transcript list to string
def transkript_to_string(transkript_list):
    return "\n".join(transkript_list)

# Function to divide text into chunks
def divide_into_chunks(text, max_words_per_chunk):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_word_count = 0

    for sentence in sentences:
        words_in_sentence = len(word_tokenize(sentence))
        if current_word_count + words_in_sentence > max_words_per_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_word_count = words_in_sentence
        else:
            current_chunk.append(sentence)
            current_word_count += words_in_sentence

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


class Summarizer:
    def __init__(self):
        self.llm = Together(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            temperature=0.1,
            max_tokens= 1024,
            top_k=1,
        together_api_key="ce2345c478268c88d8952d1324945d1f5f766bb43ccb0733c954ccebc10c32f3"    
        )
# together_api_key = "0c7ca1d8efd796b972cf1a5593343213bd4ab46451a2cecbcac333fa6f02793f"
    def invoke_with_retry(self, full_input, retries=3, retry_delay=30):
        for attempt in range(retries):
            try:
                output_summary = self.llm.invoke(full_input)
                return output_summary
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print("Max retries reached. Could not get a response from the server.")
                    raise e

    def generate_biography(self, input_text):
        self.llm.temperature = 0.1
        self.llm.max_tokens = 1024
        self.llm.top_k = 1
        
        prompt = """
I would like you to generate biography of an interviewee based on the following structured questions in German language, make sure it is in german language only. Please address each question thoroughly, ensuring that the narrative flows smoothly from one life stage to the next. The biography should include the following information:

Birth and Early Family Life:

When and where was the interviewee born? Include the date and location of birth.
Who are the interviewee's parents? Provide their names, backgrounds, and any relevant details about their lives.
Does the interviewee have any siblings? If so, provide details about them, including names and relationships.
Education:

Which school or schools did the interviewee attend? Mention the date, names of the institutions, locations, and any significant experiences or achievements during their education.
Career and Professional Life:

What profession did the interviewee learn or train for? Mention date and describe the nature of their training or education in this field.
Which jobs or professions has the interviewee practiced? Include details about the dates, roles, companies, or organizations they worked for, and any significant milestones or achievements in their career.
Life Events and Personal Milestones:

What were the formative or significant life events with years mentioned in the interviewee's childhood? Mention dates, Include any experiences that had a lasting impact.
What were the formative or significant life events with years mentioned during the interviewee's adolescence?  Mention dates, Describe how these events influenced their path in life.
What were the formative or significant life events with years mentioned in the interviewee's early adult years? Include details about any dates, transitions, challenges, or accomplishments during this period.
What were the formative or significant life events with years mentioned during the interviewee's adult years?  Mention dates, Describe key experiences that shaped their personal or professional life.
What were the formative or significant life events with years mentioned in the interviewee's late adult years? Highlight any dates, major changes, achievements, or reflections during this time.
Personal Life:

Did the interviewee marry  with years mentioned? If yes, provide details about their spouse,dates, including the name and any significant information about their relationship.
Does the interviewee have children with years mentioned? If so, provide details about their children, dates, including names and any significant life events related to them.
Significant Life Events:

What are the most significant life events that have shaped the interviewee's life with years mentioned? Reflect on how these events with years mentioned impacted their personal growth, relationships, or career, dates.
Please ensure the biography is coherent, chronological, detailed, and presents a well-rounded view of the interviewee's life journey with years mentioned.
        """
        
        chunks = divide_into_chunks(input_text, max_words_per_chunk=70000)
        biography_parts = []
        
        for chunk in chunks:
            full_input = chunk + prompt
            output_summary = self.invoke_with_retry(full_input)
            biography_parts.append(output_summary.strip())

        full_biography = " ".join(biography_parts)
        return full_biography

    # def extend_biography(self, partial_biography, input_text):
    #     self.llm.temperature = 0.1
    #     self.llm.max_tokens = 800
    #     self.llm.top_k = 1
        
    #     prompt = f"""
    #     Hier ist der erste Teil der Biografie: {partial_biography}
    #     Nun sehen Sie sich die Daten erneut an und ergänzen Sie die Biografie um die fehlenden Informationen.
    #     """

    #     chunks = divide_into_chunks(input_text, max_words_per_chunk=70000)
    #     extended_biography_parts = []
        
    #     for chunk in chunks:
    #         full_input = chunk + prompt
    #         output_summary = self.invoke_with_retry(full_input)
    #         extended_biography_parts.append(output_summary.strip())

    #     full_extended_biography = " ".join(extended_biography_parts)
    #     return self.remove_incomplete_sentence(full_extended_biography)

    # def refine_biography_to_500_words(self, extended_biography, input_text):
    #     self.llm.temperature = 0.1
    #     self.llm.max_tokens = 512
    #     self.llm.top_k = 1

    #     prompt = f"""
    #     Hier ist der erste Teil der Biografie: {extended_biography}
    #     Nun sehen Sie sich die Daten erneut an und ergänzen Sie die Biografie um die fehlenden Informationen.
    #     """
        
    #     chunks = divide_into_chunks(input_text, max_words_per_chunk=70000)
    #     refined_parts = []

    #     for chunk in chunks:
    #         full_input = chunk + prompt
    #         output_summary = self.invoke_with_retry(full_input)
    #         refined_parts.append(output_summary.strip())

    #     full_refined_biography = " ".join(refined_parts)
    #     return self.remove_incomplete_sentence(full_refined_biography)

    # def remove_incomplete_sentence(self, biography):
    #     words = word_tokenize(biography)
    #     if len(words) <= 800:
    #         return biography
        
    #     truncated_words = words[:800]
    #     truncated_text = " ".join(truncated_words)
    #     last_full_stop_index = truncated_text.rfind('.')
        
    #     if last_full_stop_index != -1:
    #         return truncated_text[:last_full_stop_index + 1]
    #     else:
    #         return truncated_text



# Function to save text to PDF
def save_text_to_pdf(text, pdf_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add text to the PDF
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    
    # Save the PDF
    pdf.output(pdf_path)

# Function to process the files
def process_file_and_update_status(file):
    try:
        transcript_data = None
        file_name = file.filename
        base_file_name = os.path.basename(file_name)  # Extract only the file name

        if file_name.endswith('.csv'):
            df = read_csv(file)
            df['Transkript'] = df['Transkript'].fillna('').astype(str)
            transcript_data = "\n".join(df['Transkript'].tolist())
        elif file_name.endswith('.docx'):
            transcript_data = read_docx(file)
        elif file_name.endswith('.pdf'):
            transcript_data = read_pdf(file)

        if transcript_data:
            socketio.emit('update', {'file': base_file_name, 'status': 'Processing'}, namespace='/')
            summarizer = Summarizer()
            biography = summarizer.generate_biography(transcript_data)
            output_pdf_path = os.path.join(PROCESSED_FOLDER, base_file_name.rsplit('.', 1)[0] + '.pdf')
            save_text_to_pdf(biography, output_pdf_path)
            socketio.emit('update', {'file': base_file_name, 'status': 'Completed'}, namespace='/')
        else:
            socketio.emit('update', {'file': base_file_name, 'status': 'Failed'}, namespace='/')
    except Exception as e:
        print(f"Error processing file {file_name}: {e}")
        socketio.emit('update', {'file': base_file_name, 'status': 'Failed'}, namespace='/')

               
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('files')
        folder_files = request.files.getlist('folder')  # Get files from folder selection

        # Combine both file lists (folder files and individual files)
        all_files = files + folder_files

        for file in all_files:
            if file:
                thread = threading.Thread(target=process_file_and_update_status, args=(file,))
                thread.start()
        return jsonify({'message': 'Files are being processed.'})
    return render_template('index.html')

# Download processed PDF
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)

if __name__ == '__main__':
    socketio.run(app, debug=True)