# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging
from urllib.parse import urljoin

from lxml import etree

from odoo import models

_logger = logging.getLogger(__name__)
VOXEL_REQUEST_TIMEOUT = 60


class VoxelMixin(models.AbstractModel):
    _inherit = "voxel.mixin"

    def enqueue_voxel_report(self, report):
        eta = self.company_id._get_voxel_report_eta()
        queue_obj = self.env["queue.job"].sudo()
        for record in self.sudo():
            active_job = record.voxel_job_ids.filtered(
                lambda job: job.state
                in ("wait_dependencies", "pending", "enqueued", "started")
            )[:1]
            if active_job:
                record._servincom_mark_voxel_pending()
                continue
            new_delay = (
                record.with_context(company_id=record.company_id.id)
                .with_delay(
                    eta=eta,
                    max_retries=1,
                    description=record._servincom_get_voxel_job_description(),
                )
                ._get_and_send_voxel_report(report)
            )
            job = queue_obj.search([("uuid", "=", new_delay.uuid)], limit=1)
            record.voxel_job_ids |= job
            record._servincom_mark_voxel_pending()

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
        clean_report_xml = etree.tostring(
            tree,
            xml_declaration=True,
            encoding="UTF-8",
            pretty_print=True,
        )
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

    def _request_to_voxel(
        self, request_method, folder, company=None, voxel_filename=None, data=None
    ):
        login = self.get_voxel_login(company)
        if not login:
            raise Exception
        url = urljoin(login.url, folder)
        url += url.endswith("/") and "" or "/"
        response = request_method(
            url=urljoin(url, voxel_filename or ""),
            auth=(login.user, login.password),
            data=data,
            timeout=VOXEL_REQUEST_TIMEOUT,
        )
        _logger.debug("Voxel request response: %s", str(response))
        if response.status_code != 200:
            response.raise_for_status()
        return response

    def _servincom_get_voxel_job_description(self):
        self.ensure_one()
        parts = ["Voxel"]
        document_name = self.display_name
        if "name" in self._fields and self.name:
            document_name = self.name
        parts.append(document_name)
        if "partner_id" in self._fields and self.partner_id:
            parts.append(self.partner_id.display_name)
        if "amount_total" in self._fields:
            amount = self.amount_total
            currency = (
                self.currency_id.name
                if "currency_id" in self._fields and self.currency_id
                else ""
            )
            parts.append(f"{amount:.2f} {currency}".strip())
        return " - ".join(parts)

    def _servincom_mark_voxel_pending(self):
        self.ensure_one()
        if self._name != "account.move":
            return
        self.write(
            {
                "voxel_state": "pending",
                "processing_error": False,
            }
        )

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
