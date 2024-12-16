import concurrent.futures
import requests
from datetime import datetime

def get_station_arrivals(station_id):
    headers = {
        'Cache-Control': 'no-cache'
    }
    url = f"https://api.tfl.gov.uk/StopPoint/{station_id}/Arrivals"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return str(e)

def get_time_without_seconds(dt_str):
    dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%SZ')
    return dt.strftime('%H:%M')

def format_time_to_station(seconds, expectedArrival):
    if seconds < 60:
        return "Due"
    else:
        return get_time_without_seconds(expectedArrival)

def filter_arrivals_by_platform(stationId, platformName):
    arrivals = get_station_arrivals(stationId)

    filtered_arrivals = [
        {**arrival, 'timeToStation': format_time_to_station(arrival['timeToStation'], arrival['expectedArrival'])}
        for arrival in arrivals
        if arrival['platformName'] == platformName
    ]
    
    return sorted(filtered_arrivals, key=lambda x: x['expectedArrival'])

def get_arrivals_and_latest_location(station_id, platform_name):
    filtered_arrivals = filter_arrivals_by_platform(station_id, platform_name)

    if filtered_arrivals:
        arrivals_str = ' | '.join(
            f"{arrival['timeToStation']}" if arrival['timeToStation'] != "Due" else "Due"
            for arrival in filtered_arrivals
        )
        
        current_location = filtered_arrivals[0]['currentLocation']
    else:
        arrivals_str = ""
        current_location = "Not Available"

    return {
        'arrival_times': arrivals_str,
        'current_location': current_location
    }

def get_arrivals_and_destination(station_id, platform_name):
    filtered_arrivals = filter_arrivals_by_platform(station_id, platform_name)
    
    # Group by destination
    destinations = {}
    for arrival in filtered_arrivals:
        destination = arrival.get('destinationName') or arrival.get('towards')
        if destination not in destinations:
            destinations[destination] = []
        destinations[destination].append(arrival['timeToStation'])

    # Build the result list
    result = []
    for destination, times in destinations.items():
        times_str = ' | '.join(
            f"{time}" if time != "Due" else "Due"
            for time in times
        )
        result.append({
            'destination': destination,
            'arrival_times': times_str
        })
        
    return result

def get_arrivals_by_line_simplified(station_id, line_ids):
    # Fetching all arrivals at the given station
    arrivals = get_station_arrivals(station_id)

    # Dictionary to store the formatted and sorted results by line ID
    results = {}

    # Processing each line ID in the list
    for line_id in line_ids:
        # Formatting and filtering arrivals by line ID
        line_arrivals = [
            (arrival['timeToStation'], format_time_to_station(arrival['timeToStation'], arrival['expectedArrival']))
            for arrival in arrivals if 'lineId' in arrival and arrival['lineId'] == line_id
        ]

        if line_arrivals:
            # Sort by actual time-to-station value, which is the first element of the tuple
            line_arrivals.sort(key=lambda x: x[0])
            # Extract the formatted times for the final result
            formatted_arrival_times = [time[1] for time in line_arrivals]
            results[line_id] = " | ".join(formatted_arrival_times)

    return results

def fetch_bus_arrivals_concurrently(bus_list):
    def fetch_and_process_arrivals(bus_info):
        station_id = bus_info['station_id']
        line_ids = bus_info['lineId']
        return get_arrivals_by_line_simplified(station_id, line_ids)

    # Define the number of workers based on bus list length, or tailor as needed
    num_workers = len(bus_list)

    # Use ThreadPoolExecutor to manage a pool of threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Mapping each element of bus_list to the function
        future_to_bus_info = {executor.submit(fetch_and_process_arrivals, bus): bus for bus in bus_list}

        # Collecting results as they complete
        results_dict = {}
        for future in concurrent.futures.as_completed(future_to_bus_info):
            bus_info = future_to_bus_info[future]
            try:
                results = future.result()
                results_dict[bus_info['station_id']] = results
            except Exception as exc:
                print(f"{bus_info['station_id']} generated an exception: {exc}")

        return results_dict