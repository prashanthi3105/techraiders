from dataclasses import dataclass, field
from typing import List, Optional

class EnumESG:
    NONE = ""
    ESG_SCORE = 'ESGScore'
    ENVIRONMENT = 'Environment'
    SOCIAL = 'Social' 
    REPORTING = 'Reporting'

@dataclass
class MetaData:
    question: str = ""
    esgType: EnumESG = EnumESG.NONE
    esgIndicators: str = ""
    primaryDetails: str = ""
    secondaryDetails: str = ""
    citationDetails: str = ""
    pageNumber: int = 0

@dataclass
class Metrics:
    timeTaken: int = 0
    leveragedModel: str = ""
    f1Score: str = ""

@dataclass
class ResponseInternalDetails:
    entityName: str = ""
    benchmarkDetails: List[MetaData] = field(default_factory=list)
    metrics: Metrics = Metrics()  

@dataclass
class ResponseInternalDetailsScalar:
    entityName: str = ""
    benchmarkDetails: MetaData = MetaData()
    metrics: Metrics = Metrics() 

@dataclass
class PdfReportResponse:  # Changed class name to conform to Python naming conventions
    pdfUrlPath: str = ""

@dataclass
class UploadRequest:
    esgResponse: List[ResponseInternalDetails] = field(default_factory=list)

@dataclass
class UploadRequestType:
    esgResponse: List[ResponseInternalDetailsScalar] = field(default_factory=list)

@dataclass
class KeepAliveResponse:  # Changed class name to conform to Python naming conventions
    status: str = ""
    message: str = ""

@dataclass
class PDFReportResponse:  # Changed class name to conform to Python naming conventions
    pdfUrlPath: str = ""
