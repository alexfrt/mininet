from mininet.net import Mininet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from math import sqrt

import os
import time
import argparse

networksCounter = 0

def buildNetwork(mininet, hostsCount, ipScope, loss, bandwidth, delay):
    global networksCounter
    
    switch = mininet.addSwitch('s%s' % networksCounter)
    hosts = []

    for i in range(0, hostsCount):
        host = mininet.addHost('h%s%s' % (networksCounter, i), ip = "%s.%s" % (ipScope, i))
        mininet.addLink(host, switch) #bw = bandwidth, delay = "%sms" % delay, loss=loss
        hosts.append(host)

    networksCounter += 1

    return (switch, hosts)

def setupNetworks(mininet, networkSetup, loss, bandwidth, delay):
    switches = []
    hosts = []

    #Build all sub networks
    for setup in networkSetup:
        nodes = buildNetwork(mininet, networkSetup[setup], setup, loss, bandwidth, delay)
        switches.append(nodes[0])
        hosts.extend(nodes[1])

    #Connect all switchs in line
    for i, sA in enumerate(switches):
        for sB in switches[i + 1:]:
            mininet.addLink(sA, sB) #bw = bandwidth * 20, delay = delay / 3, loss= loss / 2

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

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', help='server port', default=9999)
    parser.add_argument('-b', help='server transmission bitrate in kbps', default=2048)
    parser.add_argument('-n', help='how many subnetworks to build', default=3)
    parser.add_argument('-c', help='how many hosts per subnetwork', default=5)
    parser.add_argument('--loss', help='links loss percentage', default=0)
    parser.add_argument('--bandwidth', help='links bandwidth in mbps', default=0)
    parser.add_argument('--delay', help='links delay in ms', default=0)
    args = parser.parse_args()
    
    net = Mininet()

    info('*** Adding controller\n')
    net.addController('c0')

    info('*** Setting up networks ***\n')
    networkSetup = {}
    for i in range(200, 200 + int(args.n)):
        networkSetup['192.168.%s' % i] = int(args.c)

    info('     Config: %s\n' % networkSetup)
        
    nodes = setupNetworks(net, networkSetup, args.loss, args.bandwidth, args.delay)

    info('*** Starting network ***\n')
    net.start()

    info('*** Starting traffic server ***\n')
    server = nodes[1][0]
    startTrafficServer(server, int(args.p), int(args.b))

    time.sleep(2)

    info('*** Starting traffic clients ***\n')
    clients = nodes[1][1:]
    startTrafficClients(clients, server.IP(), int(args.p))

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
