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

        # Decode base64 PDF
        pdf_bytes = base64.b64decode(base64_pdf)

        images = render_pdf_pages_to_pngs(pdf_bytes,300)  

        if not images:
            return func.HttpResponse("PDF contained no pages.", status_code=400)

        zip_bytes = create_zip_in_memory(images)


        zip_name = f"labels.zip"
        headers = {
            "Content-Type": "application/zip",
            "Content-Disposition": f'attachment; filename="{zip_name}"'
        }
        return func.HttpResponse(body=zip_bytes, status_code=200, headers=headers)

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
        return []

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
            imgs.append((filename, png_bytes))
    return imgs


def create_zip_in_memory(files):
    """
    files: iterable of (filename, bytes)
    returns bytes of zip file
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, filebytes in files:
            zf.writestr(filename, filebytes)
    buf.seek(0)
    return buf.read()