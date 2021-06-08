import tkinter
import tkinter as tk
from tkinter import *
from tkinter import font
from tkinter import messagebox, Scrollbar,Canvas
from tkinter import Menu, filedialog
from PIL import ImageTk, Image
from tkinter import ttk
from datetime import datetime
from datetime import timedelta
import random
from apiclient.discovery import build
import urllib.request
from tkinter import ttk
import webbrowser
import json
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle,os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import threading,time
from tkinter import simpledialog
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io,socket

root = tkinter.Tk()
WIDTH=900
HEIGHT=600
root.geometry(f"{WIDTH}x{HEIGHT}+100+50")
root.resizable(0,0)
root.title("Google Drive Content reader")

text_font = font.Font(family='Raleway', size=10, weight='bold')

credentials=None
service=None
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly','https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/drive.photos.readonly','https://www.googleapis.com/auth/drive.appdata',
          'https://www.googleapis.com/auth/drive.metadata']
connected=False

extension_mime = {'aac':'audio/aac','css':'text/css','csv':'text/csv','doc':'application/msword',
                  'docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                  'gz':'application/gzip','gif':'image/gif','htm':'text/html','html':'text/html',
                  'jpeg':'image/jpeg','jpg':'image/jpeg','mp3':'audio/mpeg','pdf':'application/pdf',
                  'rar':'application/vnd.rar','txt':'text/plain','png':'image/png','pptx':'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                  'ppt':'application/vnd.ms-powerpoint','avi':'video/x-msvideo','wav':'audio/wav','xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                  'xls':'application/vnd.ms-excel'}

search_mime = {'Audios':['audio/aac','audio/mpeg','audio/wav'],'MS Word':'application/msword',
                  'Images':['image/gif','image/jpeg','image/png'],'PDF':'application/pdf',
                  'Winrar/Zip':'application/vnd.rar','Text file':'text/plain',
                  'PPTS':'application/vnd.ms-powerpoint','Videos':'video/x-msvideo',
                  'Excel sheets':'application/vnd.ms-excel','Folders':'application/vnd.google-apps.folder'}
#['image/gif','image/jpeg','image/jpeg','image/png']
SITE_LIST = []
ID_LIST=[]
REFRESH = False
CURRENT_DIR='nil'
file_to_copy_move = {}
copy=False
move=False
def get_credentials():
    global credentials,service
    CLIENT_SECRET_FILE = 'client_secret.json'
    credentials = None
    
    if os.path.exists("token.pickle"):
        print("Loading credentials from file...")
        with open("token.pickle","rb") as token:
            credentials = pickle.load(token)
    
    # if there are no valid credentials available, then either refresh the token or log in
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("refereshing access token")
            credentials.refresh(Request())
        else:
            print("Fetching new tokens")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            credentials = flow.run_local_server(port=8080,prompt='consent',authorization_prompt_message='')
            
            with open('token.pickle','wb') as f:
                print("saving credentials for future use")
                pickle.dump(credentials,f)

    service = build('drive', 'v3', credentials=credentials)

def update_drive_usage():
    pass

count_of_teachers = 0


class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self,bg='#fff')
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)
        
        #canvas.grid(row=0,column=0)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class File_Item:
    def __init__(self,frame,fid,filename,mimeType,photoLink,modifiedTime,owners,ownerphoto):
        #print(fid,name,mimeType,photoLink,modifiedTime,owners,ownerphoto)
        self.frame = frame
        self.item_frame = Frame(self.frame,width=WIDTH-250,height= 100,bg='#fff',cursor='hand2')
        self.item_frame.bind('<Enter>',self.change_text)
        self.item_frame.bind('<Leave>',self.default_text)
        self.item_frame.bind('<Button-3>',self.open_menu)
        self.thumbnail = photoLink
        self.mimeType = mimeType
        self.status=0
        if self.mimeType == 'application/vnd.google-apps.folder':            
            self.item_frame.bind('<Button-1>',self.open_folder)
        self.fid = fid
        if self.mimeType != 'application/vnd.google-apps.folder':            
            self.download_user_image(self.thumbnail,'photo')
            self.file_photo = ImageTk.PhotoImage(Image.open(f"photo_{self.fid}.png").resize((100,100)))       
        else:
            self.file_photo = ImageTk.PhotoImage(Image.open(self.thumbnail).resize((100,100)))
        self.file_photo_label = Label(self.item_frame,width=100,height=100,image=self.file_photo,bg='#fff')
        self.file_photo_label.image = self.file_photo
        self.file_photo_label.bind('<Button-3>',self.open_menu)
        if self.mimeType == 'application/vnd.google-apps.folder':
            self.file_photo_label.bind('<Button-1>',self.open_folder)
        self.name = filename
        self.file_name = Label(self.item_frame,fg='#000',bg='#fff',text=self.name,font=('Raleway',14,'bold'))
        self.file_name.bind('<Button-3>',self.open_menu)        
        if self.mimeType == 'application/vnd.google-apps.folder':
            self.file_name.bind('<Button-1>',self.open_folder)
        self.modtime = modifiedTime.split('T')[0]
        self.date = Label(self.item_frame,fg='#000',bg='#fff',text='Modified Date: '+self.modtime,font=('Raleway',8,'bold'))
        self.owners = owners
        self.owner_label = Label(self.item_frame,fg='#000',bg='#fff',text='Owner: '+self.owners,font=('Raleway',8,'bold'))
        
        self.owner_photo = ownerphoto
        self.download_user_image(self.owner_photo,'owner')
        self.user_photo = ImageTk.PhotoImage(Image.open(f"owner_{self.fid}.png").resize((20,20)))   
        self.user_photo_label = Label(self.item_frame,width=20,height=20,image=self.user_photo,bg='#fff')
        self.user_photo_label.image = self.user_photo
        self.copy = False
        self.move = False
        self.display()
    def display(self):
        #self.item_frame.pack(side='left',expand=True)
        self.item_frame.pack(side='left')#grid(row=0,column=0) expand=True,fill='both'
        self.file_photo_label.grid(row=0,column=0,rowspan=2)
        self.file_name.grid(row=0,column=1,columnspan=3)
        self.date.grid(row=1,column=1,padx=10)
        self.owner_label.grid(row=1,column=2,padx=10)        
        self.user_photo_label.grid(row=1,column=3)
    
    def update_progress(self):
        print('calling',self.status)
        if self.status != 0:
            print(self.status.progress())
            download_percent.config(text='{0} %'.format(self.status.progress()*100))
        download_percent.after(1000,self.update_progress)
    def download(self):
        request = service.files().get_media(fileId=self.fid)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fd=fh, request=request)
        done=False        
        #self.update_progress()
        while not done:                         
            self.status,done = downloader.next_chunk()
            #download_percent.config(text='{0} %'.format(self.status.progress()*100))

        fh.seek(0)
        with open(os.path.join('./downloads',self.name),'wb') as f:
            f.write(fh.read())
            f.close()
        print('DONE')
            
    def download_file(self):
        print('DOWNLOADED')
        x = threading.Thread(target=self.download)
        x.start()
        
    def open_menu(self,event): 
        global copy,move
        print('called')          
        self.popup_menu = tkinter.Menu(self.item_frame,tearoff = 0)
        self.popup_menu.add_command(label = "Download",command = lambda:self.download_file())
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label = "Rename",command = lambda:print('hi'))
        self.popup_menu.add_command(label = "Remove",command = lambda:self.remove_file())
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label = "Copy",command = lambda:self.copy_files_folder())
        self.popup_menu.add_command(label = "Move",command = lambda:self.move_files_folder())
        if copy or move:
            self.popup_menu.add_command(label = "Paste",command = lambda:self.paste_File())
        try:
            self.popup_menu.tk_popup(event.x_root,event.y_root)
        finally:
            self.popup_menu.grab_release()
    
    def remove_file(self):       
        global REFRESH 
        service.files().delete(fileId=self.fid).execute()
        messagebox.showinfo("Information","File Removed Permanently")
        REFRESH = True
        create_right_frame_content()
            
    def copy_files_folder(self):
        global file_to_copy_move,copy,move
        file_to_copy_move['id'] = self.fid
        file_to_copy_move['name'] = self.name
        copy = True
        move = False
        
    def move_files_folder(self):
        global file_to_copy_move,copy,move
        file_to_copy_move['id'] = self.fid
        file_to_copy_move['name'] = self.name
        copy = False
        move = True
    
    def paste_File(self):
        global file_to_copy_move,copy,move
        if copy:
            folder_to_paste = self.fid or CURRENT_DIR
            file_metadata = {'name':file_to_copy_move['name'],'parents':[folder_to_paste]}
            service.files().copy(fileId=file_to_copy_move['id'],body=file_metadata).execute()
            copy = False
            move = False
        if move:
            folder_to_move = self.fid or CURRENT_DIR
            service.files().update(fileId=file_to_copy_move['id'],addParents=folder_to_move).execute()
            copy = False
            move = False
            
    def open_folder(self,event):
        global CURRENT_DIR
        CURRENT_DIR = self.fid
        #print('HEREEEE')
        #x = threading.Thread(target=create_right_frame_content,args=(self.fid,self.name))
        #x.start()
        create_right_frame_content(self.fid,self.name)
    def change_text(self,event):
        self.file_name.config(font=('Raleway',14,'bold','underline'))
        
    def default_text(self,event):
        self.file_name.config(font=('Raleway',14,'bold'))

    def download_user_image(self,URL,text):
        with urllib.request.urlopen(URL) as url:
            with open(f'{text}_{self.fid}.png','wb') as f:
                f.write(url.read())   
        

def insert_record_treeview(data):
    global my_tree,count_of_teachers
    my_tree.tag_configure('oddrow', background="white")
    my_tree.tag_configure('evenrow', background="lightblue")
         
    b = tkinter.Button(right_frame,text='Button 1',width=50,height=30)
    b.pack()
    #print(data)
    for record in data:
        if count_of_teachers % 2 == 0:
            my_tree.insert(parent='', index='end', iid=count_of_teachers, text="", values=(record[0], record[1], record[2],b,"xyzwrspqr"), tags=('evenrow',))
        else:
        	my_tree.insert(parent='', index='end', iid=count_of_teachers, text="", values=(record[0], record[1], record[2],b,"xyzwrspqr"), tags=('oddrow',))
        count_of_teachers += 1

def download_photo(URL):
    with urllib.request.urlopen(URL) as url:
        with open('profile_photo.png','wb') as f:
            f.write(url.read())   
    
    user_photo = ImageTk.PhotoImage(Image.open("profile_photo.png").resize((70,50)))
    user_label.config(image=user_photo)
    user_label.image = user_photo

class SiteMap:    
    def __init__(self,frame,fid='nil',fname='My Drive'):
        self.frame = frame
        self.fid = fid
        self.fname = fname
        self.filename = Label(self.frame,text=self.fname,fg='#fcfcfa',font=('Raleway',10,'bold','underline'),bg='#4c915e',cursor='hand2')
        self.filename.bind('<Button-1>',self.refresh_drive)
        self.arrow = Label(self.frame,text='>',fg='#fcfcfa',font=('Raleway',10,'bold'),bg='#4c915e')
        self.display()                   
    def display(self):
        self.filename.pack(side='left',padx=(5,5))
        self.arrow.pack(side='left',padx=(5,5))
        
    def refresh_drive(self,event): 
        global REFRESH,CURRENT_DIR
        CURRENT_DIR = self.fid
        REFRESH = True
        index = ID_LIST.index(self.fid)
        ID_COPY = ID_LIST.copy()
        for i in range(index+1,len(ID_COPY)):
            SITE_LIST[i].filename.destroy()
            SITE_LIST[i].arrow.destroy()
            ID_LIST.pop(i)
            SITE_LIST.pop(i)
        
        if self.fid == 'nil':
            x = threading.Thread(target=create_right_frame_content)
            x.start()
            #create_right_frame_content()
        else:
            x = threading.Thread(target=create_right_frame_content,args=(self.fid,self.fname))
            x.start()
            #create_right_frame_content(self.fid,self.fname)
    
def create_right_frame_content(fid='nil',fname='My Drive'):
    global REFRESH
    for a in right_frame.winfo_children():
        a.destroy()
    scroll_f = ScrollableFrame(right_frame)
    scroll_f.pack(expand=True,fill='both')
    #scroll_f.grid(row=0,column=0)
    files_res=None
    if fid == 'nil':          #MY DRIVE ID 0AMtLSW2vDFAjUk9PVA
        files_req = service.files().list(q=f"'0AMtLSW2vDFAjUk9PVA' in parents",spaces='drive',fields='files(id,name,mimeType,iconLink,thumbnailLink,modifiedTime,owners,parents)')
        files_res = files_req.execute()
        #print(files_res)
    else:
        files_req = service.files().list(q=f"'{fid}' in parents",fields='files(id,name,mimeType,iconLink,thumbnailLink,modifiedTime,owners,parents)')
        files_res = files_req.execute()
        #print(folder_res)
    if not REFRESH:
        site = SiteMap(top_frame,fid,fname)
        SITE_LIST.append(site)
        ID_LIST.append(fid)

    REFRESH = False
    
    for index,files in enumerate(files_res['files']):
        f1 = Frame(scroll_f.scrollable_frame,width=WIDTH-250,height=100,bg='#fff')
        f1.pack(padx=10,pady=10)
        f1.pack_propagate(0)
        #f1.grid(row=rowno,column=colno,padx=20,pady=10)
        if files['mimeType'] == 'application/vnd.google-apps.folder':
            File_Item(f1,files['id'],files['name'],files['mimeType'],'folder.png',files['modifiedTime'],files['owners'][0]['displayName'],files['owners'][0]['photoLink'])    
        else:
            File_Item(f1,files['id'],files['name'],files['mimeType'],files['thumbnailLink'],files['modifiedTime'],files['owners'][0]['displayName'],files['owners'][0]['photoLink'])

def check_internet():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        sock = socket.create_connection(("www.google.com", 80))
        if sock is not None:
            print('Clossing socket')
            sock.close            
        return True
    except OSError:
        pass
    return False

def fetch_user_data(event):
    global connected,CURRENT_DIR
        
    result  = check_internet()
    if result:
        pass
    else:
        messagebox.showinfo("Information","Please Check your Internet connection first")
        return
    
    if not credentials or credentials.expired:
        get_credentials()
    req=service.about().get(fields='*')
    res = req.execute()
    #print(res)
    user_emailid.config(text=res['user']['emailAddress'])
    #download_photo(res['user']['photoLink'])
    x = threading.Thread(target=download_photo, args=(res['user']['photoLink'],))
    x.start()
    usage_size = (int(res['storageQuota']['usage']) / 1024) / 1024
    usage_size = round(usage_size,1)
    storage_quota_label.config(text=f'Disk usage: {usage_size} MB of 15 GB')
    
    #print(res['storageQuota']['limit'])
    #https://www.googleapis.com/drive/v3/files?corpora=domain&fields=%2A&alt=json
    #files_req = service.files().list(q="mimeType='application/vnd.google-apps.folder'",fields='files(id, name)',spaces='drive')    
    #x = threading.Thread(target=create_right_frame_content)
    #x.start()
    CURRENT_DIR='nil'
    create_right_frame_content()    
    connected = True
    #drive_req = service.drives().list() 
    #drive_res= drive_req.execute()
    #print(drive_res)
    
#    names_list=[]
#    owners_name=[]
#    owners_address = []
#    for file in files_res['files']:
#        names_list.append(file['name'])
#        owners_name.append(file['owners'][0]['displayName'])
#        owners_address.append(file['owners'][0]['emailAddress'])
#    #print(files_res)
#    print('file names',names_list)
#    print('OWNERS',owners_name)
#    print('EMAIL',owners_address)
    
        
    #create_tree_view()
def change_user_account(event):
    os.remove("client_secret.json") 
    fetch_user_data()    

def new_folder():
    if connected:
        folder_name = ''
        answer = simpledialog.askstring("Input", "Folder Name",parent=root)
        if answer is not None:
            #print("Your first name is ", answer)
            if answer == '':
                folder_name = 'New Folder'
            else:
                folder_name = answer
        else:
            return
        if CURRENT_DIR == 'nil':
            file_metadata = {'name':folder_name,'mimeType':'application/vnd.google-apps.folder'}
        else:
            file_metadata = {'name':folder_name,'parents':[CURRENT_DIR],'mimeType':'application/vnd.google-apps.folder'}
        service.files().create(body=file_metadata).execute()
        x = threading.Thread(target=create_right_frame_content)
        x.start()
    else:
        messagebox.showinfo("Information","Please Click connect first")

def upload_folder():
    if connected:
        pass
    else:
        messagebox.showinfo("Information","Please Click connect first")

def uploader():
    if connected:
        my_filetypes = [('all files', '.*'), ('text files', '.txt')]
        answer = filedialog.askopenfilename(parent=root,
                                    initialdir=os.getcwd(),
                                    title="Please select a file:",
                                    filetypes=my_filetypes)
        if answer is not None:
            file_name = answer.split('/')[-1]
            extension = (answer.split('/')[-1]).split('.')[-1]
            mime_type = extension_mime[extension]
            #print(extension,mime_type)
            if CURRENT_DIR == 'nil':
                file_metadata = {'name':file_name}
            else:
                file_metadata = {'name':file_name,'parents':[CURRENT_DIR]}
            media = MediaFileUpload(answer,mimetype=mime_type)
            service.files().create(body=file_metadata,media_body=media).execute()
            create_right_frame_content()
            messagebox.showinfo("Information","Upload Completed")
    else:
        messagebox.showinfo("Information","Please Click connect first")
        
def upload_file():
    x = threading.Thread(target=uploader)
    x.start()
        
def open_menu(event):        
    popup_menu = tkinter.Menu(left_frame,tearoff = 0)
    popup_menu.add_command(label = "New Folder",command = lambda:new_folder())
    popup_menu.add_separator()
    popup_menu.add_command(label = "Upload File",command = lambda:upload_file())
    popup_menu.add_command(label = "Upload Folder",command = lambda:upload_folder())
    try:
        popup_menu.tk_popup(event.x_root,event.y_root)
    finally:
        popup_menu.grab_release()

def paste_File():
    global file_to_copy_move,copy,move
    if copy:
        folder_to_paste = CURRENT_DIR
        file_metadata = {'name':file_to_copy_move['name'],'parents':[folder_to_paste]}
        service.files().copy(fileId=file_to_copy_move['id'],body=file_metadata).execute()
        copy = False
    if move:
        folder_to_move = CURRENT_DIR
        service.files().update(fileId=file_to_copy_move['id'],addParents=folder_to_move).execute()
        move = True
        
def open_right_frame_menu(event): 
    global copy,move        
    popup_menu = tkinter.Menu(right_frame,tearoff = 0)
    popup_menu.add_command(label = "Paste",command = lambda:paste_File())
    try:
        popup_menu.tk_popup(event.x_root,event.y_root)
    finally:
        popup_menu.grab_release()
    
def display_searched_files():
    mime = search_mime[filetype.get()]
    for a in right_frame.winfo_children():
        a.destroy()
    scroll_f1 = ScrollableFrame(right_frame)
    scroll_f1.pack(expand=True,fill='both')
    if type(mime) == list:
        for m in mime:
            response = service.files().list(q=f"mimeType='{m}'",fields='files(id,name,mimeType,iconLink,thumbnailLink,modifiedTime,owners,parents)',spaces='drive').execute()
            for files in response.get('files', []):
                f11 = Frame(scroll_f1.scrollable_frame,width=WIDTH-250,height=100,bg='#fff')
                f11.pack(padx=10,pady=10)
                f11.pack_propagate(0)
                #print ('Found file: %s (%s)' % (file.get('name'), file.get('id')))
                File_Item(f11,files['id'],files['name'],files['mimeType'],files['thumbnailLink'],files['modifiedTime'],files['owners'][0]['displayName'],files['owners'][0]['photoLink'])

    else:
        response = service.files().list(q=f"mimeType='{mime}'",fields='files(id,name,mimeType,iconLink,thumbnailLink,modifiedTime,owners,parents)',spaces='drive').execute()
        for files in response.get('files', []):
            #print ('Found file: %s (%s)' % (file.get('name'), file.get('id')))
            f11 = Frame(scroll_f1.scrollable_frame,width=WIDTH-250,height=100,bg='#fff')
            f11.pack(padx=10,pady=10)
            f11.pack_propagate(0)
            #print ('Found file: %s (%s)' % (file.get('name'), file.get('id')))
            File_Item(f11,files['id'],files['name'],files['mimeType'],files['thumbnailLink'],files['modifiedTime'],files['owners'][0]['displayName'],files['owners'][0]['photoLink'])

def search_drive(event):
    print(filetype.get())
    print(search_box.get())
    x = threading.Thread(target=display_searched_files)
    x.start()
                        
left_frame = Frame(root,width=220,height=600,bg='#4c915e')
left_frame.pack(side='left')
left_frame.pack_propagate(0)

drive_photo = ImageTk.PhotoImage(Image.open("gdrive logo.png").resize((70,50)))  # PIL solution
drive_label = Label(left_frame,width=70, height=50,image=drive_photo,bg='#4c915e',cursor='hand2')  #relief=RAISED 
drive_label.pack(pady=(15,0))
#label.bind('<Button-1>',open_youtube)

user_photo = ImageTk.PhotoImage(Image.open("userlogo.png").resize((70,50)))  # PIL solution
user_label = Label(left_frame,width=70, height=50,image=user_photo,bg='#4c915e',cursor='hand2')  #relief=RAISED 
user_label.pack(pady=(15,0))

email_frame = Frame(left_frame,width=220,height=600,bg='#4c915e')
email_frame.pack()
user_emailid = Label(email_frame,text='Email: NA',font=text_font,bg='#4c915e',fg="#fcfcfa")
user_emailid.pack(side='left',pady=(15,0),fill='x',expand=True)
change_user_photo = ImageTk.PhotoImage(Image.open("edit.png").resize((20,20)))
change_user_label = Label(email_frame,width=20, height=20,image=change_user_photo,bg='#4c915e',cursor='hand2')
change_user_label.pack(side='left',pady=(15,0),fill='x',expand=True)
change_user_label.bind('<Button-1>',change_user_account)
               
storage_quota_label = Label(left_frame,text=f'Disk usage: NA',bg='#4c915e',fg="#fcfcfa")
storage_quota_label.pack()

search_frame = Frame(left_frame,width=180,height=600,bg='#4c915e')
search_frame.pack(pady=50)
search_frame.pack_propagate(0)
n = tk.StringVar()
filetype = ttk.Combobox(search_frame, width = 100, textvariable = n)
filetype['values'] = ('Select File type', 
                          'Images',
                          'PDF',
                          'Videos',
                          'Audios',
                          'PPTS',
                          'Excel sheets',
                          'Folders',
                          'Text file',
                          'Winrar/Zip')
filetype.current(0)
filetype.pack(pady=10)
search_box = Entry(search_frame,width=100,font=('Raleway',8))
search_box.pack(pady=5)
go_but = Button(search_frame,text='Search',font=('Raleway',8,'bold'),width=100,bg='#207fc7',fg='#fff',cursor='hand2')                
go_but.bind('<Button-1>',search_drive)
go_but.pack(pady=5)

download_percent = Label(left_frame,text='',bg='#4c915e',fg="#fcfcfa",font=('Raleway',14,'bold'))
download_percent.pack(pady=(15,0),padx=(20,0))

add_photo = ImageTk.PhotoImage(Image.open("add.png").resize((60,60))) 
add_but_label = Label(left_frame,image=add_photo,height=60,width=60,bg='#4c915e',cursor='hand2')
add_but_label.pack(side='bottom',padx=(150,0),pady=(0,20))
add_but_label.bind('<Button-1>',open_menu)


top_frame = Frame(root,width=WIDTH-220,height=80,bg='#4c915e')
top_frame.pack(side='top',expand=True,fill='x')
top_frame.pack_propagate(0)

#site = SiteMap(top_frame)
#SITE_LIST.append(site)
#ID_LIST.append('nil')
                      
right_frame = Frame(root,width=WIDTH-220,height=520,bg='#fff')
right_frame.pack(side='bottom',expand=True,fill='both')
right_frame.pack_propagate(0)
right_frame.bind('<Button-3>',open_right_frame_menu)

connect_but = Button(right_frame,text='Connect',font=text_font,bg='#4c915e',fg="#fcfcfa") 
connect_but.pack(pady=(250,0))   
connect_but.bind('<Button-1>',fetch_user_data)       

root.mainloop()