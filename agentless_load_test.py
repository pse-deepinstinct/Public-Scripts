# Example of to to load test an Agentless scanner by repeatedly sending a file
# for scanning and then printing a summary of the results to the console

import deepinstinctagentless as di, time, json

#CONFIGURATION
scanner_ip = '192.168.0.50'
file_to_scan = 'example.pdf'
number_of_scans = 5000

# ESTABLISH VARIABLES
start_time = time.perf_counter()
n = 0
total_scan_duration_in_microseconds = 0
total_file_size_in_bytes = 0

# EXECUTE THE SCANS
while n < number_of_scans:
    verdict = di.scan_file(file_to_scan, scanner_ip)
    total_scan_duration_in_microseconds += verdict['scan_duration_in_microseconds']
    total_file_size_in_bytes += verdict['file_size_in_bytes']
    n += 1
    print('Completed scan', n,'of',number_of_scans, end='\r')

# CALCULATE RESULTS
results = {}
results['scan_count'] = n
results['runtime_in_seconds'] = time.perf_counter() - start_time
results['scan_time_in_seconds'] = total_scan_duration_in_microseconds / 1000000
results['scan_volume_in_megabytes'] = total_file_size_in_bytes / 1000000
results['ratio_of_time_spent_scanning'] = results['scan_time_in_seconds'] / results['runtime_in_seconds']
results['gross_throughput_in_megabytes_per_second'] = results['scan_volume_in_megabytes'] / results['scan_time_in_seconds']
results['net_throughput_in_megabytes_per_second'] = results['scan_volume_in_megabytes'] / results['runtime_in_seconds']

# PRINT RESULTS TO CONSOLE
print('\n', json.dumps(results, indent=4))
