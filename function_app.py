import azure.functions as func
#from azure.functions import HttpRequest, HttpResponse, FunctionApp
#import logging
import base64
import json
import pymupdf 
from io import BytesIO

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.function_name(name="PDF2PNG")
@app.route(route="PDF2PNG",methods=["POST"])
def PDF2PNG(req: func.HttpRequest) -> func.HttpResponse:
    #logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
        #logging.info(f'{req_body}')
        base64_pdf = req_body.get("base64Pdf")

        if not base64_pdf:
            return func.HttpResponse(
                "Please provide a 'base64Pdf' field in the request body.",
                status_code=400
            )

        # Decode base64 PDF
        pdf_bytes = base64.b64decode(base64_pdf)

        # Open PDF with PyMuPDF
        pdf_doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

        # Render first page as PNG
        page = pdf_doc[0]  # first page
        pix = page.get_pixmap(dpi=300)  # high resolution

        # Save PNG to memory
        img_bytes = pix.tobytes("png")
        base64_png = base64.b64encode(img_bytes).decode("utf-8")

        return func.HttpResponse(
            json.dumps({"base64Png": base64_png}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(
            f"Error processing PDF: {str(e)}",
            status_code=500
        )