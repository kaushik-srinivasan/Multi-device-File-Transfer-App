import os
import random
import posixpath
import http.server
import urllib.parse
import cgi
import shutil
import mimetypes
import re
import sys
import ssl
import time, threading, socket, socketserver
from socketserver import ThreadingMixIn
import threading
from io import BytesIO

class ThreadingSimpleServer(ThreadingMixIn, http.server.HTTPServer):
    pass

class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()

    def do_POST(self):
        """Serve a POST request."""
        r, info = self.deal_post_data()
        print(r, info, "by: ", self.client_address)
        #f = StringIO()
        f = BytesIO()
        f.write(b'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write(b"<html>\n<title>Upload Result Page</title>\n")
        f.write(b"<body>\n<h2>Upload Result Page</h2>\n")
        f.write(b"<hr>\n")
        if r:
            f.write(b"<strong>Success:</strong>")
        else:
            f.write(b"<strong>Failed:</strong>")
        #f.write(info)
        f.write(info.encode())
        f.write(("<br><a href=\"%s\">back</a>" % self.headers['referer']).encode())
        f.write(b"...here...</a>.</small></body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        if f:
            self.copyfile(f, self.wfile)
            f.close()
        
    def deal_post_data(self):
        uploaded_files = []
        boundary = self.headers['content-type'].split("=")[1].encode()
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        #########################################################
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode())
            if not fn:
                return (False, "Can't find out file name...")
            path = self.translate_path(self.path)
            fn = os.path.join(path, fn[0])
            line = self.rfile.readline()
            remainbytes -= len(line)
            line = self.rfile.readline()
            remainbytes -= len(line)
            try:
                out = open(fn, 'wb')
            except IOError:
                return (False, "No file chosen...")
            else:
                with out:
                    preline = self.rfile.readline()
                    remainbytes -= len(preline)
                    while remainbytes > 0:
                        line = self.rfile.readline()
                        remainbytes -= len(line)
                        if boundary in line:
                            preline = preline[0:-1]
                            if preline.endswith(b'\r'):
                                preline = preline[0:-1]
                            out.write(preline)
                            uploaded_files.append(fn)
                            break
                #return (True, "File '%s' upload success!" % fn)
                        else:
                            out.write(preline)
                            preline = line
        return (True, "File '%s' upload success!" % ",".join(uploaded_files))
        #return (False, "Unexpect Ends of data.")

    def send_head(self):
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def list_directory(self, path):
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        #f = StringIO()
        f = BytesIO()
        displaypath = cgi.escape(urllib.parse.unquote(self.path))
        f.write(b'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        #f.write(("<html>\n<title>FIRE SHARE-WebShare</title>\n").encode())
        f.write(b"<html>\n<title>FIRE SHARE-WebShare</title>\n")
        #f.write(("<body>\n<h1 align=center style=\"font-family:Courier; color:black;\">FIRE SHARE-WebShare</h1>\n").encode())
        f.write(b"<body>\n<h1 align=center style=\"font-family:Courier; color:black;\">FIRE SHARE-WebShare</h1>\n")
        f.write(b"<hr>\n")
        #f.write(("<h2 align=left style=\"font-family:Courier; color:black; font-size: 20px;\">SHARED FILES DIRECTORY</h2>\n").encode())
        f.write(b"<h2 align=left style=\"font-family:Courier; color:black; font-size: 20px;\">SHARED FILES DIRECTORY</h2>\n")
        f.write(b"<hr>\n")
        f.write(b"<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
        f.write(b"<br><br>")
        f.write(b"<div><input name=\"file\" type=\"file\" style=\"font-size: 20px\" multiple/></div>")
        f.write(b"<br><br>")
        #####3 it is there
        #f.write(b"<input type=\"image\" src=\"data:image/jpeg;base64,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\" alt=\"Submit form\" width=\"100\"/></form>\n")
        f.write(("<input type=\"image\" src=\"content.jpg\" alt=\"Submit form\" width=\"100\"/></form>\n").encode())
        '''f.write(b"<button type=\"submit\">")
        f.write(b"<img src=\"data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBw8QEBUSEA8TFhISEhYQEhIYDRcXFhsWFRUXFh4XFxYYHCgiGBolGxYZIjIhJSkrMDEvGB81OT8sNyg5LysBCgoKDg0OGxAQGzAmICU1LSstLSsrLS0tKzUrLTMtLSsvLzArLS0tLS0tLS0tLy0tLS0tLS0tLS0tLS0tLS0tLf/AABEIAOIA3wMBEQACEQEDEQH/xAAcAAEAAgIDAQAAAAAAAAAAAAAABQcEBgIDCAH/xABOEAABBAABBAoMCwcDBQEAAAABAAIDEQQFBhIhBxMVMUFRUmFxkRQiMjRTVYGUorHR0xckNXJzdIKhssHCI0Jis8PS8DNUo0NjkpPhNv/EABoBAQACAwEAAAAAAAAAAAAAAAADBAEFBgL/xAA5EQEAAQICBgcHBAIBBQAAAAAAAQIDBBEFEhMxUXEUITIzQWHBNFJygZGx0SI1ofBC4SMGFSRE8f/aAAwDAQACEQMRAD8AvFAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQCUGO/GxDfePIb9S8TXTHilizcnwcd0YeX6J9ixtKeLPR7nA3Rh5fon2JtKeJ0e5wN0YeX6J9ibSnidHucDdGHl+ifYm0p4nR7nA3Rh5fon2JtKeJ0e5wN0YeX6J9ibSnidHucDdGHl+ifYm0p4nR7nA3Rh5fon2JtKeJ0e5wN0YeX6J9ibSnidHucDdGHl+ifYs7SnidHucDdGHl+ifYsbWnidHucDdGHl+ifYm1p4nR7nA3Rh5fon2JtaeJ0e5wN0YeX9x9ibWjidHucHzdGHl/cfYm1o4s9HucH0ZRh5Y6j7E2tPFjo9zg745mu7lwPQbXuKoncjqoqp3w5rLyICAgICAgII/KOVGRAiwXAWbOodJUVd2KVmxhqrnX4NKyrndZIZ2/OdTPI3h+5VKrsy3VnARTHX1fdBy5dxLv+pXM1oH/ANUetK5GHtx4OrdfE+Gd1prS9bC3wN18T4Z3WmtJsLfA3XxPhndaa0mwt8DdfE+Gd1prSbC3wN18T4Z3WmtJsLfA3XxPhndaa0mwt8DdfE+Gd1prSbC3wN18T4Z3Wmcmxt8DdbE+Gd1rGcmxt8DdbEeGd1pnJsbfA3WxHhndaZybG3wN1sR4Z3Wmcmxt8DdbEeGd1rOcmxt8DdbEeGd1rGcmxt8DdXEeGd1pnJsbfAGV8QP+s77j6ws60mxt8GZhc45mntwHc47V3WNX3LMVyirwtEx1NuyNnU1+onSHCD3Y/uCsUX58WrxGj8uunq+zaYZWvaHNNg7xVqJiYzhqaqZpnKd7msvIgICAgjMt5SELKB7ZwOviA33KK7c1YW8Lh9rVnO6P7kq/K+VXTOoE6AOocZ4yqEzm6W1ZiiPNG2vKYtAtAtAtAtAtAtAtAtAtAtAtAtAtAtAtAtAtByjkLSC00RvFZYmM+qW55q5xaJp51ahIP1hTWrurPXuavG4PXjON/h+G/g3vK+559QEBAQVfnhlUyONHU80PmN3uv2rXXa9ac3UYOxs6Ij+5tXtRLxaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaDuwuILHh3X0LLzMZwtPNHKYli2ou7eMDVxsO8Rx1vdXGr9irOnLg5rSNnZ3c43T1/lPqZQEBBiZVl0IJXDfEbiOnRK81zlTMpsPTrXaY84U3lWS5OgAfn+a1kuupjKGJaw9FoFoFoFoFoFoFoFoA172/vAIwszNbNCKOHSxUTXyyUS1zQQwcDRz8Z8nAr1qxER+qOtz2M0hXVXlanKI4eLXc881zhjt0IJgcdY39An9J4DwbyhvWdXrjcv4DHbWNSvtff8A21W1XbMtAtAtAtAtAtAtAtAtBL5IywcNi8FIT2skwwcnzZxoj/kbGfIrWFn9Uw1Ol6P+Kmrz+8f6XGrjnxAQR2cR+KTfRO9Sju9iVnB9/RzhTONdbz5PUFrXWum0C0C0C0C0C0C0C0C0G+7H+bd1i5m88DSP+Qj1dfErdi1/lPyaTSWM32aPn+Pz9FgK20jhLE17S1wBa4FrgRYIPAQkxmzEzE5wqbO/Nx2Ck0m2YHntHck7+g4+o8I6Fr7trUnq3OmwOMi/TlPaj+fNr1qFfLQLQLQLQLQLQLQLQRudeJMeGY9vdRytkb0s0nD7wrGF7bXaXj/xo5x6vR6vOaEBBGZzH4nP9E71KO72JWsD7RRzhS2Id2x/zgWtdbVvddowWgWgWgWgWgWgWg2bMnNw4uTbJB+wjPbfxu39Ac3H1cOqeza15znc1+Pxmxp1ae1P8ef4Wy0ACgKA1AK+5l9QEGPj8HHPG6KVukx4oj8xxEb9rFVMVRlL3buVW6oqpnrhTmceRZMFNtb9bTbo313Tf7hwj2rXXLc0Tk6nC4mm/RrRv8YRVqNaLQLQLQLQLQLQLQRGeZ+J/a/S5WMN255KGl/ZY5x6vS6vOYEBBF50d5T/AEL/AFKO72JW8B7Tb5wpSY9sVrYdbX2nXaPJaBaBaBaBaBaCTzeyNJjZxEzU3upH1qa3j6eABe7dE1zkr4nEU2KNaflHFdGAwccEbYom0xgoD8zxknXa2VNMUxlDlLlyq5VNVW+WQsvAgICCOy9keLGQmKTpY+tbXcDh7OELxXRFcZSmw9+qzXr0/wD1TGVMBLhpXRStpzT5COBzTwgrXVUzTOUurs3qbtEV07mJa8pS0C0C0C0C0C0ERnifif2v0uU+F7yeSjpf2WOcer00r7lxAQRWdXeWI+hf6lHe7EreA9pt84UjMe2K1sbnXXO1LhaPBaBaBaBaBaDuweGfNI2ONuk950Wjn/IcNrMRMzlDxXXTRTNVW6F1Zs5DZgoBG3W89tK+u6d7BvALY27cURk5XFYmq/XrTu8ISykVhAQEBAQQGd+bjcbFqoTMBMT/ANDv4T9x19MV23rx5rmDxc2K/Kd8eqnJ43McWPaWuaS1zSNYI4CtfMZdUuopqiqIqp3S67WHotAtAtAtAtBE53n4p9r9LlPhe8nkpaY9kp5x6vTivuWEBBFZ1944j6F/qUV7u5XNH+1W+cKPlOsrWxudbd7UuFrLwWgWgWgWgWgsLYnZATM41t4oC98Rkfu/a3/IreGiOvi0ul5r/TH+PqsZW2jEBAQEBAQEFUbKb4ezGBlbYIbmrnd2l/xVpc9aPMqeJiM4b7RFVWpVE7vD1adaqtwWgWgWgWgWgic7T8U8v6XKbC95PJT0x7HTzj1enlsHKiAgic7O8cR9C/1KK93crmj/AGq3zhRsp1rW07nXXu3LhayjLQLQLQLQLQc4pXMIcxzmuG85ri0joI1hZiZjrh5qppqjKqM4ZW7OL/3eJ87l/uXva18Vfodj3IN2cX/vMT53L/cm1r4nQ7HuQtnY8nfJk+N0j3vcXyW5zy52qRw33G1dsTM0Zy0GkLdNF+aaYyjq+zZVKpCDSNlbGSxYeAxSyRl2J0XFkjmEjaZTRLSNVgHyKC/VNNPU2OjbdFy7MVxnGX4Vxuzi/wDeYnzuX+5VNrXxbvodj3IDljF/7vE+dy/3Jta+J0Ox7kMLjOuybJJsknhJOsnnK8TMzvWKaYpjKmMoLWHotAtAtAtAtBFZ2H4qen9LlNhe9nkqaY9jp5x6vUC2DlBAQRGd3eGI+gf+FRX+7q5LujvarfOFFynWtbTudde7cuFrKItAtAtAtAtAtAtAtBcuxn8mx/Pl/mOV/D9hzOk/aZ+X2bSp2vEGg7MPe2H+tf0JlXxPYbTRPfTy9YVfaouiLQLQLQLQLQLQLQLQRedR+Knp/S5S4XvZ5KumPYqecer1Eti5MQEERnf3hifoH/hKiv8Ad1cl3RvtdvnCiJDrWso3Ouv95Lja9IS0C0C0C0C0C0C0C0FzbGXybH8+X+a5X8P2HNaT9pn5fZtSna8QaBsx97Yf61/QmVfE9htNE99PL1hV1qi6EtAtAtAtAtAtAtAtBF50H4sen9LlLhe9nkr6Y9hp5x6vUi2LkhAQQ+ePyfifoH/hKhxHdVcl7Rntdr4oUNIda1tG512I7yXG16QFoFoFoFoFoFoFoFoLo2MPk2P58v8ANcr+H7v6ua0n7TPy+za1O14gr/Zk72w/1r+hMq+J7DaaJ76eXrCrLVF0JaBaBaBaBaBaBaBaCMzmPxY9P6XKTC99PJBpn2CnnHq9TLZOREBBDZ5/J+K+ryfhKiv93VyXtGe2Wvij7qEeda1lHZddie9n++Dja9IC0C0C0C0C0C0C0C0F1bF3yZH8+X+a5X8N3f1+7mtJ+0z8vs2xTteIK+2Zu9cP9a/oTKDEdhtNE99PL1hVVqg6EtAtAtAtAtAtAtAtBG5yn4uen9LlJhe+nkh0z+30fFHq9ULZOQEBBC55/J2K+ryfhKiv93VyX9F+2Wvij7qCeda1lvsuuxXez/fB8telctAtAtAtAtAtAtAtBbuxHlJj8I6C+3hkc6uEskOkD/5aQ8gV3DVfpyc/pW1MXYr8J9G9qy1Qgq7ZkymxzoMM025hOJk19zbTGwHp0nn7POq2Jq6oht9EW516q/DLJXFqk3xaBaBaBaBaBaBaBaCNzj73P+fule8J308kWmf2+j4o9XqpbNx4gIIXPT5OxX1eT8JUV/u6uS/ov2y18UfdQDzrWrt9l12K72f74ONr2rloFoFoFoFoFoFoFoMvJWU5sLK2aB+jI3eO+CDvtcOFp4vzC9U1TTOcI7tqm7TNFcdSysmbK0BaBicNI1/CY9F7D5HEEdGvpVunE0zvaO7om5E/onOPpLHy1srDRLcHhnaZ1CWag0c4YxxLuglqVYmnwLWirkz+uco/lWs875Hukke58kjtN73HtnOPCfuAA1AAAUAqlVU1TnLeWrVNunVp3OFrykLQLQLQLQLQLQLQLQR+cXe5/wA4CveE76eSLTP7fR8X5eq1s3HiAghc9Pk7FfV5PwlRX+7q5L+i/bLXxR93n6Q61q7fZddiu9n++Dja9q5aBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaDBzh72P+cDlJhe+nki0z+30fFHq9VrZOPEBBC56fJ2K+ryfhKiv93VyX9F+2Wvij7vPkp1lau32XXYrvZ/vg4WvauWgWgWgsvKmbOCZkNuKbABOcNBIZNsf3T9r0jo6Va9I8Ct7KnZa2XXk0kYu90vZ59WtMZdXFX2So2vxELHC2vniY4cbXSNaRq5iVWpjOYhuLkzFFUx4RP2btspZvYPBMgOGhDDI94edN7rAaCO6cVYv26aYiYhqtHYq7duTFc59Xqr7THGqubcZS5OaRVgi96xV9HGssROe5s+xxkuDF47asRHpx7Q9+jpOHbNcwA20g8JUtmmKqspU8fdrtWdaicpzj1YOe2Ciw+UcRDCzRjjdGGNsmtKCJ51kkntnE+VYvUxTVlD1gbtV2zFVc9fWiIonvvQY51b+iwurppR5LU1RG+XA6iQdRGojhHSFhkv2IOUjHN7ppF71tI9ayxExO5xtYZfSDo6VHR5VGuveQzjPJYmdebeCgyPHiYodGZzcOS/bHn/U0dLtS6tdngVuu1TFvOI62mw+Lu1YrZzPVnPhHhmrq1UbktAtAtBh5wd7Hy+pykwvfTyRaZ/b6Pij1erFsnHiAghc9Pk7FfV5PwlRX+7q5L+i/bLXxR93nqc9sVq7fZddiu9n++Drte1ctAtAtBcmWv/zLPqeF9cSvz3Pyc3/78/FP3VTkI/G8P9Zg/msVOjtQ6C93dXKfssfZw/0sN9JJ+AK1iuzDSaI72eXrCey7jcLhcmYfEYiAS7U2B0UeoaUpj0W3eqhZdZutG9ZAUkzTFGcqtFNyu/NFE5TMzDHzUzpgyy2XD4jCtaQ3SMZftjXMJqwdEEEGuDhFLzRcpuZxMJMRhbmEmK6avnDWswsndi5enw4NiKKVrSd/RJic2+fRcFHap1bswu4y9tcFTXxmPVjZYyMMbnHNA69AvjfIQaOgzCwk0eC9Tb/iWK6Na7kzh72xwWvG/ry55tjzsz3ZkqVuDwmEjOhG1z+20GNDrprQ0G3ULJ5xv3qluXYt9UQpYbB14rO5VV8977l3D4fLOSjjI4gyeNj3t5QdHelGXV2zTRrpB1LFURdozje92q68Ff2dU/p8fn4/3k1zMDLmTcFh3vc18uPdplkTcNI52i3uWMeGFrdLUSb/AHhe8o7E0RGfitaRt37lcUx2OfV827ZqZYxWURIzHZN2uLRFF7HaLrNFpbI0E6uFT0VTXnE0tdiLNOHym3czny8PpLSc1s1YJssYiFzbw+Eke7QOsHt6Yx3G0a+nR13ZVei1E3Jjwhsr2NrpwlNcdqrqz5b55p7OLZIhw+JfhBghJBEdqldtgF6u2ayPRIcBdayLIPSpbl6mmdXJSw2j7l2jaRVlwZeybte4w2n/AEtLD7X8zTbo7/NS9Xctn1POB1ulxrb+vP6Spi1r3SloFoFoMXL3e3X6nKTC99PJFpn9vo+KPV6tWyceICCFzz+TsV9Xk/CVFf7urkv6L9stfFH3eeMQe2P+cC1dvsuuxXez/fB12vauWgWgWguvJMAylm+2CJzdPsdsGs6hJDVB3ECWjyG1sKP12so5Obv/APDjJqq3Z5/KetpubOYGUezInTwbXFFKyV7zKw2I3B1NDXEkmq8qr0Wa9aM2yxGkLGymKJzmYmN0+KQ2b8oMdJh8O0gujZJNIOLT0Wsvpp/UF7xU9UQq6HonXqr+TZc7MhzY3JEMcABkY2GZrCQNLRjotBOq6caviUtdM1W8oVcPeptYrWq3ZyidirNTF4aeTEYmIx/szCxpcC46TmuJoE0BoDrUdi1VTOcrWksXbuURRROfXnLFzQx7MRnHipozbHMlDTwER7TFY5joWOYrNM53pYu0TTo+mJ45/dxGUmYfOmZ0hAbIWQFxOoF+Fg0fSa0eVYmrK8zRbm5o/KPCc/o+bJmaGNlxpxGHhMrJWMDtEjSa9g0dYJGogDX073Di/bqmrOHrRuKtUW5ornKc805gIXZIyFJ2TQlLJDoaQP7SawyMVvnW265+DWpbcbO31qeJrjE4n9HlEfl15lYd2FyHt+ChbJinxuf3Nlzw8tANUSGgdzfBxlYsxlbzjekx1U3MVqVzlGcRy82Rsez5YnlllygXti0A2KN0LYxpE2SGAB1ADfdfdalm1VXV11PGMt4e3EU2pznx68/9I7MzHMjy7lCJxAdM86HOY3EkDnpxP2SvNE5XaoS36JqwVuqPDP8Amf8ATX87MxcoOx8pggL455XSskD2ho2w6RD7NiiT5FFds1TXMwt4PG2aLERXOUx4fhtmyThNoyI2K72o4aO+PQc1t/cp7sZWslDBV6+MirjnP8Spm1r3SFoFoFoMfLve3X6nKTCd9PJFpn9vo+KPV6tWyceICDDyzhNvw00XhYnxjpc0j815rp1qZhPhruyvUXOExP0l5pxYIdrFEjWOcaqWnt7sndY2nK5nHi6bUimWgWgWgkMjZcxWDcXYad0ZPdAUWu+cxwIPTVr3RXVTuQ3sPbvRlXH5Tk+yTldzdHshjb/ebh2aXpWPuUvSa1ONFWInx+v+mq4iZzy573uc95Lnvc4ucTW+SdZUFVU1dcr9q3TbiKaYyhcmfmNlgyRhJYZHMkY/Dlr2nWP2Th5RWqjqKvXJmLeceTnsLRTXippqjOJ1vVXeVM+cp4mMxSYohjhTwyNrC4cTnNF1zAi1Xm/XMZNrRo2xTVnlM80TknKs+Ek2zDSmOTRLNIMY7tTRIp7SOAcHAo6a5pnOFq7Zou06lcdTqyhjpcRK+ad5fLIQXvLWi9FoYNTQAO1aBqHAsVVTVOcs2bVNqnVo3J/J2yBlSBgY3E6TQKbtkYeQOLSOs+UlS0364jJUuaOsVzrZZckXlvL+Lxrg7FTufo9w2g1jb4WsaAL5zZ514ru1V70tjCWrPXTHXxlkZBzrx2BBbhp6Y42Y3MD2XxgHePQQlF2qjcYjCWr/AF1x18Ydj89Mpmfb+zHiTQMYpjNBrSQSGxlpaLLRrq9Q1r1t6880caOsRTq5flF4vKc8sxxEkpMxcHbaGtjdpNAAcNrDQDqGvfUdVU1TnKzbs0W6NSN3n1p2XZCys6Pa+y6BGiXiFgkr5wGo84FqXpFeSp/2zD62eU8s+r8/yjMXnHjZcO3DSYlzsOwMDYzHHvR1o9sGaRqhvnXw2vM3apjKU1GDs0XNpTGUou1EtFoFoFoOnLrSY2RDunXQ560fW5TYKM66qvl/foq/9Q16li1Z8d/0jL1erlsHKCAgIKK2TMgnDYt5aP2cxM8fST27fI430OC1V6jZ3fKXb4C90zBR71HVPp9Y/mGk2sPJaBaBaBaBaBaDJxGUcRI0MkxEz2NohjsRI5goUKYXUKG9qXua6pjKZRU2LdNWtFMZsa14SloFoFoFoFoFoFoFoFoFoFoFoO7DR6TuYayvFdWULGGtbSvr3QzM0sEcflfDxjWxsrZXH/twnbCTzEgD7QWzw1rZ28p3uU0tjIxWJmqnsx1Ryjx+c/w9MqZrRAQEERnRkGPHYcxP1OHbRvqy143jzjgI4ior1qLlOrK7gMbXg70XKd26Y4x/dygMvZEmw0zo5WaL26yOAjgcw8LT/mvUtX10Tq1uzmmjEUbexOcT4f3x8voiV7VHxAQEBAQEBAQEBAQEBAQEBAQEHZDEXHV1rFVUU70tqzVcnKHXlLFtY3a2HX++78ulT4WxNU7Sv5KGl9I0WaJwtiev/KfTnPjw3b91w7CuabsNA7GTtIlxLQI2kUWQ74PMXmjXE1vOtjLlFmLAICAgIIzL2QsPjY9rnZdXoPGp7TxtP5bx4VHctU3IyqW8Jjb2Fr17U848J5wo7O/NibJ7z2QwmEmmYprTtZveD6/03cztXESqFWFuUdjrh01nTODxHfRqVcfD6/mPm19sDHa2SNI6QfUVDM109qmV6izZuxnauxMc4n7S+9hHlBY2vk99Cn3oOwjygm18joU+9B2EeUE2vkdCn3oOwjygm18joU+9B2EeUE2vkdCn3oOwjygm18joU+9B2EeUE2vkdCn3oOwjygm18joU+9B2EeUE2vkdCn3oOwjygm18joU+9B2EeUE2vkdCn3oOwjygm18joU+9B2EeUE2vkdCn3oOwjygm18joU+9B2EeUE2vkdCn3oOw+NwTacIJweW+qHW58DO6kDjxDX6lJTbvV7qcuatcxOAsdu5rTwjr+3rLExGUnvpkTSNI6LQBbyTwADh5hrVu1g6aZ1q+uf4aTG6duXY2diNSn+Z/Hy6/NZmxzsWP0m4rKTKa0h0WFO+TwOmHAP4OviVzNoVzLAICAgICAg4yMDgQ4AgiiCLBB4CEGkZc2KMk4klzYnQPO+6F4aP8A1uBYPIAs5yxMRO9rkuwbDfaY+QD+LDNcesOHqWdaWNWng4fAZH4wd5mPeJrSatPA+AyPxg7zMe8TWk1aeB8BkfjB3mY94mtJq08D4DI/GDvMx7xNaTVp4HwGR+MHeZj3ia0mrTwPgMj8YO8zHvE1pNWngfAZH4wd5mPeJrSatPA+AyPxg7zMe8TWk1aeB8BkfjB3mY94mtJq08D4DI/GDvMx7xNaTVp4HwGR+MHeZj3ia0mrTwPgMj8YO8zHvE1pNWngfAZH4wd5mPeJrSatPA+AyPxg7zMe8TWk1aeB8BsfjF3mY94msascGXg9hHCAgzY3EPA4GNjjB5jYceorGb03fN7NDJ+A14XDNa+qMpt8h+26zXMNSwJ1AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEH/9k=\" width=\"100\" border-radius=10px/>")
        f.write(b"</button>")'''
        f.write(b"<hr>")
        f.write(b"<hr>\n<ul>\n")
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.write(b"<input style=\"float:right;\" border=1 type=\"image\" src=\"http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-down-icon.png\" alt=\"Submit\" width=\"40\"/>\n")
            f.write(('<a href="%s" style=\"font-size: 30px;color: blue;\">%s</a>\n' % (urllib.parse.quote(linkname), cgi.escape(displayname))).encode())
            ##########################################################################################################################
            f.write(b"<hr>\n")
        f.write(b"</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.parse.unquote(path))
        words = path.split('/')
        #words = filter(None, words)
        words = [_f for _f in words if _f]
        path = os.getcwd()
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path

    def copyfile(self, source, outputfile):
        shutil.copyfileobj(source, outputfile)

    def guess_type(self, path):

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })
##############################################################################3
#def test(HandlerClass=SimpleHTTPRequestHandler, ServerClass=http.server.HTTPServer, protocol="HTTP/1.1"):
def test(HandlerClass=SimpleHTTPRequestHandler, ServerClass=ThreadingSimpleServer, protocol="HTTP/1.1"):
#def test(HandlerClass=SimpleHTTPRequestHandler, ServerClass=ThreadingSimpleServer):
    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 8000

    hname = socket.gethostname()
    ipdr = socket.gethostbyname(hname)
    server_address = (str(ipdr), port)
    HandlerClass.protocol_version = protocol
    httpd = ServerClass(server_address, HandlerClass)
    sa = httpd.socket.getsockname()
    print("Serving HTTP on", sa[0], "port", sa[1], "...")
    httpd.serve_forever()

if __name__ == '__main__':
    test()

