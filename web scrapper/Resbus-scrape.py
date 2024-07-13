
#Import required libraries
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import traceback
from selenium.webdriver.common.keys import Keys
import pymysql

'''Function to get details of each RTC. @input is url for one RTC'''
def getRTCDetails(rtcURL):
    routes = {}
    try:
        print (rtcURL)
        rtcDriver = webdriver.Chrome()
        rtcDriver.get(rtcURL)
        delaySecs = 15
        page_loaded = EC.presence_of_element_located((By.CLASS_NAME,'DC_117_pageTabs'))
        WebDriverWait(rtcDriver,delaySecs).until(page_loaded)
        #pages = rtcDriver.find_elements(By.CLASS_NAME,'DC_117_pageTabs')
        #print(len(pages))
        routes = getRoutes(rtcDriver)
        for routeName in routes:
            getBuses(rtcDriver,routeName, routes[routeName])
    except TimeoutException:
        print('No routes found for ',rtcURL)
    except Exception as e:
        print(traceback.format_exc())
    finally:
        print(routes)
        rtcDriver.quit()

'''Function to collect route details for the given RTC. Details include Route Name & URL for the Route'''
def getRoutes(pDriver):
    routeURLs = {}
    try:
        pageTable = pDriver.find_element(By.CLASS_NAME, 'DC_117_paginationTable')
        #Scroll to pagination table, otherwise click event will not be enabled
        pDriver.execute_script("arguments[0].scrollIntoView();", pageTable)
        pages = pDriver.find_elements(By.CLASS_NAME,'DC_117_pageTabs')
        # loop through the pages and get route details
        isFirst = True
        delaySecs = 15
        for page in pages:
            page.click()
            page_loaded = EC.presence_of_element_located((By.CLASS_NAME,'route'))
            WebDriverWait(pDriver,delaySecs).until(page_loaded)
                
            routeLinks = pDriver.find_elements(By.CLASS_NAME,'route')
            for route in routeLinks:
                routeURLs.setdefault(route.text,route.get_attribute('href'))
                # routeURLs.append(route.get_attribute('href'))
            isFirst = False
        return routeURLs
    except Exception as e:
        print(traceback.format_exc())
        raise e

''' Function to get buses on a given route'''
''' Inputs: active webdriver, route dictionary '''
def scroll_down(elem, num):
    for _ in range(num):
        time.sleep(.01)
        elem.send_keys(Keys.PAGE_DOWN)

''' Scroll the page till bottom to load all buses '''
def scroll_page(pDriver):
    SCROLL_PAUSE_TIME = 2
    elem = pDriver.find_element(By.TAG_NAME,"body")
    prev_height = elem.get_attribute("scrollHeight")
    for i in range(0, 500):
        # note that the pause between page downs is only .01 seconds
        # in this case that would be a sum of 1 second waiting time
        scroll_down(elem,100)
        # Wait to allow new items to load
        time.sleep(SCROLL_PAUSE_TIME)

        #check to see if scrollable space got larger
        #also we're waiting until the second iteration to give time for the initial loading
        if elem.get_attribute("scrollHeight") == prev_height and i > 0:
            break
        prev_height = elem.get_attribute("scrollHeight")     

'''For the given route, get all the buses'''        
def getBuses(pDriver,routeName,routeURL):
    try:
        url = routeURL
        pDriver.get(url)
        delaySecs = 15
        page_loaded = EC.presence_of_element_located((By.CLASS_NAME,'bus-items'))
        WebDriverWait(pDriver,delaySecs).until(page_loaded)
        # if there are any govt buses, click & expand them 
        resultSection = pDriver.find_element(By.ID,'result-section')
        groupData = resultSection.find_elements(By.CLASS_NAME,'group-data')
        i = len(groupData)
        # if there are more than one govt bus services, start from bottom
        # otherwise endless scroll will hide the View button making in unclickable
        while (i > 0):
            button = groupData[i-1].find_element(By.CLASS_NAME,'button')
            #pDriver.execute_script("arguments[0].scrollIntoView();", button)
            button.click()
            pDriver.find_element(By.TAG_NAME,'body').send_keys(Keys.PAGE_UP)
            i = i - 1
        
        scroll_page(pDriver)
        busItems = pDriver.find_elements(By.CLASS_NAME,'bus-items')
        print('Number of busItems : ', len(busItems))
        
        insertBusDetails(busItems,routeName,routeURL)
        
        
    except Exception as e:
        print(traceback.format_exc())
        raise e
    
''' Parse and insert bus details '''
def insertBusDetails(busItems,routeName,routeURL):
#     db_cols = ['route_name','route_link','bus_name','bus_type','depart_time','duration','arrival_time',
#               'rating','price','seats_available','depart_loc','arrival_loc']
    try:
        #Todo: this function call insert per row... efficient method is to call multiple inserts or df to sql
        conn = pymysql.connect(host='localhost', 
            user='root',  
            password = "Stars@4321", 
            db='redbus', 
            ) 
        cur  = conn.cursor()
        for busItem in busItems:
            buses = busItem.find_elements(By.CLASS_NAME,'bus-item-details')
            for bus in buses:
                try:
                    busName = bus.find_element(By.CLASS_NAME, 'travels').text
                    busType = bus.find_element(By.CLASS_NAME, 'bus-type').text
                    depTime = bus.find_element(By.CLASS_NAME, 'dp-time').text
                    depLoc = bus.find_element(By.CLASS_NAME, 'dp-loc').text
                    duration = bus.find_element(By.CLASS_NAME, 'dur').text
                    arrivalTime = bus.find_element(By.CLASS_NAME, 'bp-time').text
                    arrivalLoc = bus.find_element(By.CLASS_NAME, 'bp-loc').text
                    rating = bus.find_element(By.CLASS_NAME, 'rating-sec').text
                    rating = float(rating) if is_float(rating) else 0
                    fare = bus.find_element(By.CLASS_NAME, 'fare').text
                    fare = extract_fare(fare)
                    seatsLeft = bus.find_element(By.CLASS_NAME, 'seat-left').text
                    seatsLeft = extract_seats(seatsLeft)
                    # windowsLeft = bus.find_element(By.CLASS_NAME, 'window-left').text
                    # print(routeName,routeURL,busName,busType,depTime,depLoc,duration,arrivalTime,arrivalLoc,rating,fare,seatsLeft)
                    query = f"INSERT INTO bus_routes1 (route_name,route_link,bus_name,bus_type,depart_time,duration, \
                                arrival_time,rating,price,seats_available,depart_loc,arrival_loc) \
                                values(\"{routeName}\", \"{routeURL}\", \"{busName}\",\"{busType}\",\"{depTime}\", \
                               \"{duration}\",\"{arrivalTime}\",{rating},{fare},{seatsLeft},\"{depLoc}\",\"{arrivalLoc}\")"
                    cur.execute(query) 
                except NoSuchElementException as e:
                    print(f'Error inserting :{routeName} , {e.msg}')
                except Exception as e:
                    print(query)
                    print(f'Error inserting :{routeName} , {e.msg}')
        
    except Exception as e:
        print(query)
        print(f'Error inserting :{routeName} , {e.msg}')
    finally:
        conn.commit() 
        conn.close()
        print('inserted for ', routeName)

# split 'INR 100' string and extract int
def extract_fare(s):
    splits = s.split(' ')
    if is_float(splits[len(splits)-1]):
        return float(splits[len(splits)-1])
    else:
        return 200

def extract_seats(s):
    splits = s.split(' ')
    if is_int(splits[0]):
        return int(splits[0])
    else:
        return 1 


#check whether string can be converted to float
def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

#check whether string is a number
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


if __name__=="__main__": 
    #Load driver and load home page
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.headless = True
    driver = webdriver.Chrome(options=chromeOptions)  

    #Load Page
    driver.get('https://www.redbus.in/');

    # Find URL for RTC directory and load the page in the same tab
    delaySecs = 10
    element_present = EC.presence_of_element_located((By.CLASS_NAME,'rtcHeadViewAll'))
    WebDriverWait(driver,delaySecs).until(element_present)
    viewAll = driver.find_element(By.CLASS_NAME,'rtcHeadViewAll')
    viewAllUrl = viewAll.find_element(By.TAG_NAME,'a')
    # print(viewAllUrl.get_attribute('href'))
    # print(viewAll.text)
    # print(driver.current_url)
    driver.get(viewAllUrl.get_attribute('href'))
    # print(driver.current_url)

    # Get URLs for RTCs which has routes... 
    # TNSTC doesn't have any routes, we can ignore them
    rtc_links_present = EC.presence_of_element_located((By.CLASS_NAME,'D113_ul_rtc'))
    WebDriverWait(driver,delaySecs).until(rtc_links_present)
    rtcList = driver.find_element(By.CLASS_NAME,'D113_ul_rtc')
    rtcLinks = rtcList.find_elements(By.CLASS_NAME,'D113_link')
    print(rtcLinks[0].text)

    # skip first 4 as they don't have any routes
    # TODO: right way to check is, load the page and check for routes list

    rtcURLs = []
    for link in rtcLinks[4:]:
        rtcURLs.append(link.get_attribute('href'))
    print(len(rtcURLs))
    driver.quit()     


    for link in rtcURLs:
        getRTCDetails(link)