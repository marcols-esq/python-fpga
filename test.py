from interface.atlys_interface import AtlysInterface
from sys import argv

if __name__ == '__main__':
    atlys = AtlysInterface(argv[1])
    test_value = 0x4
    test_address = 0x6
    atlys.write(test_address, test_value)
    if (atlys.read(test_address) == test_value):
        print("Read value matches written value")
    else:
        print("Read value does not match written value")
    
