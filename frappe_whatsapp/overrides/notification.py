import json
import frappe
from frappe import utils
from frappe.utils.safe_exec import get_safe_globals
from frappe.email.doctype.notification.notification import get_context
from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_notification.whatsapp_notification import (
    notify,
)
from frappe_whatsapp.app_config import APP_TITLE
from frappe.desk.form.utils import get_pdf_link
from frappe.utils import datetime


def whatsapp_validate(notification_doc):
    pass


def whatsapp_send(notification_doc, doc):
    if (
        notification_doc.channel == "WhatsApp"
        and notification_doc.custom_whatsapp_app == APP_TITLE
    ):
        context = get_context(doc)
        context = {"doc": doc, "alert": notification_doc, "comments": None}
        if doc.get("_comments"):
            context["comments"] = json.loads(doc.get("_comments"))
        if notification_doc.is_standard:
            notification_doc.load_standard_properties(context)

        doc_data = doc.as_dict()
        if notification_doc.condition:
            # check if condition satisfies
            if not frappe.safe_eval(
                notification_doc.condition, get_safe_globals(), dict(doc=doc_data)
            ):
                return

        template = frappe.db.get_value(
            "WhatsApp Templates",
            notification_doc.whatsapp_whatsapp_template,
            fieldname="*",
        )

        if template:
            data = whatsapp_prepare_message_data(
                notification_doc, doc, doc_data, template
            )
            whatsapp_send_message(notification_doc, doc, data, context)


def whatsapp_prepare_message_data(notification_doc, doc, doc_data, template):
    data = {
        "messaging_product": "whatsapp",
        "type": "template",
        "template": {
            "name": template.actual_name,
            "language": {"code": template.language_code},
            "components": [],
        },
    }

    # Pass parameter values
    if notification_doc.whatsapp_fields:
        parameters = []
        for field in notification_doc.whatsapp_fields:
            value = doc_data[field.field_name]
            if isinstance(
                doc_data[field.field_name], (datetime.date, datetime.datetime)
            ):
                value = str(doc_data[field.field_name])
            parameters.append({"type": "text", "text": value})

        data["template"]["components"] = [{"type": "body", "parameters": parameters}]

    if notification_doc.whatsapp_attach_document_print:
        # frappe.db.begin()
        key = doc.get_document_share_key()  # noqa
        frappe.db.commit()
        print_format = "Standard"
        doctype = frappe.get_doc("DocType", doc_data["doctype"])
        if doctype.custom:
            if doctype.default_print_format:
                print_format = doctype.default_print_format
        else:
            default_print_format = frappe.db.get_value(
                "Property Setter",
                filters={
                    "doc_type": doc_data["doctype"],
                    "property": "default_print_format",
                },
                fieldname="value",
            )
            print_format = (
                default_print_format if default_print_format else print_format
            )
        link = get_pdf_link(
            doc_data["doctype"], doc_data["name"], print_format=print_format
        )

        filename = f'{doc_data["name"]}.pdf'
        url = f"{utils.get_url()}{link}&key={key}"

    elif notification_doc.whatsapp_custom_attachment:
        filename = notification_doc.whatsapp_file_name

        if notification_doc.whatsapp_attach_from_field:
            file_url = doc_data[notification_doc.whatsapp_attach_from_field]
            if not file_url.startswith("http"):
                # get share key so that private files can be sent
                key = doc.get_document_share_key()
                file_url = f"{utils.get_url()}{file_url}&key={key}"
        else:
            file_url = notification_doc.whatsapp_attach

        if file_url.startswith("http"):
            url = f"{file_url}"
        else:
            url = f"{utils.get_url()}{file_url}"

    if template.header_type == "DOCUMENT":
        data["template"]["components"].append(
            {
                "type": "header",
                "parameters": [
                    {
                        "type": "document",
                        "document": {"link": url, "filename": filename},
                    }
                ],
            }
        )
    elif template.header_type == "IMAGE":
        data["template"]["components"].append(
            {
                "type": "header",
                "parameters": [{"type": "image", "image": {"link": url}}],
            }
        )

    notification_doc.whatsapp_content_type = template.header_type.lower()
    return data


def whatsapp_send_message(notification_doc, doc, data, context):
    receivers = notification_doc.get_receiver_list(doc, context)
    for receiver in receivers:
        data["to"] = receiver
        notify(notification_doc, data)
