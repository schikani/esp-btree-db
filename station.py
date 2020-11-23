import os
import network
import btree    #   ____
import time     #<  O| O
import machine  #<  <~~>

# Colors for our console
HEADER = '\033[95m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RED = '\033[91m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

END = '\033[0m'
CLEAR = '\033[2J'
CLEAR_LINE = '\033[2K'

# Here we use a fancy way of defining where the color starts and ends
## using ANSI escape sequences. This strategy will be also used later
### in the script.

PROMPT = "{1}<{2}:{1}>{0} ".format(END, BLUE, RED)

MYDB = "mydb"

def banner(new_data=False):


#-----------------------------------------------------
    print("""{1}
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^{0}{2}
d     -- ESP WIFI STATION           b
d-----------------------------------b
d         USING BTREE DB --         b
d                                   b
d                                   b{0}{3}
d      by: Shivang Chikani          b
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^{0}"""
.format(END, RED, YELLOW, GREEN))
#          {0}  {1}    {2}   {3}
#------------------------------------------------------

    if new_data:
        print("""{1}
----------------------------------------------------{0}
{2}     Curently there is no saved database
A new database will be created with a system reboot.{0}{1}
----------------------------------------------------{0}
""".format(END, HEADER, YELLOW))
        f = open(MYDB, "r+b")
        # Here we load the database
        db = btree.open(f)

        # Load default values
        db[b"0"] = b"{}"
        db[b"1"] = b"{'ESP_Station': 'MicroPython'}"
        db[b"2"] = b"{'max_client/s': 1}"
        db[b"3"] = b""
        db.flush()
        time.sleep(4)
        machine.reset()

try:
    f = open(MYDB, "r+b")
    db = btree.open(f)
    banner()

except OSError:
    f = open(MYDB, "w+b")
    f.close()
    banner(new_data=True)



# Get Board info.
BOARD_INFO = os.uname()
BOARD_NAME = BOARD_INFO[0]


# create access-point interface
AP = network.WLAN(network.AP_IF)
    
# create station interface
WLAN = network.WLAN(network.STA_IF)


SSID_EXISTS = False if len(db['0']) == 2 else True

#            0     1    2    3     4    5
COMMANDS = ["ap", "r", "c", "mc", "a", "d"]

#             0         1
BOARDS = ["esp8266", "esp32"]


AUTO_AP = True
AUTO_WLAN = True


class Station:
    
    """
    Station class defines all the functions necessary for btree database.
    """

    def __init__(self, board):

        # Convert bytes to python dictionaries for later use
        self.QUERY0 = eval(db[b"0"]) # wlan ssid and password
        self.QUERY1 = eval(db[b"1"]) # ap ssid and password
        self.QUERY2 = eval(db[b"2"]) # ap settings
        self.board = board.lower()
        self.check(ap=True)
        
    def check(self, ap=False):
        self.wlan_ssid = db[b"3"].decode('utf-8') # current wlan ssid

        self.ap_ssid = list(eval(db[b"1"]).keys())[0] 
        self.ap_password = list(eval(db[b"1"]).values())[0]
        self.max_clients = list(eval(db[b"2"]).values())[0]

        if AUTO_AP and self.board == BOARDS[0] and not AP.isconnected():
            AP.config(essid=self.ap_ssid, password=self.ap_password)
            AP.active(True)
            
        if AUTO_AP and self.board == BOARDS[1] and not AP.isconnected():
            AP.config(essid=self.ap_ssid)
            AP.config(max_clients=self.max_clients)
            AP.active(True)

        if ap:
            if not SSID_EXISTS:
                print("{1}No saved network/s. Returning to the station{0}".format(END, YELLOW))
                time.sleep(3)
                self.base()
            
            
            print("""{1}
-------{0}AP INFO{1}--------------------{0}
{2}
<>_<>{0} {3}Board type:{0} {4}{5}{0}{2}
<>_<>{0} {3}Discoverable as:{0} {4}{6}{0}{2}
<>_<>{0} {3}Network config:{0} {4}{7}{0}"""
.format(END, HEADER, YELLOW, BLUE, BOLD, self.board, self.ap_ssid, AP.ifconfig()))

            if self.board == BOARDS[1]:
                print("{1}<>_<>{0} {2}Maximum clients allowed:{0} {3}{4}{0}".format(END, YELLOW, BLUE, BOLD, self.max_clients))
            print("{1}----------------------------------{0}".format(END, HEADER))

        if WLAN.isconnected() and SSID_EXISTS:
            print("""{1}
-------{0}WLAN INFO{1}------------------{0}
{2}
<>_<>{0} {3}connected to:{0} {4}{5}{0}{2} 
<>_<>{0} {3}network config:{0} {4}{6}{0}{1}
----------------------------------{0}
"""
.format(END, HEADER, YELLOW, BLUE, BOLD, self.wlan_ssid, WLAN.ifconfig()))

        if AUTO_WLAN and SSID_EXISTS and not WLAN.isconnected():
            self.auto_connect()


    def wlan_connect(self, ssid, password):
        WLAN.active(False)
        time.sleep(1)
        WLAN.active(True)
        attempt = 0
        print("{1}connecting...{0}".format(END, BLUE))
        WLAN.connect(ssid, password)
        time.sleep(2)
        while True:
            # It shows the connected network.
            if WLAN.isconnected():
                db[b"3"] = b"{}".format(ssid)
                db.flush()
                self.check()
                break

            if attempt == 6:
                print("{1}still connecting...{0}".format(END, BLUE))

            if attempt == 8:
                print("{1}one last try...{0}".format(END, BLUE))

            # When 10 tries are done, it breaks the while loop.
            if attempt == 10 and not WLAN.isconnected():
                print("{1}Having some network problems.{0}".format(END, YELLOW))
                break

            if not WLAN.isconnected():
                WLAN.connect(ssid, password)
                time.sleep(2)
                attempt += 1

    def access_point(self):
        if self.board == BOARDS[0]:
            print("{1}Type AP SSID{0}".format(END, BLUE))
            ssid = input(PROMPT)
            if ssid != "":
                print("{1}Type AP Password{0}".format(END, BLUE))
                password = input(PROMPT)
                ap_ssid_password = {ssid: password}
                db[b"1"] = b"{}".format(ap_ssid_password)
                db.flush()
                print("{1}Your device will be visible as{0} {2}{3}{0}".format(END, BLUE, BOLD, ssid))
                time.sleep(3)
                self.base()
            if ssid == "":
                print("{1}AP SSID cannot be an empty string.{0}".format(END, YELLOW))
                time.sleep(3)
                self.base()

        if self.board == BOARDS[1]:
            print("{1}Type AP SSID{0}".format(END, BLUE))
            ssid = input(PROMPT)
            if ssid != "":
                ap_ssid_password = {ssid: None}
                print("{1}Type the amount of max clients allowed (1 ~ 10){0}".format(END, BLUE))
                try:
                    m_c = int(input(PROMPT))
                    if m_c > 10:
                        m_c = 10
                    max_clients = {"max_client/s": m_c}
                    db[b"1"] = b"{}".format(ap_ssid_password)
                    db[b"2"] = b"{}".format(max_clients)
                    db.flush()
                    print("{1}Your device will be visible as{0} {2}{3}{0}".format(END, BLUE, BOLD, ssid))
                    print("{1}Max clients are set to{0} {2}{3}{0}".format(END, BLUE, BOLD, m_c))
                    time.sleep(4)
                    self.base()
                except ValueError:
                    print("{1}Invalid input!{0}".format(END, YELLOW))
                    time.sleep(2)
                    self.base()

            if ssid == "":
                print("{1}AP SSID cannot be an empty string.{0}".format(END, YELLOW))
                time.sleep(3)
                self.base()
                

    def radar(self):
        print("\nScanning for networks ...")
        WLAN.active(False)
        time.sleep(1)
        WLAN.active(True)
        networks_dict = {}
        # scan for access points
        networks = (ssid[0] for ssid in WLAN.scan())  # we find the ssid from the tuple
        # Here we get the index and the ssid using enumerate
        networks_with_index = (ssid for ssid in enumerate(networks, start=1))
        print("\n{1}Select the network index and press Enter{0}\n".format(END, BLUE))
        # Here we print our result and update networks_dict
        for item in networks_with_index:
            print("[{1}{2}{0}] {3}{4}{0}"
            .format(END, GREEN, str(item[0]), YELLOW, item[1].decode('utf-8')))
            networks_dict.update({item[0]: item[1].decode('utf-8')})
        
        try:
            ask_user = int(input(PROMPT))
            if ask_user in networks_dict.keys():
                self.add_a_network(ssid=networks_dict[ask_user], radar=True)
            else:
                print("{1}Invalid input!{0}".format(END, YELLOW))
                time.sleep(2)
                self.base()

        except ValueError:
            print("{1}Invalid input!{0}".format(END, YELLOW))
            time.sleep(2)
            self.base()
        
        return networks_dict

    def auto_connect(self):
        print("Searching for available networks ...")
        WLAN.active(False)
        time.sleep(2)
        WLAN.active(True)
        # Here we try to find the intersection between WLAN.scan() and our database
        intersection = set(self.QUERY0.keys()) & {i[0].decode('utf-8') for i in WLAN.scan()}
        known = list(intersection)
        if len(intersection) > 1:
            print("\n{1}found:{0} {2}{3}{0}".format(END, BLUE, BOLD, known))
            if len(known) > 1:
                for ssid in known:
                    if not WLAN.isconnected():
                        print("\n{1}attempting to connect{0} '{2}{3}{0}'\n".format(END, BLUE, BOLD, ssid))
                        self.wlan_connect(ssid, self.QUERY0[ssid])
                    else:
                        break
        if len(intersection) == 1:
            print("\n{1}found:{0} {2}{3}{0}".format(END, BLUE, BOLD, known[0]))
            print("\n{1}attempting to connect{0}".format(END, BLUE))
            self.wlan_connect(known[0], self.QUERY0[known[0]])

        if len(intersection) == 0:
            print("{1}No network matches the saved networks. Returning to the station{0}".format(END, YELLOW))
            time.sleep(4)
            self.base()
            
    def manually_connect(self):
        networks_dict = {}
        networks_with_index = [ssid for ssid in enumerate(self.QUERY0.keys(), start=1)]
        print("\n{1}Type the index to connect the network.{0}\n".format(END, BLUE))
        for item in networks_with_index:
            print("[{1}{2}{0}] {3}{4}{0}"
            .format(END, GREEN, str(item[0]), YELLOW, item[1]))
            networks_dict.update({item[0]: item[1]})
        try:
            ask_user = int(input(PROMPT))
            if ask_user in networks_dict.keys():
                self.wlan_connect(networks_dict[ask_user], self.QUERY0[networks_dict[ask_user]])
            else:
                print("{1}Invalid input!{0}".format(END, YELLOW))
                time.sleep(2)
                self.base()
        except ValueError:
            print("{1}Invalid input!{0}".format(END, YELLOW))
            time.sleep(2)
            self.base()

    def add_a_network(self, ssid=None, radar=False):
        global SSID_EXISTS

        if ssid is not None and radar:
            print("{1}Type Password for{0} '{2}{3}{0}'".format(END, BLUE, BOLD, ssid))
            password = input(PROMPT)
            self.QUERY0.update({ssid: password})
            db[b"0"] = b"{}".format(self.QUERY0)
            db.flush()
            print("{1}Network{0} {2}{3}{0} {1}is added successfully.{0}".format(END, BLUE, BOLD, ssid))
            SSID_EXISTS = True
            time.sleep(3)
            self.base()

        else:
            print("{1}Type SSID{0}".format(END, BLUE))
            ssid_ = input(PROMPT)
            if ssid_ == "":
                print("{1}SSID cannot be an empty string.{0}".format(END, YELLOW))
                time.sleep(3)
                self.base()

            if ssid_ != "":
                print("{1}Type Password for{0} {2}{3}{0}".format(END, BLUE, BOLD, ssid_))
                password = input(PROMPT)
                self.QUERY0.update({ssid_: password})
                db[b"0"] = b"{}".format(self.QUERY0)
                db.flush()
                print("{1}Network{0} {2}{3}{0} {1}is added successfully.{0}".format(END, BLUE, BOLD, ssid_))
                SSID_EXISTS = True
                time.sleep(3)
                self.base()

    def delete_a_network(self):
        networks_dict = {}
        networks_with_index = [ssid for ssid in enumerate(self.QUERY0.keys(), start=1)]
        print("\n{1}Type the index to delete the network.{0}\n".format(END, BLUE))
        for item in networks_with_index:
            print("[{1}{2}{0}] {3}{4}{0}"
            .format(END, GREEN, str(item[0]), YELLOW, item[1]))
            networks_dict.update({item[0]: item[1]})
        
        try:
            ask_user = int(input(PROMPT))
            if ask_user in networks_dict.keys():
                del self.QUERY0[networks_dict[ask_user]]
                db[b"0"] = b"{}".format(self.QUERY0)
                db.flush()
                print("{1}Network{0} {2}{3}{0} {1}is removed successfully.{0}"
                .format(END, BLUE, BOLD, networks_dict[ask_user]))
                time.sleep(3)
                self.base()
            else:
                print("{1}Invalid input!{0}".format(END, YELLOW))
                time.sleep(2)
                self.base()
        except ValueError:
            print("{1}Invalid input!{0}".format(END, YELLOW))
            time.sleep(2)
            self.base()

            
    def base(self):
        """
        This is the main base where user interaction is carried on. 
        """
        time.sleep(1)
        print(CLEAR)
        print("""
------------------------------------------------------
            {1}Welcome to the Station!{0}
                                                       
{2}* Type any below given commands and press Enter  {0}
    {2}* Just press Enter to exit the station{0}
                                                       
   {3}{4}AP{0}{5} to configure the Access point settings  {0}
   {3}{4}R{0}{5}  to start the Radar                      {0}
   {3}{4}C{0}{5}  to auto-connect to a saved network      {0}
   {3}{4}MC{0}{5} to manually connect to a saved network  {0}
   {3}{4}A{0}{5}  to add a new network                    {0}
   {3}{4}D{0}{5}  to remove a network                     {0}
------------------------------------------------------
""".format(END, HEADER, YELLOW, PROMPT, BOLD, BLUE))

        command = input(PROMPT).lower()


        if command == COMMANDS[0]:
            self.access_point()

        elif command == COMMANDS[1]:
            self.radar()

        elif command == COMMANDS[2] and SSID_EXISTS:
            self.auto_connect()

        elif command == COMMANDS[3] and SSID_EXISTS:
            self.manually_connect()

        elif command == COMMANDS[4]:
            self.add_a_network()

        elif command == COMMANDS[5] and SSID_EXISTS:
            self.delete_a_network()

        elif (command in COMMANDS[2] or command in COMMANDS[3] or command in COMMANDS[5]) and not SSID_EXISTS:
            print("{1}No saved network/s.{0}".format(END, YELLOW))


        else:
            pass

def station(base=False, boot=False):
    
    if base:
        return Station(board=BOARD_NAME).base()
    
    if boot:
        return Station(board=BOARD_NAME).__init__

station(boot=True)

# This line should be used in boot.py
## from station import station

# This command can be used in REPL to call station console
## station(1)
