from __future__ import annotations 

import datetime 
from functools import lru_cache 

from azure .storage .blob import (
BlobServiceClient ,
ContainerClient ,
generate_blob_sas ,
BlobSasPermissions ,
)

from shared .config .settings import get_settings 

@lru_cache ()
def get_container_client ()->ContainerClient :
    s =get_settings ()
    service_client =BlobServiceClient .from_connection_string (s .azure_storage_connection_string )
    container =service_client .get_container_client (s .azure_storage_container )
    try :
        container .create_container ()
    except Exception :
        pass 
    return container 

def upload_bytes (key :str ,data :bytes ,content_type :str ="application/octet-stream")->None :
    container =get_container_client ()
    from azure .storage .blob import ContentSettings 

    container .upload_blob (
    name =key ,data =data ,overwrite =True ,
    content_settings =ContentSettings (content_type =content_type ),
    )

def download_bytes (key :str )->bytes :
    container =get_container_client ()
    downloader =container .download_blob (key )
    return downloader .readall ()

def generate_read_url (key :str ,expires_in_seconds :int =86400 )->str :
    s =get_settings ()
    container =get_container_client ()
    account_name =container .account_name 
    account_key =_account_key_from_connection_string (s .azure_storage_connection_string )

    sas_token =generate_blob_sas (
    account_name =account_name ,
    container_name =container .container_name ,
    blob_name =key ,
    account_key =account_key ,
    permission =BlobSasPermissions (read =True ),
    expiry =datetime .datetime .utcnow ()+datetime .timedelta (seconds =expires_in_seconds ),
    )
    blob_client =container .get_blob_client (key )
    return f"{blob_client .url }?{sas_token }"

def _account_key_from_connection_string (conn_str :str )->str :
    parts =dict (p .split ("=",1 )for p in conn_str .split (";")if "="in p )
    return parts ["AccountKey"]
