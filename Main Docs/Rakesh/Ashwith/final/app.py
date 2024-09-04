# from flask import Flask, render_template, request
# import os
# import threading
# import pandas as pd
# from nltk.tokenize import word_tokenize, sent_tokenize
# from fpdf import FPDF
# import time
# from flask_socketio import SocketIO, emit
# from langchain_together import Together
# import nltk
# nltk.download('punkt')

# app = Flask(__name__)
# socketio = SocketIO(app)

# # Directory path for processing

# directory_path = "C:\\Users\\hsrak\\Desktop\\case_study\\Files"
# output_directory = os.path.join(directory_path, "output_pdfs")

# # Ensure output directory exists
# if not os.path.exists(output_directory):
#     os.makedirs(output_directory)

# # Function to read CSV
# def read_csv(file_path):
#     try:
#         df = pd.read_csv(file_path, sep='\t')
#         return df
#     except Exception as e:
#         print(f"Error reading CSV file: {e}")
#         return None

# # Function to extract rows
# def extract_rows_with_sprecher(df, sprecher_prefix):
#     df = df.dropna(subset=['Sprecher'])
#     filtered_rows = df[df['Sprecher'].str.startswith(sprecher_prefix)]
#     transkript_list = filtered_rows['Transkript'].tolist()
#     return transkript_list

# # Convert transcript list to string
# def transkript_to_string(transkript_list):
#     return "\n".join(transkript_list)

# # Function to divide text into chunks
# def divide_into_chunks(text, max_words_per_chunk):
#     sentences = sent_tokenize(text)
#     chunks = []
#     current_chunk = []
#     current_word_count = 0

#     for sentence in sentences:
#         words_in_sentence = len(word_tokenize(sentence))
#         if current_word_count + words_in_sentence > max_words_per_chunk:
#             chunks.append(' '.join(current_chunk))
#             current_chunk = [sentence]
#             current_word_count = words_in_sentence
#         else:
#             current_chunk.append(sentence)
#             current_word_count += words_in_sentence

#     if current_chunk:
#         chunks.append(' '.join(current_chunk))

#     return chunks

# class Summarizer:
#     def __init__(self):
#         self.llm = Together(
#             model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
#             temperature=0.1,
#             max_tokens= 1024,
#             top_k=1,
#             together_api_key="126022cbbf2d4e73287470a6cafe29a87a3423b0c0511c2a68c9da83f16f2665"
#         )

# #160be45af627da8e0d12935e59de9db8648a6327ba2a81a563bacb39750a052e

#     def invoke_with_retry(self, full_input, retries=3, retry_delay=30):
#         # for attempt in range(retries):
#         #     try:
#         #         output_summary = self.llm.invoke(full_input)
#         #         return output_summary
#         #     except Exception as e:
#         #         if "524" in str(e) and attempt < retries - 1:
#         #             print(f"Error 524: Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{retries})")
#         #             time.sleep(retry_delay)
#         #             retries += 1

#         #         else:
#         #             raise
#           for attempt in range(retries):
#             try:
#                 output_summary = self.llm.invoke(full_input)
#                 return output_summary
#             except Exception as e:
#                 print(f"Attempt {attempt + 1} failed: {str(e)}")
#                 if attempt < retries - 1:
#                     time.sleep(2 ** attempt)  # Exponential backoff
#                 else:
#                     print("Max retries reached. Could not get a response from the server.")
#                     raise e


#     def generate_biography(self, input_text):
#         self.llm.temperature = 0.1
#         self.llm.max_tokens = 1024
#         self.llm.top_k = 1
        
#         prompt = """
#         Du bist ein deutsches Textzusammenfassungsmodell. Erstellen Sie eine prägnante Zusammenfassung des obigen Textes in deutscher Sprache innerhalb von 500 Wörtern. Konzentrieren Sie sich auf die wichtigsten Punkte und bewahren Sie Klarheit. Work only with the data given and do not provide your conclusions or interpretations of the biography or the data provided. Work only with the data.
#         """
        
#         chunks = divide_into_chunks(input_text, max_words_per_chunk = 70000)
#         biography_parts = []
        
#         for chunk in chunks:
#             full_input = chunk + prompt
#             output_summary = self.invoke_with_retry(full_input)
#             biography_parts.append(output_summary.strip())

#         full_biography = " ".join(biography_parts)
#         return full_biography


#     def extend_biography(self, partial_biography, input_text):
#         self.llm.temperature = 0.1
#         self.llm.max_tokens = 800 
#         self.llm.top_k = 1
        
#         prompt = f"""
#         Hier ist der erste Teil der Biografie: {partial_biography}
#         Nun sehen Sie sich die Daten erneut an und ergänzen Sie die Biografie um die fehlenden Informationen.
#         """

#         chunks = divide_into_chunks(input_text, max_words_per_chunk=70000)
#         extended_biography_parts = []
        
#         for chunk in chunks:
#             full_input = chunk + prompt
#             output_summary = self.invoke_with_retry(full_input)
#             extended_biography_parts.append(output_summary.strip())

#         full_extended_biography = " ".join(extended_biography_parts)
#         return self.remove_incomplete_sentence(full_extended_biography)


#     def refine_biography_to_500_words(self, extended_biography, input_text):
#         self.llm.temperature = 0.1
#         self.llm.max_tokens = 512
#         self.llm.top_k = 1

#         prompt = f"""
# Hier ist der erste Teil der Biografie: {extended_biography}
#         Nun sehen Sie sich die Daten erneut an und ergänzen Sie die Biografie um die fehlenden Informationen.
#                 """
        
#         chunks = divide_into_chunks(input_text, max_words_per_chunk=70000)
#         refined_parts = []

#         for chunk in chunks:
#             full_input = chunk + prompt
#             output_summary = self.invoke_with_retry(full_input)
#             refined_parts.append(output_summary.strip())

#         full_refined_biography = " ".join(refined_parts)
#         return self.remove_incomplete_sentence(full_refined_biography)

#     def remove_incomplete_sentence(self, biography):
#         words = word_tokenize(biography)
#         if len(words) <= 500:
#             return biography
        
#         truncated_words = words[:500]
#         truncated_text = " ".join(truncated_words)
#         last_full_stop_index = truncated_text.rfind('.')
        
#         if last_full_stop_index != -1:
#             return truncated_text[:last_full_stop_index + 1]
#         else:
#             return truncated_text

# # Function to save text to PDF
# def save_text_to_pdf(text, pdf_path):
#     pdf = FPDF()
#     pdf.set_auto_page_break(auto=True, margin=15)
#     pdf.add_page()
#     pdf.set_font("Arial", size=12)
    
#     # Add text to the PDF
#     for line in text.split('\n'):
#         pdf.multi_cell(0, 10, line)
    
#     # Save the PDF
#     pdf.output(pdf_path)

# # Function to process the files
# def process_file_and_update_status(file_name):
#     file_path = os.path.join(directory_path, file_name)
#     df = read_csv(file_path)
    
#     if df is not None:
#         summarizer = Summarizer()
#         sprecher_prefix = 'IP_'
#         transkript_list = extract_rows_with_sprecher(df, sprecher_prefix)
#         transcript_data = transkript_to_string(transkript_list)

#         socketio.emit('update', {'file': file_name, 'status': 'Processing'})
        
#         # Step 1: Generate the initial biography with chunking
#         initial_biography = summarizer.generate_biography(transcript_data)
        
#         # Step 2: Extend the biography with additional details, also using chunking
#         extended_biography = summarizer.extend_biography(initial_biography, transcript_data)
        
#         # Step 3: Refine the biography to 500 words and remove incomplete sentences
#         refined_biography = summarizer.refine_biography_to_500_words(extended_biography, transcript_data)
        
#         # Save the refined biography as a PDF
#         output_pdf_path = os.path.join(output_directory, file_name.replace('.csv', '.pdf'))
#         save_text_to_pdf(refined_biography.strip(), output_pdf_path)

#         socketio.emit('update', {'file': file_name, 'status': 'Completed'})
        
#     else:
#         socketio.emit('update', {'file': file_name, 'status': 'Failed'}, broadcast=True)

# # Flask route to display and run the process
# @app.route('/', methods=['GET', 'POST'])
# def home():
#     # Initialize an empty status_dict to be used in the template
#     status_dict = {}

#     if request.method == 'POST':
#         # Start the file processing in separate threads
#         for file_name in os.listdir(directory_path):
#             if file_name.endswith('.csv'):
#                 # Initialize status as "Waiting"
#                 status_dict[file_name] = "Waiting"
#                 # Start the processing in a new thread
#                 thread = threading.Thread(target=process_file_and_update_status, args=(file_name,))
#                 thread.start()

#     return render_template('index.html', status_dict=status_dict)

# if __name__ == "__main__":
#     socketio.run(app, debug=True)


from flask import Flask, render_template, request, redirect, url_for, send_file, flash
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

nltk.download('punkt')

app = Flask(__name__)
socketio = SocketIO(app)
app.secret_key="126022cbbf2d4e73287470a6cafe29a87a3423b0c0511c2a68c9da83f16f2665"

# Directory path for processing
directory_path = "C:/Users/asha4/OneDrive - SRH/Case Study-1/Dennis- Files/WG_ [EXTERN]  Transcripts and Biographies/"
output_directory = os.path.join(directory_path, "output_pdfs")

# Ensure output directory exists
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Function to read CSV
def read_csv(file_path):
    try:
        df = pd.read_csv(file_path, sep='\t')
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

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
        Du bist ein deutsches Textzusammenfassungsmodell. Erstellen Sie eine prägnante Zusammenfassung des obigen Textes in deutscher Sprache innerhalb von 500 Wörtern. Konzentrieren Sie sich auf die wichtigsten Punkte und bewahren Sie Klarheit. Work only with the data given and do not provide your conclusions or interpretations of the biography or the data provided. Work only with the data.
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
        Nun sehen Sie sich die Daten erneut an und ergänzen Sie die Biografie um die fehlenden Informationen.
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
        self.llm.max_tokens = 512
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


def remove_incomplete_sentences(biography):
    last_full_stop_index = biography.rfind('.')
    
    if last_full_stop_index != -1:
        return biography[:last_full_stop_index + 1]
    else:
        return biography



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
def process_file_and_update_status(file_name):
    file_path = os.path.join(directory_path, file_name)
    df = read_csv(file_path)
    
    if df is not None:
        summarizer = Summarizer()
        sprecher_prefix = 'IP_'
        transkript_list = extract_rows_with_sprecher(df, sprecher_prefix)
        transcript_data = transkript_to_string(transkript_list)

        socketio.emit('update', {'file': file_name, 'status': 'Processing'})
        
        # Step 1: Generate the initial biography with chunking
        initial_biography = summarizer.generate_biography(transcript_data)
        
        # Step 2: Extend the biography with additional details, also using chunking
        extended_biography = summarizer.extend_biography(initial_biography, transcript_data)
        
        # Step 3: Refine the biography to 500 words and remove incomplete sentences
        refined_biography = summarizer.refine_biography_to_500_words(extended_biography, transcript_data)
        incomplete_sent_removal =remove_incomplete_sentences(refined_biography)
        # Save the refined biography as a PDF
        output_pdf_path = os.path.join(output_directory, file_name.replace('.csv', '.pdf'))

        save_text_to_pdf(incomplete_sent_removal.strip(), output_pdf_path)

        socketio.emit('update', {'file': file_name, 'status': 'Completed'})
        
    else:
        socketio.emit('update', {'file': file_name, 'status': 'Failed'}, broadcast=True)

# Flask route to display and run the process
@app.route('/', methods=['GET', 'POST'])
def home():
    # Initialize an empty status_dict to be used in the template
    status_dict = {}

    if request.method == 'POST':
        # Start the file processing in separate threads
        for file_name in os.listdir(directory_path):
            if file_name.endswith('.csv'):
                # Initialize status as "Waiting"
                status_dict[file_name] = "Waiting"
                # Start the processing in a new thread
                thread = threading.Thread(target=process_file_and_update_status, args=(file_name,))
                thread.start()

    return render_template('index.html', status_dict=status_dict)

if __name__ == "__main__":
    socketio.run(app, debug=True)
