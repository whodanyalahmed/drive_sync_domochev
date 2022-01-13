from __future__ import print_function
import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
import io


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


# To list folders
def listfolders(service, filid, des):
    results = service.files().list(
        pageSize=1000, q="\'" + filid + "\'" + " in parents",
        fields="nextPageToken, files(id, name, mimeType)").execute()
    # logging.debug(folder)
    folder = results.get('files', [])
    for item in folder:
        if str(item['mimeType']) == str('application/vnd.google-apps.folder'):
            # print(item['mineType'])
            if not os.path.isdir(des+"/"+item['name']):
                os.mkdir(path=des+"/"+item['name'])
            print(item['name'])
            # LOOP un-till the files are found
            listfolders(service, item['id'], des+"/"+item['name'])
        else:
            try:

                downloadfiles(service, item['id'],
                              item['name'], item['mimeType'], des)
                print(item['name'])
            except Exception as e:
                print("info: cant download file")
                print(e)
    return folder


# To Download Files
def downloadfiles(service, dowid, name, mimeType, dfilespath):
    if mimeType == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType == 'application/vnd.google-apps.spreadsheet':
        try:
            request = service.files().export_media(fileId=dowid,
                                                   mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            print("Downloading file: " + name)
            fh = io.FileIO(dfilespath+"/" + name + '.xlsx', 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print('Download %d%%.' % int(status.progress() * 100))
            return fh
        except Exception as e:
            print('Error downloading file from Google Drive: %s' % e)
    else:

        request = service.files().get_media(fileId=dowid)
        print("Downloading file: " + name)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))
        with io.open(dfilespath + "/" + name, 'wb') as f:
            fh.seek(0)
            f.write(fh.read())


def CheckFolder(service, FileName):
    page_token = None
    # response = service.files().list(q="mimeType = 'application/vnd.google-apps.spreadsheet'",
    # response = service.files().list(q="mimeType = 'application/vnd.google-apps.folder'",
    #                                 spaces='drive',
    #                                 fields='nextPageToken, files(id, name)',
    #                                 pageToken=page_token).execute()
    response = service.files().list(pageSize=1000, q="mimeType='application/vnd.google-apps.folder' and trashed = false",
                                    spaces='drive', fields='nextPageToken, files(id, name, mimeType, parents, sharingUser)', pageToken=page_token).execute()
    items = response.get('files', [])
    #     # Process change
    #     print('Found file: %s (%s)' % (file.get('name'), file.get('id')))
    # page_token = response.get('nextPageToken', None)
    # if page_token is None:
    #     break
    # for i in items:
    #     print(i['name'])
    if not items:
        print('No files found.')
        return None
    else:
        # print('Files:')
        for item in items:
            # print(item['name'])
            if(item['name'] == FileName):
                print(FileName + " is already there")
                # print(item['name'])
                return item['id']


def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)  # credentials.json download from drive API
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)
    # Call the Drive v3 API
    foldername = input(
        "Enter folder name to sync(for complete drive type 'root'): ")
    #  path C:\Users\Daniyal\Documents
    path = input("Enter path to sync: ")
    full_folder_path = path+"/"+foldername
    # Enter The Downloadable folder ID From Shared Link
    Folder_id = CheckFolder(service, foldername)
    print(str(Folder_id) + " is the folder ID")
    if foldername == "root":

        results = service.files().list(
            pageSize=1000, q="'{}' in parents".format(foldername), fields="nextPageToken, files(id, name, mimeType)").execute()
    else:
        results = service.files().list(
            pageSize=1000, q="'{}' in parents".format(Folder_id), fields="nextPageToken, files(id, name, mimeType)").execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':

                if not os.path.isdir(full_folder_path):
                    os.mkdir(full_folder_path)
                bfolderpath = full_folder_path+"/"
                if not os.path.isdir(bfolderpath+item['name']):
                    os.mkdir(bfolderpath+item['name'])

                folderpath = bfolderpath + item['name']
                listfolders(service, item['id'], folderpath)
            else:
                if not os.path.isdir(full_folder_path):
                    os.mkdir(full_folder_path)
                bfolderpath = full_folder_path+"/"
                # if not os.path.isdir(bfolderpath + item['name']):
                #     os.mkdir(bfolderpath + item['name'])
                filepath = bfolderpath
                downloadfiles(
                    service, item['id'], item['name'], item['mimeType'], filepath)


if __name__ == '__main__':
    main()
