"""Email templates — structured alert emails with consistent branding.

Beck: Templates as data, not code. Each template is a pure function from
alert data to rendered content.
"""

from __future__ import annotations

from dataclasses import dataclass
from string import Template


@dataclass(frozen=True)
class EmailContent:
    """Rendered email ready for sending."""

    subject: str
    body_html: str
    body_text: str


# Subject line templates by alert type
SUBJECT_TEMPLATES: dict[str, str] = {
    "devaluation": "RedeemFlow Alert: ${program} points devaluation detected",
    "transfer_bonus": "RedeemFlow: ${program} transfer bonus available",
    "expiration": "RedeemFlow Warning: ${program} points expiring soon",
    "sweet_spot": "RedeemFlow: New sweet spot in ${program}",
    "price_drop": "RedeemFlow: Award price drop for ${program}",
}

# HTML body template (minimal, inline CSS for email compatibility)
_BODY_STYLE = (
    "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;"
    " max-width: 600px; margin: 0 auto; padding: 20px;"
)
_ALERT_STYLE = (
    "background: ${priority_bg}; border-left: 4px solid ${priority_color};"
    " padding: 16px; border-radius: 4px; margin-bottom: 24px;"
)
_CTA_STYLE = (
    "display: inline-block; background: #e11d48; color: white;"
    " padding: 12px 24px; border-radius: 6px; text-decoration: none;"
    " font-size: 14px; font-weight: 500;"
)
HTML_TEMPLATE = Template(
    f"""<!DOCTYPE html>
<html>
<body style="{_BODY_STYLE}">
  <div style="border-bottom: 2px solid #e11d48; padding-bottom: 16px; margin-bottom: 24px;">
    <h1 style="color: #e11d48; font-size: 20px; margin: 0;">RedeemFlow</h1>
  </div>
  <div style="{_ALERT_STYLE}">
    <h2 style="margin: 0 0 8px; font-size: 16px; color: #111;">${{title}}</h2>
    <p style="margin: 0; color: #444; font-size: 14px;">${{message}}</p>
  </div>
  <div style="margin-bottom: 24px;">
    <table style="width: 100%; border-collapse: collapse;">
      <tr>
        <td style="padding: 8px 0; color: #666; font-size: 13px;">Program</td>
        <td style="padding: 8px 0; font-weight: bold;">${{program}}</td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #666; font-size: 13px;">Priority</td>
        <td style="padding: 8px 0; font-weight: bold; color: ${{priority_color}};">${{priority}}</td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #666; font-size: 13px;">Type</td>
        <td style="padding: 8px 0; font-size: 13px;">${{alert_type}}</td>
      </tr>
    </table>
  </div>
  <div style="text-align: center; margin: 24px 0;">
    <a href="${{action_url}}" style="{_CTA_STYLE}">View Details</a>
  </div>
  <div style="border-top: 1px solid #eee; padding-top: 16px; margin-top: 24px; color: #999; font-size: 12px;">
    <p>You received this because of your RedeemFlow notification preferences.</p>
    <p><a href="https://redeemflow.com/settings/notifications" style="color: #e11d48;">Manage</a></p>
  </div>
</body>
</html>"""
)

TEXT_TEMPLATE = Template("""RedeemFlow Alert
================

${title}

${message}

Program: ${program}
Priority: ${priority}
Type: ${alert_type}

View details: ${action_url}

---
Manage your notification preferences at https://redeemflow.com/settings/notifications
""")

PRIORITY_COLORS: dict[str, tuple[str, str]] = {
    "critical": ("#dc2626", "#fef2f2"),
    "high": ("#ea580c", "#fff7ed"),
    "medium": ("#ca8a04", "#fefce8"),
    "low": ("#6b7280", "#f9fafb"),
}


def render_alert_email(
    alert_type: str,
    priority: str,
    title: str,
    message: str,
    program: str,
    action_url: str = "https://redeemflow.com/dashboard",
) -> EmailContent:
    """Render an alert notification email."""
    priority_color, priority_bg = PRIORITY_COLORS.get(priority, ("#6b7280", "#f9fafb"))

    subject_template = SUBJECT_TEMPLATES.get(alert_type, "RedeemFlow Alert: ${program}")
    subject = Template(subject_template).safe_substitute(program=program)

    context = {
        "title": title,
        "message": message,
        "program": program,
        "priority": priority,
        "alert_type": alert_type,
        "action_url": action_url,
        "priority_color": priority_color,
        "priority_bg": priority_bg,
    }

    body_html = HTML_TEMPLATE.safe_substitute(**context)
    body_text = TEXT_TEMPLATE.safe_substitute(**context)

    return EmailContent(
        subject=subject,
        body_html=body_html,
        body_text=body_text,
    )
