from uuid import uuid4
import hashlib

def uuid():
    return str(uuid4())

string_number_map = {}
def convert_to_number(string):
    '''Attempt to create a unique integer for a string.  Cannot guarantee complete uniqueness'''
    global string_number_map
    if string in string_number_map:
        return string_number_map[string]
    else:
        string_val = int(str(int(hashlib.md5(string.encode('utf-8')).hexdigest(), 16))[0:7]) # This is 7 because enums seem to error above this value
        string_number_map[string] = string_val
        return string_val
