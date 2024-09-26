import pandas as pd
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from langchain_together import Together
import time
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import os
import time
from docx import Document

nltk.download('punkt')

# Function to extract rows from a DataFrame where 'Sprecher' column starts with the specified prefix.
def extract_rows_with_sprecher(df, sprecher_prefix):
    df = df.dropna(subset=['Sprecher'])
    filtered_rows = df[df['Sprecher'].str.startswith(sprecher_prefix)]
    transkript_list = filtered_rows['Transkript'].tolist()
    return transkript_list

# Function to convert the 'Transkript' column to a single string.
def transkript_to_string(transkript_list):
    return "\n".join(transkript_list)

# Function to divide text into chunks close to a specified maximum number of words without cutting through sentences.
def divide_into_chunks(text, max_words_per_chunk):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_word_count = 0

    for sentence in sentences:
        words_in_sentence = len(sentence.split())
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
            max_tokens= 300,
            top_k=1,
            together_api_key="809750d4770635c394317b2afb1baefa7173070c968384d8ed26c9a0a1e72a10"
        )
       
       self.llm2 = Together(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            temperature=0.1,
            max_tokens= 512,
            top_k=1,
            together_api_key="809750d4770635c394317b2afb1baefa7173070c968384d8ed26c9a0a1e72a10"
        )
       
       self.llm1 = Together(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            temperature=0.1,
            max_tokens= 300,
            top_k=1,
            together_api_key="809750d4770635c394317b2afb1baefa7173070c968384d8ed26c9a0a1e72a10"
        )
    #89f6359c5009e4d13ca731bb9085bf686123aa816e64ede39a6b295143c086c3
    #104dd97ba7c157e74fd5bda4afcad7774ff340adeb30773c3c0a7639e4fae45e
    #126022cbbf2d4e73287470a6cafe29a87a3423b0c0511c2a68c9da83f16f2665   
    def generate_biography(self, input_text):

            prompt = """
    Du bist ein deutsches Textzusammenfassungsmodell. Erstellen Sie eine prägnante Zusammenfassung des obigen Textes in deutscher Sprache innerhalb von 500 Wörtern. Konzentrieren Sie sich auf die wichtigsten Punkte und bewahren Sie Klarheit.
                    """

            full_input = input_text + prompt

            retry_delay = 30  # Delay in seconds

            while True:
                try:
                    # Invoke the LLM model to generate the biography
                    output_summary = self.llm.invoke(full_input)
                    return output_summary

                except Exception as e:
                    if "rate limited" in str(e).lower():
                        print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        print(f"An error occurred: {e}")
                        raise

    def final_biography(self, input_text):

            prompt1 = """
            Bitte erstellen Sie eine Biografie auf Basis des untenstehenden Textes in deutscher Sprache mit maximal 500 Wörtern. Nehmen Sie keine eigenständigen Ergänzungen vor und achten Sie auf Professionalität.
            """

            full_input = input_text + prompt1

            retry_delay = 30  # Delay in seconds

            while True:
                try:
                    # Invoke the LLM model to generate the biography
                    output_summary = self.llm1.invoke(full_input)
                    return output_summary

                except Exception as e:
                    if "rate limited" in str(e).lower():
                        print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        print(f"An error occurred: {e}")
                        raise

    def refine_biography(self, input_text):
            """
            Refines the biography to be close to 500 words, makes sure of sentence completeness
            and natural flow.
            """
            def truncate_to_word_limit(text, limit):
                words = word_tokenize(text)
                if len(words) > limit:
                    words = words[:limit]
                return ' '.join(words)

            words = word_tokenize(input_text)
            
            # If the input is already under or at 500 words, return as is
            if len(words) <= 500:
                return input_text

            # Tokenize the text into sentences
            sentences = sent_tokenize(input_text)
            refined_text = ""
            current_word_count = 0
            
            for sentence in sentences:
                sentence_word_count = len(word_tokenize(sentence))
                if current_word_count + sentence_word_count <= 500:
                    refined_text += sentence + " "
                    current_word_count += sentence_word_count
                else:
                    # If adding this sentence exceeds the word limit, break
                    break

            # Ensuring the final text is close to 500 words
            refined_text = refined_text.strip()
            refined_text = truncate_to_word_limit(refined_text, 500)

            return refined_text
    def final_2_biography(self, input_text):
        prompt = """
        Du bist ein deutsches Textzusammenfassungsmodell. Erstellen Sie eine prägnante Zusammenfassung des oben genannten Textes auf Deutsch innerhalb von 500 Wörtern und behalten Sie alle wichtigen Daten bei. Konzentrieren Sie sich auf die wichtigsten Punkte und bewahren Sie Klarheit.
        """
        # Erstellen Sie eine professionelle Biografie, indem Sie sich auf den Sprecher mit allen Daten und Ereignissen im Zusammenhang mit diesen Daten konzentrieren, in deutscher Sprache von maximal 500 Wörtern, indem Sie den untenstehenden Text verwenden, strukturelle Fehler korrigieren und Wiederholungen oder überflüssige Informationen entfernen, ohne eigenständige Ergänzungen vorzunehmen, um alle wichtigen Dinge beizubehalten."""
            #Sie sind ein deutsches Textbiografie-Generatormodell. Erstellen Sie eine kleine, prägnante Biografie des obigen Textes auf Deutsch. Konzentrieren Sie sich auf die wichtigsten Punkte und bewahren Sie Klarheit."""
        # You are a professional biography writer. 
        # Extract the important dates and events assiciated with it and create a concise biography in german and don't add anything extra other than which is present in  the above text.The biography should be no longer than 500 words.
    

        full_input = input_text + prompt

        retry_delay = 30  # Delay in seconds

        while True:
            try:
                # Invoke the LLM model to generate the biography
                output_summary = self.llm2.invoke(full_input)
                return output_summary

            except Exception as e:
                if "rate limited" in str(e).lower():
                    print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"An error occurred: {e}")
                    raise

# Function to generate a biography from text chunks.
def generate_biography(summarizer, input_text):
    chunks=divide_into_chunks(input_text,1000) 
    summary=""
    chunk_number = 1  # Initialize a counter for chunk numbering

    for chunk in chunks:
        print(f"Chunk {chunk_number}:")
        print(chunk)  # Print the chunk to observe its content
        summary += summarizer.generate_biography(chunk) + "\n"
        chunk_number += 1  # Increment the chunk number for the next iteration
        # input_text = summary
    return summary

# Function to save the final biography to a PDF file.
# def save_biography_to_pdf(text, filename_prefix="biography"):
#     try:
#         filename = f"{filename_prefix}.pdf"
#         c = canvas.Canvas(filename, pagesize=A4)
#         text = text.split('\n')
#         text = [line.strip() for line in text if line.strip() != '']
#         width, height = A4
#         left_margin = 72
#         right_margin = width - 72
#         y = height - 72
#         max_width = right_margin - left_margin
        
#         for line in text:
#             wrapped_lines = simpleSplit(line, "Helvetica", 12, max_width)
#             for wrapped_line in wrapped_lines:
#                 c.drawString(left_margin, y, wrapped_line)
#                 y -= 15
#                 if y < 72:
#                     c.showPage()
#                     y = height - 72
        
#         c.save()
#         print(f"Biography saved to {filename}")
#         return filename
#     except Exception as e:
#         print(f"An error occurred while saving the PDF: {e}")
#         return None

# Function to read data from a CSV file.
def read_csv(file_path):
    try:
        df = pd.read_csv(file_path, sep='\t')
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

# Function to read data from a DOCX file.
def read_docx(file_path):
    try:
        doc = Document(file_path)
        data = [p.text for p in doc.paragraphs if p.text]
        return " ".join(data)
    except Exception as e:
        print(f"Error reading DOCX file: {e}")
        return None

def final_biography(summarizer, input_text):
    chunks = divide_into_chunks(input_text, 1000)
    summary = ""
    chunk_number = 1

    for chunk in chunks:
        # print(f"Chunk {chunk_number}:")
        # print(chunk)  # Print the current chunk to observe its content
        # print("\n")
        summary += summarizer.final_biography(chunk) + "\n"
        chunk_number += 1
    return summary

def count_words(sentence):
    # Split the sentence into words using space as a delimiter
    words = sentence.split()
    # print(words)
    # Count the number of words
    num_words = len(words)
    return num_words

def final_2_biography(Summarizer, input_text):
    chunks=divide_into_chunks(input_text,1000) 
    summary=""
    chunk_number = 1  # Initialize a counter for chunk numbering

    for chunk in chunks:
        # print(f"Chunk {chunk_number}:")
        # print(chunk)  # Print the chunk to observe its content
        summary += Summarizer.final_2_biography(chunk) + "\n"
        chunk_number += 1  # Increment the chunk number for the next iteration
        # input_text = summary
    return summary

def remove_incomplete_sentence(biography):
    """
    Remove incomplete sentence at the end of the biography.
    """
    last_full_stop_index = biography.rfind('.')
    
    if last_full_stop_index != -1:
        return biography[:last_full_stop_index + 1]
    else:
        return biography
    
# Main function to process the input file and generate a biography.
def process_file(file_path):
    summarizer = Summarizer()
    
    if file_path.endswith('.csv'):
        df = read_csv(file_path)
        if df is not None:
            sprecher_prefix = 'IP_'
            transkript_list = extract_rows_with_sprecher(df, sprecher_prefix)
            transcript_data = transkript_to_string(transkript_list)
        else:
            print("Failed to read CSV file.")
            return
    elif file_path.endswith('.docx'):
        transcript_data = read_docx(file_path)
        if not transcript_data:
            print("Failed to read DOCX file.")
            return
    else:
        print("Unsupported file format.")
        return

    biography = generate_biography(summarizer, transcript_data)
    print("Biography : \n ", count_words(biography), biography.strip())

    x_biography = final_biography(summarizer, biography)
    summary = remove_incomplete_sentence(x_biography) 
    print("summary : \n ", count_words(summary), summary.strip())

    if count_words(summary) <= 600:
        refined_biography = summarizer.refine_biography(summary)
        print("Refined : \n", count_words(refined_biography), refined_biography.strip())
    else :
        x = remove_incomplete_sentence(summary) 
        x1_biography= final_2_biography(summarizer,x)
        summary1 = remove_incomplete_sentence(x1_biography) 
        print("Summary 1: ", count_words(summary1), summary1.strip())
    # filename = save_biography_to_pdf(refined_biography, "final_biography")

    # if filename:
    #     print(f"Biography saved to {filename}")
    # else:
    #     print("Failed to save biography to PDF.")


if __name__ == "__main__":
# Example usage
    file_path = "c:\\Users\\hsrak\\Desktop\\case_study\\Final\\adg0002_er_2024_04_23.csv"  # Change this to your CSV or DOCX file path
    process_file(file_path)
