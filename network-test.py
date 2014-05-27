#!/usr/bin/env python
# Tool for quickly checking network performance

import argparse
import subprocess
import re
import sys
import platform
import os
import time

import paramiko

# For logging
from datetime import datetime
import csv


def ping_test(addr, n = 10):
    
    print('Testing {0} pings to address {1}.\n'.format(n,addr))
    
    # Initialize values
    minimum = float('Inf')
    maximum = float('Inf')
    average = float('Inf')    
    lost = float('Inf')

    count_flag = '-c'
    if 'win' in sys.platform:
        count_flag = '-n'

    try:
        ping = subprocess.Popen(['ping', addr, count_flag, str(n)],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        (out,err) = ping.communicate()
        if out and ('win' in sys.platform):
            try:
                # Windows-specific output parsing
                minimum = int(re.findall(r'Minimum = (\d+)', out)[0])
                maximum = int(re.findall(r'Maximum = (\d+)', out)[0])
                average = int(re.findall(r'Average = (\d+)', out)[0])
                lost = int(re.findall(r'Lost = (\d+)', out)[0])
            except:
                print('No data for one of minimum/maximum/average/lost')
        elif out:
            try:
                # Linux-specific output parsing
                summary = re.findall(r'rtt min/avg/max/mdev = (\S+)', out)[0]
                (minimum, average, maximum, mdev) = (float(x) for x in summary.split('/'))
                lost = int(re.findall(r'(\d+)% packet loss', out)[0])
            except:
                print('No data for one of minimum/maximum/average/lost')
        else:
            print('No ping')

    except subprocess.CalledProcessError:
        print('Could not get a ping!')

    return(minimum, maximum, average, lost)

def copy_test(addr, file_path, target_path, username, password):

    print('Transferring file {0} to {1}:{2}.'.format(file_path, addr, target_path))
    
    # Determine file size
    size = os.path.getsize(file_path) / (1000 * 1000) # File size, in MB
    elapsed_time = float('Inf')

    ### Set up the SFTP connection ###
    
    # Get known host keys
    host_keys = {}
    try:
        host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
    except IOError:
        print('*** Unable to open host keys file!')
    if host_keys.has_key(addr):
        hostkeytype = host_keys[addr].keys()[0]
        hostkey = host_keys[addr][hostkeytype]
        print('Using host key of type {0}'.format(hostkeytype))

    # Connect and use paramiko Transport to negotiate SSH2 accross the connection
    port = 22
    try:
        print('Establishing SSH connection to: {0}:{1}'.format(addr, port))
        t = paramiko.Transport((addr, port))
        #t.start_client()
        t.connect(username=username, password=password, hostkey=hostkey)
        print('Connection established! Starting file transfer, please be patient...')
        sftp = paramiko.SFTPClient.from_transport(t)

        start_time = time.time()
        sftp.put(file_path, target_path)
        elapsed_time = time.time() - start_time

    except Exception, e:
        print('*** Caught exception {0}: {1}'.format(e.__class__, e))
        try:
            t.close()
        except:
            pass


    throughput = size * 8 / elapsed_time

    return (size, elapsed_time, throughput)

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Tool for network performance testing.')
    parser.add_argument('-a','--address', help='Target address.', required=True)
    parser.add_argument('-n', help='Number of times to ping.', type=int, default=10)
    parser.add_argument('--log_folder', help='Folder for storing logs.', default='./logs')
    parser.add_argument('--data_folder', help='Folder for keeping data.', default='./data')
    parser.add_argument('-f','--data_file', help='Data file name.', required=True)
    parser.add_argument('-l','--location', help='Test location.', required=True)
    parser.add_argument('-u','--username', help='Remote machine username.', required=True)
    parser.add_argument('-p','--password', help='Remote machine password.', required=True)
    parser.add_argument('-d','--remote_dir', 
                        help='Remote folder, relative to /home/username.', 
                        default='Downloads')
    args = parser.parse_args()

    # Get time and platform info
    print('Platform: {0}\n'.format(platform.platform()))
    
    # Run the ping test
    (minimum, maximum, average, lost) = ping_test(args.address, args.n)
    print('--- Ping test results (approximate round-trip times) ---\n')
    print('Minimum = {0}ms\nMaximum = {1}ms\nAverage = {2}ms\nLost = {3}%\n\n'.format(minimum,
                                                                           maximum,
                                                                           average,
                                                                           lost))

    # Run the file transfer test
    data_folder = args.data_folder
    if data_folder[-1] != '/': 
          data_folder = data_folder + '/'
    remote_dir = args.remote_dir
    if remote_dir[-1] != '/':
        remote_dir += '/'
    (size, elapsed_time, throughput) = copy_test(args.address, 
                                                 data_folder + args.data_file,
                                                 '/home/' + args.username + '/' + remote_dir + args.data_file,
                                                 args.username,
                                                 args.password)

    print('--- File transfer test results ---\n')
    print('File size = {0}MB'.format(size))
    print('Elapsed time = {0}s'.format(elapsed_time))
    print('Average throughput = {0}Mbps'.format(throughput))

    # Save the results to log file
    now_str = str(datetime.now()).split('.')[0]
    now_str = now_str.replace(' ','-').replace(':','-')
    log_folder = args.log_folder
    if log_folder[-1] != '/':
          log_folder = log_folder + '/'
    log_path = log_folder + now_str + '_' + args.location + '.csv'
    with open(log_path, 'wb') as csvfile:
          logwriter = csv.writer(csvfile, delimiter=';')
          logwriter.writerow(['Location', args.location])
          logwriter.writerow(['Time', str(datetime.now())])
          logwriter.writerow(['Platform', platform.platform()])
          logwriter.writerow(['Network adapter', ''])
          logwriter.writerow(['Target', args.address])
          logwriter.writerow(['Target platform', ''])
          logwriter.writerow(['Target network adapter', ''])
          logwriter.writerow(['--- Ping test ---', ''])
          logwriter.writerow(['Ping count', args.n])
          logwriter.writerow(['Ping minimum round-trip [ms]', minimum])
          logwriter.writerow(['Ping maximum round-trip [ms]', maximum])
          logwriter.writerow(['Ping average round-trip [ms]', average])
          logwriter.writerow(['Ping lost packages [%]', lost])
          logwriter.writerow(['--- File transfer test ---', ''])
          logwriter.writerow(['File size [MB]', size])
          logwriter.writerow(['Transfer time [s]', elapsed_time])
          logwriter.writerow(['Throughput [Mb/s]', throughput])

          
