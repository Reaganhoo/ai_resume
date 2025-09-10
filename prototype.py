import gradio as gr
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import fitz  # PyMuPDF for PDF text extraction

# -------------------------------
# 1. Load model & tokenizer
# -------------------------------
model_name = "microsoft/phi-2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    dtype=torch.float16
)

# -------------------------------
# 2. Hardcoded knowledge base
# -------------------------------
with open("knowledge_base.txt", "r", encoding="utf-8") as f:
    knowledge_base = f.read()

# Example job list (you can expand this later)
job_options = [
    "Mechanical Engineer",
    "Mechatronics Engineer",
    "AI Engineer",
    "Software Engineer",
    "Embedded Systems Engineer",
    "Suggest Suitable Jobs (AI decides)"
]

# -------------------------------
# 3. Resume analysis function
# -------------------------------
def analyze_resume(resume_file, selected_job):
    # Extract text from PDF
    doc = fitz.open(resume_file)
    resume_text = "".join([page.get_text() for page in doc])

    # Build prompt
    if selected_job == "Suggest Suitable Jobs (AI decides)":
        prompt = f"""
You are a career advisor.

Knowledge base:
{knowledge_base}

Candidate resume:
{resume_text}

Task:
1. Suggest the top 2–3 job roles in engineering that best match this resume.
2. For each suggested role, explain why it is a good fit.
3. List missing skills the candidate should improve to be competitive.
Answer only in clear bullet points.

"""
    else:
        prompt = f"""
You are a resume screening assistant.

Knowledge base:
{knowledge_base}

Candidate resume:
{resume_text}

Task:
1. Compare the resume with the job requirements for: {selected_job}.
2. List the strengths that match the job role.
3. List the missing or weak skills for this role.
4. Give clear improvement suggestions.
Provide the result in a structured format (Strengths, Weaknesses, Improvements).
Do NOT repeat the knowledge base or the resume in your answer.

"""

    # Run model
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=512)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    # --- Post-processing to clean output ---
    # Keep only from "Strengths:" onwards (if found)
    for marker in ["Strengths:"]: #, "strengths:"
        if marker in result:
            result = result.split(marker, 1)[1]
            result = marker + result  # add marker back
            break

    return result


# -------------------------------
# 4. Gradio UI
# -------------------------------
with gr.Blocks() as demo:
    gr.Markdown("## 📄 AI Resume Analyzer (Malaysia Engineering Jobs)")

    with gr.Row():
        resume_input = gr.File(label="Upload Resume (PDF)", type="filepath")
        job_input = gr.Dropdown(
            choices=job_options,
            value="Mechanical Engineer",
            label="Select Job Role"
        )

    analyze_button = gr.Button("🔍 Analyze Resume")
    output_box = gr.Textbox(label="Solution", lines=20)

    analyze_button.click(
        fn=analyze_resume,
        inputs=[resume_input, job_input],
        outputs=output_box
    )

demo.launch()
