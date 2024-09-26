from langchain_together import Together

class Summarizer:
    def __init__(self):
        self.llm = Together(
            model="meta-llama/Llama-3-8b-hf",  
            temperature=0.1,
            max_tokens=1024,
            top_k=1,
            together_api_key="104dd97ba7c157e74fd5bda4afcad7774ff340adeb30773c3c0a7639e4fae45e"
        )

        
        # self.llm_model_A = Together(
        #     model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        #     temperature=0.1,
        #     max_tokens=2048,  # Adjust max_tokens to a lower value
        #     top_k=1,
        #     together_api_key="0b62aef01076ddb412af8164502a71f3f5fc60e13c3d478298cf3c3736fff474"
        # )
        
        # self.llm_model_B = Together(
        #     model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        #     temperature=0.1,
        #     max_tokens=2048,  # Adjust max_tokens to a lower value
        #     top_k=1,
        #     together_api_key="0b62aef01076ddb412af8164502a71f3f5fc60e13c3d478298cf3c3736fff474"
        # )

    # def generate_biography(self, input_text):
    #     prompt = """
    #     Sie sind ein professioneller Biografieautor. Schreiben Sie eine präzise und strukturierte Biografie basierend auf dem folgenden Text. Verwenden Sie klare, stichpunktartige Sätze und halten Sie sich an die chronologische Reihenfolge der Ereignisse. Geben Sie spezifische biografische Details wie Geburtsdatum, familiären Hintergrund, Ausbildung, Berufserfahrung, Ehen und wichtige Lebensereignisse an. Vermeiden Sie Redundanzen und Wiederholungen.
    #     """""
    #     full_input = input_text + prompt
    #     output_A = self.llm_model_A.invoke(full_input, max_tokens=2048)
    #     output_B = self.llm_model_B.invoke(full_input, max_tokens=2048)
        
    #     # Combine outputs A and B (example: sequential combination)
    #     output_summary = output_A + "\n\n" + output_B
        
    #     return output_summary    


    def generate_biography(self, input_text):
        prompt = f"""
        Bitte erstellen Sie eine rein textbasierte Biografie ohne Programmcode. Der Hauptfokus liegt auf: {input_text[:100]}...
        Erzählen Sie die Geschichte mit einem Schwerpunkt auf bedeutenden Lebensereignissen, persönlichen Einsichten und fügen Sie relevante Anekdoten hinzu, um die Biografie lebendiger zu gestalten.
        """
        full_input = prompt + input_text
        output_summary = self.llm.invoke(full_input)
        return output_summary