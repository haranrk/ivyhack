from r2r.client import R2RClient
from main import *
import uuid

# base_url = "https://sciphi-640688a6-7152-47c6-89c0-d1c3aa778184-qwpin2swwa-ue.a.run.app"
base_url = "https://sciphi-640688a6-7152-47c6-89c0-d1c3aa778184-qwpin2swwa-ue.a.run.app"
client = R2RClient(base_url)
emails = get_email_details_from_senders_cached()

entries = [
    {
        "document_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, email["id"])),  # document_id
        "blobs": {"txt": email["body"]},
        "metadata": {"tags": "bulk"},
    }
    for email in emails
    # {
    #     "document_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "doc 3")),
    #     "blobs": {"txt": "Third test entry"},
    #     # "metadata": {"tags": "example"},
    # },
]
bulk_upsert_response = client.add_entries(entries, do_upsert=True)
print(bulk_upsert_response)

# print("Searching remote db...")
# search_response = client.search("Crypto", 5)
# print(f"Search response:\n{search_response}\n\n")
