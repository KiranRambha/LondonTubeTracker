import concurrent.futures
import requests
from datetime import datetime

# Helper functions
def get_station_arrivals(station_id):
    """Fetch station arrival data with error handling."""
    headers = {'Cache-Control': 'no-cache'}
    url = f"https://api.tfl.gov.uk/StopPoint/{station_id}/Arrivals"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return []

def format_time_to_station(seconds, expected_arrival):
    """Format time to station into a readable format."""
    if seconds < 60:
        return "Due"
    dt = datetime.strptime(expected_arrival, '%Y-%m-%dT%H:%M:%SZ')
    return dt.strftime('%H:%M')

def group_arrivals_by_platform(arrivals, platform_name):
    """Filter and sort arrivals by platform."""
    return sorted(
        [
            {
                **arrival,
                'formattedTime': format_time_to_station(arrival['timeToStation'], arrival['expectedArrival'])
            }
            for arrival in arrivals if arrival.get('platformName') == platform_name
        ],
        key=lambda x: x['expectedArrival']
    )

def group_arrivals_by_line(arrivals, line_ids):
    """Group arrivals by line ID and format times."""
    results = {line_id: [] for line_id in line_ids}
    for arrival in arrivals:
        line_id = arrival.get('lineId')
        if line_id in line_ids:
            formatted_time = format_time_to_station(arrival['timeToStation'], arrival['expectedArrival'])
            results[line_id].append((arrival['timeToStation'], formatted_time))

    # Sort and format results
    for line_id, times in results.items():
        times.sort()  # Sort by actual time-to-station
        results[line_id] = " | ".join(time[1] for time in times)

    return {k: v for k, v in results.items() if v}

def get_arrivals_by_line_simplified(station_id, line_ids):
    arrivals = get_station_arrivals(station_id)
    return group_arrivals_by_line(arrivals, line_ids)

# Main Functions
def get_arrivals_and_latest_location(station_id, platform_name):
    arrivals = get_station_arrivals(station_id)
    platform_arrivals = group_arrivals_by_platform(arrivals, platform_name)

    if platform_arrivals:
        return {
            'arrival_times': " | ".join(arrival['formattedTime'] for arrival in platform_arrivals),
            'current_location': platform_arrivals[0].get('currentLocation', "Not Available")
        }
    return {'arrival_times': "", 'current_location': "Not Available"}

def get_arrivals_and_destination(station_id, platform_name):
    arrivals = get_station_arrivals(station_id)
    platform_arrivals = group_arrivals_by_platform(arrivals, platform_name)

    destinations = {}
    for arrival in platform_arrivals:
        destination = arrival.get('destinationName') or arrival.get('towards', 'Unknown Destination')
        destinations.setdefault(destination, []).append(arrival['formattedTime'])

    return [
        {'destination': dest, 'arrival_times': " | ".join(times)}
        for dest, times in destinations.items()
    ]

def fetch_bus_arrivals_concurrently(bus_list):
    """Fetch arrivals concurrently for multiple bus stations and lines."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(bus_list)) as executor:
        future_to_bus_info = {
            executor.submit(
                get_arrivals_by_line_simplified, bus['station_id'], bus['lineId']
            ): bus
            for bus in bus_list
        }
        results_dict = {}
        for future in concurrent.futures.as_completed(future_to_bus_info):
            bus_info = future_to_bus_info[future]
            try:
                results = future.result()
                results_dict[bus_info['station_id']] = results
            except Exception as exc:
                print(f"Error fetching data for station {bus_info['station_id']}: {exc}")
        return results_dict
