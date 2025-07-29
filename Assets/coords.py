from collections import namedtuple
__transl_x = 123888
__transl_y = 158000
__scale = 459
Point = namedtuple('Point', ['x', 'y'])
def get_number_in_range(min_value, max_value):
    try:
        number = int(input(f"Enter a number between {min_value} and {max_value}: "))
        if min_value <= number <= max_value:
            return number
        else:
            print("Number is out of range.")
            return None
    except ValueError:
        print("Invalid input. Please enter an integer.")
        return None
def sav_to_map(x: float, y: float) -> Point:
    newX = x + __transl_x
    newY = y - __transl_y
    return Point(x=round(newY/__scale), y=round(newX/__scale))
def map_to_sav(x: int, y: int) -> Point:
    newX = x * __scale
    newY = y * __scale
    return Point(x=newY - __transl_x, y=newX + __transl_y)
def convert_coordinates(conversion_type=None, x=None, y=None):
    if conversion_type is None:
        print("1. Convert .sav to in-game")
        print("2. Convert in-game to .sav")
        choice = get_number_in_range(1, 2)
        if choice is None: return
        conversion_type = "sav_to_map" if choice == 1 else "map_to_sav"
    if x is None or y is None:
        try:
            if conversion_type == "sav_to_map":
                x = int(input("Enter Sav X coordinate: "))
                y = int(input("Enter Sav Y coordinate: "))
            else:
                x = int(input("Enter In-game X coordinate: "))
                y = int(input("Enter In-game Y coordinate: "))
        except ValueError:
            print("Invalid input. Please enter an integer.")
            return
    if conversion_type == "sav_to_map":
        result = sav_to_map(x, y)
    else:
        result = map_to_sav(x, y)
    print(result)
    return result
def main(): convert_coordinates()
if __name__ == "__main__": main()