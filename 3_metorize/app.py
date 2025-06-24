from flask import Flask, render_template, request, send_file
import openai
from pydub import AudioSegment
import numpy as npc
import wave
import os
from openai import OpenAI

from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

audio_data = None
sample_rate = 44100

os.environ['OPENAI_API_KEY'] = ""
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


def send_email(Subject, Body):
    load_dotenv()

    GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")  # e.g. "you@gmail.com"
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")  # your 16-char app password

    msg = EmailMessage()
    msg["Subject"] = Subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = "borowski.cacper@gmail.com"
    msg.set_content(Body)

@app.route('/send_email', methods=['POST'])
def send_email_route():
    subject = request.form.get('subject', 'Default Subject')
    body = request.form.get('body', 'Default Body')
    
    # Call your email function
    send_email(subject, body)



# Format the AI response for better readability
def format_insights(insights_text):
    sections = insights_text.split("**")  # Split by bold markers
    formatted = ""

    for section in sections:
        if section.strip().startswith("Summary of Mentorship Session"):
            formatted += f"<h2>{section.strip()}</h2>"
        elif section.strip().startswith("1. Main Agenda"):
            formatted += f"<h3>{section.strip()}</h3>"
        elif section.strip().startswith("2. Topics Covered"):
            formatted += f"<h3>{section.strip()}</h3>"
        elif section.strip().startswith("3. Key Insights & Advice"):
            formatted += f"<h3>{section.strip()}</h3>"
        elif section.strip().startswith("4. Action Items"):
            formatted += f"<h3>{section.strip()}</h3>"
        elif section.strip().startswith("-"):
            formatted += f"<ul><li>{section.strip()}</li></ul>"
        else:
            formatted += f"<p>{section.strip()}</p>"

    return formatted

@app.route('/transcriber', methods=['POST', 'GET'])
def transcriber():
    if 'file' not in request.files:
        return render_template('transcriber.html', message='Upload file')

    file = request.files['file']
    if file.filename == '':
        return render_template('transcriber.html', message='No file found')

    # Ensure the 'uploads/converted/' directory exists
    os.makedirs('uploads/converted/', exist_ok=True)

    # Save the uploaded file to a desired location
    file.save('uploads/' + file.filename)
    output_wav_file = f'uploads/converted/{file.filename}.wav'
    convert_audio_to_wav('uploads/' + file.filename, output_wav_file)

    # Check file size
    if os.path.getsize(output_wav_file) > 25 * 1024 * 1024:  # 25 MB limit
        return render_template('transcriber.html', message='File size exceeds 25 MB limit after conversion.')

    # Process the audio file
    with open(output_wav_file, 'rb') as audio_file:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)

    # Generate insights from the transcription
    transcription_text = transcript.text
    # Generate insights from the transcription
    insights_prompt = (
        f"You are an expert mentorship assistant. Given a transcript of a mentorship session, generate a professional, structured summary with the following sections:\n\n"
        f"1. Main Agenda\n"
        f"Briefly state the primary goal(s) or focus of the session based on the mentee’s needs (e.g. job search, interview prep, project feedback, or navigating a workplace issue).\n\n"
        f"2. Topics Covered\n"
        f"List key discussion areas, including topics that stemmed from the main agenda as well as any relevant tangents (e.g. mentor sharing personal experience or related stories).\n\n"
        f"3. Key Insights & Advice\n"
        f"Highlight practical insights, frameworks, or perspectives shared by the mentor that would be useful for the mentee to remember or apply.\n\n"
        f"4. Action Items\n"
        f"Generate clear, tangible next steps for the mentee, informed by the discussion. Focus on steps that align with the mentee’s goals and reflect advice given (e.g. practice questions, networking strategies, project ideas).\n\n"
        f"Tone: Clear, concise, and professional. Output should look like something you’d send as a post-session recap in a mentorship platform or dashboard.\n\n"
        f"The following is a transcription of the mentorship session:\n\n"
        f"{transcription_text}"
    )
    insights_response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Use "gpt-4" if needed
        messages=[
            {"role": "system", "content": "You are an assistant that extracts insights from transcriptions."},
            {"role": "user", "content": insights_prompt}
        ],
        max_tokens=500,
        temperature=0.7
    )

    # Access the generated content correctly
    insights_text = insights_response.choices[0].message.content.strip()

    # Format the insights before rendering
    formatted_insights = format_insights(insights_text)
    return render_template(
        'transcriber.html',
        message=transcription_text,
        insights=formatted_insights,
        filename=file.filename
    )


    # return render_template('transcriber.html', message=transcript.text, filename=file.filename)

def convert_audio_to_wav(input_audio_file, output_wav_file):
    # Load the audio file using pydub
    audio = AudioSegment.from_file(input_audio_file)

    # Compress the audio by reducing the sample rate and bitrate
    audio = audio.set_frame_rate(16000)  # Reduce sample rate to 16 kHz
    audio = audio.set_channels(1)       # Convert to mono
    audio.export(output_wav_file, format="wav", bitrate="64k") 

if __name__ == "__main__":
    app.run(debug=True, port=5006)
