import uuid
import base64
import defusedxml.ElementTree as ET
from typing import List, Dict

def decrypt_rdm_str(val: str) -> str:
    """Decodes standard Base64 password fields found in unencrypted RDM exports."""
    if not val:
        return ""
    try:
        raw = base64.b64decode(val).decode("utf-8")
        if raw.isprintable():
            return raw
    except Exception:
        pass
    return val

def find_tag_value(element, candidate_tags: list) -> str:
    """Recursively inspects element and sub-elements for matching tag names."""
    for tag in candidate_tags:
        found = element.find(tag)
        if found is not None and found.text:
            return found.text.strip()
    # Search all children recursively if not found at root level
    for child in element.iter():
        if child.tag in candidate_tags and child.text:
            return child.text.strip()
    return ""

def parse_rdm_file(file_path: str) -> List[Dict]:
    tree = ET.parse(file_path)
    root = tree.getroot()

    connections = root.findall(".//Connection") or root.findall(".//RDMConnection")
    results = []

    for conn in connections:
        name = find_tag_value(conn, ["Name", "ConnectionName"]) or "Unnamed Server"
        group_path = find_tag_value(conn, ["Group", "GroupName", "Folder"]) or "Root"
        host = find_tag_value(conn, ["Url", "Host", "HostName", "Server", "IP"]) or ""
        conn_type = (find_tag_value(conn, ["ConnectionType", "Type"]) or "RDP").upper()
        
        # Deep username extraction across all Devolutions schema variations
        username = find_tag_value(conn, [
            "UserName", "Username", "User", "CredentialUserName", 
            "RDPUserName", "DefaultUserName", "CustomUserName"
        ])
        
        domain = find_tag_value(conn, [
            "Domain", "DomainName", "CredentialDomain", "RDPDomain"
        ])

        # Password extraction across plain and base64 tags
        raw_pwd = find_tag_value(conn, [
            "SafePassword", "Password", "ClearTextPassword", 
            "CredentialPassword", "CustomPassword"
        ])
        password = decrypt_rdm_str(raw_pwd)

        # Port mapping
        port = 3389
        if "SSH" in conn_type:
            port = 22
        elif "VNC" in conn_type:
            port = 5900

        port_val = find_tag_value(conn, ["Port", "CustomPort"])
        if port_val and port_val.isdigit():
            port = int(port_val)

        if not host:
            continue

        results.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "group_path": group_path.replace("\\", "/"),
            "protocol": "RDP" if "SSH" not in conn_type and "VNC" not in conn_type else conn_type,
            "host": host,
            "port": port,
            "username": username,
            "domain": domain,
            "password": password
        })

    return results
