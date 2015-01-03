from mininet.topo import Topo

class FacebookTopo(Topo):

    def __init__(self, racksize, rackcount, clustercount):
        Topo.__init__(self)

        fc1 = self.addSwitch('fc1')
        fc2 = self.addSwitch('fc2')
        fc3 = self.addSwitch('fc3')
        fc4 = self.addSwitch('fc4')
        fcs = [fc1, fc2, fc3, fc4]

        self.addLink(fc1, fc2)
        self.addLink(fc2, fc3)
        self.addLink(fc3, fc4)
        self.addLink(fc4, fc1)

        for i in range(1, clustercount + 1):
            csw1 = self.addSwitch('c%dcsw1' % i)
            csw2 = self.addSwitch('c%dcsw2' % i)
            csw3 = self.addSwitch('c%dcsw3' % i)
            csw4 = self.addSwitch('c%dcsw4' % i)
            csws = [csw1, csw2, csw3, csw4]

            self.addLink(csw1, csw2)
            self.addLink(csw2, csw3)
            self.addLink(csw3, csw4)
            self.addLink(csw4, csw1)

            for csw in csws:
                for fc in fcs:
                    self.addLink(csw, fc)

            for j in range(1, rackcount + 1):
                rsw = self.addSwitch('c%drsw%d' % (i, j))
                
                for k in range(1, racksize + 1):
                    host = self.addHost('c%dr%dh%d' % (i, j, k))
                    self.addLink(rsw, host)

                for csw in csws:
                    self.addLink(rsw, csw)

topos = { 'facebooktopo': ( lambda: FacebookTopo(10, 3, 2) ) }