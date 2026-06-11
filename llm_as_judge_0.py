from dotenv import load_dotenv
from openai import OpenAI
import csv

load_dotenv('.env')
llm = OpenAI()

def eval_assumed_product(trace):
    response = llm.responses.create(
        model="gpt-4.1",
        temperature=0,
        input=f"""<overview>You are an LLM judge that evaluates the output of another LLM 
        called the "troubleshooter". The troubleshooter is a chatbot assistant that advises human users about
        software from a company called GROSS. The products are: 
            * Flamehamster, a web browser.
            * Rumblechirp, an email client.
            * GuineaPigment, a drawing tool for creating/editing SVGs
            * EMRgency, an electronic medical record system
            * Verbiage++, a content management system.
            
        The troubleshooter helps troubleshoot user issues with these software products.
        Now, sometimes, it may not be clear from the user input which product they're
        discussing. When this happens, the chatbot should ask a clarifying question to
        help figure out which product the user is referring to.</overview>

        <instructions>
        You are to inspect a conversation between the troubleshooter LLM and the human
        user and output a judgment of either "PASS" or "FAIL"
        
        * Render FAIL if the troubleshooter gives advice
        before the user explicitly mentions which product the user is discussing.
        * Render PASS otherwise.
        </instructions>
        
        Okay, we're ready to begin. Here is a conversation; determine whether it's PASS or FAIL:

        <conversation>{trace}</conversation>
        """
    )

    return response.output_text


def run_evals(traces_file):
    fails = []
    num_passes = 0
    trace_number = 0

    with open(traces_file, encoding="utf-8") as f:
        for line in f:
            trace = line.strip()
            llm_judgment = eval_assumed_product(trace)

            trace_number += 1
            if llm_judgment == "PASS":
                print(f"{trace_number}: PASS")
                num_passes += 1
            else:
                print(f"{trace_number}: FAIL")
                fails.append({"trace_number": trace_number, "trace": trace})

    print(fails)
    
    accuracy = num_passes / trace_number if trace_number else 0.0
    print(f"Traces: {trace_number}")
    print(f"Passes: {num_passes}")
    print(f"Fails: {len(fails)}")
    print(f"Accuracy: {accuracy:.0%}")


run_evals("production_traces.csv") # uncomment to run evals on production

# Alignment
def evaluate_eval(traces_file):
    tp = tn = fp = fn = 0

    with open(traces_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        
        for i, row in enumerate(reader):
            llm_judgment = eval_assumed_product(row[0])
            human_judgment = row[1]
            print(f"{i + 1}: human: {human_judgment} | llm: {llm_judgment}")
            if human_judgment == "PASS":
                if llm_judgment == "PASS":
                    tp += 1
                else:
                    fn += 1
            elif human_judgment == "FAIL":
                if llm_judgment == "FAIL":
                    tn += 1
                else:
                    fp += 1

    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    tnr = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    print(f"TPR: {tpr:.0%}, TNR: {tnr:.0%}")

# evaluate_eval("labeled_traces.csv") # uncomment to evaluate our llm-as-judge eval