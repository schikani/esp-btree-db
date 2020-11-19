import os
import network
import btree    #   ____
import time     #<  O| O
import machine  #<  <~~>


MYDB = "mydb"

def banner(new_data=False):
    print("""
    
    DDDDDD   ^^^^^^^^^^^^^^^^^^^^^^^^^^    BBBBBB
        d                                   b
        d     -- ESP WIFI STATION           b
        d-----------------------------------b
        d         USING BTREE DB --         b
        d                                   b
        d       by: Shivang Chikani         b
    DDDDDD   ^^^^^^^^^^^^^^^^^^^^^^^^^^    BBBBBB

    """)

    if new_data:
        print("""
    ----------------------------------------------------
            Curently there is no saved database
    A new database will be created with a system reboot.
    ----------------------------------------------------
        """)
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
            print("\n"+"-------AP INFO--------------"+"\n")
            print('<>_<> Board type: ', self.board)
            print('<>_<> Discoverable as: ', self.ap_ssid)
            print('<>_<> Network config:', AP.ifconfig())
            if self.board == BOARDS[1]:
                print('<>_<> ' + 'Maximum clients allowed: ' + str(self.max_clients) + "\n")

            else:
                print("")
        
        if WLAN.isconnected() and SSID_EXISTS:
            print("\n"+"-------WLAN INFO------------"+"\n")
            print('<>_<> ' + 'connected to:', self.wlan_ssid)
            print('<>_<> ' + 'network config:', WLAN.ifconfig())
            

        if AUTO_WLAN and SSID_EXISTS and not WLAN.isconnected():
            self.auto_connect()
        
        if not SSID_EXISTS:
            print("No saved network/s. Returning to the station")
            time.sleep(3)
            self.base()


    def wlan_connect(self, ssid, password):
        WLAN.active(False)
        time.sleep(1)
        WLAN.active(True)
        attempt = 0
        print("connecting...")
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
                print("still connecting...")

            if attempt == 8:
                print("one last try...")

            # When 10 tries are done, it breaks the while loop.
            if attempt == 10 and not WLAN.isconnected():
                print("Having some network problems.")
                break

            if not WLAN.isconnected():
                attempt += 1
                WLAN.connect(ssid, password)
                time.sleep(2)

    def access_point(self):
        if self.board == BOARDS[0]:
            print("Type AP SSID")
            ssid = input("<:> ")
            if ssid != "":
                print("Type AP Password")
                password = input("<:> ")
                ap_ssid_password = {ssid: password}
                db[b"1"] = b"{}".format(ap_ssid_password)
                db.flush()
                print("Your device will be visible as '{}'".format(ssid))
                time.sleep(3)
                self.base()
            if ssid == "":
                print("AP SSID cannot be an empty string.")
                time.sleep(3)
                self.base()

        if self.board == BOARDS[1]:
            print("Type AP SSID")
            ssid = input("<:> ")
            if ssid != "":
                ap_ssid_password = {ssid: None}
                print("Type the amount of max clients allowed (1 ~ 10)")
                try:
                    m_c = int(input("<:> "))
                    if m_c > 10:
                        m_c = 10
                    max_clients = {"max_client/s": m_c}
                    db[b"1"] = b"{}".format(ap_ssid_password)
                    db[b"2"] = b"{}".format(max_clients)
                    db.flush()
                    print("Your device will be visible as '{}'".format(ssid))
                    print("Max clients are set to '{}'".format(m_c))
                    time.sleep(4)
                    self.base()
                except ValueError:
                    print("Invalid input!")
                    time.sleep(2)
                    self.base()

            if ssid == "": 
                print("AP SSID cannot be an empty string.")
                time.sleep(3)
                self.base()
                

    def radar(self):
        WLAN.active(False)
        time.sleep(2)
        WLAN.active(True)
        networks_dict = {}
        # scan for access points
        networks = [ssid[0] for ssid in WLAN.scan()]  # we find the ssid from the tuple
        # Here we get the index and the ssid using enumerate
        networks_with_index = [ssid for ssid in enumerate(networks, start=1)]
        # Here we print our result and update networks_dict
        print("")
        for item in networks_with_index:
            networks_dict.update({item[0]: item[1].decode('utf-8')})
            print("[" + str(item[0]) + "] " + item[1].decode('utf-8'))
        print("\n"+"Select the network index and press Enter")
        try:
            ask_user = int(input("<:> "))
            if ask_user in networks_dict.keys():
                self.add_a_network(ssid=networks_dict[ask_user], radar=True)
            else:
                print("Invalid input!")
                time.sleep(2)
                self.base()

        except ValueError:
            print("Invalid input!")
            time.sleep(2)
            self.base()
        
        # return networks_dict

    def auto_connect(self):
        WLAN.active(False)
        time.sleep(2)
        WLAN.active(True)
        # Here we try to find the intersection between WLAN.scan() and our database
        intersection = set(self.QUERY0.keys()) & {i[0].decode('utf-8') for i in WLAN.scan()}
        known = list(intersection)
        if len(intersection) > 1:
            print("found: {}".format(known))
            if len(known) > 1:
                for ssid in known:
                    if not WLAN.isconnected():
                        print("\n"+"attempting to connect '{}'".format(ssid)+"\n")
                        self.wlan_connect(ssid, self.QUERY0[ssid])
                    else:
                        break
        if len(intersection) == 1:
            print("found: '{}'".format(known[0]))
            print("\n"+"attempting to connect '{}'".format(known[0])+"\n")
            self.wlan_connect(known[0], self.QUERY0[known[0]])

        if len(intersection) == 0:
            print("No network matches the saved networks. Returning to the station")
            time.sleep(3)
            self.base()
            
    def manually_connect(self):
        networks_dict = {}
        networks_with_index = [ssid for ssid in enumerate(self.QUERY0.keys(), start=1)]
        print("")
        for item in networks_with_index:
            print("[" + str(item[0]) + "] " + item[1])
            networks_dict.update({item[0]: item[1]})
        print("")
        print("Type the index and press enter to connect the respective network")
        try:
            ask_user = int(input("<:> "))
            if ask_user in networks_dict.keys():
                self.wlan_connect(networks_dict[ask_user], self.QUERY0[networks_dict[ask_user]])
            else:
                print("Invalid input!")
                time.sleep(2)
                self.base()
        except ValueError:
            print("Invalid input!")
            time.sleep(2)
            self.base()

    def add_a_network(self, ssid=None, radar=False):
        global SSID_EXISTS

        if ssid is not None and radar:
            print("Type Password for '{}'".format(ssid))
            password = input("<:> ")
            self.QUERY0.update({ssid: password})
            db[b"0"] = b"{}".format(self.QUERY0)
            db.flush()
            print("Network '{}' is added successfully.".format(ssid))
            SSID_EXISTS = True
            time.sleep(3)
            self.base()

        else:
            print("Type SSID")
            ssid_ = input("<:> ")
            if ssid_ == "":
                print("SSID cannot be an empty string.")
                time.sleep(3)
                self.base()

            if ssid_ != "":
                print("Type Password for '{}'".format(ssid_))
                password = input("<:> ")
                self.QUERY0.update({ssid_: password})
                db[b"0"] = b"{}".format(self.QUERY0)
                db.flush()
                print("Network '{}' is added successfully.".format(ssid_))
                SSID_EXISTS = True
                time.sleep(3)
                self.base()

    def delete_a_network(self):
        networks_dict = {}
        networks_with_index = [ssid for ssid in enumerate(self.QUERY0.keys(), start=1)]
        print("")
        for item in networks_with_index:
            print("[" + str(item[0]) + "] " + item[1])
            networks_dict.update({item[0]: item[1]})
        print("")
        print("Type the index and press enter to connect the respective network")
        try:
            ask_user = int(input("<:> "))
            if ask_user in networks_dict.keys():
                del self.QUERY0[networks_dict[ask_user]]
                db[b"0"] = b"{}".format(self.QUERY0)
                db.flush()
                print("Network '{}' is removed successfully.".format(networks_dict[ask_user]))
                time.sleep(3)
                self.base()
            else:
                print("Invalid input!")
                time.sleep(2)
                self.base()
        except ValueError:
            print("Invalid input!")
            time.sleep(2)
            self.base()

            
    def base(self):
        """
        This is the main base where user interaction is carried on. 
        """
        print("""
___________________________________________________________
|                * Welcome to the Station! *              |
|                                                         |
|    * Type any below given commands and press Enter *    |
|         * Just press Enter to exit the station *        |
|                                                         |
|    <:> "AP" to configure the Access point settings      |
|    <:> "R" to start the Radar                           |
|    <:> "C" to auto-connect to a saved network           |
|    <:> "MC" to manually connect to a saved network      |
|    <:> "A" to add a new network                         |
|    <:> "D" to remove a network                          |
|_________________________________________________________|
            """)

        command = input("<:> ").lower()


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
            print("No saved network/s.")


        else:
            pass

def station(base=False, boot=False):
    
    if base:
        return Station(board=BOARD_NAME).base()
    
    if boot:
        return Station(board=BOARD_NAME)

station(boot=True)

# This line should be used in boot.py
## from station import station

# This command can be used in REPL to call station console
## station(1)
