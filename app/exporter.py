import csv
import io
import uuid
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any


def export_to_csv(records: List[Dict[str, Any]]) -> str:
    """Exports connection list to standard CSV format."""
    output = io.StringIO()
    fields = ["name", "host", "port", "group_path", "username", "domain"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for r in records:
        writer.writerow(r)
    return output.getvalue()


def export_to_rdm(records: List[Dict[str, Any]]) -> str:
    """Exports connection list into Devolutions .rdm XML schema."""
    root = ET.Element("ArrayOfConnection")

    for r in records:
        conn_el = ET.SubElement(root, "Connection")

        conn_id = r.get("id") or str(uuid.uuid4())
        ET.SubElement(conn_el, "ID").text = str(conn_id)
        ET.SubElement(conn_el, "Name").text = r.get("name", "")
        ET.SubElement(conn_el, "ConnectionType").text = "RDPConfigured"

        if r.get("group_path"):
            ET.SubElement(conn_el, "Group").text = r.get("group_path")

        # RDP specific metadata payload
        rdp_el = ET.SubElement(conn_el, "RDP")
        ET.SubElement(rdp_el, "Url").text = r.get("host", "")
        ET.SubElement(rdp_el, "Port").text = str(r.get("port", 3389))
        ET.SubElement(rdp_el, "UserName").text = r.get("username", "")
        ET.SubElement(rdp_el, "Domain").text = r.get("domain", "")

    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


def export_to_rdp_bundle(records: List[Dict[str, Any]], zip_path: str):
    """Generates standard Microsoft .rdp files inside a zipped bundle."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in records:
            safe_name = "".join(c for c in r.get("name", "Session") if c.isalnum() or c in (" ", "_", "-")).strip()
            folder = r.get("group_path", "").strip("/").replace("/", "_")
            file_name = f"{folder}_{safe_name}.rdp" if folder else f"{safe_name}.rdp"

            full_address = f"{r.get('host')}:{r.get('port', 3389)}"
            username = f"{r.get('domain')}\\{r.get('username')}" if r.get("domain") else r.get("username", "")

            rdp_content = (
                f"full address:s:{full_address}\n"
                f"username:s:{username}\n"
                "screen mode id:i:2\n"
                "use multimon:i:0\n"
                "desktopwidth:i:1600\n"
                "desktopheight:i:900\n"
                "session bpp:i:32\n"
                "compression:i:1\n"
                "keyboardhook:i:2\n"
                "audiomode:i:0\n"
                "redirectprinters:i:0\n"
                "redirectclipboard:i:1\n"
                "dynamic resolution:i:1\n"
            )
            zf.writestr(file_name, rdp_content)
