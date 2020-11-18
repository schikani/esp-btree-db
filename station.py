import os
import network
import btree
import time
import machine


MYDB = "mydb"

def banner(new_data=False):
    print("""
    
    DDDDDD   ^^^^^^^^^^^^^^^^^^^^^^^^^^    BBBBBB
        d                                   b
        d      --  WIFI STATION             b
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




# Convert bytes to python dictionaries for later use
QUERY0 = eval(db[b"0"])
QUERY1 = eval(db[b"1"])
QUERY2 = eval(db[b"2"])




#               0                    1               2
QUERY = ["ssid_password", "ap_ssid_password", "ap_settings"]

#            0     1    2    3     4    5
COMMANDS = ["ap", "r", "c", "mc", "a", "d"]

#             0         1
BOARDS = ["esp8266", "esp32"]


# Get Board info.
board_info = os.uname()
board_name = board_info[0]


# create access-point interface
ap = network.WLAN(network.AP_IF)
    
# create station interface
wlan = network.WLAN(network.STA_IF)




AUTO_AP = True
AUTO_WLAN = True

SSID_EXISTS = False if len(db['0']) == 2 else True



class Station:

    """
    Station class defines all the functions necessary for btree database.
    """

    def __init__(self, board):
        self.board = board.lower()
        self.auto_mode()


    def auto_mode(self):
        """
        Sets required AP settings at boot based on the board detected.
        Auto connects to a saved network at boot.
        """
        ap_ssid = list(QUERY1.keys())[0]
        ap_password = list(QUERY1.values())[0]


        if AUTO_AP and self.board == BOARDS[0]:
            ap.config(essid=ap_ssid, password=ap_password)
            ap.active(True)
            

        if AUTO_AP and self.board == BOARDS[1]:
            ap.config(essid=ap_ssid)
            ap.config(max_clients=list(QUERY2.values())[0])
            ap.active(True)

        print("")
        print('<>_<> Board type: ', board_name)
        print('<>_<> Discoverable as: ', ap_ssid)
        print('<>_<> Network config:', ap.ifconfig())
        print("")

        if AUTO_WLAN and SSID_EXISTS:
            self.auto_connect()
        
        if not SSID_EXISTS:
            print("No saved network/s. Returning to the station")
            time.sleep(3)
            self.base()


    def wlan_connect(self, ssid, password):
        wlan.active(False)
        time.sleep(1)
        wlan.active(True)
        attempt = 0
        print("connecting...")
        wlan.connect(ssid, password)
        time.sleep(2)
        while True:
            # It shows the connected network.
            if wlan.isconnected():
                print("")
                print('<>_<> ' + 'connected to:', ssid)
                print('<>_<> ' + 'network config:', wlan.ifconfig())
                print("")
                break

            if attempt == 6:
                print("still connecting...")

            if attempt == 8:
                print("one last try...")

            # When 10 tries are done, it breaks the while loop.
            if attempt == 10 and not wlan.isconnected():
                print("Having some network problem. Please try again later.")
                time.sleep(3)
                break

            if not wlan.isconnected():
                attempt += 1
                wlan.connect(ssid, password)
                time.sleep(3)

    def access_point(self):
        if self.board == BOARDS[0]:
            print("Type AP SSID")
            ssid = input("<:> ")
            print("Type AP Password")
            password = input("<:> ")
            ap_ssid_password = {ssid: password}
            db[b"1"] = b"{}".format(ap_ssid_password)
            db.flush()
            print("Your device will be visible as {}".format(ssid))
            time.sleep(3)
            self.base()

        if self.board == BOARDS[1]:
            print("Type AP SSID")
            ssid = input("<:> ")
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
                print("Your device will be visible as {}".format(ssid))
                print("Max clients are set to {}".format(m_c))
                time.sleep(4)
                self.base()
            except ValueError:
                print("Invalid input!")
                time.sleep(2)
                self.base()
                

    def radar(self, add=True):
        wlan.active(False)
        time.sleep(2)
        wlan.active(True)
        networks_dict = {}
        # scan for access points
        networks = [ssid[0] for ssid in wlan.scan()]  # we find the ssid from the tuple
        # Here we get the index and the ssid using enumerate
        networks_with_index = [ssid for ssid in enumerate(networks, start=1)]
        # Here we print our result and update networks_dict

        for item in networks_with_index:
            networks_dict.update({item[0]: item[1].decode('utf-8')})
            if add:
                print("[" + str(item[0]) + "] " + item[1].decode('utf-8'))
        if add:
            print("Select the network index and press Enter")
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
        
        return networks_dict

    def auto_connect(self):
        intersection = set(self.radar(add=False).values()) & set(QUERY0.keys())
        known = list(intersection)
        if len(intersection) > 0:
            print("found: {}".format(known[0]))
            self.wlan_connect(known[0], QUERY0[known[0]])

        else:
            print("No network matches the saved networks. Returning to the station")
            time.sleep(3)
            self.base()
            


    def manually_connect(self):
        networks_dict = {}
        networks_with_index = [ssid for ssid in enumerate(QUERY0.keys(), start=1)]
        for item in networks_with_index:
            print("[" + str(item[0]) + "] " + item[1])
            networks_dict.update({item[0]: item[1]})
        print("Type the index and press enter to connect the respective network")
        ask_user = int(input("<:> "))
        if ask_user in networks_dict.keys():
            self.wlan_connect(networks_dict[ask_user], QUERY0[networks_dict[ask_user]])

        else:
            print("Invalid input!")
            time.sleep(2)
            self.base()

    def add_a_network(self, ssid=None, radar=False):
        global SSID_EXISTS

        if ssid is not None and radar:
            print("Type Password for {}".format(ssid))
            password = input("<:> ")
            QUERY0.update({ssid: password})
            db[b"0"] = b"{}".format(QUERY0)
            db.flush()
            print("Network {} is added successfully.".format(ssid))
            SSID_EXISTS = True
            time.sleep(3)
            self.base()

        else:
            print("Type SSID")
            ssid_ = input("<:> ")
            print("Type Password for {}".format(ssid_))
            password = input("<:> ")
            QUERY0.update({ssid_: password})
            db[b"0"] = b"{}".format(QUERY0)
            db.flush()
            print("Network {} is added successfully.".format(ssid))
            SSID_EXISTS = True
            time.sleep(3)
            self.base()

    def delete_a_network(self):
        networks_dict = {}
        networks_with_index = [ssid for ssid in enumerate(QUERY0.keys(), start=1)]
        for item in networks_with_index:
            print("[" + str(item[0]) + "] " + item[1])
            networks_dict.update({item[0]: item[1]})
        print("Type the index and press enter to connect the respective network")
        try:
            ask_user = int(input("<:> "))
            if ask_user in networks_dict.keys():
                del QUERY0[networks_dict[ask_user]]
                db[b"0"] = b"{}".format(QUERY0)
                db.flush()
                print("Network {} is removed successfully.".format(networks_dict[ask_user]))
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
        print("""
          __|_________________________________________________________|__
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

def station():
    
    return Station(board=board_name).base()

station()