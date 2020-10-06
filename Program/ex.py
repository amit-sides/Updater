import PySimpleGUI as sg


def main():
    sg.theme('DarkAmber')
    
    with open("text.txt", "r") as f:
        info = f.read()
    
    sg.popup("Ex", info)
    
    pass


if __name__ == "__main__":
    main()
