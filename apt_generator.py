import json
def apt_generator(path:str) -> list:
    apartments = []
    with open(path) as file:
        building_configs = json.load(file)
        for config in building_configs:
            buildings = config["buildings"]
            for building in buildings:
                floors = config["floors"]
                for floor in range(floors):
                    apts = config["apartments_per_floor"]
                    for apt in range(1,apts+1):
                        apt_num = floor * 10 + apt
                        apt_record = {"apt_num" : apt_num,"building" : building,"floor": floor,"display_name": f"{building}/{apt_num}"}
                        apartments.append(apt_record)
        return apartments          


