from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import date, timedelta
import sys
from termcolor import cprint
import colorama
import subprocess

"""
    This script log in into korty.org service within the contex of
    AM Tenis Klub. Then it checks if there are any free courts within
    given date and hour.
    It checks if only full hour is available. Halfs are not regarded

"""

# wednesday nas no of 1
req_day = "Tuesday"
# req_hour = "19:00"
req_hours = ['19:00', '20:00', '21:00']


# map string of day into appropriate day number starting from
# Monday = 0, Tuesday = 1, etc
def days_to_numbers(req_day):
    days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
            "Sunday")

    day_cnt = 0
    # (0 - Monday, 6 - Sunday)
    for day in days:
        if day == req_day:
            return day_cnt
        day_cnt = day_cnt + 1


# chrome webdriver configuration to be run headless
run_headless = 1
# create instance of browser
chrome_options = Options()
chrome_options.add_argument("--headless")
if run_headless == 0:
    driver = webdriver.Chrome()
elif run_headless == 1:
    driver = webdriver.Chrome(options=chrome_options)
else:
    cprint('Browser not correctly configured!\nExiting...!', 'red')
    exit()

# just to have colorful output on windows console
colorama.init()
# to separate output from script visually
intro = '\n\n\n'
# sys.stdout.write(intro)
subprocess.call(["cls"], shell=True)
print(intro)
# for each our provided in hours array
for req_hour in req_hours:

    requested_day = days_to_numbers(req_day)
    requested_hour = req_hour

    # variable for time slot
    time_slot = None
    # variable for court number
    court_number = None
    # Constant for text meaning reservation to be made put in href
    RESERVE = "Rezerwuj"
    # login config
    main_url = "https://korty.org/klub/"
    club_tag = "am-tenis"
    url_params = "/dedykowane?data_grafiku=<YYYY-MM-DD>&dyscyplina=1&strona="
    court_url_template = main_url + club_tag + url_params

    play_date = date.today()
    today_name = date.strftime(play_date, '%A')
    no_of_today = date.weekday(play_date)

    # array for messages
    messages = []
    # increment through whole week in order to find next date to be checked
    courts_url = ""
    for i in range(7):
        # increment date of 1
        play_date += timedelta(days=1)
        # get the number of day
        no_of_play_date = date.weekday(play_date)
        # if number of day is equal to the one we are looking for
        # then build ULR end exit
        if no_of_play_date == requested_day:
            courts_url = court_url_template.replace("<YYYY-MM-DD>",
                                                    str(play_date))
            break
    text = '\tChecking court availability for date: ' + str(req_day) + ' '\
           + str(play_date) + ' at ' + str(req_hour)
    cprint(text, 'blue')
    messages.append(play_date)
    # because there are two tabs of courts on
    # AM Tenis we need to go through both
    cprint('\tLooking: ', 'blue', end="")
    for tab in range(2):
        court_tab_url = courts_url + str(tab)
        driver.get(court_tab_url)
        # check if you are on the requested site
        # print("Connecting to the website: ", court_tab_url)
        assert "AM Tenis" in driver.title
        table = driver.find_element_by_tag_name("tbody")
        rows = table.find_elements_by_tag_name("tr")
        row_no = 1
        prv_time_slot = None
        for row in rows:
            slot_flag = 0
            hour_flag = 0
            cells = row.find_elements_by_tag_name("td")
            column_no = 1
            for cell in cells:
                # progress bar
                if column_no == 4:
                    sys.stdout.write('.')
                    sys.stdout.flush()

                # reset flag showing if something to be reserved has been found
                is_free = 0
                # first TD tag contains time of slot
                if column_no == 1:
                    time_slot = cell.text
                # if any of cells in given time slot has value of
                # RESERVE variable
                # set flag upon this lot
                if cell.find_elements_by_link_text(RESERVE) and \
                        time_slot == req_hour:
                    messages.append(time_slot)
                # increment column counter
                column_no = column_no + 1
            # increment row counter

    # Clean up duplicated messages
    msg_cnt = 0
    courts_no = 0
    for msg in messages:
        if msg_cnt == 0:
            pass
        if msg == requested_hour:
            courts_no = courts_no + 1
            msg_cnt = msg_cnt + 1
    if courts_no > 0:
        if courts_no == 1:
            plural = "is"
        else:
            plural = "are"
        text = '\n\n\t\t' + 'For nearest ' + req_day + ' ' + str(play_date) + \
               ' there ' + plural + ' available ' + str(courts_no) + \
               ' courts at ' + str(req_hour) + '\n'
        cprint(text, 'green')
    else:
        text = '\n\n\t\t' + 'There is no available courts at nearest ' + \
               req_day + ' ' + str(play_date) + ' at ' + req_hour + '\n'
        cprint(text, 'red')
# close browser
text = "\tClosing browser... need to wait..."
cprint(text, 'blue')
driver.quit()
cprint("\t***************************************** All done!" + intro, 'blue')
# try to send email here

