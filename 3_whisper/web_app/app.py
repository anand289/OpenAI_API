from flask import Flask, render_template, request
import openai
import os
os.environ['OPENAI_API_KEY']= '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'
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return render_template('index.html', message='No file part')

    file = request.files['file']

    if file.filename == '':
        return render_template('index.html', message='No selected file')

    if file:
        # Save the uploaded file to a desired location
        file.save('uploads/' + file.filename)
        audio_file = open('uploads/' + file.filename,'rb')
        transcript = openai.Audio.transcribe("whisper-1",audio_file)
        return render_template('index.html', message=transcript['text'], filename=file.filename)
    

if __name__ == '__main__':
    app.run(debug=True, port=5001)
