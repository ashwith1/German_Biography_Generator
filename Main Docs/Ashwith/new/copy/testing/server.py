# backend_server.py

import pandas as pd
from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/process_csv', methods=['POST'])
def process_csv():
    file = request.files['file']
    file_path = os.path.join("/tmp", file.filename)
    file.save(file_path)

    # Call the notebook or processing script to generate the biography
    result = subprocess.run(
        ["jupyter", "nbconvert", "--to", "notebook", "--execute", "--output", "/tmp/result.ipynb", "test.ipynb", "--ExecutePreprocessor.timeout=600"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        return jsonify({'error': 'Failed to process the CSV file'}), 500

    # Assuming the result of the notebook execution is stored in a text file or similar
    with open("/tmp/biography.txt", "r") as bio_file:
        biography_text = bio_file.read()

    return jsonify({'biography': biography_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
