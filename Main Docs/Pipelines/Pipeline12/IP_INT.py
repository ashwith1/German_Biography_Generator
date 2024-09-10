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
            together_api_key="ce2345c478268c88d8952d1324945d1f5f766bb43ccb0733c954ccebc10c32f3"
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
        self.llm.max_tokens = 2048
        self.llm.top_k = 1
        
#         prompt = """ 
        
#         Ich möchte, dass Sie eine detaillierte Biografie eines Interviewpartners auf der Grundlage der folgenden strukturierten Fragen in deutscher Sprache erstellen. Bitte stellen Sie sicher, dass die Biografie präzise und sachlich ist und einer streng chronologischen Reihenfolge folgt. Vermeiden Sie persönliche Erkenntnisse, Emotionen oder Überlegungen, sofern diese nicht ausdrücklich in den Daten enthalten sind. Der Fokus sollte auf bestimmten Lebensereignissen liegen, mit klaren Daten und sachlichen Informationen. Die Biografie sollte narrative Ausschmückungen und subjektive Details vermeiden und sich strikt an den sachlichen und geradlinigen Stil einer formellen Biografie halten. Gehen Sie auf jeden Abschnitt spezifisch und klar ein und vermeiden Sie Verallgemeinerungen.

# Wichtige Richtlinien:

# Detaillitätsgrad:

# Die Biografie sollte sich auf bestimmte Lebensereignisse konzentrieren. Geben Sie beispielsweise genaue Daten, Orte und Rollen im Zusammenhang mit wichtigen Lebensereignissen an.
# Vermeiden Sie narrative Ausschmückungen oder subjektive Überlegungen darüber, wie Ereignisse das Leben des Interviewpartners beeinflusst haben könnten. Präsentieren Sie stattdessen sachliche Informationen über das Ereignis selbst.
# Ton und Stil:

# Verwenden Sie einen geradlinigen und sachlichen Ton, ähnlich einer formellen Biografie. Verzichten Sie auf persönliche Kontexte, emotionale Beschreibungen oder subjektive Sprache.
# Das Ergebnis sollte einem historischen Bericht ähneln, sich ausschließlich auf Fakten konzentrieren und Elemente im Memoirenstil vermeiden.
# Chronologie und Struktur:

# Befolgen Sie für jede Lebensphase eine strikte chronologische Reihenfolge mit klaren Markierungen für wichtige Lebensereignisse wie Schulzeit, berufliche Meilensteine ​​und Familienereignisse.
# Kombinieren oder verändern Sie die Abfolge der Ereignisse nicht. Jedes Ereignis sollte in der Reihenfolge dargestellt werden, in der es aufgetreten ist, ohne dass sich narrative Elemente überschneiden oder der Fluss verändert wird.
# Genauigkeit der Fakten:

# Geben Sie genaue Details zu Rollen, Jobs, Organisationen und wichtigen Meilensteinen an. Wenn der Interviewte beispielsweise für eine bestimmte Organisation gearbeitet hat (z. B. „Winterhilfswerk der NSV“ oder „Reicharbeitsdienst in Mühlheim“), erwähnen Sie die genaue Rolle, Daten und Details der Position.
# Vermeiden Sie es, Erfahrungen zu verallgemeinern. Wenn ein bestimmtes Lebensereignis oder eine bestimmte Rolle erwähnt wird, stellen Sie sicher, dass die Biografie die genaue Art der Erfahrung mit relevanten sachlichen Details widerspiegelt.
# Kurzfassung der Biografie:

# Geburt und frühes Familienleben:

# Wann und wo wurde der Interviewte geboren? Geben Sie das genaue Geburtsdatum und den Geburtsort an.
# Wer sind die Eltern des Interviewten? Geben Sie deren Namen, Berufe und relevante sachliche Details zu ihrem Leben an.
# Hat der Interviewte Geschwister? Wenn ja, geben Sie Details zu ihren Namen, Beziehungen und Lebenswegen an.
# Ausbildung:

# Welche Schule oder Schulen hat der Interviewte besucht? Geben Sie die genauen Namen der Einrichtungen, ihre Standorte und die besuchten Jahre an.
# Gab es während der Ausbildung bemerkenswerte Erfolge oder bedeutende Ereignisse? Listen Sie spezifische akademische Meilensteine ​​oder Auszeichnungen auf und vermeiden Sie subjektive Kommentare.
# Karriere und Berufsleben:

# Für welchen Beruf hat der Interviewte eine Ausbildung gemacht? Beschreiben Sie die Art seiner beruflichen Ausbildung und wo er seine Ausbildung erhalten hat (bestimmte Einrichtungen oder Programme).
# Welche Jobs oder Berufe hat der Interviewte ausgeübt? Geben Sie Details zu bestimmten Rollen, den Unternehmen oder Organisationen, für die er gearbeitet hat, und allen bemerkenswerten Erfolgen oder Meilensteinen an. Geben Sie nach Möglichkeit genaue Titel und Daten an.
# Lebensereignisse und persönliche Meilensteine:

# Welche bedeutenden Lebensereignisse ereigneten sich in der Kindheit des Interviewten? Stellen Sie diese Ereignisse sachlich dar, mit konkreten Daten und Orten.
# Was waren die wichtigsten Lebensereignisse während der Adoleszenz? Beschreiben Sie, wie diese das zukünftige Leben des Interviewten geprägt haben, ohne subjektive Überlegungen oder Interpretationen hinzuzufügen.
# Was waren die bedeutenden Ereignisse im frühen Erwachsenenalter? Nennen Sie wichtige Erfolge oder Übergänge und konzentrieren Sie sich dabei auf bestimmte, sachliche Meilensteine.
# Was waren die wichtigsten Lebensereignisse im Erwachsenenalter? Konzentrieren Sie sich auf Ereignisse, die ihr Berufs- oder Privatleben geprägt haben, und stellen Sie sie klar und sachlich präzise dar.
# Welche wichtigen Lebensereignisse ereigneten sich im späten Erwachsenenalter? Geben Sie Einzelheiten zu wichtigen Veränderungen oder Erfolgen in dieser Zeit an, ohne emotionale Kommentare.
# Privatleben:

# Hat der Interviewte geheiratet? Wenn ja, geben Sie den Namen des Ehepartners, das Datum der Heirat und alle relevanten Einzelheiten über den Ehepartner und ihre Beziehung an.
# Hat der Interviewte Kinder? Wenn ja, listen Sie die Namen ihrer Kinder und alle wichtigen Meilensteine ​​oder Lebensereignisse auf, die sie betreffen, und konzentrieren Sie sich dabei auf bestimmte Fakten.
# Bedeutende Lebensereignisse:

# Welche sind die bedeutendsten Lebensereignisse, die das Leben des Interviewten insgesamt geprägt haben? Fassen Sie diese Ereignisse sachlich zusammen und konzentrieren Sie sich dabei auf ihre Auswirkungen auf die Karriere, Beziehungen oder persönliche Entwicklung des Interviewpartners, vermeiden Sie jedoch subjektive oder emotionale Sprache.
# Wichtige Hinweise:

# Halten Sie sich an ein klares, prägnantes Format und stellen Sie sicher, dass die Biografie leicht verständlich ist und subjektive Interpretationen vermieden werden.
# Stellen Sie die sachliche Genauigkeit sicher, indem Sie konkrete Daten, Namen und Orte verwenden.
# Vermeiden Sie das Hinzufügen eines Erzählflusses, der von der strengen chronologischen Reihenfolge und dem sachlichen Ton abweicht.
# Fügen Sie keine persönlichen Überlegungen, Meinungen oder Kommentare ein. Bewegungsausgestaltungen, sofern sie nicht direkt in den Quelldaten vorgesehen sind.

#          """

        prompt = """
        
                I would like you to generate a detailed 500 word complete biography of an interviewee based on the following structured questions in German language. Please address each question thoroughly, ensuring that the narrative flows smoothly from one life stage to the next. The biography should include the following information:

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

What were the formative or significant life events in the interviewee's childhood? Mention dates, Include any experiences that had a lasting impact.
What were the formative or significant life events during the interviewee's adolescence?  Mention dates, Describe how these events influenced their path in life.
What were the formative or significant life events in the interviewee's early adult years? Include details about any dates, transitions, challenges, or accomplishments during this period.
What were the formative or significant life events during the interviewee's adult years?  Mention dates, Describe key experiences that shaped their personal or professional life.
What were the formative or significant life events in the interviewee's late adult years? Highlight any dates, major changes, achievements, or reflections during this time.
Personal Life:

Did the interviewee marry? If yes, provide details about their spouse,dates, including the name and any significant information about their relationship.
Does the interviewee have children? If so, provide details about their children, dates, including names and any significant life events related to them.
Significant Life Events:

What are the most significant life events that have shaped the interviewee's life overall? Reflect on how these events impacted their personal growth, relationships, or career, dates.
Please ensure the biography is coherent, chronological, detailed, and presents a well-rounded view of the interviewee's life journey.

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

    def refine_biography_to_500_words(self, initial_biography, input_text):
        self.llm.temperature = 0.1
        self.llm.max_tokens = 600
        self.llm.top_k = 1

        prompt = f"""
        Hier ist der erste Teil der Biografie: {initial_biography}
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
        
        # Added to handle both 'IP_' and 'INT_' prefixes
        transkript_list_ip = extract_rows_with_sprecher(df, 'IP_')  # Process rows with 'IP_' prefix
        transkript_list_int = extract_rows_with_sprecher(df, 'INT_')  # Process rows with 'INT_' prefix
        
        # Combine both transcript lists into one
        combined_transkript_list = transkript_list_ip + transkript_list_int
        transcript_data = transkript_to_string(combined_transkript_list)  # Convert combined list to string
        
        socketio.emit('update', {'file': os.path.basename(file_path), 'status': 'Processing'})

        initial_biography = summarizer.generate_biography(transcript_data)
        print(initial_biography)
        
        # extended_biography = summarizer.extend_biography(initial_biography, transcript_data)
        # print(extended_biography)
        refined_biography = summarizer.refine_biography_to_500_words(initial_biography, transcript_data)
        print(refined_biography)
        # incomplete_sent_removal = remove_incomplete_sentences(refined_biography)
        # print(incomplete_sent_removal)
        
        doc_io = save_text_to_docx(refined_biography)
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
