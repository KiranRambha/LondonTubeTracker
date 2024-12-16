def get_refresh_count():
    """
    Reads the current refresh count from 'partial_refresh_count.txt'.
    
    Returns:
        int: The current refresh count.
    """
    try:
        with open('partial_refresh_count.txt', 'r') as file:
            return int(file.read())
    except FileNotFoundError:
        # If the file does not exist, default to 0
        return 0

def set_refresh_count(count):
    """
    Writes a new refresh count to 'partial_refresh_count.txt'.
    
    Args:
        count (int): The refresh count to write.
    """
    try:
        with open('partial_refresh_count.txt', 'w') as file:
            file.write(str(count))
    except Exception as e:
        # If there's an error, print it
        print(f"Error setting refresh count: {e}")