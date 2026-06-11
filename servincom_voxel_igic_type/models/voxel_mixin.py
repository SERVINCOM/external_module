# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging

from lxml import etree

from odoo import models

_logger = logging.getLogger(__name__)


class VoxelMixin(models.AbstractModel):
    _inherit = "voxel.mixin"

    def _get_and_send_voxel_report(self, report):
        self.ensure_one()
        report_ref = report
        if not isinstance(report_ref, str):
            report_ref = (
                report_ref.get_external_id().get(report_ref.id)
                or report_ref.report_name
            )
        report_xml = self.env["ir.actions.report"]._render_qweb_xml(
            report_ref, self.ids, {}
        )[0]
        tree = etree.fromstring(report_xml, etree.XMLParser(remove_blank_text=True))
        clean_report_xml = etree.tostring(tree, xml_declaration=True, encoding="UTF-8")
        clean_report_text = clean_report_xml.decode("UTF-8")
        file_name = self._get_voxel_filename()

        self._servincom_store_voxel_xml(file_name, clean_report_text, clean_report_xml)
        try:
            self._send_voxel_report("Outbox", file_name, clean_report_xml)
        except Exception as error:
            error_message = self._servincom_get_voxel_error_message(error)
            self.write(
                {
                    "voxel_state": "sent_errors",
                    "processing_error": error_message,
                }
            )
            _logger.exception("Voxel send failed for %s", file_name)
            if hasattr(self, "message_post"):
                self.message_post(
                    body=(
                        "Voxel XML generated and attached, but the send failed: "
                        f"{error_message}"
                    )
                )
            return False

        self.write({"voxel_state": "sent"})
        return True

    def _update_voxel_export_status(self, company):
        try:
            return super()._update_voxel_export_status(company)
        except Exception as error:
            if self._servincom_is_voxel_folder_listing_not_allowed(error):
                _logger.warning(
                    "Voxel folder listing is not allowed for company %s. "
                    "Skipping export status update.",
                    company.display_name,
                )
                return False
            raise

    def _servincom_get_voxel_error_message(self, error):
        error_message = f"{error.__class__.__name__}: {error}"
        response = getattr(error, "response", None)
        if response is not None:
            response_text = (response.text or "").strip()
            if len(response_text) > 2000:
                response_text = response_text[:2000] + "..."
            error_message = "\n".join(
                item
                for item in (
                    error_message,
                    f"HTTP status: {response.status_code}",
                    f"URL: {response.url}",
                    f"Response body: {response_text}" if response_text else "",
                )
                if item
            )
        return error_message

    def _servincom_is_voxel_folder_listing_not_allowed(self, error):
        current = error
        while current:
            response = getattr(current, "response", None)
            if response is not None and response.status_code == 405:
                return True
            current = getattr(current, "__cause__", None) or getattr(
                current, "__context__", None
            )
        return False

    def _servincom_store_voxel_xml(self, file_name, report_text, report_bytes):
        self.write(
            {
                "voxel_filename": file_name,
                "voxel_xml_report": report_text,
                "processing_error": False,
            }
        )
        attachment = self.env["ir.attachment"].create(
            {
                "name": file_name,
                "res_model": self._name,
                "res_id": self.id,
                "type": "binary",
                "datas": base64.b64encode(report_bytes).decode("ascii"),
                "mimetype": "application/xml",
            }
        )
        if hasattr(self, "message_post"):
            self.message_post(
                body="Voxel XML generated.",
                attachment_ids=[attachment.id],
            )
        return attachment
