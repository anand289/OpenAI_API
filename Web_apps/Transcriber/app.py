from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from openai import OpenAI

import os

os.environ['OPENAI_API_KEY'] = ""
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcriber', methods=['POST', 'GET'])
def transcriber():
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
        return render_template('transcriber.html', message=transcript.text, filename=file.filename)

if __name__ == '__main__':
    app.run(debug=True,port=5007)
