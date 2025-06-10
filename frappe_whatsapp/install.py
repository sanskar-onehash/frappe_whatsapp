import frappe
from frappe_whatsapp.app_config import APP_TITLE


def after_install():
    try:
        add_app_to_whatsapp_apps()
        add_custom_fields_to_notification()
    except Exception as e:
        frappe.log_error(f"Error occured after installing {APP_TITLE} app:", e)


def add_app_to_whatsapp_apps():
    try:
        field = frappe.db.get_list(
            "Custom Field",
            ["*"],
            {"dt": "Notification", "fieldname": "custom_whatsapp_app"},
        )[0]

        options = field.get("options", "").split("\n")

        if APP_TITLE not in options:
            options.append(APP_TITLE)
            frappe.db.set_value(
                "Custom Field", field.name, "options", "\n".join(options)
            )
            frappe.db.commit()
    except IndexError:
        raise Exception("Notification field custom_whatsapp_app not present.")


def add_custom_fields_to_notification():
    custom_fields = [
        {
            "dt": "Notification",
            "fieldname": "whatsapp_whatsapp_template",
            "fieldtype": "Link",
            "label": "Template",
            "options": "WhatsApp Templates",
            "insert_after": "custom_whatsapp_app",
            "module": "Frappe Whatsapp",
            "depends_on": 'eval: (doc.channel == "WhatsApp") && (doc.custom_whatsapp_app == "WhatsApp")',
        },
        {
            "dt": "Notification",
            "default": "0",
            "description": "WhatsApp Template requires a document. ",
            "fieldname": "whatsapp_attach_document_print",
            "fieldtype": "Check",
            "insert_after": "sender_email",
            "depends_on": 'eval: (doc.channel == "WhatsApp") && (doc.custom_whatsapp_app == "WhatsApp")',
            "module": "Frappe Whatsapp",
            "label": " Attach Document Print",
        },
        {
            "dt": "Notification",
            "default": "0",
            "description": "WhatsApp Template requires document",
            "fieldname": "whatsapp_custom_attachment",
            "fieldtype": "Check",
            "label": "Custom attachment",
            "module": "Frappe Whatsapp",
            "insert_after": "whatsapp_attach_document_print",
            "depends_on": "eval: (doc.channel == 'WhatsApp') && (doc.custom_whatsapp_app == 'WhatsApp')",
        },
        {
            "dt": "Notification",
            "depends_on": "eval:doc.whatsapp_custom_attachment",
            "description": "Upload the file as public. Whatsapp cannot access the private file.",
            "fieldname": "whatsapp_attach",
            "fieldtype": "Attach",
            "module": "Frappe Whatsapp",
            "insert_after": "whatsapp_custom_attachment",
            "label": "Attach",
        },
        {
            "dt": "Notification",
            "depends_on": "eval:doc.whatsapp_custom_attachment",
            "description": "Attach media from doctype field",
            "fieldname": "whatsapp_attach_from_field",
            "fieldtype": "Data",
            "module": "Frappe Whatsapp",
            "insert_after": "whatsapp_attach",
            "label": "Attach from field ",
        },
        {
            "dt": "Notification",
            "depends_on": "eval:doc.whatsapp_custom_attachment",
            "fieldname": "whatsapp_file_name",
            "fieldtype": "Data",
            "module": "Frappe Whatsapp",
            "label": "File name",
            "insert_after": "whatsapp_attach_from_field",
        },
        {
            "dt": "Notification",
            "description": "Enter fields in the right sequence as per the template parameters.",
            "fieldname": "whatsapp_fields",
            "fieldtype": "Table",
            "label": "Fields",
            "module": "Frappe Whatsapp",
            "options": "WhatsApp Message Fields",
            "insert_after": "condition",
        },
    ]

    for field in custom_fields:
        if not frappe.db.exists(
            "Custom Field", {"dt": "Notification", "fieldname": field["fieldname"]}
        ):
            new_field = frappe.get_doc({"doctype": "Custom Field", **field})
            new_field.insert()
            frappe.db.commit()
