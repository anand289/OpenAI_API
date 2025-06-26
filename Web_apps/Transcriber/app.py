from flask import Flask, render_template, request, session, redirect, url_for
from flask_wtf import FlaskForm
from openai import OpenAI

import os

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
    
    if 'file' not in request.files:
        return render_template('transcriber.html', message='No file found')

    file = request.files['file']

    if file.filename == '':
        return render_template('transcriber.html', message='No selected file')

    if file:
        # Save the uploaded file to a desired location
        file.save('uploads/' + file.filename)
        audio_file_path = 'uploads/' + file.filename

        with open(audio_file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(model="whisper-1",file=audio_file)
            transcript_text = transcript.text
            # Call GPT to summarize the text
            summary_response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Or "gpt-4" if needed
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes meeting or speech transcriptions."},
                    {"role": "user", "content": f"Please summarize the following transcription:\n\n{transcript_text}"}
                ],
                temperature=0.5
            )
            summary_text = summary_response.choices[0].message.content
        return render_template('transcriber.html', message=transcript_text, summary=summary_text, filename=file.filename)

if __name__ == '__main__':
    app.run(debug=True,port=5004)