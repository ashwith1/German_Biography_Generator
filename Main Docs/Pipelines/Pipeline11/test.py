from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
import os
import io
from fpdf import FPDF
import pandas as pd
from nltk.tokenize import word_tokenize, sent_tokenize
from flask_socketio import SocketIO, emit
from langchain_together import Together
import nltk
import time

nltk.download('punkt')

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key = "126022cbbf2d4e73287470a6cafe29a87a3423b0c0511c2a68c9da83f16f2665"

output_directory = "output_pdfs"
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_csv(file_path):
    try:
        df = pd.read_csv(file_path, sep='\t')
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None
    
def remove_incomplete_sentences(biography):
    last_full_stop_index = biography.rfind('.')
    
    if last_full_stop_index != -1:
        return biography[:last_full_stop_index + 1]
    else:
        return biography    

def extract_rows_with_sprecher(df, sprecher_prefix):
    df = df.dropna(subset=['Sprecher'])
    filtered_rows = df[df['Sprecher'].str.startswith(sprecher_prefix)]
    transkript_list = filtered_rows['Transkript'].tolist()
    return transkript_list

def transkript_to_string(transkript_list):
    return "\n".join(transkript_list)

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
            max_tokens=1024,
            top_k=1,
            together_api_key="6788ace2080edcd6805e9d9c58270166e6f8dabe5e36b98714832e9cac711ef8"
        )

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
        
        I would like you to generate a detailed biography of an interviewee based on the following structured questions in german. Please address each question thoroughly, ensuring that the narrative flows smoothly from one life stage to the next. The biography should include the following information:

Birth and Early Family Life:

When and where was the interviewee born? Include the date and location of birth.
Who are the interviewee's parents? Provide their names, backgrounds, and any relevant details about their lives.
Does the interviewee have any siblings? If so, provide details about them, including names and relationships.
Education:

Which school or schools did the interviewee attend? Mention the names of the institutions, locations, and any significant experiences or achievements during their education.
Career and Professional Life:

What profession did the interviewee learn or train for? Describe the nature of their training or education in this field.
Which jobs or professions has the interviewee practiced? Include details about the roles, companies, or organizations they worked for, and any significant milestones or achievements in their career.
Life Events and Personal Milestones:

What were the formative or significant life events in the interviewee's childhood? Include any experiences that had a lasting impact.
What were the formative or significant life events during the interviewee's adolescence? Describe how these events influenced their path in life.
What were the formative or significant life events in the interviewee's early adult years? Include details about any transitions, challenges, or accomplishments during this period.
What were the formative or significant life events during the interviewee's adult years? Describe key experiences that shaped their personal or professional life.
What were the formative or significant life events in the interviewee's late adult years? Highlight any major changes, achievements, or reflections during this time.
Personal Life:

Did the interviewee marry? If yes, provide details about their spouse, including the name and any significant information about their relationship.
Does the interviewee have children? If so, provide details about their children, including names and any significant life events related to them.
Significant Life Events:

What are the most significant life events that have shaped the interviewee's life overall? Reflect on how these events impacted their personal growth, relationships, or career.
Please ensure the biography is coherent, detailed, and presents a well-rounded view of the interviewee's life journey.
        """
        
        chunks = divide_into_chunks(input_text, max_words_per_chunk=70000)
        biography_parts = []
        
        for chunk in chunks:
            full_input = chunk + prompt
            output_summary = self.invoke_with_retry(full_input)
            biography_parts.append(output_summary.strip())

        full_biography = " ".join(biography_parts)
        return full_biography

    def extend_biography(self, partial_biography, input_text):
        self.llm.temperature = 0.1
        self.llm.max_tokens = 800
        self.llm.top_k = 1
        
        prompt = f"""
        Hier ist der erste Teil der Biografie: {partial_biography}
        Schauen Sie sich nun die Daten noch einmal an und ergänzen Sie die Biografie um die fehlenden Informationen.
        """
        
        chunks = divide_into_chunks(input_text, max_words_per_chunk=70000)
        extended_biography_parts = []
        
        for chunk in chunks:
            full_input = chunk + prompt
            output_summary = self.invoke_with_retry(full_input)
            extended_biography_parts.append(output_summary.strip())

        full_extended_biography = " ".join(extended_biography_parts)
        return self.remove_incomplete_sentence(full_extended_biography)

    def refine_biography_to_500_words(self, extended_biography, input_text):
        self.llm.temperature = 0.1
        self.llm.max_tokens = 600
        self.llm.top_k = 1

        prompt = f"""
        Hier ist der erste Teil der Biografie: {extended_biography}
        Nun sehen Sie sich die Daten erneut an und ergänzen Sie die Biografie um die fehlenden Informationen.
        """
        
        chunks = divide_into_chunks(input_text, max_words_per_chunk=70000)
        refined_parts = []

        for chunk in chunks:
            full_input = chunk + prompt
            output_summary = self.invoke_with_retry(full_input)
            refined_parts.append(output_summary.strip())

        full_refined_biography = " ".join(refined_parts)
        return self.remove_incomplete_sentence(full_refined_biography)

    def remove_incomplete_sentence(self, biography):
        words = word_tokenize(biography)
        if len(words) <= 800:
            return biography
        
        truncated_words = words[:800]
        truncated_text = " ".join(truncated_words)
        last_full_stop_index = truncated_text.rfind('.')
        
        if last_full_stop_index != -1:
            return truncated_text[:last_full_stop_index + 1]
        else:
            return truncated_text

def save_text_to_docx(text):
    from docx import Document
    doc = Document()
    doc.add_paragraph(text)

    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

@app.route('/process_and_download', methods=['POST'])
def process_and_download():
    if 'file' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('home'))
    
    file = request.files['file']
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(output_directory, filename)
        file.save(file_path)
        doc_io = process_file_and_update_status(file_path)
        if doc_io:
            return send_file(doc_io, as_attachment=True, download_name=filename.replace('.csv', '.docx'), mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        
        flash("File processing failed.", "danger")
    else:
        flash("Invalid file format or no file selected.", "danger")
    
    return redirect(url_for('home'))


def process_file_and_update_status(file_path):
    df = read_csv(file_path)
    
    if df is not None:
        summarizer = Summarizer()
        sprecher_prefix = 'IP_'
        transkript_list = extract_rows_with_sprecher(df, sprecher_prefix)
        transcript_data = transkript_to_string(transkript_list)

        socketio.emit('update', {'file': os.path.basename(file_path), 'status': 'Processing'})

        initial_biography = summarizer.generate_biography(transcript_data)
        print(initial_biography)
        # extended_biography = summarizer.extend_biography(initial_biography, transcript_data)
        # print(extended_biography)
        # refined_biography = summarizer.refine_biography_to_500_words(extended_biography, transcript_data)
        # print(refined_biography)
        # incomplete_sent_removal = remove_incomplete_sentences(refined_biography)
        # print(incomplete_sent_removal)
        doc_io = save_text_to_docx(initial_biography)
        socketio.emit('update', {'file': os.path.basename(file_path), 'status': 'Completed'})
        return doc_io
    else:
        socketio.emit('update', {'file': file_path, 'status': 'Failed'}, broadcast=True)
    return None

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)
