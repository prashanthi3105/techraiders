from flask import jsonify, request
import sustainabilityresponse

def test_data():
    return {
        "esgResponse": [
            {
                "entityName": "string",
                "benchmarkDetails": {
                    "question": "ESG Risk Rating for MSCI",
                    "esgType": "ESGScore",
                    "esgIndicators": "MSCISustainalytics",
                    "primaryDetails": "",
                    "secondaryDetails": "",
                    "citationDetails": "string",
                    "pageNumber": 0
                },
                "metrics": {
                    "timeTaken": 0,
                    "leveragedModel": "string",
                    "f1Score": 0
                }
            }
        ]
    }

def test_data_2():
    return {
        "esgResponse": [
            {
                "entityName": "string",
                "benchmarkDetails": [
                    {
                        "question": "ESG Risk Rating for MSCI",
                        "esgType": "ESGScore",
                        "esgIndicators": "MSCISustainalytics",
                        "primaryDetails": "",
                        "secondaryDetails": "",
                        "citationDetails": "string",
                        "pageNumber": 0
                    },
                    {
                        "question": "what is net zero target",
                        "esgType": "Environment",
                        "esgIndicators": "NetZeroTarget",
                        "primaryDetails": "",
                        "secondaryDetails": "",
                        "citationDetails": "string",
                        "pageNumber": 0
                    },
                    # More benchmark details...
                ],
                "metrics": {
                    "timeTaken": 0,
                    "leveragedModel": "string",
                    "f1Score": 0
                }
            }
        ]
    }

def safe_fetch(json, field_key):
    try:
        return json[field_key]
    except (KeyError, IndexError):
        return None

def map_upload_request_type(json, entity_name):
    json = test_data()

    response = response_esg.UploadRequestType()
    response.esgResponse = safe_fetch(json, 'esgResponse')

    return response

def map_upload_request(json, entity_name):
    json = test_data_2()

    response = response_esg.UploadRequest()
    response.esgResponse = safe_fetch(json, 'esgResponse')

    return response
