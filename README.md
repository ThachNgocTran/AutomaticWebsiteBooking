# AutomaticWebsiteBooking
A tool that helps automate the checking of availability and the booking. It's website-specific.

More details coming!!!

# Usage

```
python AutomaticBooking.py -url "https://web.daslab.app/book/location/1051" -url_openingtimes "https://api.daslab.app/locations/1051/opening_times"
```

# Assumption

+ The user should be already logged in.
+ The cookie banner (when first time accessing the website) should be already clicked.

# Requirements

+ Chrome Browser (tested: v91)
+ Chrome Driver
  + https://sites.google.com/chromium.org/driver/downloads
  + Put exe location into `PATH`.
+ Selenium

# Demo

[![IMAGE ALT TEXT](http://img.youtube.com/vi/Q7rMhvYnFsU/0.jpg)](https://www.youtube.com/watch?v=Q7rMhvYnFsU "Automate booking in Chrome with Python and Selenium")

# TODO

1. Figure out a way to click on Cookie banner when first visiting.
2. Figure out a way to check if requiring login banner at any step.
3. Figure out a way to not kill Chrome at the end, allowing users to log in.
