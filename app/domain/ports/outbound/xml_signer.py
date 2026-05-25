from __future__ import annotations


class XmlSigner:
    def sign(self, xml_string: str, private_key: object, certificate: object) -> str:
        raise NotImplementedError
