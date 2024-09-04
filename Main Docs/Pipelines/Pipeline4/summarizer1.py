from utils import RateLimiter
from langchain_together import Together

class Summarizer:
    def __init__(self, rate_limiter):
        self.rate_limiter = rate_limiter

        self.llm = Together(
            model="meta-llama/Llama-3-8b-hf",
            temperature=0.1,
            max_tokens=1024,
            top_k=1,
            together_api_key="104dd97ba7c157e74fd5bda4afcad7774ff340adeb30773c3c0a7639e4fae45e"
        )


#104dd97ba7c157e74fd5bda4afcad7774ff340adeb30773c3c0a7639e4fae45e

    def generate_biography(self, input_text):
        prompt = """
    Schreiben Sie in einem Erzählstil, um die Biografie ansprechend zu gestalten. Skizzieren Sie die wichtigsten Ereignisse im Leben des Probanden chronologisch.
    Fügen Sie Zitate, Anekdoten und interessante Fakten hinzu, um dem Text mehr Tiefe zu verleihen.
    Stellen Sie das Thema vor und geben Sie einen kurzen Überblick über seine Bedeutung.
    Besprechen Sie den Hintergrund, die Familie und die prägenden Jahre des Themas.
    Heben Sie wichtige Erfolge und Beiträge hervor.
    Besprechen Sie alle Hindernisse oder Schwierigkeiten, mit denen die Person konfrontiert war, und wie sie diese überwunden haben.
    Geben Sie Einblicke in ihre Persönlichkeit, Beziehungen und Hobbys. Geben Sie die Wirkung des Subjekts an, was es am Ende getan hat und wie man sich heute an es erinnert."""
        #     Sie sind ein professioneller Biografieautor. Der angegebene Text enthält mehrere Interviewtranskripte. Erstellen Sie eine umfassende und detaillierte präzise Biografie auf Deutsch. Geben Sie spezifische biografische Details wie Geburtsdatum, familiären Hintergrund, Ausbildung, Berufserfahrung, Ehen und wichtige Lebensereignisse an. Stellen Sie sicher, dass die Biografie gut organisiert und klar strukturiert ist. Ordnen Sie die Biografie chronologisch an. Stellen Sie sicher, dass alle wichtigen Details enthalten sind und dass die Biografie eine klare und vollständige Darstellung des Lebenswegs bietet. Vermeiden Sie Redundanzen und Wiederholungen.
    #    """
        # You are a professional biography author. Write a biography of the above interview, which is in German language. Focus on key points and maintain clarity.
        # """
        full_input = input_text + prompt

        print("Sending to API:", full_input[:500])  # Debugging: print first 500 characters
        self.rate_limiter.wait()  # Ensure rate limiting

        output_summary = self.llm.invoke(full_input)
        return output_summary
    # 
    def improve_coherence(self, input_text):
        # prompt = """
        # You are a professional biography author inspector. Fix the structural errors in the above biography don't forget to mention the dates as it is in the original text, in a correct connected flow. Remove if there are any repeated statements or redundant information.
        # """

        prompt = """
        Sie sind ein professioneller Biografieautor. Korrigieren Sie die Strukturfehler in der folgenden Biografie. Stellen Sie sicher, dass das Datum wie im Originaltext erwähnt wird und dass der Text korrekt und kohärent in einem kontinuierlichen Fluss fließt. Entfernen Sie alle überflüssigen Informationen und stellen Sie sicher, dass die Biografie gut organisiert und klar strukturiert ist.
        Verbinden Sie alle Zeilen und erstellen Sie einen interaktiv lesbaren Absatz."""# from pandas import pd

        # input_text = pd.read_csv("C:\\Users\\hsrak\\Desktop\\case study\\adg0001_er_2024_04_23.csv")

        full_input = input_text + prompt
        output_summary = self.llm.invoke(full_input)
        # print(output_summary)
        return output_summary
    
    def para(self, input_text):
        # prompt = """
        # You are a professional biography author inspector. Fix the structural errors in the above biography don't forget to mention the dates as it is in the original text, in a correct connected flow. Remove if there are any repeated statements or redundant information.
        # """

        prompt = """
        Bitte fassen Sie die bereitgestellten Informationen in einem besser lesbaren Absatz zusammen.
        """# from pandas import pd

        # input_text = pd.read_csv("C:\\Users\\hsrak\\Desktop\\case study\\adg0001_er_2024_04_23.csv")

        full_input = input_text + prompt
        
        print("Sending to API:", full_input[:500])  # Debugging: print first 500 characters
        self.rate_limiter.wait()  # Ensure rate limiting

        output_summary = self.llm.invoke(full_input)
        # print(output_summary)
        return output_summary


