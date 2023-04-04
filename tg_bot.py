import os


def main():
    folder_name = 'questions'
    files_names = os.listdir(path=folder_name)
    for file_name in files_names:
        file_path = os.path.join(folder_name, file_name)
        with open(file_path, mode='r', encoding='KOI8-R') as file:
            n = 0
            for line in file:
                print(line)
                n += 1
                if n == 47:
                    break


if __name__ == '__main__':
    main()
