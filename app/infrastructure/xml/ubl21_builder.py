from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from lxml import etree
from app.config import settings

from app.domain.entities.comprobante import Comprobante, Item

NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS_EXT = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
NS_DS = "http://www.w3.org/2000/09/xmldsig#"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS_SAC = "urn:sunat:names:specification:ubl:peru:schema:xsd:SunatAggregateComponents-1"
NS_INVOICE = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"


class Ubl21Builder:
    def __init__(self):
        self._razon_social   = settings.SUNAT_RAZON_SOCIAL
        self._tipo_operacion = settings.SUNAT_TIPO_OPERACION
        self._ubigeo         = settings.SUNAT_UBIGEO
        self._codigo_local = settings.SUNAT_CODIGO_LOCAL
        self._direccion      = settings.SUNAT_DIRECCION
        self._distrito       = settings.SUNAT_DISTRITO
        self._provincia      = settings.SUNAT_PROVINCIA
        self._departamento   = settings.SUNAT_DEPARTAMENTO
        self._pais           = settings.SUNAT_PAIS

    def _make_doc(self, tag: str, ns: str, text: str = None) -> etree.Element:
        el = etree.Element(f"{{{ns}}}{tag}")
        if text is not None:
            el.text = text
        return el

    def _make_q(self, tag: str, ns: str, text: str = "") -> str:
        return f"{{{ns}}}{tag}"

    def _build_header(self, root: etree.Element, comprobante: Comprobante, es_factura: bool = False) -> None:
        root.append(self._make_doc("UBLVersionID", NS_CBC, "2.1"))
        root.append(self._make_doc("CustomizationID", NS_CBC, "2.0"))
        root.append(self._make_doc("ID", NS_CBC, str(comprobante.serie_correlativo)))
        root.append(self._make_doc("IssueDate", NS_CBC, comprobante.fecha_emision.strftime("%Y-%m-%d")))
        root.append(self._make_doc("IssueTime", NS_CBC, comprobante.fecha_emision.strftime("%H:%M:%S")))

        invoice_type = self._make_doc("InvoiceTypeCode", NS_CBC, comprobante.tipo.value)
        if comprobante.tipo.value == "01":
            invoice_type.set("listID", "0101")
            invoice_type.set("listAgencyName", "PE:SUNAT")
            invoice_type.set("listName", "Tipo de Documento")
            invoice_type.set("listURI", "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01")
        else:
            invoice_type.set("listID", "0101")
        root.append(invoice_type)

        root.append(self._make_doc("DocumentCurrencyCode", NS_CBC, comprobante.moneda.value))

    def _build_signature(self, root: etree.Element, comprobante: Comprobante) -> None:
        sig = etree.SubElement(root, self._make_q("Signature", NS_CAC))
        sig.append(self._make_doc("ID", NS_CBC, "IDSignSG"))

        # SignatoryParty completamente vacío
        etree.SubElement(sig, self._make_q("SignatoryParty", NS_CAC))

        digital_attachment = etree.SubElement(sig, self._make_q("DigitalSignatureAttachment", NS_CAC))
        ext_ref = etree.SubElement(digital_attachment, self._make_q("ExternalReference", NS_CAC))
        ext_ref.append(self._make_doc("URI", NS_CBC, "#IDSignSG"))

    def _build_UBLExtensions(self, root: etree.Element) -> None:
        ext = etree.SubElement(root, self._make_q("UBLExtensions", NS_EXT))
        ubl_ext = etree.SubElement(ext, self._make_q("UBLExtension", NS_EXT))
        etree.SubElement(ubl_ext, self._make_q("ExtensionContent", NS_EXT))

    def _build_accounting_supplier(self, root: etree.Element, comprobante: Comprobante, es_factura: bool = False) -> None:
        supplier = etree.SubElement(root, self._make_q("AccountingSupplierParty", NS_CAC))
        party = etree.SubElement(supplier, self._make_q("Party", NS_CAC))

        party_id = etree.SubElement(party, self._make_q("PartyIdentification", NS_CAC))
        id_el = self._make_doc("ID", NS_CBC, str(comprobante.ruc_emisor))
        id_el.set("schemeID", "6")
        party_id.append(id_el)

        party_name = etree.SubElement(party, self._make_q("PartyName", NS_CAC))
        party_name.append(self._make_doc("Name", NS_CBC, self._razon_social))

        party_legal = etree.SubElement(party, self._make_q("PartyLegalEntity", NS_CAC))
        party_legal.append(self._make_doc("RegistrationName", NS_CBC, self._razon_social))

        if es_factura:
            reg_address = etree.SubElement(party_legal, self._make_q("RegistrationAddress", NS_CAC))
            reg_address.append(self._make_doc("AddressTypeCode", NS_CBC, self._codigo_local))

    def _build_items(self, root: etree.Element, items: list, comprobante: Comprobante) -> None:
        for item in items:
            line = etree.SubElement(
                root, self._make_q("InvoiceLine", NS_CAC)
            )
            line.append(
                self._make_doc("ID", NS_CBC, str(items.index(item) + 1))
            )
            line.append(
                self._make_doc("InvoicedQuantity", NS_CBC, str(item.cantidad))
            )
            line[-1].set("unitCode", item.unidad_medida)
            line.append(
                self._make_doc("LineExtensionAmount", NS_CBC, str(item.subtotal))
            )
            line[-1].set("currencyID", comprobante.moneda.value)

            pricing = etree.SubElement(line, self._make_q("PricingReference", NS_CAC))
            alternative_condition = etree.SubElement(
                pricing, self._make_q("AlternativeConditionPrice", NS_CAC)
            )
            precio_con_igv = round(item.precio_unitario * (1 + item.igv_porcentaje), 2)
            alternative_condition.append(
                self._make_doc("PriceAmount", NS_CBC, str(precio_con_igv))
            )
            alternative_condition[-1].set("currencyID", comprobante.moneda.value)
            alternative_condition.append(
                self._make_doc("PriceTypeCode", NS_CBC, "01")
            )

            tax_total = etree.SubElement(
                line, self._make_q("TaxTotal", NS_CAC)
            )
            tax_total.append(
                self._make_doc("TaxAmount", NS_CBC, str(item.igv))
            )
            tax_total[-1].set("currencyID", comprobante.moneda.value)
            tax_subtotal = etree.SubElement(
                tax_total, self._make_q("TaxSubtotal", NS_CAC)
            )
            taxable = self._make_doc("TaxableAmount", NS_CBC, str(item.subtotal))
            taxable.set("currencyID", comprobante.moneda.value)
            tax_subtotal.append(taxable)

            tax_amount_sub = self._make_doc("TaxAmount", NS_CBC, str(item.igv))
            tax_amount_sub.set("currencyID", comprobante.moneda.value)
            tax_subtotal.append(tax_amount_sub)

            tax_category = etree.SubElement(
                tax_subtotal, self._make_q("TaxCategory", NS_CAC)
            )
            tax_category.append(self._make_doc("ID", NS_CBC, "S"))
            tax_category.append(self._make_doc("Percent", NS_CBC, str(round(item.igv_porcentaje * 100, 2))))
            tax_category.append(self._make_doc("TaxExemptionReasonCode", NS_CBC, "10"))
            tax_scheme = etree.SubElement(
                tax_category, self._make_q("TaxScheme", NS_CAC)
            )
            tax_scheme.append(self._make_doc("ID", NS_CBC, "1000"))
            tax_scheme.append(self._make_doc("Name", NS_CBC, "IGV"))
            tax_scheme.append(self._make_doc("TaxTypeCode", NS_CBC, "VAT"))

            item_detail = etree.SubElement(
                line, self._make_q("Item", NS_CAC)
            )
            item_detail.append(
                self._make_doc("Description", NS_CBC, item.descripcion)
            )

            price = etree.SubElement(
                line, self._make_q("Price", NS_CAC)
            )
            price.append(
                self._make_doc("PriceAmount", NS_CBC, str(item.precio_unitario))
            )
            price[-1].set("currencyID", comprobante.moneda.value)

    def _build_legal_monetary_total(
        self, root: etree.Element, comprobante: Comprobante, subtotal: Decimal, total: Decimal
    ) -> None:
        legal = etree.SubElement(root, self._make_q("LegalMonetaryTotal", NS_CAC))

        line_ext = self._make_doc("LineExtensionAmount", NS_CBC, str(subtotal))
        line_ext.set("currencyID", comprobante.moneda.value)
        legal.append(line_ext)

        tax_inclusive = self._make_doc("TaxInclusiveAmount", NS_CBC, str(total))
        tax_inclusive.set("currencyID", comprobante.moneda.value)
        legal.append(tax_inclusive)

        charge_total = self._make_doc("ChargeTotalAmount", NS_CBC, "0.00")
        charge_total.set("currencyID", comprobante.moneda.value)
        legal.append(charge_total)

        payable = self._make_doc("PayableAmount", NS_CBC, str(total))
        payable.set("currencyID", comprobante.moneda.value)
        legal.append(payable)

    def _build_tax_total(
        self, root: etree.Element, comprobante: Comprobante, igv: Decimal, subtotal: Decimal
    ) -> None:
        tax_total = etree.SubElement(root, self._make_q("TaxTotal", NS_CAC))

        tax_amount = self._make_doc("TaxAmount", NS_CBC, str(igv))
        tax_amount.set("currencyID", comprobante.moneda.value)
        tax_total.append(tax_amount)

        tax_subtotal = etree.SubElement(tax_total, self._make_q("TaxSubtotal", NS_CAC))

        # 👈 base imponible global
        taxable = self._make_doc("TaxableAmount", NS_CBC, str(subtotal))
        taxable.set("currencyID", comprobante.moneda.value)
        tax_subtotal.append(taxable)

        tax_amount_sub = self._make_doc("TaxAmount", NS_CBC, str(igv))
        tax_amount_sub.set("currencyID", comprobante.moneda.value)
        tax_subtotal.append(tax_amount_sub)

        tax_category = etree.SubElement(tax_subtotal, self._make_q("TaxCategory", NS_CAC))
        tax_category.append(self._make_doc("ID", NS_CBC, "S"))
        tax_category.append(self._make_doc("Percent", NS_CBC, "18.00"))
        tax_scheme = etree.SubElement(tax_category, self._make_q("TaxScheme", NS_CAC))
        tax_scheme.append(self._make_doc("ID", NS_CBC, "1000"))
        tax_scheme.append(self._make_doc("Name", NS_CBC, "IGV"))
        tax_scheme.append(self._make_doc("TaxTypeCode", NS_CBC, "VAT"))

    def build_boleta(
        self,
        comprobante: Comprobante,
        subtotal: Decimal,
        igv: Decimal,
        total: Decimal,
    ) -> str:
        root = etree.Element(
            f"{{{NS_INVOICE}}}Invoice",
            nsmap={
                "cbc": NS_CBC,
                "cac": NS_CAC,
                "ext": NS_EXT,
                "ds": NS_DS,
                "xsi": NS_XSI,
                "sac": NS_SAC,
            },
        )
        root.set(f"{{{NS_XSI}}}schemaLocation", (
            "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2 "
            "http://www.cpe.sunat.gob.pe/sites/default/files/archivos/2.1/UBL-2.1.xsd"
        ))

        self._build_UBLExtensions(root)
        self._build_header(root, comprobante)
        self._build_signature(root, comprobante)
        self._build_accounting_supplier(root, comprobante)

        if comprobante.tipo_doc_cliente and comprobante.num_doc_cliente:
            customer = etree.SubElement(
                root, self._make_q("AccountingCustomerParty", NS_CAC)
            )
            customer_party = etree.SubElement(customer, self._make_q("Party", NS_CAC))
            customer_id = etree.SubElement(
                customer_party, self._make_q("PartyIdentification", NS_CAC)
            )
            customer_id.append(
                self._make_doc("ID", NS_CBC, comprobante.num_doc_cliente)
            )
            if comprobante.tipo_doc_cliente == "6":
                customer_id[0].set("schemeID", "6")
            else:
                customer_id[0].set("schemeID", "1")
            if comprobante.nombre_cliente:
                customer_party_legal = etree.SubElement(
                    customer_party, self._make_q("PartyLegalEntity", NS_CAC)
                )
                customer_party_legal.append(
                    self._make_doc("RegistrationName", NS_CBC, comprobante.nombre_cliente)
                )

        self._build_tax_total(root, comprobante, igv, subtotal)
        self._build_legal_monetary_total(root, comprobante, subtotal, total)
        self._build_items(root, comprobante.items, comprobante)

        return etree.tostring(root, xml_declaration=True, encoding="UTF-8").decode("utf-8")

    def build_factura(
        self,
        comprobante: Comprobante,
        subtotal: Decimal,
        igv: Decimal,
        total: Decimal,
    ) -> str:
        root = etree.Element(
            f"{{{NS_INVOICE}}}Invoice",
            nsmap={
                "cbc": NS_CBC, "cac": NS_CAC, "ext": NS_EXT,
                "ds": NS_DS, "xsi": NS_XSI, "sac": NS_SAC,
            },
        )
        root.set(f"{{{NS_XSI}}}schemaLocation", (
            "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2 "
            "http://www.cpe.sunat.gob.pe/sites/default/files/archivos/2.1/UBL-2.1.xsd"
        ))

        self._build_UBLExtensions(root)
        self._build_header(root, comprobante, es_factura=True)
        self._build_signature(root, comprobante)
        self._build_accounting_supplier(root, comprobante, es_factura=True)

        if comprobante.num_doc_cliente:
            customer = etree.SubElement(root, self._make_q("AccountingCustomerParty", NS_CAC))
            customer_party = etree.SubElement(customer, self._make_q("Party", NS_CAC))
            customer_id = etree.SubElement(customer_party, self._make_q("PartyIdentification", NS_CAC))
            id_el = self._make_doc("ID", NS_CBC, comprobante.num_doc_cliente)
            id_el.set("schemeID", "6")  # RUC siempre en facturas
            customer_id.append(id_el)
            party_legal = etree.SubElement(customer_party, self._make_q("PartyLegalEntity", NS_CAC))
            party_legal.append(self._make_doc("RegistrationName", NS_CBC, comprobante.nombre_cliente or ""))

        if True:  # es_factura siempre en build_factura
            note = self._make_doc("Note", NS_CBC, self._tipo_operacion)
            note.set("languageLocaleID", "2006")
            root.append(note)

        self._build_tax_total(root, comprobante, igv, subtotal)
        self._build_legal_monetary_total(root, comprobante, subtotal, total)
        self._build_items(root, comprobante.items, comprobante)

        return etree.tostring(root, xml_declaration=True, encoding="UTF-8").decode("utf-8")

    def build_anulacion(self, comprobante: Comprobante, motivo: str) -> str:
        root = etree.Element(
            self._make_q("Invoice", NS_DS),
            nsmap={
                "cbc": NS_CBC,
                "cac": NS_CAC,
                "ext": NS_EXT,
                "ds": NS_DS,
                "xsi": NS_XSI,
                "sac": NS_SAC,
            },
        )
        root.tag = self._make_q("Invoice", NS_CAC)

        self._build_UBLExtensions(root)
        root.append(self._make_doc("UBLVersionID", NS_CBC, "2.1"))
        root.append(self._make_doc("CustomizationID", NS_CBC, "2.0"))
        root.append(
            self._make_doc("ID", NS_CBC, str(comprobante.serie_correlativo))
        )
        root.append(
            self._make_doc(
                "IssueDate", NS_CBC, datetime.now().strftime("%Y-%m-%d")
            )
        )
        root.append(
            self._make_doc(
                "IssueTime", NS_CBC, datetime.now().strftime("%H:%M:%S")
            )
        )
        root.append(self._make_doc("InvoiceTypeCode", NS_CBC, "01"))
        root.append(self._make_doc("DocumentCurrencyCode", NS_CBC, "PEN"))

        self._build_signature(root, comprobante)
        self._build_accounting_supplier(root, comprobante)

        billing_ref = etree.SubElement(
            root, self._make_q("BillingReference", NS_CAC)
        )
        inv_doc_ref = etree.SubElement(
            billing_ref, self._make_q("InvoiceDocumentReference", NS_CAC)
        )
        inv_doc_ref.append(
            self._make_doc("ID", NS_CBC, str(comprobante.serie_correlativo))
        )
        inv_doc_ref.append(
            self._make_doc("DocumentTypeCode", NS_CBC, "01")
        )

        return etree.tostring(root, xml_declaration=True, encoding="UTF-8").decode("utf-8")
