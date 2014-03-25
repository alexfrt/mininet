from mininet.net import Mininet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from math import sqrt

import os
import time

networksCounter = 0

def buildNetwork(mininet, hostsCount, ipScope):
    global networksCounter
    
    switch = mininet.addSwitch('s%s' % networksCounter)
    hosts = []

    for i in range(0, hostsCount):
        host = mininet.addHost('h%s%s' % (networksCounter, i), ip = "%s.%s" % (ipScope, i))
        mininet.addLink(host, switch)
        hosts.append(host)

    networksCounter += 1

    return (switch, hosts)

def setupNetworks(mininet, networkSetup):
    switches = []
    hosts = []

    #Build all sub networks
    for setup in networkSetup:
        nodes = buildNetwork(mininet, networkSetup[setup], setup)
        switches.append(nodes[0])
        hosts.extend(nodes[1])

    #Connect all switchs in line
    for i, sA in enumerate(switches):
        for sB in switches[i + 1:]:
            mininet.addLink(sA, sB)

    return (switches, hosts)

def startTrafficServer(host, port, bitrate):
    host.cmd("java -jar server.jar %s 50 %s &" % (port, bitrate)) #port - senders - bitrate

def startTrafficClients(clients, serverIp, serverPort):
    for host in clients:
        host.cmd("java -jar client.jar %s %s > result-%s &" % (serverIp, serverPort, host.name))

def extractResults(clients):
    clientsResults = []
    for host in clients:
        hostResults = []
        logFile = open('result-%s' % host.name, 'r')
        for line in logFile:
            hostResults.append(int(line))

        clientsResults.append(hostResults[1:])

        logFile.close()
        os.remove(logFile.name)

    return clientsResults

def getStatistics(clientsResults):
    hostsResults = []
    
    for clientResult in clientsResults:
        n, mean, std = len(clientResult), 0, 0
        
        for a in clientResult:
            mean = mean + a
        mean = mean / n

        for a in clientResult:
            std = std + (a - mean)**2
        std = sqrt(std / n-1)

        hostsResults.append({
            "mean" : mean,
            "stddev" : std,
            "min" : min(clientResult),
            "max" : max(clientResult)
        })

    return hostsResults

def showStatistics(statistics):
    globalMean = 0
    meanStddev = 0
    meanMin = 0
    meanMax = 0
    
    for stats in statistics:
        globalMean += stats["mean"]
        meanStddev += stats["stddev"]
        meanMin += stats["min"]
        meanMax += stats["max"]

    print "*" * 60
    print ""
    print " Mean bitrate: %s" % (globalMean / len(statistics))
    print " Mean std dev: %s" % (meanStddev / len(statistics))
    print " Mean min:     %s" % (meanMin / len(statistics))
    print " Mean max:     %s" % (meanMax / len(statistics))
    print ""
    print "*" * 60

if __name__ == '__main__':
    setLogLevel('info')
    
    net = Mininet()

    info('*** Adding controller\n')
    net.addController('c0')

    info('*** Setting up networks ***\n')

    networkSetup = {'192.168.201' : 10, '192.168.202' : 10}
    info('     Config: %s\n' % networkSetup)
        
    nodes = setupNetworks(net, networkSetup)

    info('*** Starting network ***\n')
    net.start()

    info('*** Starting traffic server ***\n')
    server = nodes[1][0]
    startTrafficServer(server, 9999, 3 * 1024) #3 mbps

    time.sleep(2)

    info('*** Starting traffic clients ***\n')
    clients = nodes[1][1:]
    startTrafficClients(clients, server.IP(), 9999)

    CLI(net)

    info('*** Killing server and clients ***\n')
    server.cmd("killall -9 java")

    info('*** Collecting clients results ***\n')
    clientsResults = extractResults(clients)

    info('Results:\n')
    statistics = getStatistics(clientsResults)
    showStatistics(statistics)

    info('*** Stopping network ***\n')
    net.stop()
