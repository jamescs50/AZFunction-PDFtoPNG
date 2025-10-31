import azure.functions as func
#from azure.functions import HttpRequest, HttpResponse, FunctionApp
#import logging
import base64
import json
import pymupdf 
import zipfile
import io
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

        #logging.info("about to start reading pdf")
        # Decode base64 PDF
        pdf_bytes = base64.b64decode(base64_pdf)

        #logging.info("about to start converting pdf")

        try:
            images = render_pdf_pages_to_pngs(pdf_bytes, dpi=300)
        except Exception as e:
            #logging.exception("Render error: %s", e)
            return func.HttpResponse(
                json.dumps({"error": f"Failed to render PDF: {str(e)}"}),
                status_code=500,
                mimetype="application/json"
            )


        if not images:
            return func.HttpResponse("PDF contained no pages.", status_code=400)

#        logging.info(images_dict)
#        logging.info(json.dumps(images_dict))

        json_result = [
            {
                "page": idx + 1,
                "filename": fname,
                "image_base64": base64.b64encode(data).decode("utf-8"),
            }
            for idx, (fname, data) in enumerate(images)
        ]

        return func.HttpResponse(
            json.dumps(json_result,indent=2),
            mimetype="application/json",
            status_code=200
        )




    except Exception as e:
        return func.HttpResponse(
            f"Error processing PDF: {str(e)}",
            status_code=500
        )
    


def render_pdf_pages_to_pngs(pdf_bytes: bytes, dpi: int = 300):
    """
    Renders each page in pdf_bytes to PNG image bytes.
    Returns list of tuples: (filename, png_bytes)
    """
    if not pdf_bytes:
        return {}

    # Cap DPI to something reasonable to avoid enormous images
    max_dpi = 300
    dpi = min(dpi, max_dpi)
    # MuPDF default: 72 DPI. Scale = dpi / 72
    scale = dpi / 72.0
    mat = pymupdf.Matrix(scale, scale)

    imgs = []
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        page_count = doc.page_count
        for i in range(page_count):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=mat, alpha=False)  # alpha False => RGB
            png_bytes = pix.tobytes("png")
            filename = f"page_{i+1:03d}.png"
            imgs.append((filename,png_bytes))
    return imgs
