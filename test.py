from datetime import date

# Sample dictionary with unique keys and lists of lists
data = {
    'key1': [[date(2023, 5, 17), 'value1'], [date(2023, 5, 17), 'value2']],
    'key2': [[date(2024, 6, 1), 'value3'], [date(2024, 6, 1), 'value4']],
    'key3': [[date(2022, 12, 25), 'value5'], [date(2022, 12, 25), 'value6']]
}


# Function to find the key with the most recent date
def find_commit_with_most_recent_date(data):
    most_recent_date = date.min
    most_recent_commit = None

    for key, lists in data.items():
        current_date = lists[0][2] if lists else date.min

        if current_date > most_recent_date:
            most_recent_date = current_date
            most_recent_commit = key

    return most_recent_commit



# Get the key and its list with the most recent date
recent_key, recent_list = find_key_with_most_recent_date(data)

print(f"The key with the most recent date is: {recent_key}")
print(f"The list for this key is: {recent_list}")
