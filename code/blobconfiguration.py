from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

def upload_blob(file):
    """
    Upload file to Azure Blob Storage container
    """

    # Replace the connection string with your actual connection string
    connection_string = "DefaultEndpointsProtocol=https;AccountName=hacksustainesg;AccountKey=UlenjLhRTRnBPKwU4/Lu0+3p9+vYRRsBXTQiEh+GUrzZTINLC+uoHK2KUZCUB2EKR4BSy4GV4ovw+AStuU2YEg==;EndpointSuffix=core.windows.net"
    
    # Replace the container name with your actual container name
    container_name = "team-416"

    # Create a BlobServiceClient using the connection string
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # Create a ContainerClient for the specified container
    container_client = blob_service_client.get_container_client(container_name)

    # Define the destination blob name
    destination_blob_name = file.filename

    print(f'File: {file.filename} to be uploaded to destination {destination_blob_name}')

    # Upload the file to the container
    blob_client = container_client.get_blob_client(destination_blob_name)
    with open(file.filename, "rb") as data:
        blob_client.upload_blob(data)

    print(f'File: {file.filename} uploaded to destination {destination_blob_name}')


def get_blob_url(blob_name):
    """
    Generate URL to access blob in Azure Blob Storage container
    """

    # Replace the connection string with your actual connection string
    connection_string = "DefaultEndpointsProtocol=https;AccountName=hacksustainesg;AccountKey=UlenjLhRTRnBPKwU4/Lu0+3p9+vYRRsBXTQiEh+GUrzZTINLC+uoHK2KUZCUB2EKR4BSy4GV4ovw+AStuU2YEg==;EndpointSuffix=core.windows.net"
    
    # Replace the container name with your actual container name
    container_name = "Team-416"

    # Create a BlobServiceClient using the connection string
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # Generate URL for the specified blob
    blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
    return blob_url
