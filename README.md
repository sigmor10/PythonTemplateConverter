# PythonTemplateConverter
A simple python app for converting xml template files to organized yaml format.
**Made in Python 3.13**.

## Main functionality

- Conversion of **xml** files of known structure to explicitly defined in code structure and saves result **yaml** format.
- Cleaning **SQL** queries and redefining parameters to work with **.Net Dapper**.
- Changing **Declare** statements by adding suffix **"_sql"** to avoid collision with redefined parameters.
- Can convert multiple files in single run and recreate folder structure they were provided in.

## Compiling

- Download repository and install dependencies.
- Place xml files to convert in **input** subdirectory of the root directory of the project
- Run the app
- Collect converted files from newly created out directory.

## Used packages

- pathlib
- xml.etree.ElementTree
- yaml
- re

## Author
Jakub Kinder (sigmor10)

## License

[LICENSE](LICENSE)