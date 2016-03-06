__author__ = 'amarcillo'


def get_interface_ip(ifname):
        import socket

        import fcntl
        import struct
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                    ifname[:15]))[20:24])


def get_lan_ip():
    import socket
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip.startswith("127."):
            interfaces = [
                "eth0",
                "eth1",
                "eth2",
                "wlan0",
                "wlan1",
                "wifi0",
                "ath0",
                "ath1",
                "ppp0",
                ]
            for ifname in interfaces:
                try:
                    ip = get_interface_ip(ifname)
                    break
                except IOError:
                    pass
        return ip
    except:
        print 'error al obtener direccion ip del servidor'
        return '142.4.207.146'
