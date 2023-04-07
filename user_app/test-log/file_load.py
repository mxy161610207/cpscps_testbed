import tkinter as tk
import socket
import json
from tkinter import filedialog,messagebox

class FileTransferGUI:
    def __init__(self, master):
        self.master = master
        master.title("File Transfer")

        # create a label widget for the local file path
        self.local_file_label = tk.Label(master, text="文件目录:")
        self.local_file_label.grid(row=0, column=0)

        # create an entry widget for the local file path
        self.local_file_entry = tk.Entry(master)
        self.local_file_entry.grid(row=0, column=1)

        # create a button widget to browse for the local file
        self.browse_button = tk.Button(master, text="选择文件", command=self.browse_file)
        self.browse_button.grid(row=0, column=2)

        # create a label widget for the remote host
        self.remote_host_label = tk.Label(master, text="Remote host:")
        self.remote_host_label.grid(row=1, column=0)

        # create an entry widget for the remote host
        self.remote_host_entry = tk.Entry(master)
        self.remote_host_entry.insert(0, "127.0.0.1")
        self.remote_host_entry.grid(row=1, column=1)

        # create a label widget for the remote port
        self.remote_port_label = tk.Label(master, text="Remote port:")
        self.remote_port_label.grid(row=2, column=0)

        # create an entry widget for the remote port
        self.remote_port_entry = tk.Entry(master)
        self.remote_port_entry.insert(0, "1998")
        self.remote_port_entry.grid(row=2, column=1)

        # create a button widget to transfer the file
        self.transfer_button = tk.Button(master, text="文件传输", command=self.transfer_file)
        self.transfer_button.grid(row=3, column=1)

        # create a button widget to print the file
        self.print_button = tk.Button(self.master, text="文件打印", command=self.create_print_json)
        self.print_button.grid(row=4, column=1)

        self.print_button = tk.Button(self.master, text="关闭服务器", command=self.shutdown)
        self.print_button.grid(row=5, column=1)

    def browse_file(self):
        # open a file dialog to select a file
        file_path = filedialog.askopenfilename(initialdir=".")
        # set the file path entry to the selected file path
        self.local_file_entry.delete(0, tk.END)
        self.local_file_entry.insert(0, file_path)

    def transfer_file(self,act="file"):
        # get the local file path and remote host and port from the GUI widgets
        local_file_path = self.local_file_entry.get()
        remote_host = self.remote_host_entry.get()
        remote_port = int(self.remote_port_entry.get())

        # open the local file and read its contents
        with open(local_file_path, 'rb') as f:
            file_contents = f.read()

        # create a socket and connect to the remote host and port
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = "file"+" "+str(len(file_contents))
        s.sendto(data.encode('utf-8'), (remote_host, remote_port))
        s.sendto(file_contents, (remote_host, remote_port))

        # close the socket
        s.close()

        # show a message box to indicate success
        messagebox.showinfo("File Transfer", "文件传输成功")

    def create_print_json(self):
        # get the local file path and remote host and port from the GUI widgets
        local_file_path = self.local_file_entry.get()
        remote_host = self.remote_host_entry.get()
        remote_port = int(self.remote_port_entry.get())

        # open the local file and read its contents
        with open(local_file_path, 'rb') as f:
            file_contents = f.read()

        # create a socket and connect to the remote host and port
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = "print"+" "+str(len(file_contents))
        s.sendto(data.encode('utf-8'), (remote_host, remote_port))
        s.sendto(file_contents, (remote_host, remote_port))

        # close the socket
        s.close()

        # show a message box to indicate success
        messagebox.showinfo("File Print", "文件打印成功")

    def shutdown(self):
        # get the local file path and remote host and port from the GUI widgets
        remote_host = self.remote_host_entry.get()
        remote_port = int(self.remote_port_entry.get())


        # create a socket and connect to the remote host and port
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = "end 0"
        s.sendto(data.encode('utf-8'), (remote_host, remote_port))

        # close the socket
        s.close()

        # show a message box to indicate success
        messagebox.showinfo("shutdown", "远程服务器关闭")


root = tk.Tk()
gui = FileTransferGUI(root)
root.mainloop()
