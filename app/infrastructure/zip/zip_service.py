from __future__ import annotations
import io
import zipfile
from typing import Tuple


class ZipService:
    def compress(self, xml_string: str, base_filename: str) -> Tuple[bytes, str]:
        zip_buffer = io.BytesIO()
        xml_filename = f"{base_filename}.xml"
        zip_filename = f"{base_filename}.zip"

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(xml_filename, xml_string.encode("utf-8"))

        return zip_buffer.getvalue(), zip_filename

    def extract_xml(self, zip_bytes: bytes) -> str:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            names = zf.namelist()
            xml_files = [n for n in names if n.endswith(".xml")]
            if not xml_files:
                raise ValueError("No se encontró archivo XML dentro del ZIP")
            return zf.read(xml_files[0]).decode("utf-8")
