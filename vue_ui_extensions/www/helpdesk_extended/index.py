import frappe

no_cache = 1


def get_context(context):
	from helpdesk.www.helpdesk.index import get_boot

	frappe.db.commit()  # nosemgrep — persist CSRF/session state from get_boot like upstream helpdesk
	context.boot = get_boot()
	context.site_name = frappe.local.site
	if frappe.session.user != "Guest":
		from frappe.utils.telemetry import capture

		capture("active_site", "helpdesk")
	return context
