# track-N-save
A website designed to track the expiry dates of food, medicine etc. and sends alert messages to their whatsapp

Install necessary packages - mongodb (database), flask (for website creation), twilio (to connect and to send whatsapp alerts)

Change the reciepient whatsapp number in app.py code, in line 19

Sign in Twilio website and replace the account sid and authorized token with yours in lines 16 and 17 in app.py

https://youtu.be/UVez2UyjpFk?si=vu0DWuTXeuyB4ULY -----> video to send a trial msg to whatsapp

For automatic alerts run the app_auto.py instead of app.py, you can change the time for automatic alert to happen, in line 56 of app.auto.py
