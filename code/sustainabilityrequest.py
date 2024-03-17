class UploadRequest:
    def __init__(self, file, param):
        self.entityName = param
        self.documentUpload = file

class UploadRequestType:
    def __init__(self, file, entityName, esgType, esgIndicator):
        self.entityName = entityName
        self.esgType = esgType
        self.esgIndicator = esgIndicator
        self.documentUpload = file

class PDFReportRequest:
    def __init__(self, file, entityName):
        self.entityName = entityName
        self.documentUpload = file
