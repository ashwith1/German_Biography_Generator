from langchain_together import Together

class Summarizer:
    def __init__(self):
        self.llm = Together(
            model = "Meta-Llama-3-70B-Instruct",
            #model = "mistralai/Mistral-7B-Instruct-v0.2",
            #model= "mistralai/Mixtral-8x7B-Instruct-v0.1",
            # model = "snorkelai/Snorkel-Mistral-PairRM-DPO",
            temperature=0.6,
            max_tokens=2048,
            top_k=1,
            together_api_key="0b62aef01076ddb412af8164502a71f3f5fc60e13c3d478298cf3c3736fff474"
        )


    def generate_summary(self, input_text):
        prompt = """
       You are a German text Generator model. Generate a concise summary of the above text, including specific biographical details such as birth date, family background, education, work experience, marriages, and significant life events. Maintain clarity and focus on key points.
        """
        # prompt = """
        # Du bist ein deutsches Textzusammenfassungsmodell. Erstellen Sie eine prägnante Zusammenfassung des obigen Textes in deutscher Sprache. Konzentrieren Sie sich auf die wichtigsten Punkte und bewahren Sie Klarheit.
        # # """
        full_input = input_text + prompt
        output_summary = self.llm.invoke(full_input)
        return output_summary
    

    def generate_biography(self, input_text):
        # prompt = """
        # Sie sind ein professioneller Biografieautor. Schreiben Sie eine Biografie der obigen Interviewzusammenfassung in deutscher Sprache. Konzentrieren Sie sich auf spezifische biografische Details wie Geburtsdatum, familiären Hintergrund, Bildung, Berufserfahrung, Ehen und wichtige Lebensereignisse. Bewahren Sie Klarheit und konzentrieren Sie sich auf die wichtigsten Punkte.
        # # """
        prompt ="""
Sie sind ein professioneller Biografieautor. Schreiben Sie eine Biografie der obigen Interviewzusammenfassung. Konzentrieren Sie sich auf spezifische biografische Details wie Geburtsdatum, familiären Hintergrund, Bildung, Berufserfahrung, Ehen und wichtige Lebensereignisse. Stellen Sie sicher, dass die Biografie klar strukturiert und auf die wichtigsten Punkte fokussiert ist.

Biografische Daten:
- Geboren am 29.05.1925 in Hemer, Sauerland...
[Rest of biographical data structured similarly]

Bitte bewahren Sie Klarheit und folgen Sie einem strukturierten Format.
       """
        # You are a professional biography author. Write a biography of the above interview, which is in German language. Focus on key points and maintain clarity.
        # """
        full_input = input_text + prompt
        output_summary = self.llm.invoke(full_input)
        return output_summary


    def improve_coherence(self, input_text):
        prompt = """
        You are a professional biography author. Fix the structural errors in the above biography and reproduce it in German language. Remove if there are any repeated statements or redundant information.
        """

        # prompt = """
        # As a professional biography author, your task is to refine the provided biography. 
        # Remove any repeated statements or redundant information to maintain conciseness and clarity. 
        # Make sure to produce the revised biography in German language.
        # """
        # from pandas import pd

        # input_text = pd.read_csv("C:\\Users\\hsrak\\Desktop\\case study\\adg0001_er_2024_04_23.csv")

        full_input = input_text + prompt
        output_summary = self.llm.invoke(full_input)
        return output_summary
