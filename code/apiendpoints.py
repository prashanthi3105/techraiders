from dataclasses import asdict
from flask import Flask, jsonify, request
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from markupsafe import escape

import request_esg
import response_esg
import mapper

app = Flask(__name__)

# Azure Blob Storage Configuration
connection_string = "DefaultEndpointsProtocol=https;AccountName=hacksustainesg;AccountKey=UlenjLhRTRnBPKwU4/Lu0+3p9+vYRRsBXTQiEh+GUrzZTINLC+uoHK2KUZCUB2EKR4BSy4GV4ovw+AStuU2YEg==;EndpointSuffix=core.windows.net"
container_name = "Team-416"

blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

# Utility function to upload file to Azure Blob Storage
def upload_blob(file_content, entity_name):
    blob_client = container_client.get_blob_client(f"{entity_name}.pdf")
    blob_client.upload_blob(file_content)

# Good for testing if the endpoint is alive
@app.route('/')
def index():
    return escape("Hello, this is the home index")

# Upload ESG for given entity and retrieve all ESG benchmark documents
@app.route('/api/esg/benchmark/upload/<entityName>', methods=['POST'])
def esg_entity_name(entityName):
    file = request.files['documentUpload']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File uploaded is not a PDF'}), 400

    upload_blob(file.stream, entityName)

    response_upload = response_esg.UploadRequest()
    response_upload = mapper.mapUploadRequest(None, entityName)

    return jsonify(asdict(response_upload)), 200

# Fetch specific ESG indicator for given entity
@app.route('/api/esg/benchmark/upload/<entityName>/<esgType>/<esgIndicator>', methods=['POST'])
def esg_upload(entityName, esgType, esgIndicator):
    file = request.files['documentUpload']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File uploaded is not a PDF'}), 400

    upload_blob(file.stream, entityName)

    response_upload_type = response_esg.UploadRequestType()
    response_upload_type = mapper.mapUploadRequestType(None, entityName)

    return jsonify(asdict(response_upload_type)), 200

# Find status of the benchmarking service
@app.route('/api/esg/benchmark/keepalive', methods=['GET'])
def keep_alive():
    response_keep_alive = response_esg.KeepAliveRepsonse()
    response_keep_alive.status = 'UP'
    response_keep_alive.message = 'The service is up'

    return jsonify(asdict(response_keep_alive)), 200

# Get PDF URL for given entity name
@app.route('/api/esg/benchmark/pdf-report/<entityName>', methods=['POST'])
def pdf_report(entityName):
    file = request.files['documentUpload']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File uploaded is not a PDF'}), 400

    upload_blob(file.stream, entityName)

    response = response_esg.PDFReportRepsonse()
    response.pdfUrlPath = f"https://hacksustainesg.blob.core.windows.net/Team-416/{entityName}.pdf"

    return jsonify(asdict(response)), 200

if __name__ == "__main__":
    app.run()
