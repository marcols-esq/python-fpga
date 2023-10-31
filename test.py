from atlys_interface import AtlysInterface

if __name__ == '__main__':
    atlys = AtlysInterface()
    test_value = 0x4
    test_address = 0x6
    atlys.write(test_address, test_value)
    if (atlys.read(test_address) == test_value):
        print("Read value matches written value")
    else:
        print("Read value does not match written value")
    
