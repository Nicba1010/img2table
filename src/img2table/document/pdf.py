# coding: utf-8
from dataclasses import dataclass
from functools import cached_property
from typing import Dict, List, Optional

import cv2
import fitz
import numpy as np
from img2table.document.base import Document
from img2table.document.base.rotation import fix_rotation_image
from img2table.ocr.pdf import PdfOCR
from img2table.tables.objects.extraction import ExtractedTable


@dataclass
class PDF(Document):
    pages: List[int] = None
    detect_rotation: bool = False
    pdf_text_extraction: bool = True
    _rotated: bool = False

    def validate_pages(self, value, **_) -> Optional[List[int]]:
        if value is not None:
            if not isinstance(value, list):
                raise TypeError(f"Invalid type {type(value)} for pages argument")
            if not all(isinstance(x, int) for x in value):
                raise TypeError("All values in pages argument should be integers")
        return value

    def validate_pdf_text_extraction(self, value, **_) -> int:
        if not isinstance(value, bool):
            raise TypeError(f"Invalid type {type(value)} for pdf_text_extraction argument")
        return value

    def validate__rotated(self, value, **_) -> int:
        return value

    @cached_property
    def images(self) -> List[np.ndarray]:
        mat = fitz.Matrix(200 / 72, 200 / 72)
        doc = fitz.Document(stream=self.bytes, filetype='pdf')

        # Get all images
        images = list()
        for page_number in self.pages or range(doc.page_count):
            page = doc.load_page(page_id=page_number)
            pix = page.get_pixmap(matrix=mat)
            img = np.frombuffer(buffer=pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, 3))

            # To grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # # Increase contrast
            alpha = 1.1  # Contrast control (1.0-3.0)
            beta = 0  # Brightness control (0-100)
            contrast_enhanced = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

            # Thresholding for making grays whiter and blacks blacker
            # _, thresholded = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY)

            thresholded = contrast_enhanced

            # Handle rotation if needed
            if self.detect_rotation:
                final, self._rotated = fix_rotation_image(img=thresholded)
            else:
                final, self._rotated = thresholded, False
            images.append(final)

        return images

    def extract_tables(self, ocr: "OCRInstance" = None, implicit_rows: bool = False, borderless_tables: bool = False,
                       min_confidence: int = 50) -> Dict[int, List[ExtractedTable]]:
        """
        Extract tables from document
        :param ocr: OCRInstance object used to extract table content
        :param implicit_rows: boolean indicating if implicit rows are splitted
        :param borderless_tables: boolean indicating if borderless tables should be detected
        :param min_confidence: minimum confidence level from OCR in order to process text, from 0 (worst) to 99 (best)
        :return: dictionary with page number as key and list of extracted tables as values
        """
        if not self._rotated and self.pdf_text_extraction:
            # Try to get OCRDataframe from PDF
            self.ocr_df = PdfOCR().of(document=self)

        return super().extract_tables(ocr=ocr,
                                      implicit_rows=implicit_rows,
                                      borderless_tables=borderless_tables,
                                      min_confidence=min_confidence)
