# BM869S-remote-access
My python 3 based interface to the Brymen 868S multimeter USB interface 

Brymen sells a USB adapter for their multimeter. I wrote a bit of Python code that interprets the data from the multimeter which is actually just a list of all activated segments and announciators on the LCD panel. This is a one-way interface, so its not allowing you to change anything.  I have tested the code on Linux and Windows 7.
The biggest hurdle is that the interface shows up as a HID (Human Interface Device) not as a standard serial port. That said, I found that neither Linux nor Windows 7 needed any additional drivers but for Python, the additional "hid" package is needed.

Assuming that Python 3 (at least 3.7) and pip is installed and using the command prompt:

For Linux or Windows use:
   
   pip3 install hid

for Windows in addition:

   download hidapi-win.zip from: https://github.com/libusb/hidapi/releases

   unpack (contains a x86 and x64 folder with DLLs)
   assuming you have a 64-bit installation of Windows, copy the files in the X64 folder into Windows/System32 folder. You need admin privileges for that.
 
for Linux: your username should be in the dialout group, or else you may get a "no permissions" error when trying to access the HID interface. Don't forget that you need to logout and login back again before a change to group membership becomes active. 

BM869S.py implements a class BM869S and can be used by other python programs simply using

  from BM869S import BM869S
  
instantiate for example:

  MyMeter = BM869S()
  
use: 
  reading = MyMeter.readdata()
  print(reading)
    
readdata() which returns a list with 4 strings. These are 
0: the number as shown on the main display of the BM869S
1: the unit&mode belonging to the main display, e.g. "AC V" or "OHM"
2: the number as shown on the secondary display (or blank if no secondary display is active)
3: the unit&mode belonging to the secondary display, e.g. "HZ" (or blank)


In addition you can run BM869S.py directly as a main program. It implements a small logger that reads data from the BM869S and saves it in a .CSV file which you can open with any spreadsheet program.  With no parameters, it creates a logfile called "BM869s_<date&time>.csv  with <date&time> being the current time and date and logs once per second. To stop use control-C. You can change the log-file name using the --out command line argument and the time using --time 


Note: The BM869S meter must be turned-on for this to work. The software will hang if you turn the meter off (or if it turns itself off after being idle for too long!)
