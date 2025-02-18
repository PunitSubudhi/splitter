import requests
import io

def upload_csv_to_gofile(csv_string, token):
    try:
        # Fetch an available server
        server_response = requests.get('https://api.gofile.io/servers')
        if server_response.status_code != 200:
            raise Exception(f"Failed to query servers: {server_response.status_code}")
        
        server_data = server_response.json()
        # 'servers' is a list of available servers with "name" and "zone"
        if "data" not in server_data or "servers" not in server_data["data"]:
            raise Exception(f"Unexpected server response format: {server_data}")
        
        servers_list = server_data["data"]["servers"]
        if not servers_list:
            raise Exception(f"No servers returned: {server_data}")
        
        # Pick the first available server for upload
        server_name = servers_list[0]["name"]

        # Prepare and send the upload request
        upload_url = f"https://{server_name}.gofile.io/contents/uploadfile"
        csv_file = io.StringIO(csv_string)
        files = {"file": ("upload.csv", csv_file)}
        upload_response = requests.post(
            upload_url,
            files=files,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if upload_response.status_code != 200:
            raise Exception(f"Failed to upload file: {upload_response.status_code}")
        
        upload_data = upload_response.json()
        print(f"Upload response: {upload_data}")
        if "data" not in upload_data or "downloadPage" not in upload_data["data"]:
            raise Exception(f"Unexpected upload response format: {upload_data}")
        
        download_url = upload_data["data"]["downloadPage"]
        print(f"Download URL: {download_url}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Usage example (replace token with your own):
csv_string = "name,age\nJohn Doe,30\nJane Doe,25"
upload_csv_to_gofile(csv_string, 'uuo3ntVHGDnVEWQ06yf0uVM5J8BjKZa0')