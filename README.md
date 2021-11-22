# Multi-device-File-Transfer-App

Problem Statement and Solution- Transfering files between devices over a network has become a hassle as various applications either cap the transfer size or limit the size of files that can be transfered. It also comes with unwanted plugins and advertisements which make the application heavy and undesirable to use.
The solution is to develop an app that employs the common feature in all devices, the web. Instead of creating a specific application for file transfer which has proven to be a hassle, a simple and lite program that can run in the background which can transfer files using your browser can be created. This has been achieved at a small scale for upto 100 clients with simultaneous requests for different files with negligible drop in transfer speed (~6 MB/S) and WITHOUT THE NEED FOR INTERNET DATA.

The application is very light ~5.25 MB and once run is very simple to use providing quick response and flexibility.

Instructions-
  caveats:
    a) The application was developed on windows OS and hence the .exe file
    b) If you any other executable file relevant to your OS, download the .py file and use a python bundler of your choice.
    c) If you need to change the port number, change it to in the .py file and then use a python bundler.
    d) If you need to transfer a complete folder, zip it and then store it in the main folder.
1) Download the .exe file into a folder and run it.
2) Ensure your devices are on the same network/ connected to the same hotspot.
3) Enter the IP:PORT combination into the browser search box.
4) You can upload or download any file that you want to and from the main folder. You can also traverse through the various folders within the main folder.

The app can run in the backend without disturbing the user and the clients can access the server using any browser on any device running any OS.

*For security(yet to be implemented) reasons, create a separate directory for file transfers and change the port number if required. 

Bug Fixes (in progress)-
After uploading a file to the server, there is an error message. IGNORE IT.
