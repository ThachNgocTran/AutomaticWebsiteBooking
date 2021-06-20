# AutomaticWebsiteBooking
A tool that helps automate the checking of availability and the booking. It's website-specific. As an example, website "https://web.daslab.app" is used.

# Usage

```
python AutomaticBooking.py -url "https://web.daslab.app/book/location/1051" -url_openingtimes "https://api.daslab.app/locations/1051/opening_times"
```

+ After opening, Chrome is not killed. Therefore, users can take advantage of this in order to log in or to click any cookie banner. The next time when the script is run, the current Chrome session will be attempted to be re-used.

# Assumption

The flow of steps should be as expected as possible. Some disruptions should be prevented, such as:

+ Login banner.
+ Cookie banner.

# Requirements

+ Chrome Browser (tested: v91)
+ Chrome Driver
  + https://sites.google.com/chromium.org/driver/downloads
  + Put exe location into `PATH`.
+ Selenium

# Demo

+ YouTube

[![IMAGE ALT TEXT](http://img.youtube.com/vi/Q7rMhvYnFsU/0.jpg)](https://www.youtube.com/watch?v=Q7rMhvYnFsU "Automate booking in Chrome with Python and Selenium")

+ Medium

[Checking and Booking of Internet services. Automatically.](https://thachngoctran.medium.com/checking-and-booking-of-internet-services-automatically-a5163395aec9)

# TODO

1. Figure out a way to click on Cookie banner when first visiting.
2. Figure out a way to check if requiring login banner at any step.
