from flask import Flask, render_template, request, session, redirect, url_for
from flask_wtf import FlaskForm
from openai import OpenAI
from yt_dlp import YoutubeDL

import uuid
import glob
import os
import markdown
import re

os.environ['OPENAI_API_KEY'] = ""
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


app = Flask(__name__)
app.secret_key = 'tarun' # Replace with a secure password

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'tarun':  # Replace with a secure password
            session['authenticated'] = True
            return redirect(url_for('transcriber'))
        else:
            return render_template('login.html', error='Invalid password')

    return render_template('login.html')

@app.route('/transcriber', methods=['POST', 'GET'])
def transcriber():
    if not session.get('authenticated'):
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('transcriber.html')

    # --- Case 1: YouTube Link ---
    if 'youtube_url' in request.form:
        youtube_url = request.form['youtube_url']
        uid = uuid.uuid4().hex
        output_template = os.path.join('uploads', f'yt_audio_{uid}.%(ext)s')
        os.makedirs('uploads', exist_ok=True)

        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'postprocessor_args': ['-t', '200'], 
                'noplaylist': True,
                'quiet': True
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])

            # Find the resulting mp3 file
            matching_files = glob.glob(os.path.join('uploads', f'yt_audio_{uid}*.mp3'))
            if not matching_files:
                raise FileNotFoundError("Audio file was not created.")

            audio_path = matching_files[0]

            with open(audio_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)

            transcript_text = transcript.text

            summary_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional summarizer. "
                            "Given a transcript, break it down into structured sections using clear, relevant headings. "
                            "Each section should summarize the topic under that heading concisely and clearly. "
                            "Use markdown-style formatting for headings (e.g., '## Introduction')."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Summarize the following transcription:\n\n{transcript_text}"
                    }
                ],
                temperature=0.5
            )
            summary_text = summary_response.choices[0].message.content
            summary_html = markdown.markdown(summary_text)

            # Replace heading levels (e.g., h2 -> h6, h3 -> h6)
            summary_html = re.sub(r'<h[1-6]>', '<h6>', summary_html)
            summary_html = re.sub(r'</h[1-6]>', '</h6>', summary_html)

            return render_template('transcriber.html', message=transcript_text, summary=summary_html,active_tab='youtube')       

        except Exception as e:
            return render_template('transcriber.html', message=f"Error processing YouTube video: {str(e)}")

    # --- Case 2: File Upload (local or recorded) ---
    if 'file' not in request.files:
        return render_template('transcriber.html', message='No file found')

    file = request.files['file']
    if file.filename == '':
        return render_template('transcriber.html', message='No selected file', active_tab='upload')

    if file:
        os.makedirs('uploads', exist_ok=True)
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)

        with open(file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        transcript_text = transcript.text

        summary_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional summarizer. "
                            "Given a transcript, break it down into structured sections using clear, relevant headings. "
                            "Each section should summarize the topic under that heading concisely and clearly. "
                            "Use markdown-style formatting for headings (e.g., '## Introduction')."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Summarize the following transcription:\n\n{transcript_text}"
                    }
            ],
            temperature=0.5
        )
        summary_text = summary_response.choices[0].message.content
        summary_html = markdown.markdown(summary_text)

        # Replace heading levels (e.g., h2 -> h6, h3 -> h6)
        summary_html = re.sub(r'<h[1-6]>', '<h6>', summary_html)
        summary_html = re.sub(r'</h[1-6]>', '</h6>', summary_html)

        return render_template('transcriber.html', message=transcript_text, summary=summary_html, filename=file.filename,
                                active_tab='record' if file.filename.endswith('.webm') else 'upload')

if __name__ == '__main__':
    app.run(debug=True,port=5031)