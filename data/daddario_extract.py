"""
WIP

Extract data from the D'Addario string tension chart PDF
into a more useful format.

The chart is available at:
https://www.daddario.com/globalassets/pdfs/accessories/tension_chart_13934.pdf
"""
import PyPDF2

f = open("tension_chart_13934.pdf", "rb")
pdf = PyPDF2.PdfFileReader(f)

assert pdf.numPages == 14

page = pdf.getPage(4)
print(page.extractText())


f.close()
