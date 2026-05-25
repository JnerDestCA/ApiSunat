from __future__ import annotations
from lxml import etree
from signxml import XMLSigner, methods

from app.domain.ports.outbound.xml_signer import XmlSigner


class XmlSignerAdapter(XmlSigner):
    def sign(self, xml_string: str, private_key: object, certificate: object) -> str:
        root = etree.fromstring(xml_string.encode("utf-8"))

        ns = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
        ext_content = root.find(f".//{{{ns}}}ExtensionContent")
        if ext_content is not None:
            for child in list(ext_content):
                ext_content.remove(child)

        signer = XMLSigner(
            method=methods.xmldsig,
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
        )

        signed_root = signer.sign(
            root,
            key=private_key,
            cert=certificate,
            location=(
                "ext:UBLExtensions",
                "ext:UBLExtension",
                "ext:ExtensionContent",
            ),
        )

        return etree.tostring(
            signed_root, xml_declaration=True, encoding="UTF-8"
        ).decode("utf-8")
