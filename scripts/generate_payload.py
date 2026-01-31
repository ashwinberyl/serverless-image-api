import base64
import json
import sys
import os

def create_payload(image_path):
    if not os.path.exists(image_path):
        print(f"Error: File '{image_path}' not found.")
        return

    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    payload = {
        "image_data": encoded_string,
        "filename": os.path.basename(image_path),
        "user_id": "user123",
        "metadata": {
            "title": "Postman Upload",
            "description": "Uploaded via Postman",
            "tags": ["test", "postman"],
            "location": "LocalStack"
        }
    }
    
    # Write directly to file with clean UTF-8 (no BOM)
    output_file = "payload.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    print(f"✓ Payload written to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_payload.py <path_to_image>")
        sys.exit(1)
    
    create_payload(sys.argv[1])
