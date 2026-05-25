from __future__ import annotations
import xmlsec
from lxml import etree
from cryptography.hazmat.primitives import serialization

from app.domain.ports.outbound.xml_signer import XmlSigner

NS_EXT = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
NS_DS  = "http://www.w3.org/2000/09/xmldsig#"

class XmlSignerAdapter(XmlSigner):
    def sign(self, xml_string: str, private_key: object, certificate: object) -> str:
        NS_EXT = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
        
        root = etree.fromstring(xml_string.encode("utf-8"))

        ext_content = root.find(f".//{{{NS_EXT}}}ExtensionContent")
        if ext_content is None:
            raise ValueError("No se encontró ExtensionContent en el XML")

        # xmlsec construye la estructura ds:Signature correcta
        signature_node = xmlsec.template.create(
            root,
            c14n_method=xmlsec.constants.TransformExclC14N,
            sign_method=xmlsec.constants.TransformRsaSha256,
            name="IDSignSG",
        )
        ext_content.append(signature_node)

        ref = xmlsec.template.add_reference(
            signature_node,
            digest_method=xmlsec.constants.TransformSha256,
            uri="",
        )
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformExclC14N)

        key_info = xmlsec.template.ensure_key_info(signature_node)
        xmlsec.template.add_x509_data(key_info)

        key_pem  = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM)

        key = xmlsec.Key.from_memory(key_pem, xmlsec.KeyFormat.PEM)
        key.load_cert_from_memory(cert_pem, xmlsec.KeyFormat.CERT_PEM)

        ctx = xmlsec.SignatureContext()
        ctx.key = key
        ctx.sign(signature_node)

        return etree.tostring(
            root, xml_declaration=True, encoding="UTF-8"
        ).decode("utf-8")