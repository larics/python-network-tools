#!/usr/bin/env python
# Tool for quickly checking network performance

import argparse
import subprocess
import re
import sys
import platform
import os
import time

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
        ping = subprocess.Popen(['ping', addr, '-n', str(n)],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        (out,err) = ping.communicate()
        if out:
            try:
                minimum = int(re.findall(r'Minimum = (\d+)', out)[0])
                maximum = int(re.findall(r'Maximum = (\d+)', out)[0])
                average = int(re.findall(r'Average = (\d+)', out)[0])
                lost = int(re.findall(r'Lost = (\d+)', out)[0])
            except:
                print('No data for one of minimum/maximum/average/lost')
        else:
            print('No ping')

    except subprocess.CalledProcessError:
        print('Could not get a ping!')

    return(minimum, maximum, average, lost)

def copy_test(addr, file_path):

    print('Transferring file {0} to address {1}.'.format(file_path, addr))
    
    # Initialize values
    size = os.path.getsize(file_path) / (1000 * 1000) # File size, in MB
    start_time = time.time()
    time.sleep(1)
    elapsed_time = time.time() - start_time
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
    parser.add_argument('-t','--target_platform', help='Target platform.', required=True)
    args = parser.parse_args()

    # Get time and platform info
    print('Platform: {0}\n'.format(platform.platform()))
    
    # Run the ping test
    (minimum, maximum, average, lost) = ping_test(args.address, args.n)
    print('--- Ping test results (approximate round-trip times) ---\n')
    print('Minimum = {0}ms\nMaximum = {1}ms\nAverage = {2}ms\nLost = {3}%\n\n'.format(minimum,
                                                                           maximum,
                                                                           average,
                                                                           lost / args.n * 100))

    # Run the file transfer test
    data_folder = args.data_folder
    if data_folder[-1] != '/': 
          data_folder = data_folder + '/'
    (size, elapsed_time, throughput) = copy_test(args.address, data_folder + args.data_file)
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
          logwriter.writerow(['Platform', platform.platform()])
          logwriter.writerow(['Time', str(datetime.now())])
          logwriter.writerow(['Target', args.address])
          logwriter.writerow(['Target platform', args.target_platform])
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

          
