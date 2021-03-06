from boxpython import BoxAuthenticateFlow, BoxSession, BoxError
from request import BoxRestRequest
from google_vision import GoogleVision
import keyring
import requests

#Tokens Changed Callback
def tokens_changed(refresh_token, access_token):
    keyring.set_password("system", "BOX_ACCESS_TOKEN", access_token),
    keyring.set_password("system", "BOX_REFRESH_TOKEN", refresh_token)

#Upload File
def upload(file_name, folder_id, file_location):
    response = box.upload_file(file_name, folder_id, file_location)
    print('File ID: %s' % response['entries'][0]['id'])
    return response['entries'][0]['id']

#Download File
def download(file_id, file_location):
    response = box.download_file(file_id, file_location)
    print("Success")

#Delete File
def delete(file_id):
    response = box.delete_file(file_id)
    print("Success")

#Helper method to manage request to Google Vision from send_to_vision
def request(method, command):
    data = None
    querystring = None
    files = None
    headers = None
    stream = None
    json_data = True
    if files or (data and isinstance(data, MultipartUploadWrapper)):
        url_prefix = BoxRestRequest.API_UPLOAD_PREFIX
    else:
        url_prefix = BoxRestRequest.API_PREFIX

    if headers is None:
        headers = {}
    headers['Authorization'] = 'Bearer %s' % keyring.get_password("system", "BOX_ACCESS_TOKEN")

    url = '%s/%s' % (url_prefix, command)

    if json_data and data is not None:
        data = json.dumps(data)

    kwargs = { 'headers' : headers }
    if data is not None: kwargs['data'] = data
    if querystring is not None: kwargs['params'] = querystring
    if files is not None: kwargs['files'] = files
    if stream is not None: kwargs['stream'] = stream
    #if self.timeout is not None: kwargs['timeout'] = self.timeout

    return requests.request(method=method, url=url, **kwargs)


#Send to Google Vision
def send_to_vision(file_id, chunk_size=1024*1024*1):
    req = request("GET", "files/%s/content" % (file_id, ))
    total = -1
    image_content = ''
    if hasattr(req, 'headers'):
        lower_headers = {k.lower():v for k,v in req.headers.items()}
        if 'content-length' in lower_headers:
            total = lower_headers['content-length']

    transferred = 0
    for chunk in req.iter_content(chunk_size=chunk_size):
        if chunk:
            #fp.write(chunk)
            #fp.flush()
            image_content += chunk
            transferred += len(chunk)

    #print(image)
    gv = GoogleVision()
    gv.vision_from_data(image_content)

#----------------------------------------------------------------------------------------------
# Access a BoxSession, upload file to box, send file to Google Vision, and delete file from Box
#----------------------------------------------------------------------------------------------

# Generate BoxAuthenticationFlow
flow = BoxAuthenticateFlow(keyring.get_password("system", "BOX_CLIENT_ID"), keyring.get_password("system", "BOX_CLIENT_SECRET"))
flow.get_authorization_url()
access_token = keyring.get_password("system", "BOX_ACCESS_TOKEN")
refresh_token = keyring.get_password("system", "BOX_REFRESH_TOKEN")

'''
#Uncomment this to get a new access and refresh token from a code
access_token, refresh_token = flow.get_access_tokens('P6jKDBZXFYGuGoAkxLTlaAxmxwv3e0cD')
'''

# Generate BoxSession
box = BoxSession(keyring.get_password("system", "BOX_CLIENT_ID"), keyring.get_password("system", "BOX_CLIENT_SECRET"), refresh_token, access_token, tokens_changed)

# Uplaod file to Box
new_file_id = upload('obama.jpeg', 0, 'obama.jpeg')
# Send file to Google Vision
send_to_vision(new_file_id)
# Delete file from Google Vision
delete(new_file_id)
