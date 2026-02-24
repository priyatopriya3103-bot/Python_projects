import qrcode

url = input("Enter thr url :").strip()
file_path = r"D:/Important !!/Python/Final projects/Bank/File organiser"

qr = qrcode.QRCode()
qr.add_data(url)

img = qr.make_image()
img.save(file_path)


print("Qr generated successfully")