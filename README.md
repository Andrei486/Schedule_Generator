# Carleton Schedule Generator

---

## Current Version
Version 1.0.1, July 7 2020
## History
- Version 1.0.0, July 4 2020: base functionality
- Version 1.0.1, July 7 2020: fixed an issue in which prohibited sections would be ignored

## Information
This project can be reached at apopescu486@gmail.com.

## Description
This application is a schedule generator for Carleton University, which can use up-to-date data from Carleton University's public course listings to find out what sections are available for specified courses and construct schedules using that information. This can also generate a smaller **sample** of schedules, which cover as many different sections as possible, in case some become full or unavailable.
Search options include:
- Term to schedule for
- List of required courses
- List of possible elective courses
- Number of electives required among those in the list
- List of sections that should not be considered

## Installation
Users of this application should download the `schedule_generator.exe` installer and extract the file to an empty folder. A message will be displayed once installation is complete.

## Usage
After running the installer, run the executable `Application.exe` that will be created. Wait for a window to open, then select your search options and generate the schedules as instructed in the window.
The application will generate files in the same folder it is placed in. Two of these contain data related to the search and its options, while two others are output files containing the created schedules. Because of this, the last search can be remembered and reused without re-specifying options.

## Known Issues
- The first time the application is used to make a search, Windows may ask for permission to open a browser. This will cause the search to fail, regardless of whether permission is granted. The user must exit the application and return to it in order to properly execute the search.
- The generator may schedule sections shown as "Open" even though all remaining seats are reserved by the Department.

## Credits
Andrei Popescu (apopescu486@gmail.com)

## License
MIT License

Copyright (c) [2020] [Andrei Popescu]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
